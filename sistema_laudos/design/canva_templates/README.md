# Espelho local dos templates do Claude Design

Espelho (parcial) do projeto **"Paula Pacheco Design System"** (Claude Design,
projectId `1429c6fb-e92f-4c44-a2bd-3c70304f9031`), com a **mesma estrutura de
paths** do projeto, para o render das páginas-imagem funcionar **sem rede**:

```
templates/<nome>/<Nome>.dc.html            template ANOTADO (o que o motor lê)
templates/<nome>/<Nome>.original.dc.html   original sincronizado, intocado
assets/{fonts,logos}/                      fontes e logos para o render
tokens/*.css, styles.css                   CSS real do design system (referência)
```

O pipeline (`gerador/render_paginas.py`) trata cada `.dc.html` como **markup
estático**: extrai o miolo da tag `x-dc`, descarta o runtime (`<script>`) e
resolve apenas os nós de dado, pelo contrato de anotação:

- `{{campo}}` — texto/atributo variável (valores escapados);
- par de comentários `dc:variante:NOME` … `/dc:variante:NOME` — blocos
  condicionais. Um template pode combinar variantes independentes: na capa,
  o fundo (`azul-marinho` × `foto-com-overlay`) e a moldura de foto
  (`foto-moldura`, ativa no fundo navy quando há foto).

Cores primárias da marca nos templates usam `var(--pp-*, #hex-original)` —
as CSS custom properties são geradas de `../tokens.json` e injetadas no
`<head>` na hora do render (`/design-sync` continua sendo a fonte da verdade).
Tons de escala que não existem em `tokens.json` (navy-200/300/900, rgba dos
gradientes) permanecem literais, fiéis ao markup sincronizado.

## Fluxo de re-sincronização

1. Baixar do Claude Design o `.dc.html` atualizado → salvar como
   `<Nome>.original.dc.html` (intocado).
2. Diffar contra o original anterior; reaplicar as anotações no
   `<Nome>.dc.html` (ver o cabeçalho de cada arquivo anotado).
3. Copiar assets novos/alterados mantendo os caminhos relativos do projeto.

## Estado atual

| Item | Estado |
|---|---|
| `templates/laudo-capa/LaudoCapa.dc.html` | ✅ **REAL anotado** — markup pixel-perfect do Claude Design com os nós de dado do contrato (`numero`, `nome_imovel`, `endereco`, `cliente_linha`, `emissao`, `perita_capa`, `credenciais_linha`, `foto_capa`) e as variantes `foto-com-overlay` / `foto-moldura`. Validado nas 3 combinações (navy, overlay, navy+moldura) a 300 dpi com as fontes reais. |
| `templates/laudo-capa/LaudoCapa.original.dc.html` | ✅ Original sincronizado, intocado (referência de re-sync; dados de exemplo do laudo 54/2026). |
| `assets/fonts/VisiaPro-*.otf` | ✅ Reais (comercial, licença da Paula) — 5 pesos usados nos laudos: ExtraLight 200, Light 300, Regular 400, SemiBold 600, Heavy 900. Itálicos/Bold/ExtraBold **não** espelhados (nenhum template de laudo os usa; copiar do projeto se um novo template precisar). |
| `assets/fonts/IBMPlexMono-*.ttf` | ✅ Regular/Medium/SemiBold (google/fonts, OFL — `OFL-IBMPlexMono.txt`). O `styles.css` do projeto a importa do Google Fonts; no render offline ela é servida daqui via `@font-face` gerado em `render_paginas.py`. |
| `assets/fonts/Montserrat-*.ttf` | ✅ Variável oficial (google/fonts, OFL — `OFL.txt`), fallback de corpo. |
| `assets/logos/` | ✅ `logo-tagline-branca.png`, `icone-branco.png`, `icone-principal.png` — PNGs reais do projeto. |
| `styles.css`, `tokens/*.css` | ✅ Espelhados como **referência** do design system. Atenção: os `@import` remotos (Google Fonts) do `styles.css` não funcionam offline — o render não consome esses arquivos diretamente; as fontes vêm dos `@font-face` locais. |
| Demais templates (`laudo-vistoria`, `laudo-metodos`, …) | Pendentes — trazer um a um pelo fluxo acima (mapeamento em `../NOTES-templates.md`). |
