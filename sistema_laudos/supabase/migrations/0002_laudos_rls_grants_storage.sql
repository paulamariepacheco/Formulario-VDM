-- ============================================================
-- Fase 2: acesso ao schema `laudos` para o app de captura.
-- Grants + RLS (política inicial permissiva; endurecida em 0003) +
-- bucket privado de fotos no Storage.
-- ============================================================

grant usage on schema laudos to authenticated, service_role;
grant all privileges on all tables in schema laudos to authenticated, service_role;
grant all privileges on all sequences in schema laudos to authenticated, service_role;
alter default privileges in schema laudos grant all on tables to authenticated, service_role;
alter default privileges in schema laudos grant all on sequences to authenticated, service_role;

do $$
declare t text;
begin
  foreach t in array array['laudos','ambientes','anomalias','fotos','capitulos_fixos']
  loop
    execute format('alter table laudos.%I enable row level security;', t);
    execute format('drop policy if exists %I on laudos.%I;', t||'_auth_all', t);
    execute format($p$create policy %I on laudos.%I
                      for all to authenticated using (true) with check (true);$p$,
                   t||'_auth_all', t);
  end loop;
end $$;

-- Storage: bucket privado de fotos
insert into storage.buckets (id, name, public)
values ('laudos-fotos', 'laudos-fotos', false)
on conflict (id) do nothing;

drop policy if exists laudos_fotos_auth_read on storage.objects;
create policy laudos_fotos_auth_read on storage.objects
  for select to authenticated using (bucket_id = 'laudos-fotos');
drop policy if exists laudos_fotos_auth_insert on storage.objects;
create policy laudos_fotos_auth_insert on storage.objects
  for insert to authenticated with check (bucket_id = 'laudos-fotos');
drop policy if exists laudos_fotos_auth_update on storage.objects;
create policy laudos_fotos_auth_update on storage.objects
  for update to authenticated using (bucket_id = 'laudos-fotos');
drop policy if exists laudos_fotos_auth_delete on storage.objects;
create policy laudos_fotos_auth_delete on storage.objects
  for delete to authenticated using (bucket_id = 'laudos-fotos');

-- Expor o schema `laudos` ao PostgREST (para o cliente JS consultá-lo).
-- Se a config gerenciada do Supabase sobrescrever, adicionar `laudos` em
-- Dashboard → Settings → API → Exposed schemas.
alter role authenticator set pgrst.db_schemas = 'public, storage, graphql_public, laudos';
notify pgrst, 'reload config';
