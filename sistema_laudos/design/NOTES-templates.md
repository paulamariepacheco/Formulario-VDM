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
| `laudo-capa` | `_capa()` — **feito** (PoC) | Variantes de fundo; foto de capa = `Laudo.foto_capa`. |
| `laudo-motivacao` | cap. 2 — `_capitulo_fixo("motivacao")` | Texto fixo curto; 1 página. |
| `laudo-vistoria` | cap. 3 — `_vistoria()` | Tem image-slots (mapa, fachada); dados: datas, acompanhamento, ambientes. Fotos avulsas hoje entram aqui — ver `laudo-fotografico`. |
| `laudo-metodos` | cap. 4 — `_capitulo_fixo("metodos")` | Infográfico de metodologia. |
| `laudo-especificacoes` | cap. 7 — `_capitulo_fixo("especificacoes")` | |
| `laudo-referencial` | cap. 9 — `_capitulo_fixo("referencial")` | Normas ABNT/IBAPE. |
| `laudo-encerramento` | cap. 10 — `_encerramento()` | ATENÇÃO: contagem de páginas usa campo NUMPAGES do Word; como imagem, o número precisa ser resolvido ANTES do render (2 passadas) ou mantido nativo. Assinatura física também pesa a favor de manter parte nativa — decidir com a Paula. |
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

## Avisos técnicos para a próxima fatia

1. **Sumário/TOC**: capítulo virado imagem não gera entrada no TOC. Manter um
   heading nativo âncora (ex.: fonte 1pt branca, ou heading normal antes da
   página-imagem) para o TOC e a numeração continuarem corretos.
2. **Âncora full-bleed**: usar `docx_util.inserir_imagem_pagina_inteira`
   (wp:anchor relativo à página; id do `wp:docPr` precisa ser único por
   imagem — hoje fixo em 1001 porque só a capa usa; parametrizar ao inserir
   várias páginas-imagem).
3. **Pipeline**: 1 launch de Chromium por página é lento; ao renderizar vários
   capítulos, reutilizar o browser (refatorar `renderizar_pagina_png` para
   aceitar batch/context manager).
4. **Supabase**: `nome_imovel`, `foto_capa_url` e `capa_fundo` ainda não
   existem no schema `laudos` (o loader usa `.get()` e tolera a ausência);
   criar migração `0005` + campos nos dois apps quando a Paula validar a capa.
