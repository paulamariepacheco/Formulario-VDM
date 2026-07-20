# Plano de Manutenção Predial — app para condomínios

Aplicativo web (arquivo único `index.html`) para gestão da manutenção de
**condomínios residenciais ou comerciais**, com **login exclusivo por condomínio**
e dados na nuvem (Supabase), estruturado conforme:

- **ABNT NBR 5674:2024** — Gestão da manutenção de edificações;
- **ABNT NBR 14037:2024** — Manual de uso, operação e manutenção;
- **ABNT NBR 16747:2020** — Inspeção predial;
- Ebook **"Plano de Manutenção em Edificações — Guia Prático para Síndicos"**
  (Pacheco Engenharia e Perícias) e material sobre a dimensão jurídica do plano.

## Login e multi-condomínio (Supabase + RLS)

- **Acesso sem senha** por link mágico (Supabase Auth): o usuário informa o e-mail
  e recebe um link de acesso.
- **Isolamento por condomínio:** cada condomínio é um registro próprio; um usuário só
  enxerga os condomínios dos quais é membro. Garantido no banco por **Row Level Security**
  (schema `manutencao`), não apenas na interface.
- **Vários condomínios por conta:** a administradora/perita pode gerenciar quantos
  condomínios quiser e alternar entre eles pelo seletor no topo.
- **Convite por e-mail:** em *Edificação → Gerenciar acesso*, o responsável convida
  co-síndico, conselho ou administradora; o convite fica pendente até o primeiro acesso
  da pessoa (que o reivindica automaticamente ao logar com o mesmo e-mail).
## Controle de acesso e papéis (admin)

- **Acesso restrito por contrato:** só e-mails na *allowlist* (liberados por Paula) ou
  admins podem **criar/gerir um condomínio** (ser o principal). Quem entra sem liberação
  vê a tela "Acesso ainda não liberado" com o contato da Pacheco.
- **Papéis por condomínio:**
  - **principal (síndico)** — único por condomínio; acesso total. Sua **troca é feita
    apenas pela administração** (Paula), via painel Admin.
  - **zelador** — registra manutenções, OS, checklists e fotos; não altera o cadastro
    nem gerencia acesso.
  - **somente leitura** — consulta tudo (inclui relatório), sem editar.
- **Painel de Administração** (aba visível só para admin): liberar/suspender/remover
  e-mails da allowlist, ver todos os condomínios com o principal, transferir o principal
  e acompanhar a fila de e-mails. Admins iniciais: `pericias@pachecoeng.com.br` e
  `paula.mariesp@gmail.com` (tabela `manutencao.admins`).
- Papéis e allowlist são **impostos por RLS** (não só na interface): leitura não escreve,
  zelador não altera cadastro/acesso, e a criação exige autorização.

## Cadastro estendido

Além da capa técnica, o cadastro guarda: **e-mail para alertas**, **seguro predial**
(seguradora, apólice, vigência, coberturas), **contatos de emergência**, **elevadores**
(conservadora, quantidade, contrato, validade do RIA), **AVCB/CLCB** (nº, validade,
situação) e **contrato com a administradora**.

## Módulos

| Módulo | O que faz |
|---|---|
| **Painel do Síndico** | KPIs (pendências, cumprimento do programa, custos preventivo × corretivo, OS abertas, garantias a vencer), prioridades de ação e alerta de responsabilidade civil/penal quando há manutenção vencida. |
| **Edificação** | Cadastro/"capa técnica" do condomínio + gestão de acesso (convites). |
| **Inventário** | Sistemas e componentes com criticidade (1–3), normas e situação. |
| **Plano de Manutenção** | Programa por sistema: tipo, periodicidade, responsável, ART/RRT, método e critério de aceitação. |
| **Agenda** | Cronograma calculado (última execução + periodicidade); registro de execução gera OS automática. |
| **Ordens de Serviço** | Histórico de intervenções (origem, prioridade, executante, custos, vínculo com garantia) **com fotos anexadas**. |
| **Garantias** | Prazos da construtora/fornecedores com data-fim calculada e alerta em 90 dias. |
| **Inspeções e Laudos** | Registro das inspeções prediais (NBR 16747), vistorias e laudos, com ART **e fotos anexadas**. |
| **Checklist** | Roteiro de inspeção visual periódica; itens reprovados geram OS corretivas. |
| **Relatório** | Prestação de contas para assembleia, pronta para imprimir/PDF (com logo). |
| **Dados** | Exportação de backup JSON do condomínio. |

## Plano-modelo embutido

O botão **"Gerar plano-modelo (NBR 5674)"** carrega 12 sistemas e ~35 atividades com as
periodicidades usuais (reservatórios semestral, SPDA anual, revisão elétrica anual,
extintores mensal/anual, elevadores mensal, inspeção predial bienal, calhas trimestral,
bombas semestral etc.), prontos para ajustar ao manual da edificação.

## Identidade visual

Logo oficial **Pacheco Engenharia e Perícias** (`assets/logo-icone.png`,
`assets/logo-tagline.png`, extraídos dos arquivos vetoriais da marca) no login, no
cabeçalho e no relatório. Paleta e tipografia do **Paula Pacheco Design System**
(`sistema_laudos/design/tokens.json`): azul `#171f3d`, terracota `#BE7C4D`, Visia
Pro/Montserrat.

## Fotos (OS e inspeções)

- Anexo de fotos nas **Ordens de Serviço** e nas **Inspeções/laudos**, com **legenda** por foto.
- **Compressão no cliente** (máx. ~1600px, JPEG ~80%) antes do envio — sem etapa manual.
- Armazenadas em **bucket privado** `manutencao-fotos` no Supabase Storage, com caminho
  `{condominio_id}/{tipo}/{uuid}.jpg`. As miniaturas usam **URLs assinadas** temporárias.
- **RLS por condomínio no Storage:** só membros do condomínio (1º segmento do caminho)
  leem/enviam/excluem suas fotos. Excluir uma OS/inspeção remove as fotos do Storage.

## Banco de dados

- Schema **`manutencao`** no projeto Supabase `noknoebspmrbigwhyucn` (convive com `laudos`).
- Migrações versionadas (**já aplicadas**):
  - `supabase/migrations/0001_schema_manutencao.sql` — tabelas, RLS e funções;
  - `supabase/migrations/0002_storage_fotos.sql` — bucket privado + políticas de fotos;
  - `supabase/migrations/0003_criar_condominio_rpc.sql` — RPC `criar_condominio`
    (`security definer`) para criar o condomínio + vínculo de dono sem depender do
    `WITH CHECK` do INSERT direto (evita falha de RLS ao criar o 1º condomínio);
  - `supabase/migrations/0004_acesso_papeis_notificacoes.sql` — admins, allowlist
    (`acessos`), papéis (zelador/leitura) com RLS separando leitura×escrita, gate de
    autorização na criação, `transferir_principal` (admin), `proximo_numero_os` e a
    tabela `notificacoes` (fila de e-mails: novo principal e vencimentos).
- Tabelas: `condominios`, `membros` (vínculo usuário↔condomínio + convites) e `registros`
  (polimórfico: sistema | atividade | os | garantia | inspecao | checklist, em `jsonb`;
  fotos ficam como `[{path,legenda}]` dentro do `dados` da OS/inspeção).
- RLS: um usuário só acessa condomínios dos quais é membro; funções `eh_membro`,
  `eh_dono` e `reivindicar_convites` (todas `security definer` com `search_path` fixo).

### Configuração do Supabase (feito)

- Migrações `0001` e `0002` aplicadas.
- `manutencao` adicionado aos **Exposed schemas** do PostgREST.
- Bucket privado `manutencao-fotos` criado com RLS por condomínio.

### Configuração pendente (1 passo manual, ao publicar)

No painel do Supabase → **Authentication → URL Configuration**, incluir a **URL onde o
app for publicado** (Site URL e Redirect URLs) para o link mágico redirecionar de volta.
Ex.: `https://plano.pachecoeng.com.br` ou a URL do Netlify. Ao rodar localmente,
`http://localhost:...` também precisa constar.

## Como publicar (Netlify)

Site estático — `netlify.toml` já incluído nesta pasta. Passos:

1. No Netlify: **Add new site → Import an existing project** e conecte o repositório
   `paulamariepacheco/Formulario-VDM`.
2. Em **Site settings → Build & deploy → Build settings**, defina
   **Base directory = `plano_manutencao`** (o `netlify.toml` cuida do resto:
   publish = a própria pasta, sem build).
3. Após o deploy, copie a URL do site (ex.: `https://SEU-SITE.netlify.app`) e:
   - no **Supabase → Authentication → URL Configuration**, adicione essa URL em
     **Site URL** e **Redirect URLs** (para o link mágico de login voltar ao app).

Alternativas: arrastar a pasta `plano_manutencao/` em **app.netlify.com/drop**, ou
publicar em Vercel/GitHub Pages, ou abrir `index.html` localmente (nesse caso inclua
`http://localhost:PORTA` nos Redirect URLs do Supabase).

A chave usada no cliente é a **anon key** (pública por design); a proteção real dos
dados é a RLS.

## Evoluções previstas

- Fotos também no checklist e miniaturas embutidas no relatório impresso;
- Notificações de vencimento (e-mail/WhatsApp);
- Modo offline-first (fila de sync), como o app de campo dos laudos.
