-- ============================================================
-- Sistema de Laudos — Paula Pacheco Engenharia e Perícias
-- Schema dedicado (convive com combinados_paula.html no mesmo projeto Supabase).
-- Projeto: noknoebspmrbigwhyucn (sa-east-1)
--
-- Regras de negócio embutidas no banco:
--   * G×U×T e a Faixa de Prioridade são COLUNAS GERADAS (calculadas,
--     nunca digitadas) — requisito da especificação.
--   * prazo_sugerido também é derivado quando não informado.
-- ============================================================

create schema if not exists laudos;
set search_path to laudos, public;

create extension if not exists "pgcrypto";

-- ---------- Enums ----------
do $$ begin
  create type laudos.tipo_laudo as enum
    ('condominial_nao_judicial','contratual_extrajudicial','unidade_correlacao','individual');
exception when duplicate_object then null; end $$;

do $$ begin
  create type laudos.status_laudo as enum
    ('em_vistoria','em_redacao','revisao','finalizado');
exception when duplicate_object then null; end $$;

do $$ begin
  create type laudos.status_anomalia as enum ('rascunho','revisado','aprovado');
exception when duplicate_object then null; end $$;

do $$ begin
  create type laudos.vicio_falha as enum
    ('vicio_construtivo','falha_manutencao','indeterminado');
exception when duplicate_object then null; end $$;

-- ---------- laudos ----------
create table if not exists laudos.laudos (
  id                uuid primary key default gen_random_uuid(),
  numero            text not null,                     -- ex.: "50/2026"
  tipo              laudos.tipo_laudo not null,
  cliente_nome      text,
  cliente_cnpj_cpf  text,
  endereco          text,
  data_emissao      date,
  status            laudos.status_laudo not null default 'em_vistoria',
  datas_diligencia  text[] default '{}',
  acompanhamento    text,                              -- ex.: "Síndico — Sr. Murilo"
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);
create unique index if not exists laudos_numero_uidx on laudos.laudos (numero);

-- ---------- ambientes ----------
create table if not exists laudos.ambientes (
  id         uuid primary key default gen_random_uuid(),
  laudo_id   uuid not null references laudos.laudos(id) on delete cascade,
  nome       text not null,                            -- ex.: "2º Subsolo", "Sala 404"
  pavimento  text,                                     -- ordenação no mapa-chave
  ordem      int not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists ambientes_laudo_idx on laudos.ambientes (laudo_id, ordem);

-- ---------- anomalias ----------
create table if not exists laudos.anomalias (
  id                       uuid primary key default gen_random_uuid(),
  laudo_id                 uuid not null references laudos.laudos(id) on delete cascade,
  ambiente_id              uuid references laudos.ambientes(id) on delete set null,
  ordem                    int  not null default 0,
  sistema_construtivo      text not null,              -- impermeabilização, estrutura, etc.
  titulo                   text not null,
  descricao_fenomenologica text,
  mecanismo                text,
  causa_provavel           text,
  consequencias            text,
  origem_taxonomia         text,                       -- exógena/adquirida/congênita/...
  vicio_ou_falha_manutencao laudos.vicio_falha default 'indeterminado',
  gr   int not null default 1 check (gr between 1 and 3),   -- IBAPE
  g    int not null default 1 check (g  between 1 and 5),   -- Gravidade
  u    int not null default 1 check (u  between 1 and 5),   -- Urgência
  t    int not null default 1 check (t  between 1 and 5),   -- Tendência

  -- G×U×T calculado automaticamente (coluna gerada, imutável)
  gut  int generated always as (g * u * t) stored,

  -- Faixa de prioridade calculada a partir de G×U×T (5 faixas sobre 1..125)
  faixa_prioridade text generated always as (
    case
      when g * u * t >= 100 then 'Imediata'
      when g * u * t >=  60 then 'Alta'
      when g * u * t >=  30 then 'Média'
      when g * u * t >=  10 then 'Programada'
      else 'Monitoramento'
    end
  ) stored,

  prazo_sugerido text,                                 -- calculado no motor se null
  alerta_juridico boolean not null default false,
  status laudos.status_anomalia not null default 'rascunho',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists anomalias_laudo_idx on laudos.anomalias (laudo_id, ordem);
create index if not exists anomalias_sistema_idx on laudos.anomalias (laudo_id, sistema_construtivo);

-- ---------- fotos ----------
create table if not exists laudos.fotos (
  id           uuid primary key default gen_random_uuid(),
  laudo_id     uuid not null references laudos.laudos(id) on delete cascade,
  anomalia_id  uuid references laudos.anomalias(id) on delete set null,
  ambiente_id  uuid references laudos.ambientes(id) on delete set null,
  arquivo_url  text,                                   -- Supabase Storage
  legenda      text,
  ordem        int not null default 0,                 -- define a numeração final da figura
  data_captura timestamptz,
  created_at   timestamptz not null default now()
);
create index if not exists fotos_laudo_idx on laudos.fotos (laudo_id, ordem);
create index if not exists fotos_anomalia_idx on laudos.fotos (anomalia_id);

-- ---------- capitulos_fixos ----------
-- Textos-padrão reutilizáveis e versionados (Pressupostos/Ressalvas, Motivação,
-- Métodos e Procedimentos, Referencial Técnico), com variação por tipo de laudo.
create table if not exists laudos.capitulos_fixos (
  id         uuid primary key default gen_random_uuid(),
  chave      text not null,                            -- ex.: 'pressupostos', 'metodos'
  titulo     text not null,
  corpo      text not null,
  tipo       laudos.tipo_laudo,                        -- null = vale para todos os tipos
  versao     int not null default 1,
  ativo      boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists capitulos_chave_idx on laudos.capitulos_fixos (chave, tipo, versao);

-- ---------- gatilho updated_at ----------
create or replace function laudos.touch_updated_at() returns trigger as $$
begin new.updated_at := now(); return new; end $$ language plpgsql;

drop trigger if exists trg_laudos_touch on laudos.laudos;
create trigger trg_laudos_touch before update on laudos.laudos
  for each row execute function laudos.touch_updated_at();

drop trigger if exists trg_anomalias_touch on laudos.anomalias;
create trigger trg_anomalias_touch before update on laudos.anomalias
  for each row execute function laudos.touch_updated_at();
