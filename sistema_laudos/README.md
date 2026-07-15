# Sistema de Laudos — `sistema_laudos/`

Motor de geração de Laudos de Engenharia (Fase 1) e infraestrutura de dados.
Visão geral e regras de negócio: ver `../CLAUDE.md`.

## Rodar o motor (Fase 1)

```bash
pip install -r requirements.txt
python -m gerador.gerar_laudo dados/laudo_50_2026.json saida/Laudo-50-2026.docx
```

Abrir `saida/Laudo-50-2026.docx` no Word (Ctrl+A + F9 se o sumário não preencher).

### Capa com fidelidade visual (template do Claude Design)

A capa é renderizada do template A4 do design system como página-imagem
PNG 300 dpi (2480×3508) e inserida full-bleed no `.docx`. Requer Playwright:

```bash
pip install -r requirements-render.txt
# Chromium já vem pré-instalado no ambiente (CHROMIUM_PATH, padrão
# /opt/pw-browsers/chromium) — NÃO rodar `playwright install`.
```

Sem foto de capa (`foto_capa` no JSON), o template usa o fundo `azul-marinho`;
com foto, `foto-com-overlay`. Sem Playwright/Chromium o motor avisa e degrada
para a capa nativa em texto. Detalhes/estado do espelho de templates:
`design/canva_templates/README.md`; mapeamento dos próximos capítulos:
`design/NOTES-templates.md`.

## Layout

```
design/tokens.json                 cores/fontes da marca (via /design-sync)
design/canva_templates/            espelho dos templates A4 do Claude Design
design/NOTES-templates.md          mapeamento template × capítulo (próximas fatias)
supabase/migrations/               schema `laudos` + RLS/storage (já aplicado)
gerador/                           motor .docx (python-docx + Pillow)
  gerar_laudo.py                   Fase 1: gera a partir de JSON
  gerar_do_supabase.py             Fase 2: gera lendo do Supabase (+fotos)
  render_paginas.py                páginas-template → PNG 300 dpi (Playwright)
app/                               Fase 2: captura desktop (index.html)
  campo.html + sw.js + manifest    Fase 3: captura em campo (PWA offline-first)
tests/test_campo_offline.py       critério de aceite da Fase 3 (modo avião, Chromium)
dados/laudo_50_2026.json           fixture: Laudo 50/2026 — Ed. Otoni
saida/                             saída gerada (.docx + img comprimidas)
ativos_canva/                      capa/infográficos exportados do Canva (fusão)
```

## Fase 2 — captura desktop

App em `app/index.html` (login + CRUD + fotos, ligado ao Supabase). Setup e deploy:
ver `app/README.md`.

## Dados

O mesmo fixture está semeado no Supabase (`schema laudos`, projeto
`noknoebspmrbigwhyucn`). Reaplicar/atualizar:

```sql
-- migração: supabase/migrations/0001_schema_laudos.sql
-- seed:      supabase/seed_laudo_50_2026.sql
```
