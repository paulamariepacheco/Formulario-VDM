-- ============================================================================
-- Plano de Manutenção Predial — RPC de criação de condomínio
--
-- Corrige a falha "new row violates row-level security policy for table
-- condominios" ao criar o 1º condomínio. O INSERT direto dependia do
-- acoplamento frágil `criado_por DEFAULT auth.uid()` + `WITH CHECK
-- (criado_por = auth.uid())`. Esta função SECURITY DEFINER cria o condomínio
-- no servidor lendo auth.uid() diretamente (e falha com mensagem clara se a
-- sessão não estiver autenticada), deixando o trigger add_dono criar o vínculo.
-- ============================================================================

create or replace function manutencao.criar_condominio(p_nome text)
returns manutencao.condominios
language plpgsql
security definer
set search_path = manutencao, public
as $$
declare
  uid  uuid := auth.uid();
  nome text := btrim(coalesce(p_nome, ''));
  nova manutencao.condominios;
begin
  if uid is null then
    raise exception 'Sessão não autenticada: faça login novamente.'
      using errcode = '42501';
  end if;
  if nome = '' then
    raise exception 'Informe o nome do condomínio.';
  end if;

  insert into manutencao.condominios (nome, criado_por)
    values (nome, uid)
    returning * into nova;   -- trigger add_dono cria o membro 'dono'

  return nova;
end;
$$;

grant execute on function manutencao.criar_condominio(text) to authenticated;
