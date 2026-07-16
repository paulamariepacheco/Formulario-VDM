-- ============================================================
-- 0006 — Geração de documentos pelo app (sem linha de comando).
-- O botão "Gerar documento" do app desktop insere um pedido em
-- `laudos.geracoes`; um worker (GitHub Actions, rodando o motor
-- Python da Fase 1 sem alterações) atende a fila, monta o .docx,
-- converte o .pdf e sobe os arquivos ao bucket privado
-- `laudos-saida`; o app acompanha o status e baixa por URL assinada.
-- ============================================================

create table if not exists laudos.geracoes (
  id         uuid primary key default gen_random_uuid(),
  laudo_id   uuid not null references laudos.laudos(id) on delete cascade,
  formatos   text[] not null default '{docx,pdf}',
  status     text not null default 'pendente'
             check (status in ('pendente','processando','pronto','erro')),
  docx_path  text,          -- path no bucket laudos-saida
  pdf_path   text,
  erro       text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists geracoes_status_idx on laudos.geracoes (status, created_at);

drop trigger if exists geracoes_touch on laudos.geracoes;
create trigger geracoes_touch before update on laudos.geracoes
  for each row execute function laudos.touch_updated_at();

-- RLS: mesma trava de dona das demais tabelas (0003). O worker usa a
-- service role (ignora RLS) para processar e atualizar a fila.
alter table laudos.geracoes enable row level security;
do $$
declare owner_email constant text := 'paula.mariesp@gmail.com';
begin
  drop policy if exists geracoes_owner on laudos.geracoes;
  execute format($p$create policy geracoes_owner on laudos.geracoes
      for all to authenticated
      using ((auth.jwt() ->> 'email') = %L)
      with check ((auth.jwt() ->> 'email') = %L);$p$,
    owner_email, owner_email);
end $$;

-- Bucket privado dos documentos gerados. Só leitura para a dona
-- (download por URL assinada no app); escrita apenas pelo worker
-- (service role, sem política).
insert into storage.buckets (id, name, public)
values ('laudos-saida', 'laudos-saida', false)
on conflict (id) do nothing;

do $$
declare owner_email constant text := 'paula.mariesp@gmail.com';
begin
  drop policy if exists laudos_saida_owner_read on storage.objects;
  execute format($p$create policy laudos_saida_owner_read on storage.objects
      for select to authenticated
      using (bucket_id = 'laudos-saida' and (auth.jwt() ->> 'email') = %L);$p$,
    owner_email);
end $$;
