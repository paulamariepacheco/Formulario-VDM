# Sistema de Laudos — Paula Pacheco Engenharia e Perícias

> Este repositório hospeda **dois** projetos independentes da Paula:
> - **Sistema de Laudos** (este documento) — em `sistema_laudos/`.
> - **Formulário Viagem das Minas** (legado) — `index.html` na raiz. Não faz parte do sistema de laudos.

Sistema que **elimina a costura manual** de laudos de engenharia. Hoje o laudo é
montado em duas peças (capa/capítulos visuais no Canva + corpo técnico no Word) e
unido à mão, o que gera ausência de sumário, paginação quebrada, numeração de
figuras manual e PDFs pesados. Aqui os dados da vistoria são capturados de forma
**estruturada** e o laudo completo é **gerado automaticamente** como um único
`.docx`, com sumário, paginação, numeração de figuras e matrizes de risco
automáticos. O Canva passa a produzir **apenas ativos visuais** (capa,
infográficos) inseridos no documento gerado.

Autora: **Paula Marie Siqueira Pacheco** — Eng. Civil, Perita em Engenharia
Diagnóstica · CREA/MG 173201 · IBAPE/MG 1221.

---

## 0. Sistema de design (obrigatório antes de UI)

O padrão visual vem do projeto **"Paula Pacheco Design System"** no Claude Design
(paleta `#171f3d` / `#5e6161` / `#292929` / `#ffffff`, acento terracota `#BE7C4D`,
tipografia **Visia Pro** + **Montserrat**, logo double-P).

- Tokens sincronizados em `sistema_laudos/design/tokens.json` (cores, fontes,
  Grau de Risco GR1–GR3). O motor de geração lê deste arquivo — **nunca**
  hardcodar cores/fontes.
- Sempre que o design mudar no Claude Design, rodar **`/design-sync`** para
  reimportar. O design system já contém, inclusive, templates de cada seção do
  laudo e infográficos de metodologia prontos para o Canva.

## 0.1. Modelo e esforço

Projeto roda normalmente em **Opus 4.8 / esforço `high`**. Antes de qualquer
trecho com decisão de arquitetura relevante — e **obrigatoriamente antes da
Fase 3** (captura offline-first) — parar, explicar a complexidade e perguntar à
Paula se deseja trocar para **Claude Fable 5** e/ou subir o esforço para
`xhigh`/`max`.

---

## 1. Stack

| Camada | Escolha |
|---|---|
| Dados | **Supabase** (projeto `noknoebspmrbigwhyucn`, `sa-east-1`), **schema `laudos`** dedicado (convive com `combinados_paula.html`). |
| Captura | PWA — tela desktop (pós-vistoria) e mobile-first (campo, offline-first via IndexedDB + fila de sync). |
| Geração do documento | **Python** (`python-docx` + `Pillow`), rodado via Claude Code. Lê os dados e monta um `.docx` único a partir de um template-base. |
| Compressão de imagem | No pipeline (máx. 1600px, JPEG ~80%) — nunca etapa manual externa. |
| Fusão com Canva | Capa/infográficos exportados são inseridos automaticamente no documento (fusão de PDF), nunca à mão. |

---

## 2. Modelo de dados (schema `laudos`)

Tabelas: `laudos`, `ambientes`, `anomalias`, `fotos`, `capitulos_fixos`.
Migração versionada em `sistema_laudos/supabase/migrations/0001_schema_laudos.sql`
(já aplicada ao projeto).

**Regra crítica embutida no banco:** em `anomalias`, `gut` (= G×U×T) e
`faixa_prioridade` são **colunas geradas** (calculadas, nunca digitadas). As
mesmas regras existem no motor Python (`gerador/risco.py`) — DB e motor batem.

Faixas de prioridade sobre G×U×T (1–125), **calibradas pelas matrizes reais do
Laudo 50/2026 assinado**:
`Imediata ≥80 · Alta ≥40 · Média ≥20 · Programada ≥8 · Monitoramento <8`.
(Se o padrão oficial da Paula tiver cortes diferentes nos valores não
observados, ajustar em `gerador/risco.py`, migração `0004` e nos dois apps.)

---

## 3. Regras de negócio (padrão consolidado da Paula)

- Numeração sequencial "Laudo de Engenharia Nº XX/2026".
- Cabeçalho fixo com CREA/MG 173201 e IBAPE/MG 1221 em todo o corpo técnico.
- Estrutura fixa de capítulos: Pressupostos/Ressalvas → Motivação → Vistoria →
  Métodos e Procedimentos → Relatório Técnico (Diagnóstico por Sistema
  Construtivo) → Plano de Intervenção/Recuperação → Especificações e Aceite →
  Conclusões → Encerramento.
- Classificação IBAPE: GR1 (baixo/verde) · GR2 (médio/laranja) · GR3 (alto/vermelho).
- Matriz GUT qualitativa (Item / Grau IBAPE / Prazo) e quantificada
  (G, U, T, G×U×T, Faixa).
- **GR3 + risco a pessoas/bens ou estrutura ⇒ gera automaticamente** o parágrafo
  "Alerta de Responsabilidade Jurídico-Técnica" (Arts. 186, 927 e 1.348, V do CC).
- **Vício × falha de manutenção indeterminado ⇒ ressalva técnica automática.**
- Legenda de figura: `FIG. XX  [Ambiente]: [descrição objetiva]`.
- Voz impessoal em terceira pessoa ("recomenda-se", "a Perita", "constatou-se").
- Encerramento fixo: declaração de independência, aptidão para ART, contagem de
  páginas, bloco de credenciais.
- A **redação** de cada seção (campos estruturados → texto pericial corrido) segue
  a skill **`elaborador-de-laudo`** — o motor chama essa lógica, não a reinventa.

---

## 4. Fases

- **Fase 1 — Motor de geração (.docx).** ✅ Implementada (ver §5).
- **Fase 2 — Captura desktop.** ✅ Implementada (ver §5.1). App HTML+Supabase com
  login, RLS por dono, CRUD e fotos; motor lê do Supabase.
- **Fase 3 — Captura em campo (mobile, offline-first).** ✅ Implementada em
  **Claude Fable 5** após confirmação da Paula (ver §5.2). PWA `app/campo.html`
  com IndexedDB local-first, fila de sync idempotente e fotos offline.
- **Fase 4 — Extras.** Anotação de setas/círculos nas fotos; mapas-chave com pins.

---

## 5. Motor de geração (Fase 1) — como usar

```bash
cd sistema_laudos
pip install -r requirements.txt
python -m gerador.gerar_laudo dados/laudo_50_2026.json saida/Laudo-50-2026.docx
```

Saída: `sistema_laudos/saida/Laudo-50-2026.docx` (imagens comprimidas em `saida/img/`).

**Ao abrir no Word:** os campos são atualizados automaticamente; se o sumário não
preencher, selecionar tudo (Ctrl+A) e apertar **F9**.

### Estrutura do código (`sistema_laudos/gerador/`)

| Arquivo | Papel |
|---|---|
| `modelos.py` | Dataclasses `Laudo/Ambiente/Anomalia/Foto` (espelham o schema). |
| `fonte_dados.py` | Carrega de **JSON** (Fase 1) ou do **Supabase** (Fase 2, mesmo contrato). |
| `risco.py` | IBAPE + GUT + faixa + prazo + gatilhos de alerta/ressalva (calculados). |
| `textos.py` | Capítulos fixos, alerta jurídico, ressalva e encerramento (defaults). |
| `docx_util.py` | Sumário (TOC), paginação (PAGE/NUMPAGES), compressão de imagem, cores/fontes. |
| `gerar_laudo.py` | Orquestra a montagem do `.docx`. |

O motor consome apenas o objeto `Laudo`; trocar a fonte (JSON→Supabase) **não
altera o motor** — é a ponte para a Fase 2.

### Dados do Laudo 50/2026 — REAIS

`dados/laudo_50_2026.json` contém os **dados reais** do Laudo Nº 50/2026 —
Edifício Comercial Otoni (Av. do Contorno, 3772), extraídos do documento
assinado com ART MG20264991347: **13 anomalias** (2 GR3 com alerta jurídico:
peitoril da platibanda e corrosão das vigas de fachada), **9 ambientes** e as
**76 legendas** do relatório fotográfico (FIG. 08–83 do original). Os mesmos
dados estão semeados no Supabase. As **imagens** ainda são placeholders — subir
as fotos reais pelo app (Fase 2/3). Fotos **sem vínculo com anomalia** entram
no capítulo Vistoria como registro complementar.

### Critério de aceite (Fase 1) — atendido

Abrir o `.docx` no Word: sumário reflete os títulos reais; numeração de página
contínua do início ao fim; figuras na ordem e numeração corretas (FIG. 01→06).

### 5.0.1. Fidelidade visual — páginas renderizadas dos templates do design

Decisão da Paula: capítulos com template A4 no Claude Design ("Paula Pacheco
Design System") são inseridos no `.docx` como **página-imagem 300 dpi**
renderizada do próprio template com os dados do laudo — não mais texto nativo.
**Implementado** para capa e capítulos 2 (Motivação), 3 (Vistoria — híbrido:
página-template + continuação nativa 3.2 com ambientes/fotos avulsas),
4 (Métodos), 7 (Especificações), 9 (Referencial ilustrado) e 10 (Encerramento)
— `gerador/render_paginas.py` + `design/canva_templates/`:

```bash
pip install -r requirements-render.txt   # playwright (opcional)
# Chromium pré-instalado no ambiente (CHROMIUM_PATH=/opt/pw-browsers/chromium);
# NÃO rodar `playwright install`. Sem Chromium, o motor degrada para TODOS os
# capítulos nativos em texto (com aviso).
```

- Templates REAIS sincronizados (originais intocados `*.original.dc.html` +
  anotados gerados por `design/canva_templates/anotar_templates.py`); dados
  entram por `{{campo}}`, `{{{slot_raw}}}` e blocos `dc:variante:*`.
- Cores primárias via `var(--pp-*, #hex)` geradas de `design/tokens.json`;
  fontes reais espelhadas (Visia Pro, IBM Plex Mono) — nunca hardcodar no motor.
- Nº de página vivo nas páginas-imagem: slot do design medido no Chromium +
  caixa flutuante com campo `PAGE`; sumário ancorado por headings invisíveis;
  seções sem cabeçalho do Word nas páginas-template. Detalhes:
  `design/canva_templates/README.md` e `design/NOTES-templates.md`.
- Capítulos de tamanho variável (1, 5, 6, 8) permanecem nativos.

## 5.1. Captura desktop (Fase 2) — como usar

App HTML único em `sistema_laudos/app/index.html` (Supabase via CDN):

- Login por **link mágico** (Supabase Auth); acesso restrito por **RLS ao e-mail
  da proprietária** (migrações `0002`/`0003`).
- CRUD de laudo, ambientes e anomalias (com preview de G×U×T/faixa ao vivo) e
  upload de fotos ao bucket privado `laudos-fotos` (reduzidas a 1600px no cliente).
- Config única e deploy: ver `sistema_laudos/app/README.md` (Redirect URLs no
  Supabase, Exposed schemas = `laudos`, Netlify base `sistema_laudos`).

Geração a partir dos dados capturados (o motor da Fase 1 não muda, só a fonte):

```bash
cd sistema_laudos
pip install -r requirements.txt -r requirements-supabase.txt
export SUPABASE_URL="https://noknoebspmrbigwhyucn.supabase.co"
export SUPABASE_SERVICE_KEY="<service role key>"
python -m gerador.gerar_do_supabase "50/2026" "saida/Laudo-50-2026.docx"
```

`fonte_dados.carregar_do_supabase` e `gerar_do_supabase` fazem a ponte
(schema `laudos` + download das fotos do Storage).

## 5.2. Captura em campo (Fase 3) — como funciona

PWA mobile-first em `sistema_laudos/app/campo.html` (+ `sw.js`, `manifest.webmanifest`,
`icons/`), instalável na tela inicial. Feito para garagem/subsolo **sem sinal**:

- **Local-first:** toda gravação vai primeiro ao IndexedDB; rede é opcional.
- **IDs de cliente (UUID)** ⇒ FKs consistentes offline e **sync idempotente**
  (upsert por PK; reenvio não duplica). Exclusões viram *tombstones*.
- **Fila de sync:** flag `_dirty`; push em ordem pai→filho (laudo→ambiente→
  anomalia→foto; o **blob da foto sobe ao Storage antes da linha**), pull com
  LWW (registro sujo local prevalece até subir). Dispara ao voltar online,
  ao abrir o app e a cada 45s; selos "⟳ no aparelho / ✓ sincronizado" por item.
- **Fotos offline:** comprimidas no aparelho (1600px/JPEG 80%), blob guardado
  no IndexedDB até o upload; miniatura offline sai do blob local.
- Colunas geradas (`gut`, `faixa_prioridade`) e campos locais **nunca** vão no
  payload. Atualizações pós-sync **não** re-renderizam formulários (digitação
  em andamento nunca é perdida).
- 1º acesso exige internet (magic-link); depois o SW mantém a casca offline.

**Critério de aceite (modo avião) — atendido e versionado:**
`tests/test_campo_offline.py` roda o fluxo real no Chromium (Playwright):
captura offline → reload persiste → volta o sinal → tudo sobe 1x (idempotente).
Rodar: `pip install playwright pillow && python sistema_laudos/tests/test_campo_offline.py`.

---

## 6. O que evitar

- Texto fixo onde deveria haver campo estruturado (recria retrabalho manual).
- Deixar compressão de imagem para etapa manual externa (tem que estar no pipeline).
- Recriar a redação pericial do zero (reaproveitar `elaborador-de-laudo`).
- Hardcodar cores/fontes (puxar de `design/tokens.json` via `/design-sync`).

---

## 7. Próximos passos

1. Substituir a fixture pelos dados reais do Laudo 50/2026 e validar o `.docx`.
2. Fusão automática da capa/infográficos do Canva no documento gerado.
3. Wire do motor para ler `capitulos_fixos` do Supabase (hoje usa defaults).
4. Fase 2 (captura desktop) reutilizando `fonte_dados.carregar_do_supabase`.
