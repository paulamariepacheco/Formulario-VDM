-- ============================================================================
-- Plano de Manutenção Predial — alertas de vencimento (item 2)
--
-- Enfileira, uma vez por dia, um e-mail por condomínio listando manutenções e
-- garantias que vencem em 60 ou 30 dias, enviado ao e-mail cadastrado no
-- condomínio (dados->>'emailnotif', se 'notifativa' <> 'nao').
-- O envio em si é feito pela Edge Function que consome manutencao.notificacoes.
-- ============================================================================

create or replace function manutencao.gerar_alertas_vencimento()
returns integer
language plpgsql security definer
set search_path = manutencao, public
as $$
declare
  c      record;
  linhas text;
  chave  text;
  total  int := 0;
begin
  for c in
    select cd.id, cd.nome, cd.dados->>'emailnotif' as email
    from manutencao.condominios cd
    where coalesce(cd.dados->>'notifativa','sim') <> 'nao'
      and coalesce(cd.dados->>'emailnotif','') ~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$'
  loop
    with itens as (
      select 'Manutenção' as cat, r.dados->>'desc' as descr,
             (nullif(r.dados->>'ultimaExec','')::date
               + ((r.dados->>'periodicidade')::int) * interval '1 month')::date as venc
      from manutencao.registros r
      where r.condominio_id = c.id and r.tipo = 'atividade'
        and coalesce(r.dados->>'ativa','true') <> 'false'
        and nullif(r.dados->>'ultimaExec','')   is not null
        and nullif(r.dados->>'periodicidade','') is not null
      union all
      select 'Garantia',
             coalesce(r.dados->>'item','') ||
               case when coalesce(r.dados->>'desc','') <> '' then ' — ' || (r.dados->>'desc') else '' end,
             (nullif(r.dados->>'dataInicio','')::date
               + ((r.dados->>'prazoMeses')::int) * interval '1 month')::date
      from manutencao.registros r
      where r.condominio_id = c.id and r.tipo = 'garantia'
        and coalesce(r.dados->>'situacao','') <> 'Suspensa'
        and nullif(r.dados->>'dataInicio','') is not null
        and nullif(r.dados->>'prazoMeses','')  is not null
    ),
    devidos as (
      select cat, descr, venc, (venc - current_date) as dias
      from itens
      where (venc - current_date) in (30, 60)
    )
    select string_agg(
             '• [' || cat || '] ' || descr || ' — vence em ' || dias ||
             ' dias (' || to_char(venc,'DD/MM/YYYY') || ')',
             chr(10) order by venc)
      into linhas
    from devidos;

    if linhas is not null then
      chave := 'venc:' || c.id::text || ':' || current_date::text;
      if not exists (select 1 from manutencao.notificacoes
                     where tipo = 'vencimento' and dados->>'chave' = chave) then
        insert into manutencao.notificacoes(tipo, destino, assunto, corpo, dados)
        values ('vencimento', c.email,
          'Alertas de manutenção — ' || c.nome,
          'Itens do condomínio "' || c.nome || '" próximos do vencimento (60 e 30 dias):' ||
            chr(10) || chr(10) || linhas || chr(10) || chr(10) ||
            'Acesse o Plano de Manutenção para registrar as providências.' || chr(10) ||
            'Pacheco Engenharia e Perícias.',
          jsonb_build_object('chave', chave, 'condominio_id', c.id));
        total := total + 1;
      end if;
    end if;
  end loop;
  return total;
end;
$$;

-- Só a administração/cron deve gerar (não os usuários finais)
revoke execute on function manutencao.gerar_alertas_vencimento() from authenticated, anon;

-- Agendamento diário (08:00 BRT = 11:00 UTC), idempotente
do $$ begin
  perform cron.unschedule('manutencao-alertas-vencimento');
exception when others then null; end $$;
select cron.schedule('manutencao-alertas-vencimento', '0 11 * * *',
  $$select manutencao.gerar_alertas_vencimento();$$);
