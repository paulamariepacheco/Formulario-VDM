-- ============================================================
-- Fase 2 (segurança): trava o acesso ao dono.
-- Qualquer e-mail pode se autenticar via magic-link, então as políticas
-- não podem ser "sempre true" — exigem o e-mail da proprietária no JWT.
-- Para múltiplos usuários no futuro, trocar por uma tabela allowlist.
-- ============================================================

do $$
declare
  owner_email constant text := 'paula.mariesp@gmail.com';
  t text;
begin
  foreach t in array array['laudos','ambientes','anomalias','fotos','capitulos_fixos']
  loop
    execute format('drop policy if exists %I on laudos.%I;', t||'_auth_all', t);
    execute format($p$create policy %I on laudos.%I
        for all to authenticated
        using ((auth.jwt() ->> 'email') = %L)
        with check ((auth.jwt() ->> 'email') = %L);$p$,
      t||'_owner', t, owner_email, owner_email);
  end loop;

  drop policy if exists laudos_fotos_auth_read on storage.objects;
  drop policy if exists laudos_fotos_auth_insert on storage.objects;
  drop policy if exists laudos_fotos_auth_update on storage.objects;
  drop policy if exists laudos_fotos_auth_delete on storage.objects;

  execute format($p$create policy laudos_fotos_owner_read on storage.objects
      for select to authenticated
      using (bucket_id='laudos-fotos' and (auth.jwt() ->> 'email') = %L);$p$, owner_email);
  execute format($p$create policy laudos_fotos_owner_insert on storage.objects
      for insert to authenticated
      with check (bucket_id='laudos-fotos' and (auth.jwt() ->> 'email') = %L);$p$, owner_email);
  execute format($p$create policy laudos_fotos_owner_update on storage.objects
      for update to authenticated
      using (bucket_id='laudos-fotos' and (auth.jwt() ->> 'email') = %L);$p$, owner_email);
  execute format($p$create policy laudos_fotos_owner_delete on storage.objects
      for delete to authenticated
      using (bucket_id='laudos-fotos' and (auth.jwt() ->> 'email') = %L);$p$, owner_email);
end $$;

alter function laudos.touch_updated_at() set search_path = '';
