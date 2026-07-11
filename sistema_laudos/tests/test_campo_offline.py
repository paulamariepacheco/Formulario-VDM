"""
Critério de aceite da Fase 3, executado de verdade no Chromium:

  1. abrir o app de campo logado (stub de auth);
  2. MODO AVIÃO (context offline): criar laudo + ambiente + anomalia GR3 com foto;
  3. recarregar ainda offline -> dados persistem (IndexedDB);
  4. sair do modo avião -> fila sincroniza sozinha;
  5. conferir no "servidor" (stub em memória fiel à API do supabase-js):
     laudo/ambiente/anomalia/foto upsertados 1x, blob da foto subiu ao Storage
     ANTES da linha, payloads sem colunas geradas (gut/faixa) nem campos locais,
     e um segundo sync não duplica nada (idempotência).

O stub substitui apenas o transporte (CDN supabase-js); todo o código do app —
IndexedDB, fila, tombstones, merge — roda inalterado.
"""
import os, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

APP_DIR = str(Path(__file__).resolve().parents[1] / "app")
PORT = 8077

# ---------------------------------------------------------------- stub CDN
STUB = r"""
window.__srv = { laudos:[], ambientes:[], anomalias:[], fotos:[], uploads:[], events:[],
                 payloads:{ laudos:[], ambientes:[], anomalias:[], fotos:[] } };
const offline = () => !navigator.onLine;
const NETERR = { message: "TypeError: Failed to fetch (stub offline)" };

function makeChain(name){
  const st = { filters:[], single:false };
  const chain = {
    select(){ return chain; },
    eq(c,v){ st.filters.push([c,v]); return chain; },
    order(){ return chain; },
    single(){ st.single=true; return chain; },
    then(res){
      if(offline()) return res({ data:null, error:NETERR });
      let rows = window.__srv[name].filter(r => st.filters.every(([c,v]) => r[c]===v));
      res({ data: st.single ? (rows[0]||null) : rows, error:null });
    }
  };
  return chain;
}
function table(name){
  return {
    select(){ return makeChain(name); },
    upsert: async rec => {
      if(offline()) return { error:NETERR };
      window.__srv.events.push(["upsert", name, rec.id]);
      window.__srv.payloads[name].push({ ...rec });
      const arr = window.__srv[name];
      const i = arr.findIndex(r => r.id === rec.id);
      if(i >= 0) arr[i] = { ...arr[i], ...rec };
      else arr.push({ ...rec, created_at: rec.created_at || new Date().toISOString() });
      return { error:null };
    },
    delete(){ return { eq: async (c,v) => {
      if(offline()) return { error:NETERR };
      window.__srv.events.push(["delete", name, v]);
      window.__srv[name] = window.__srv[name].filter(r => r[c] !== v);
      return { error:null };
    }}; }
  };
}
window.supabase = { createClient: () => ({
  auth: {
    getSession: async () => ({ data:{ session:{ user:{ email:"paula.mariesp@gmail.com" } } } }),
    onAuthStateChange: () => ({ data:{ subscription:{ unsubscribe(){} } } }),
    signInWithOtp: async () => ({ error:null }),
    signOut: async () => ({ error:null })
  },
  from: table,
  storage: { from: () => ({
    upload: async (path, blob, opts) => {
      if(offline()) return { error:NETERR };
      window.__srv.events.push(["upload", path]);
      window.__srv.uploads.push({ path, size: blob.size, upsert: !!(opts && opts.upsert) });
      return { data:{ path }, error:null };
    },
    remove: async () => ({ data:null, error:null }),
    createSignedUrl: async () => ({ data:null, error:{ message:"stub" } })
  })}
})};
"""

def make_test_jpeg(path):
    from PIL import Image
    Image.new("RGB", (2400, 1600), "#B23A32").save(path, "JPEG", quality=90)

def wait_badge(page, value, timeout=15000):
    page.wait_for_function(
        f"document.querySelector('#sync-badge').textContent === '{value}'", timeout=timeout)

def main():
    jpeg = Path(tempfile.gettempdir()) / "laudos_campo_foto_teste.jpg"
    make_test_jpeg(jpeg)
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "-d", APP_DIR],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    ok = True
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ.get("CHROMIUM_PATH", "/opt/pw-browsers/chromium") or None)
            # service worker bloqueado para o route() funcionar; as rotas abaixo
            # fazem o papel do SW (servir a casca offline): fulfill ignora o
            # estado offline do contexto, como o cache do SW ignoraria.
            ctx = browser.new_context(service_workers="block")
            ctx.route("**cdn.jsdelivr.net/**",
                      lambda r: r.fulfill(content_type="application/javascript", body=STUB))
            shell = Path(APP_DIR, "campo.html").read_text(encoding="utf-8")
            ctx.route("**/campo.html",
                      lambda r: r.fulfill(content_type="text/html; charset=utf-8", body=shell))
            ctx.route("**/manifest.webmanifest", lambda r: r.fulfill(status=204, body=""))
            page = ctx.new_page()
            page.on("console", lambda m: m.type == "error" and print("  [console.error]", m.text))
            page.goto(f"http://localhost:{PORT}/campo.html")
            page.wait_for_selector("#scr-laudos:not(.hidden), #scr-laudo:not(.hidden)", timeout=8000)
            print("1) app abriu logado (stub) ✓")

            # ---------- MODO AVIÃO ----------
            ctx.set_offline(True)
            page.wait_for_function("document.querySelector('#conn-lbl').textContent==='offline'")
            print("2) modo avião ativado ✓")

            page.fill("#nl-numero", "77/2026")
            page.fill("#nl-cliente", "Condomínio Teste Offline")
            page.click("text=Criar (funciona offline)")
            page.wait_for_selector("#scr-laudo:not(.hidden)")

            # ambiente
            page.click("nav.bottom button[data-pane=ambientes]")
            page.fill("#am-nome", "Subsolo Teste")
            page.click("text=Adicionar")
            page.wait_for_selector("text=Subsolo Teste")

            # anomalia GR3 com foto (a forma do critério de aceite)
            page.click("nav.bottom button[data-pane=anomalias]")
            # espera o painel re-renderizar com o ambiente novo no select
            page.wait_for_function("document.querySelectorAll('#an-amb option').length === 2")
            page.fill("#an-tit", "Trinca em viga (teste offline)")
            page.fill("#an-sis", "estrutura")
            page.select_option("#an-amb", index=1)
            page.click("#gr-3")
            page.select_option("#an-g", "5"); page.select_option("#an-u", "5"); page.select_option("#an-t", "4")
            page.set_input_files("#an-foto", str(jpeg))
            page.click("text=Registrar anomalia")
            page.wait_for_selector("text=Trinca em viga (teste offline)")
            wait_badge(page, "4")
            assert page.locator(".chip.pend").count() >= 1
            print("3) offline: laudo+ambiente+anomalia+foto salvos no aparelho (4 pendentes) ✓")

            # ---------- RELOAD AINDA OFFLINE (persistência IndexedDB) ----------
            page.reload()
            page.wait_for_selector("text=Trinca em viga (teste offline)", timeout=8000)
            wait_badge(page, "4")
            srv = page.evaluate("window.__srv")
            assert len(srv["laudos"]) == 0 and len(srv["uploads"]) == 0, "nada deveria ter subido offline"
            print("4) reload offline: dados persistem no IndexedDB, nada subiu ✓")

            # ---------- SAIR DO MODO AVIÃO ----------
            ctx.set_offline(False)
            page.evaluate("window.dispatchEvent(new Event('online'))")
            wait_badge(page, "0")
            page.wait_for_selector(".chip.sync")
            srv = page.evaluate("window.__srv")

            assert [len(srv[k]) for k in ("laudos","ambientes","anomalias","fotos")] == [1,1,1,1], srv
            lau, amb, ano, fot = srv["laudos"][0], srv["ambientes"][0], srv["anomalias"][0], srv["fotos"][0]
            assert lau["numero"] == "77/2026"
            assert amb["laudo_id"] == lau["id"] and ano["laudo_id"] == lau["id"] and fot["laudo_id"] == lau["id"]
            assert ano["ambiente_id"] == amb["id"] and fot["anomalia_id"] == ano["id"], "FKs offline consistentes"
            assert ano["gr"] == 3 and ano["g"] == 5 and ano["u"] == 5 and ano["t"] == 4
            assert ano["alerta_juridico"] is True, "GR3 deve acionar alerta jurídico"
            pay = srv["payloads"]["anomalias"][0]
            for k in ("gut","faixa_prioridade","_dirty","_deleted","_err","created_at","updated_at"):
                assert k not in pay, f"payload não pode conter '{k}'"
            print("5) sync automático: 4 registros no servidor, FKs íntegras, payload limpo ✓")

            # blob subiu ANTES da linha da foto, com upsert (idempotente)
            up = srv["uploads"][0]
            assert up["path"] == fot["arquivo_url"] and up["upsert"] is True
            ev = srv["events"]
            assert ev.index(["upload", up["path"]]) < ev.index(["upsert","fotos",fot["id"]]), "blob antes da linha"
            assert 0 < up["size"] < 400_000, f"foto deveria estar comprimida (~<400KB), veio {up['size']}"
            print(f"6) foto: blob comprimido ({up['size']//1024} KB) subiu antes da linha, upsert=true ✓")

            # ---------- IDEMPOTÊNCIA: forçar segundo sync ----------
            page.evaluate("app.syncNow()")
            page.wait_for_timeout(700)
            srv2 = page.evaluate("window.__srv")
            assert [len(srv2[k]) for k in ("laudos","ambientes","anomalias","fotos")] == [1,1,1,1]
            assert len(srv2["uploads"]) == 1, "reenvio não pode reupar blob já enviado"
            print("7) segundo sync: nenhuma duplicação (idempotente) ✓")

            browser.close()
    except Exception as e:
        ok = False
        print("FALHOU:", e)
        raise
    finally:
        server.terminate()
    print("\nCRITÉRIO DE ACEITE DA FASE 3: PASSOU" if ok else "")

if __name__ == "__main__":
    main()
