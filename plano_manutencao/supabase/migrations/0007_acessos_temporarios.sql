-- ============================================================================
-- Plano de Manutenção Predial — acessos temporários (teste antes da assinatura)
--
-- A allowlist ganha `validade` (data de expiração; NULL = permanente).
--  - acesso_liberado(): só libera CRIAR/gerir condomínio se ativo e não vencido.
--  - condominio_liberado(): o condomínio fica "liberado" para EDIÇÃO enquanto o
--    principal (dono) for admin, OU não tiver restrição (legado, sem linha em
--    `acessos`), OU tiver acesso ativo e não vencido. Quando o teste vence, o
--    condomínio congela em somente-leitura até renovar/assinar.
--  - RLS de ESCRITA passa a exigir condominio_liberado (leitura permanece).
-- ============================================================================

alter table manutencao.acessos add column if not exists validade date;  -- NULL = permanente

-- Autorização para criar/gerir (considera a validade)
create or replace function manutencao.acesso_liberado(p_email text)
returns boolean language sql security definer stable
set search_path = manutencao, public as $$
  select exists(select 1 from manutencao.acessos
    where lower(email) = lower(coalesce(p_email,''))
      and status = 'ativo'
      and (validade is null or validade >= current_date));
$$;

-- Condomínio liberado para edição? (baseado no principal/dono)
create or replace function manutencao.condominio_liberado(cond uuid)
returns boolean language sql security definer stable
set search_path = manutencao, public as $$
  with dono as (
    select m.email from manutencao.membros m
    where m.condominio_id = cond and m.papel = 'dono' limit 1
  )
  select case
    when not exists (select 1 from dono) then true                                   -- sem principal: não bloqueia
    when exists (select 1 from manutencao.admins a, dono d where lower(a.email)=lower(d.email)) then true
    when not exists (select 1 from manutencao.acessos ac, dono d where lower(ac.email)=lower(d.email)) then true  -- legado / sem restrição
    else exists (select 1 from manutencao.acessos ac, dono d
      where lower(ac.email)=lower(d.email) and ac.status='ativo'
        and (ac.validade is null or ac.validade >= current_date))
  end;
$$;

-- Contexto do usuário: inclui validade/dias restantes do próprio acesso
drop function if exists manutencao.meu_contexto();
create or replace function manutencao.meu_contexto()
returns table(admin boolean, autorizado boolean, email text, validade date, dias_restantes integer)
language sql security definer stable
set search_path = manutencao, public as $$
  select
    manutencao.eh_admin(),
    manutencao.eh_admin() or manutencao.acesso_liberado(auth.jwt() ->> 'email'),
    auth.jwt() ->> 'email',
    (select ac.validade from manutencao.acessos ac where lower(ac.email)=lower(auth.jwt() ->> 'email')),
    (select (ac.validade - current_date) from manutencao.acessos ac where lower(ac.email)=lower(auth.jwt() ->> 'email'));
$$;

-- RLS de ESCRITA passa a exigir condomínio liberado (ou admin). Leitura inalterada.
drop policy if exists reg_ins on manutencao.registros;
create policy reg_ins on manutencao.registros for insert
  with check (manutencao.pode_editar(condominio_id)
              and (manutencao.condominio_liberado(condominio_id) or manutencao.eh_admin()));
drop policy if exists reg_upd on manutencao.registros;
create policy reg_upd on manutencao.registros for update
  using (manutencao.pode_editar(condominio_id))
  with check (manutencao.pode_editar(condominio_id)
              and (manutencao.condominio_liberado(condominio_id) or manutencao.eh_admin()));
drop policy if exists reg_del on manutencao.registros;
create policy reg_del on manutencao.registros for delete
  using ((manutencao.eh_dono(condominio_id) and manutencao.condominio_liberado(condominio_id)) or manutencao.eh_admin());

drop policy if exists cond_upd on manutencao.condominios;
create policy cond_upd on manutencao.condominios for update
  using (manutencao.eh_dono(id) or manutencao.eh_admin())
  with check ((manutencao.eh_dono(id) and manutencao.condominio_liberado(id)) or manutencao.eh_admin());

grant execute on all functions in schema manutencao to authenticated;
