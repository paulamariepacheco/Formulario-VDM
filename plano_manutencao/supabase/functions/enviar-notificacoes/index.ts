// Edge Function: enviar-notificacoes
// Consome a fila manutencao.notificacoes e envia os e-mails pendentes via Resend.
// Cobre: item 5 (aviso de novo condomínio à Pacheco) e item 2 (alertas de vencimento).
//
// Segredos (Supabase → Edge Functions → Secrets):
//   RESEND_API_KEY  (obrigatório para enviar; sem ele a função apenas "pula")
//   REMETENTE       (opcional; default "Pacheco Engenharia e Perícias <pericias@pachecoeng.com.br>")
//   NOTIFY_SECRET   (opcional; se definido, exige header x-notify-secret igual)
// SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são injetados automaticamente.

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  // trava opcional por segredo compartilhado (cron envia o header)
  const segredo = Deno.env.get("NOTIFY_SECRET");
  if (segredo && req.headers.get("x-notify-secret") !== segredo) {
    return json({ error: "não autorizado" }, 401);
  }

  const RESEND = Deno.env.get("RESEND_API_KEY");
  if (!RESEND) {
    // ainda não configurado — deixa a fila intacta para envio posterior
    return json({ skipped: true, motivo: "RESEND_API_KEY não configurada" });
  }
  const remetente = Deno.env.get("REMETENTE") ||
    "Pacheco Engenharia e Perícias <pericias@pachecoeng.com.br>";

  const supa = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
    { db: { schema: "manutencao" }, auth: { persistSession: false } },
  );

  const { data: pendentes, error } = await supa
    .from("notificacoes")
    .select("id, destino, assunto, corpo")
    .is("enviado_em", null)
    .order("criado_em", { ascending: true })
    .limit(100);
  if (error) return json({ error: error.message }, 500);

  let enviados = 0, falhas = 0;
  for (const n of pendentes ?? []) {
    try {
      const r = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { "Authorization": `Bearer ${RESEND}`, "Content-Type": "application/json" },
        body: JSON.stringify({ from: remetente, to: [n.destino], subject: n.assunto, text: n.corpo }),
      });
      if (r.ok) {
        await supa.from("notificacoes")
          .update({ enviado_em: new Date().toISOString(), erro: null }).eq("id", n.id);
        enviados++;
      } else {
        const t = await r.text();
        await supa.from("notificacoes").update({ erro: t.slice(0, 500) }).eq("id", n.id);
        falhas++;
      }
    } catch (e) {
      await supa.from("notificacoes").update({ erro: String(e).slice(0, 500) }).eq("id", n.id);
      falhas++;
    }
  }
  return json({ enviados, falhas, pendentes: (pendentes ?? []).length });
});
