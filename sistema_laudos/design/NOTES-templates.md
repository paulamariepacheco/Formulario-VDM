# Mapeamento: templates do Claude Design × capítulos do motor

Levantamento para as próximas fatias da decisão de **fidelidade visual total**
(capa já implementada como prova de conceito — ver `gerador/render_paginas.py`).
Fonte: `list_files` do projeto "Paula Pacheco Design System"
(`1429c6fb-e92f-4c44-a2bd-3c70304f9031`). Os `.dc.html` são A4 794×1123 px,
markup estático com dados de exemplo do laudo 54/2026 (Ed. Jardins da Cidade);
`renderVals()` vazio em todos os inspecionados — única lógica real: prop
`fundo` da capa (`sc-if` azul-marinho × foto-com-overlay).

## Templates de capítulo (renderizar como página-imagem)

| Template | Capítulo / uso no motor (`gerar_laudo.py`) | Observações |
|---|---|---|
| `laudo-capa` | `_capa()` — **feito** | Variantes de fundo; foto de capa = `Laudo.foto_capa`. |
| `laudo-motivacao` | cap. 2 — **feito** (página-imagem) | `{{objetivos_p1/p2}}` com defaults do design. |
| `laudo-vistoria` | cap. 3 — **feito** (híbrido) | Página-template (mapa FIG. 01, fachada FIG. 02, características) + continuação nativa "3.2" (ambientes + fotos avulsas). Campos novos: `mapa_localizacao`, `foto_fachada`, `legenda_*`, `caracteristicas`. |
| `laudo-metodos` | cap. 4 — **feito** (página-imagem) | Normas via slot raw (`NORMAS_PADRAO`); dica de edição do design removida na anotação. |
| `laudo-especificacoes` | cap. 7 — **feito** (página-imagem) | Conteúdo fixo do padrão consolidado. |
| `laudo-referencial` | cap. 9 — **feito** (página-imagem) | É o referencial ilustrado de trincas/umidade (não a lista de normas — esta vive no cap. 4). FIG. dinâmicas após todas as fotos do laudo. |
| `laudo-encerramento` | cap. 10 — **feito** (página-imagem) | Frase de contagem referencia o rodapé (NUMPAGES não resolve dentro de imagem); assinatura digitalizada opcional (`Laudo.assinatura`, variante `com-assinatura`); local/data de `cidade_emissao` + `data_emissao`. |
| `laudo-fotografico` | relatório fotográfico (FIG. 08–83 no laudo 50/2026) | Quantidade de fotos é variável ⇒ template deve ser página-grade repetível (N páginas) ou manter fotos nativas. Avaliar no arquivo real. |
| `laudo-mapa-chave` | Fase 4 (mapas-chave com pins) | Fora do escopo atual. |
| `laudo-inspecao-predial` | abertura/infográfico NBR 16747 (?) | Confirmar lendo o arquivo — sem capítulo 1:1 hoje. |
| `laudo-plano-manutencao` | plano de manutenção (NBR 5674) | Sem capítulo correspondente hoje; possível anexo novo. |

## Infográficos por sistema construtivo (não são capítulos)

`caixas`, `jardineiras`, `lajes-execucao`, `lajes-impermeabilizacao`,
`piso-garagem`, `pisos-externos`, `recuperacao-fachada`, `rejunte-piso`,
`reparo-concreto`, `reservatorio`, `umidade-ascendente` — metodologias de
recuperação por sistema. Uso provável: páginas-imagem inseridas no cap. 6
(Plano de Intervenção) **condicionais aos sistemas presentes** nas anomalias
do laudo (`Anomalia.sistema_construtivo`). Exige tabela de correspondência
sistema→template (ex.: "impermeabilização e drenagem" → lajes-impermeabilizacao
/ jardineiras / reservatorio conforme ambiente).

## Continuam nativos (tamanho variável / campos do Word)

- Sumário (campo TOC), cap. 1 Pressupostos (avaliar se há template), cap. 5
  Diagnóstico (tabelas GUT por anomalia), cap. 6 Plano (tabela priorizada),
  cap. 8 Conclusões (quadros-resumo).
- `proposta-*` — outro documento (proposta comercial), fora de escopo.

## Avisos técnicos (estado após a fatia dos capítulos)

1. ~~Sumário/TOC~~ — resolvido: heading âncora invisível (1 pt branco) por
   capítulo-imagem (`GeradorLaudo._pagina_imagem`).
2. ~~docPr único~~ — resolvido: ids alocados por `part.next_id` (o mesmo
   alocador das figuras inline do python-docx).
3. ~~Batch de render~~ — resolvido: `render_paginas.SessaoRender` (1 launch de
   Chromium por laudo; mede os slots `data-dc-medir` para os overlays).
4. ~~Supabase~~ — resolvido: migração `0005_campos_paginas_template.sql`
   **aplicada** ao projeto (colunas `nome_imovel`, `foto_capa_url`,
   `capa_fundo`, `mapa_localizacao_url`, `legenda_mapa`, `foto_fachada_url`,
   `legenda_fachada`, `caracteristicas` jsonb, `cidade_emissao`,
   `assinatura_url`). Desktop (`index.html`): campos no formulário Dados +
   bloco "Imagens das páginas do laudo" (upload de capa/mapa/fachada/
   assinatura ao bucket privado). Campo (`campo.html`): nome do imóvel e
   características no formulário (sincronizam pelo upsert normal); fotos dos
   slots especiais ficam no desktop. `gerar_do_supabase` baixa as 4 imagens
   junto com as fotos.
5. **Nº de página vivo**: slot do design medido no render + caixa de texto
   flutuante com campo `PAGE` (`docx_util.inserir_numero_pagina_flutuante`).
   A fonte da caixa é "IBM Plex Mono" — instalar no computador que abre o
   Word para o visual idêntico (senão cai na fonte padrão, só na caixinha).
