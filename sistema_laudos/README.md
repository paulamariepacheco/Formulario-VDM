# Sistema de Laudos — `sistema_laudos/`

Motor de geração de Laudos de Engenharia (Fase 1) e infraestrutura de dados.
Visão geral e regras de negócio: ver `../CLAUDE.md`.

## Rodar o motor (Fase 1)

```bash
pip install -r requirements.txt
python -m gerador.gerar_laudo dados/laudo_50_2026.json saida/Laudo-50-2026.docx
```

Abrir `saida/Laudo-50-2026.docx` no Word (Ctrl+A + F9 se o sumário não preencher).

## Layout

```
design/tokens.json                 cores/fontes da marca (via /design-sync)
supabase/migrations/               schema `laudos` + RLS/storage (já aplicado)
gerador/                           motor .docx (python-docx + Pillow)
  gerar_laudo.py                   Fase 1: gera a partir de JSON
  gerar_do_supabase.py             Fase 2: gera lendo do Supabase (+fotos)
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
