-- ============================================================================
-- Plano de Manutenção Predial — Storage de fotos (OS e inspeções)
-- Bucket privado; acesso isolado por condomínio via RLS.
-- Convenção de caminho:  {condominio_id}/{tipo}/{uuid}.jpg
--   → o 1º segmento da pasta é o condomínio, usado pela política de acesso.
-- ============================================================================

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('manutencao-fotos', 'manutencao-fotos', false, 10485760,
        array['image/jpeg','image/png','image/webp'])
on conflict (id) do update
  set file_size_limit   = excluded.file_size_limit,
      allowed_mime_types = excluded.allowed_mime_types;

-- Políticas em storage.objects: só membros do condomínio (1º segmento do caminho)
-- podem ler/enviar/atualizar/excluir os arquivos daquele condomínio.
drop policy if exists manut_fotos_sel on storage.objects;
create policy manut_fotos_sel on storage.objects for select to authenticated
  using (bucket_id = 'manutencao-fotos'
         and manutencao.eh_membro(((storage.foldername(name))[1])::uuid));

drop policy if exists manut_fotos_ins on storage.objects;
create policy manut_fotos_ins on storage.objects for insert to authenticated
  with check (bucket_id = 'manutencao-fotos'
              and manutencao.eh_membro(((storage.foldername(name))[1])::uuid));

drop policy if exists manut_fotos_upd on storage.objects;
create policy manut_fotos_upd on storage.objects for update to authenticated
  using (bucket_id = 'manutencao-fotos'
         and manutencao.eh_membro(((storage.foldername(name))[1])::uuid));

drop policy if exists manut_fotos_del on storage.objects;
create policy manut_fotos_del on storage.objects for delete to authenticated
  using (bucket_id = 'manutencao-fotos'
         and manutencao.eh_membro(((storage.foldername(name))[1])::uuid));
