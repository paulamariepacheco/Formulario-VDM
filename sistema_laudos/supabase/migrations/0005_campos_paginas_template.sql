-- 0005 — Campos das páginas-template (capa, vistoria, encerramento)
-- Suporte às páginas-imagem renderizadas do design (CLAUDE.md §5.0.1):
--   * capa: nome de exibição do imóvel, foto de capa e variante de fundo;
--   * vistoria: mapa de localização, foto da fachada, legendas e a lista de
--     características gerais do imóvel;
--   * encerramento: cidade de emissão e assinatura digitalizada (opcional).
-- Colunas *_url guardam o PATH no bucket privado `laudos-fotos` (mesmo
-- contrato de fotos.arquivo_url); o gerador baixa na hora de montar o .docx.

alter table laudos.laudos
  add column if not exists nome_imovel          text,
  add column if not exists foto_capa_url        text,
  add column if not exists capa_fundo           text
    check (capa_fundo in ('', 'azul-marinho', 'foto-com-overlay')
           or capa_fundo is null),
  add column if not exists mapa_localizacao_url text,
  add column if not exists legenda_mapa         text,
  add column if not exists foto_fachada_url     text,
  add column if not exists legenda_fachada      text,
  -- [{"rotulo": "Torres / blocos", "valor": "01 torre"}, ...]
  add column if not exists caracteristicas      jsonb not null default '[]'::jsonb,
  add column if not exists cidade_emissao       text,
  add column if not exists assinatura_url       text;

comment on column laudos.laudos.nome_imovel is
  'Nome de exibição do imóvel na capa (ex.: "Edifício Comercial Otoni"); vazio => usa cliente_nome';
comment on column laudos.laudos.capa_fundo is
  'Variante do template da capa; vazio/null = automático pela foto de capa';
comment on column laudos.laudos.caracteristicas is
  'Características gerais do imóvel (página Vistoria): array de {rotulo, valor}';
