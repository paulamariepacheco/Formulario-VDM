# Apps de captura (Fases 2 e 3)

| Arquivo | Uso |
|---|---|
| `index.html` | **Desktop (Fase 2)** — formulário completo pós-vistoria. |
| `campo.html` | **Campo (Fase 3)** — mobile, **funciona sem sinal** (PWA offline-first). |

Ambos usam o mesmo Supabase (schema `laudos`), login por **link mágico** e
acesso restrito por **RLS** ao e-mail da proprietária (migração `0003`).
Fotos vão ao bucket privado **`laudos-fotos`**, reduzidas a 1600px no aparelho.
Cores/fontes seguem os tokens da marca.

## Campo (offline) — o essencial

- Abra `campo.html` no celular **uma vez com internet** e faça login; adicione
  à tela inicial (PWA). Depois disso funciona em garagem/subsolo sem sinal.
- Tudo é salvo primeiro **no aparelho** (selo "⟳ no aparelho") e sobe sozinho
  quando há sinal (selo "✓ sincronizado"). O contador no topo mostra o que
  ainda não subiu; o botão **Sync** força o envio.
- Teste do modo avião automatizado: `../tests/test_campo_offline.py`.

## Configuração única no Supabase (Dashboard)

1. **Authentication → URL Configuration → Redirect URLs**: adicionar as URLs de onde
   os apps serão abertos (o `/*` cobre `index.html` e `campo.html`), ex.:
   - `http://localhost:8000/*` (teste local)
   - `https://SEU-SITE.netlify.app/*` (produção)
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
