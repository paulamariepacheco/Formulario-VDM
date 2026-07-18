-- ============================================================================
-- Plano de Manutenção Predial — schema `manutencao`
-- Multi-condomínio com login exclusivo (Supabase Auth) e isolamento por RLS.
-- Convive com o schema `laudos` no mesmo projeto (noknoebspmrbigwhyucn).
--
-- Modelo:
--   condominios  — 1 linha por condomínio (a "capa técnica" + nº sequencial de OS)
--   membros      — vínculo usuário↔condomínio; convite por e-mail antes do 1º login
--   registros    — polimórfico (sistema|atividade|os|garantia|inspecao|checklist),
--                  cada linha guarda o objeto do app em `dados` (jsonb)
--
-- Isolamento: um usuário só enxerga condomínios dos quais é membro. Convidar por
-- e-mail cria um membro com user_id nulo; no 1º acesso o próprio usuário reivindica
-- o convite (associa seu auth.uid ao e-mail) via RPC `reivindicar_convites()`.
-- ============================================================================

create schema if not exists manutencao;

-- ----------------------------------------------------------------------------
-- Tabelas
-- ----------------------------------------------------------------------------
create table if not exists manutencao.condominios (
  id          uuid primary key default gen_random_uuid(),
  nome        text not null,
  dados       jsonb not null default '{}'::jsonb,   -- cadastro da edificação
  seq_os      integer not null default 0,           -- contador de OS (OS-AAAA-NNN)
  criado_por  uuid not null default auth.uid() references auth.users(id) on delete set null,
  criado_em   timestamptz not null default now()
);

create table if not exists manutencao.membros (
  id            uuid primary key default gen_random_uuid(),
  condominio_id uuid not null references manutencao.condominios(id) on delete cascade,
  user_id       uuid references auth.users(id) on delete cascade,   -- nulo até o convidado logar
  email         text not null,
  papel         text not null default 'sindico',                    -- 'dono' | 'sindico'
  criado_em     timestamptz not null default now()
);
create unique index if not exists membros_cond_email_uidx on manutencao.membros(condominio_id, lower(email));
create index if not exists membros_user_idx on manutencao.membros(user_id);

create table if not exists manutencao.registros (
  id            uuid primary key default gen_random_uuid(),
  condominio_id uuid not null references manutencao.condominios(id) on delete cascade,
  tipo          text not null check (tipo in ('sistema','atividade','os','garantia','inspecao','checklist')),
  dados         jsonb not null default '{}'::jsonb,
  atualizado_em timestamptz not null default now()
);
create index if not exists registros_cond_tipo_idx on manutencao.registros(condominio_id, tipo);

-- ----------------------------------------------------------------------------
-- Funções auxiliares (security definer — rodam com os privilégios do dono)
-- ----------------------------------------------------------------------------

-- É membro do condomínio? (evita recursão de RLS ao consultar `membros`)
create or replace function manutencao.eh_membro(cond uuid)
returns boolean
language sql security definer stable
set search_path = manutencao, public
as $$
  select exists (
    select 1 from manutencao.membros m
    where m.condominio_id = cond and m.user_id = auth.uid()
  );
$$;

-- É dono do condomínio?
create or replace function manutencao.eh_dono(cond uuid)
returns boolean
language sql security definer stable
set search_path = manutencao, public
as $$
  select exists (
    select 1 from manutencao.membros m
    where m.condominio_id = cond and m.user_id = auth.uid() and m.papel = 'dono'
  );
$$;

-- Reivindica convites pendentes: associa o e-mail do usuário logado aos membros
-- que foram criados por convite (user_id nulo). Chamar logo após o login.
create or replace function manutencao.reivindicar_convites()
returns integer
language plpgsql security definer
set search_path = manutencao, public
as $$
declare afetados integer;
begin
  update manutencao.membros
     set user_id = auth.uid()
   where user_id is null
     and lower(email) = lower(coalesce(auth.jwt() ->> 'email', ''));
  get diagnostics afetados = row_count;
  return afetados;
end;
$$;

-- Ao criar um condomínio, o criador vira 'dono' automaticamente.
create or replace function manutencao.add_dono()
returns trigger
language plpgsql security definer
set search_path = manutencao, public
as $$
begin
  insert into manutencao.membros (condominio_id, user_id, email, papel)
  values (new.id, auth.uid(), coalesce(auth.jwt() ->> 'email', ''), 'dono')
  on conflict (condominio_id, lower(email)) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_add_dono on manutencao.condominios;
create trigger trg_add_dono
  after insert on manutencao.condominios
  for each row execute function manutencao.add_dono();

-- ----------------------------------------------------------------------------
-- Row Level Security
-- ----------------------------------------------------------------------------
alter table manutencao.condominios enable row level security;
alter table manutencao.membros     enable row level security;
alter table manutencao.registros   enable row level security;

-- condominios
drop policy if exists cond_sel on manutencao.condominios;
create policy cond_sel on manutencao.condominios for select
  using (manutencao.eh_membro(id));
drop policy if exists cond_ins on manutencao.condominios;
create policy cond_ins on manutencao.condominios for insert
  with check (criado_por = auth.uid());
drop policy if exists cond_upd on manutencao.condominios;
create policy cond_upd on manutencao.condominios for update
  using (manutencao.eh_membro(id)) with check (manutencao.eh_membro(id));
drop policy if exists cond_del on manutencao.condominios;
create policy cond_del on manutencao.condominios for delete
  using (manutencao.eh_dono(id));

-- membros (um membro enxerga e gerencia os membros dos seus condomínios;
-- exclusão de 'dono' é bloqueada para não deixar o condomínio órfão)
drop policy if exists memb_sel on manutencao.membros;
create policy memb_sel on manutencao.membros for select
  using (manutencao.eh_membro(condominio_id));
drop policy if exists memb_ins on manutencao.membros;
create policy memb_ins on manutencao.membros for insert
  with check (manutencao.eh_membro(condominio_id) and papel <> 'dono');
drop policy if exists memb_del on manutencao.membros;
create policy memb_del on manutencao.membros for delete
  using (manutencao.eh_membro(condominio_id) and papel <> 'dono');

-- registros
drop policy if exists reg_all on manutencao.registros;
create policy reg_all on manutencao.registros for all
  using (manutencao.eh_membro(condominio_id))
  with check (manutencao.eh_membro(condominio_id));

-- ----------------------------------------------------------------------------
-- Grants para o papel autenticado (PostgREST)
-- ----------------------------------------------------------------------------
grant usage on schema manutencao to authenticated;
grant select, insert, update, delete on all tables in schema manutencao to authenticated;
grant execute on all functions in schema manutencao to authenticated;
alter default privileges in schema manutencao grant select, insert, update, delete on tables to authenticated;
alter default privileges in schema manutencao grant execute on functions to authenticated;

-- IMPORTANTE (fazer no painel do Supabase, uma vez):
--   Settings → API → Exposed schemas: acrescentar `manutencao`
--   Authentication → URL Configuration: incluir a URL do app em Redirect URLs
