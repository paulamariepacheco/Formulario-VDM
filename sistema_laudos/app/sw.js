/* Service worker do app de campo (Fase 3).
   Papel único: manter a "casca" do app disponível offline
   (campo.html + manifest + ícones + supabase-js do CDN).
   NUNCA intercepta chamadas ao Supabase — dados são responsabilidade
   do IndexedDB/fila de sync do próprio app.

   v2: navegações são REDE-PRIMEIRO (atualizações do app chegam na hora;
   a cópia em cache só entra sem sinal). Assets estáticos seguem
   cache-primeiro com atualização silenciosa. */
const CACHE = "laudos-campo-v2";
const ASSETS = ["./campo.html", "./manifest.webmanifest", "./icons/icon-192.png", "./icons/icon-512.png"];
const CDN = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2";

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    // no-cache: nunca semear o cache offline com uma versão velha de CDN/HTTP
    await Promise.all(ASSETS.map((a) =>
      c.add(new Request(a, { cache: "no-cache" }))));
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

  // Navegação (abrir o app): rede primeiro — versão nova chega na hora;
  // sem sinal, cai na cópia guardada (essência do offline-first).
  if (e.request.mode === "navigate") {
    e.respondWith((async () => {
      try {
        const res = await fetch(e.request, { cache: "no-cache" });
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put("./campo.html", copy)).catch(() => {});
        }
        return res;
      } catch (_) {
        return (await caches.match("./campo.html")) || Response.error();
      }
    })());
    return;
  }

  // Demais assets: cache-primeiro com atualização silenciosa em paralelo.
  e.respondWith((async () => {
    const hit = await caches.match(e.request);
    const refresh = fetch(e.request, { cache: "no-cache" }).then((res) => {
      if (res && (res.ok || res.type === "opaque")) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy)).catch(() => {});
      }
      return res;
    }).catch(() => hit);
    return hit || refresh;
  })());
});
