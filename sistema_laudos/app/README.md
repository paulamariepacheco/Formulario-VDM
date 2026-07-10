# App de captura desktop (Fase 2)

Formulário web (HTML único + Supabase) para lançar laudo, ambientes, anomalias e
fotos. Depois o motor da Fase 1 gera o `.docx` lendo direto do Supabase.

- Login por **link mágico** (e-mail) — Supabase Auth.
- Acesso restrito por **RLS** ao e-mail da proprietária (migração `0003`).
- Fotos vão para o bucket privado **`laudos-fotos`** (reduzidas a 1600px antes do upload).
- Cores/fontes seguem os tokens da marca.

## Configuração única no Supabase (Dashboard)

1. **Authentication → URL Configuration → Redirect URLs**: adicionar as URLs de onde
   o app será aberto, ex.:
   - `http://localhost:8000` (teste local)
   - `https://SEU-SITE.netlify.app` (produção)
2. **Settings → API → Exposed schemas**: confirmar que **`laudos`** está na lista
   (a migração `0002` já tenta habilitar via SQL; isto é o fallback pelo painel).
3. O e-mail com acesso é `paula.mariesp@gmail.com` (definido na migração `0003`).
   Para trocar/adicionar, editar a política ou migrar para uma tabela allowlist.

## Rodar localmente

O login por link mágico precisa de `http://` (não `file://`):

```bash
cd sistema_laudos/app
python -m http.server 8000
# abrir http://localhost:8000
```

## Publicar no Netlify

Novo site a partir do repositório, com:
- **Base directory:** `sistema_laudos`
- **Publish directory:** `app` (já no `netlify.toml`)
- Sem comando de build.

Depois, adicionar a URL do Netlify nas Redirect URLs (passo 1).

## Gerar o documento a partir do que foi capturado

```bash
cd sistema_laudos
pip install -r requirements.txt -r requirements-supabase.txt
export SUPABASE_URL="https://noknoebspmrbigwhyucn.supabase.co"
export SUPABASE_SERVICE_KEY="<service role key>"   # máquina de confiança
python -m gerador.gerar_do_supabase "51/2026" "saida/Laudo-51-2026.docx"
```
