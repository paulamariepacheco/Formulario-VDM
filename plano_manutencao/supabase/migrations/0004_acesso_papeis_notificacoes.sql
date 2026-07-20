-- ============================================================================
-- Plano de Manutenção Predial — controle de acesso, papéis e fila de notificações
--
-- Requisitos:
--  (3) Papéis: além do principal (dono), 'zelador' (edita operacional) e
--      'leitura' (somente leitura). 1 principal por condomínio; troca de
--      principal só pela administração (Paula).
--  (4) Só quem foi liberado por Paula (allowlist) ou admin pode CRIAR condomínio.
--  (5) Ao criar um condomínio (novo principal), enfileira e-mail para a Pacheco.
--  (2) Fila de notificações também usada pelos alertas de vencimento (60/30 dias).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Administração (Paula)
-- ----------------------------------------------------------------------------
create table if not exists manutencao.admins (
  email     text primary key,
  criado_em timestamptz not null default now()
);
insert into manutencao.admins(email) values
  ('pericias@pachecoeng.com.br'), ('paula.mariesp@gmail.com')
on conflict (email) do nothing;

create or replace function manutencao.eh_admin()
returns boolean language sql security definer stable
set search_path = manutencao, public as $$
  select exists(select 1 from manutencao.admins a
    where lower(a.email) = lower(coalesce(auth.jwt() ->> 'email','')));
$$;

-- ----------------------------------------------------------------------------
-- Allowlist de acesso (quem contratou pode criar/gerir condomínio)
-- ----------------------------------------------------------------------------
create table if not exists manutencao.acessos (
  email        text primary key,
  status       text not null default 'ativo' check (status in ('ativo','suspenso')),
  observacao   text,
  liberado_por text,
  liberado_em  timestamptz not null default now(),
  atualizado_em timestamptz not null default now()
);

create or replace function manutencao.acesso_liberado(p_email text)
returns boolean language sql security definer stable
set search_path = manutencao, public as $$
  select exists(select 1 from manutencao.acessos
    where lower(email) = lower(coalesce(p_email,'')) and status = 'ativo');
$$;

-- Contexto do usuário logado (o app decide a tela a partir daqui)
create or replace function manutencao.meu_contexto()
returns table(admin boolean, autorizado boolean, email text)
language sql security definer stable
set search_path = manutencao, public as $$
  select manutencao.eh_admin(),
         manutencao.eh_admin() or manutencao.acesso_liberado(auth.jwt() ->> 'email'),
         auth.jwt() ->> 'email';
$$;

-- ----------------------------------------------------------------------------
-- Papéis: capacidade de edição (dono/sindico/zelador editam; leitura só lê)
-- ----------------------------------------------------------------------------
create or replace function manutencao.pode_editar(cond uuid)
returns boolean language sql security definer stable
set search_path = manutencao, public as $$
  select exists(select 1 from manutencao.membros m
    where m.condominio_id = cond and m.user_id = auth.uid()
      and m.papel in ('dono','sindico','zelador'));
$$;

-- ----------------------------------------------------------------------------
-- Fila de notificações (itens 5 e 2) — enviada por Edge Function/cron
-- ----------------------------------------------------------------------------
create table if not exists manutencao.notificacoes (
  id         uuid primary key default gen_random_uuid(),
  tipo       text not null,                -- 'novo_principal' | 'vencimento'
  destino    text not null,
  assunto    text not null,
  corpo      text not null,
  dados      jsonb not null default '{}'::jsonb,
  criado_em  timestamptz not null default now(),
  enviado_em timestamptz,
  erro       text
);
create index if not exists notificacoes_pendentes_idx
  on manutencao.notificacoes(criado_em) where enviado_em is null;
-- evita duplicar o mesmo alerta de vencimento no mesmo dia
create unique index if not exists notificacoes_dedup_idx
  on manutencao.notificacoes((dados->>'chave'))
  where tipo = 'vencimento' and dados ? 'chave';

-- ----------------------------------------------------------------------------
-- Criação de condomínio com gate de autorização (item 4) + aviso (item 5)
-- ----------------------------------------------------------------------------
create or replace function manutencao.criar_condominio(p_nome text)
returns manutencao.condominios
language plpgsql security definer
set search_path = manutencao, public as $$
declare
  uid  uuid := auth.uid();
  mail text := auth.jwt() ->> 'email';
  nome text := btrim(coalesce(p_nome, ''));
  nova manutencao.condominios;
begin
  if uid is null then
    raise exception 'Sessão não autenticada: faça login novamente.' using errcode = '42501';
  end if;
  if not (manutencao.eh_admin() or manutencao.acesso_liberado(mail)) then
    raise exception 'Acesso não liberado. Contate a Pacheco Engenharia e Perícias para contratar o acesso.'
      using errcode = '42501';
  end if;
  if nome = '' then
    raise exception 'Informe o nome do condomínio.';
  end if;

  insert into manutencao.condominios (nome, criado_por) values (nome, uid) returning * into nova;

  -- item 5: avisa a Pacheco sobre novo usuário principal
  insert into manutencao.notificacoes(tipo, destino, assunto, corpo, dados)
  values ('novo_principal', 'pericias@pachecoeng.com.br',
    'Novo condomínio cadastrado: ' || nome,
    'Um novo usuário principal cadastrou um condomínio no sistema.' || chr(10) ||
    'Condomínio: ' || nome || chr(10) ||
    'E-mail do principal: ' || coalesce(mail, '(desconhecido)') || chr(10) ||
    'Data/hora: ' || to_char(now(), 'DD/MM/YYYY HH24:MI'),
    jsonb_build_object('condominio_id', nova.id, 'nome', nome, 'email', mail));

  return nova;
end;
$$;

-- ----------------------------------------------------------------------------
-- Numeração de OS via RPC (permite zelador numerar sem UPDATE direto em condominios)
-- ----------------------------------------------------------------------------
create or replace function manutencao.proximo_numero_os(p_cond uuid)
returns text language plpgsql security definer
set search_path = manutencao, public as $$
declare n integer;
begin
  if not manutencao.pode_editar(p_cond) then
    raise exception 'Sem permissão para editar este condomínio.' using errcode = '42501';
  end if;
  update manutencao.condominios set seq_os = seq_os + 1 where id = p_cond returning seq_os into n;
  return 'OS-' || to_char(now(),'YYYY') || '-' || lpad(n::text, 3, '0');
end;
$$;

-- ----------------------------------------------------------------------------
-- Troca de principal — somente administração (item 3)
-- ----------------------------------------------------------------------------
create or replace function manutencao.transferir_principal(p_cond uuid, p_email text)
returns void language plpgsql security definer
set search_path = manutencao, public as $$
declare mail text := lower(btrim(coalesce(p_email,'')));
begin
  if not manutencao.eh_admin() then
    raise exception 'Apenas a administração pode transferir o principal.' using errcode = '42501';
  end if;
  if mail = '' then raise exception 'Informe o e-mail do novo principal.'; end if;

  update manutencao.membros set papel = 'sindico'
    where condominio_id = p_cond and papel = 'dono';
  insert into manutencao.membros(condominio_id, user_id, email, papel)
    values (p_cond, null, mail, 'dono')
    on conflict (condominio_id, lower(email)) do update set papel = 'dono', user_id = coalesce(manutencao.membros.user_id, excluded.user_id);
end;
$$;

-- admin: lista todos os condomínios com o principal
create or replace function manutencao.admin_listar_condominios()
returns table(id uuid, nome text, criado_em timestamptz, principal_email text, membros_qtd bigint)
language sql security definer stable
set search_path = manutencao, public as $$
  select c.id, c.nome, c.criado_em,
         (select m.email from manutencao.membros m where m.condominio_id = c.id and m.papel = 'dono' limit 1),
         (select count(*) from manutencao.membros m where m.condominio_id = c.id)
  from manutencao.condominios c
  where manutencao.eh_admin()
  order by c.criado_em desc;
$$;

-- ----------------------------------------------------------------------------
-- RLS — papéis
-- ----------------------------------------------------------------------------
-- registros: leitura para membros; escrita só quem pode_editar; exclusão só dono/admin
drop policy if exists reg_all on manutencao.registros;
drop policy if exists reg_sel on manutencao.registros;
create policy reg_sel on manutencao.registros for select
  using (manutencao.eh_membro(condominio_id) or manutencao.eh_admin());
drop policy if exists reg_ins on manutencao.registros;
create policy reg_ins on manutencao.registros for insert
  with check (manutencao.pode_editar(condominio_id));
drop policy if exists reg_upd on manutencao.registros;
create policy reg_upd on manutencao.registros for update
  using (manutencao.pode_editar(condominio_id)) with check (manutencao.pode_editar(condominio_id));
drop policy if exists reg_del on manutencao.registros;
create policy reg_del on manutencao.registros for delete
  using (manutencao.eh_dono(condominio_id) or manutencao.eh_admin());

-- condominios: admin também lê; alterar/excluir só dono/admin
drop policy if exists cond_sel on manutencao.condominios;
create policy cond_sel on manutencao.condominios for select
  using (manutencao.eh_membro(id) or manutencao.eh_admin());
drop policy if exists cond_upd on manutencao.condominios;
create policy cond_upd on manutencao.condominios for update
  using (manutencao.eh_dono(id) or manutencao.eh_admin()) with check (manutencao.eh_dono(id) or manutencao.eh_admin());
drop policy if exists cond_del on manutencao.condominios;
create policy cond_del on manutencao.condominios for delete
  using (manutencao.eh_dono(id) or manutencao.eh_admin());

-- membros: convite só dono/admin, nunca papel 'dono'; exclusão nunca do 'dono'
drop policy if exists memb_sel on manutencao.membros;
create policy memb_sel on manutencao.membros for select
  using (manutencao.eh_membro(condominio_id) or manutencao.eh_admin());
drop policy if exists memb_ins on manutencao.membros;
create policy memb_ins on manutencao.membros for insert
  with check ((manutencao.eh_dono(condominio_id) or manutencao.eh_admin()) and papel in ('zelador','leitura','sindico'));
drop policy if exists memb_del on manutencao.membros;
create policy memb_del on manutencao.membros for delete
  using ((manutencao.eh_dono(condominio_id) or manutencao.eh_admin()) and papel <> 'dono');
drop policy if exists memb_upd on manutencao.membros;
create policy memb_upd on manutencao.membros for update
  using (manutencao.eh_admin()) with check (manutencao.eh_admin());

-- allowlist / admins / notificacoes: gerenciados pela administração
alter table manutencao.acessos      enable row level security;
alter table manutencao.admins       enable row level security;
alter table manutencao.notificacoes enable row level security;

drop policy if exists acessos_admin on manutencao.acessos;
create policy acessos_admin on manutencao.acessos for all
  using (manutencao.eh_admin()) with check (manutencao.eh_admin());
drop policy if exists admins_sel on manutencao.admins;
create policy admins_sel on manutencao.admins for select using (manutencao.eh_admin());
drop policy if exists notif_admin on manutencao.notificacoes;
create policy notif_admin on manutencao.notificacoes for select using (manutencao.eh_admin());

-- ----------------------------------------------------------------------------
-- Grants
-- ----------------------------------------------------------------------------
grant select, insert, update, delete on manutencao.acessos to authenticated;
grant select on manutencao.admins to authenticated;
grant select on manutencao.notificacoes to authenticated;
grant execute on all functions in schema manutencao to authenticated;
