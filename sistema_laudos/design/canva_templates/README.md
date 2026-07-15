# Espelho local dos templates do Claude Design

Espelho (parcial) do projeto **"Paula Pacheco Design System"** (Claude Design,
projectId `1429c6fb-e92f-4c44-a2bd-3c70304f9031`), com a **mesma estrutura de
paths** do projeto, para o render das páginas-imagem funcionar **sem rede**:

```
templates/<nome>/<Nome>.dc.html   páginas A4 (794×1123 px) por capítulo
assets/fonts/                     fontes para o render (ver abaixo)
```

O pipeline (`gerador/render_paginas.py`) trata cada `.dc.html` como **markup
estático**: extrai o miolo da tag `x-dc`, descarta o runtime (`<script>`) e
resolve apenas os nós de dado, pelo contrato de anotação:

- `{{campo}}` — texto/atributo variável (valores escapados);
- par de comentários `dc:variante:NOME` … `/dc:variante:NOME` — blocos
  condicionais (usado no único `sc-if` real do design: o fundo da capa,
  `azul-marinho` × `foto-com-overlay`).

Cores/fontes **não** ficam nos templates nem no Python: viram CSS custom
properties `--pp-*` geradas de `../tokens.json` e injetadas no `<head>` na
hora do render (`/design-sync` continua sendo a fonte da verdade).

## Estado atual

| Item | Estado |
|---|---|
| `templates/laudo-capa/LaudoCapa.dc.html` | **PROVISÓRIO** — reproduz estrutura/lógica (variantes de fundo) com os tokens, mas NÃO é o markup pixel-perfect do Claude Design. Substituir pelo original sincronizado + anotar os nós de dado (instruções no cabeçalho do próprio arquivo). |
| `assets/fonts/Montserrat-*.ttf` | Oficiais (google/fonts, licença OFL — `OFL.txt`). |
| `assets/fonts/VisiaPro-*.{woff2,otf}` | **AUSENTES** (fonte comercial). Copiar dos assets do projeto Claude Design; até lá o render usa o fallback de `tokens.json` (Helvetica Neue/Arial). Os `@font-face` já apontam para esses caminhos — basta o drop-in. |
| Logo double-P (`assets/`) | AUSENTE — o provisório usa um monograma CSS. Copiar do Claude Design junto com o template real. |
| `styles.css`, `tokens/*.css` do projeto | Ainda não espelhados — trazer junto com cada template que os referencie. |
