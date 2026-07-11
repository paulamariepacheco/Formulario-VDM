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

**Configuração única** (não precisa repetir depois):

1. Instalar o [Python](https://www.python.org/downloads/) no computador (marcar
   "Add python.exe to PATH" no instalador do Windows).
2. Baixar o código deste repositório (Code → Download ZIP no GitHub, ou `git clone`).
3. Abrir o terminal/PowerShell na pasta `sistema_laudos` e rodar:
   ```bash
   pip install -r requirements.txt -r requirements-supabase.txt
   ```
4. Copiar `sistema_laudos/.env.example` para `sistema_laudos/.env` e colar a
   **service role key** (Supabase → Settings → API → service_role key — é
   secreta, nunca compartilhar nem subir ao Git; o `.env` já está no `.gitignore`).

**Uso do dia a dia** — depois da configuração acima, é só:
- **Windows:** dar duplo clique em `Gerar Laudo.bat` (dentro de `sistema_laudos/`).
- **Mac:** dar duplo clique em `Gerar Laudo.command`.
- Digite o número do laudo (ex.: `52/2026`) e aperte Enter. O `.docx` sai em
  `sistema_laudos/saida/`, com as fotos reais do Storage já embutidas.

Prefere linha de comando? O atalho acima só chama:
```bash
cd sistema_laudos
python gerar.py "51/2026"
```
