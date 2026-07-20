-- ============================================================================
-- Plano de Manutenção Predial — agendamento do envio de e-mails
--
-- Aciona a Edge Function `enviar-notificacoes`, que consome a fila
-- manutencao.notificacoes e envia via Resend. Roda 5 min após a geração
-- dos alertas de vencimento (migração 0005). Enquanto a RESEND_API_KEY não
-- estiver configurada, a função apenas "pula" e a fila aguarda.
--
-- Requer pg_net e pg_cron (já instalados). A chave usada aqui é a anon key
-- (pública por design); a função roda com verify_jwt=false.
-- ============================================================================

do $$ begin
  perform cron.unschedule('manutencao-enviar-emails');
exception when others then null; end $$;

select cron.schedule('manutencao-enviar-emails', '5 11 * * *', $cron$
  select net.http_post(
    url := 'https://noknoebspmrbigwhyucn.supabase.co/functions/v1/enviar-notificacoes',
    headers := jsonb_build_object(
      'Content-Type','application/json',
      'Authorization','Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5va25vZWJzcG1yYmlnd2h5dWNuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU4MzA2ODMsImV4cCI6MjA5MTQwNjY4M30.N4ClwgCEZaKPd4RpwsBdCb-qsDS5RS6iUsNjQalhKko'),
    body := '{}'::jsonb);
$cron$);

-- Também dispara o envio logo após o gatilho de novo condomínio (item 5):
-- a fila é esvaziada no próximo ciclo do cron; para envio imediato, a Edge
-- Function pode ser chamada sob demanda. Mantemos o ciclo diário simples.
