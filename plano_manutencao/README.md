# Plano de Manutenção Predial — app para condomínios

Aplicativo web completo (arquivo único, `index.html`) para gestão da manutenção de
**condomínios residenciais ou comerciais**, estruturado conforme:

- **ABNT NBR 5674:2024** — Gestão da manutenção de edificações (inventário, programa,
  planejamento, controle de processos, documentação e indicadores);
- **ABNT NBR 14037:2024** — Manual de uso, operação e manutenção;
- **ABNT NBR 16747:2020** — Inspeção predial;
- Ebook **"Plano de Manutenção em Edificações — Guia Prático para Síndicos"**
  (Pacheco Engenharia e Perícias) e material sobre a dimensão jurídica do plano.

## Módulos

| Módulo | O que faz |
|---|---|
| **Painel do Síndico** | KPIs (pendências, cumprimento do programa, custos preventivo × corretivo, OS abertas), prioridades de ação, alerta de responsabilidade civil/penal quando há manutenção vencida e deveres do síndico (NBR 5674). |
| **Edificação** | Cadastro/"capa técnica" do condomínio (uso residencial/comercial/misto, responsáveis, RT, versão do plano, documentação de base). |
| **Inventário** | Sistemas e componentes com criticidade (1–3), normas de referência e situação. |
| **Plano de Manutenção** | Programa de atividades por sistema: tipo, periodicidade, responsável, exigência de ART/RRT, método e critério de aceitação. |
| **Agenda** | Cronograma calculado (última execução + periodicidade), status Em dia / Vence em 30 dias / Vencida, registro de execução com geração automática de OS. |
| **Ordens de Serviço** | Histórico completo de intervenções (origem, prioridade, executante, custos, vínculo com garantia) — a rastreabilidade exigida pela NBR 5674. |
| **Garantias** | Prazos da construtora/fornecedores com data-fim calculada e alerta de vencimento em 90 dias; vínculo com OS do período. |
| **Inspeções e Laudos** | Registro das inspeções prediais (NBR 16747), vistorias e laudos, com ART e recomendações; tabela de quando contratar perícia especializada. |
| **Checklist** | Roteiro de inspeção visual periódica (16 itens típicos); itens reprovados geram OS corretivas automaticamente. |
| **Relatório** | Prestação de contas consolidada para assembleia, pronta para imprimir/salvar em PDF. |
| **Dados** | Exportação/importação de backup JSON e reset. |

## Plano-modelo embutido

O botão **"Gerar plano-modelo (NBR 5674)"** carrega 12 sistemas e ~35 atividades com as
periodicidades usuais (limpeza de reservatórios semestral, SPDA anual, revisão elétrica
anual, extintores mensal/anual, elevadores mensal, inspeção predial bienal, calhas
trimestral, bombas semestral etc.), prontos para o síndico remover o que não se aplica e
ajustar frequências ao manual da edificação.

## Como usar

É um arquivo único, sem servidor nem dependências: basta abrir
`plano_manutencao/index.html` no navegador (ou publicar em qualquer hosting estático,
ex.: Netlify — mesmo padrão do `sistema_laudos/app`).

Os dados ficam no `localStorage` do navegador do usuário (local-first). Para trocar de
dispositivo ou manter cópia de segurança, usar **Dados → Exportar/Importar JSON**.

## Design

Paleta e tipografia do **Paula Pacheco Design System** (`sistema_laudos/design/tokens.json`):
azul `#171f3d`, chumbo `#292929`, cinza `#5e6161`, terracota `#BE7C4D`, Visia Pro/Montserrat.
Se o design mudar no Claude Design, rodar `/design-sync` e refletir os valores no bloco
`:root` do `index.html`.

## Evoluções previstas

- Sincronização multiusuário via Supabase (mesmo padrão da Fase 2/3 do sistema de laudos);
- Fotos anexadas às OS e checklists;
- Notificações (e-mail/WhatsApp) de vencimentos.
