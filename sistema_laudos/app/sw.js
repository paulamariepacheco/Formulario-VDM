/* Service worker do app de campo (Fase 3).
   Papel único: manter a "casca" do app disponível offline
   (campo.html + manifest + ícones + supabase-js do CDN).
   NUNCA intercepta chamadas ao Supabase — dados são responsabilidade
   do IndexedDB/fila de sync do próprio app. */
const CACHE = "laudos-campo-v1";
const ASSETS = ["./campo.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png"];
const CDN = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await c.addAll(ASSETS);
    // cross-origin: no-cors (resposta opaca serve para <script src>)
    try { await c.add(new Request(CDN, { mode: "no-cors" })); } catch (_) {}
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;
  if (url.hostname.endsWith("supabase.co")) return;          // API/Storage: sempre rede

  e.respondWith((async () => {
    const hit = await caches.match(e.request, { ignoreSearch: e.request.mode === "navigate" });
    // cache-first para a casca; em paralelo, atualiza silenciosamente
    const refresh = fetch(e.request).then((res) => {
      if (res && (res.ok || res.type === "opaque")) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      }
      return res;
    }).catch(() => hit);
    return hit || refresh;
  })());
});
