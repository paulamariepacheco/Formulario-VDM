"""
Worker da fila de geração de documentos (`laudos.geracoes`).

O botão "Gerar documento" do app desktop insere um pedido na fila; este
worker (rodando no GitHub Actions — ver .github/workflows/gerar-laudo.yml)
atende os pedidos pendentes:

  1. monta o .docx com o motor da Fase 1 (`gerar_do_supabase`, inalterado);
  2. converte para .pdf com LibreOffice headless (fontes da marca instaladas
     pelo workflow a partir de design/canva_templates/assets/fonts);
  3. sobe os arquivos ao bucket privado `laudos-saida`;
  4. atualiza o status do pedido (pronto/erro) — o app acompanha e oferece
     o download por URL assinada.

Uso (exige service role key — apenas em ambiente de confiança):
    export SUPABASE_URL=...  SUPABASE_SERVICE_KEY=...
    python -m gerador.worker_fila
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from .gerar_do_supabase import _cliente, gerar_do_supabase

BUCKET_SAIDA = "laudos-saida"
CT_DOCX = ("application/vnd.openxmlformats-officedocument"
           ".wordprocessingml.document")


def _converter_pdf(docx: Path) -> Path:
    """Converte o .docx em .pdf com LibreOffice headless.

    O perfil de usuário isolado evita conflitos entre execuções; os campos
    (PAGE/NUMPAGES/TOC) são atualizados na importação porque o motor grava
    `w:updateFields` no documento.
    """
    perfil = tempfile.mkdtemp(prefix="lo-perfil-")
    subprocess.run(
        ["soffice", "--headless", "--norestore", "--nologo",
         f"-env:UserInstallation=file://{perfil}",
         "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
        check=True, timeout=600, capture_output=True, text=True)
    pdf = docx.with_suffix(".pdf")
    if not pdf.exists():
        raise RuntimeError("LibreOffice terminou sem produzir o PDF")
    return pdf


def processar_fila() -> int:
    client = _cliente()
    db = client.schema("laudos")
    pendentes = (db.table("geracoes").select("*").eq("status", "pendente")
                 .order("created_at").execute().data)
    if not pendentes:
        print("fila vazia.")
        return 0

    storage = client.storage.from_(BUCKET_SAIDA)
    falhas = 0
    for ped in pendentes:
        gid = ped["id"]
        db.table("geracoes").update({"status": "processando"}).eq("id", gid).execute()
        try:
            laudo_row = (db.table("laudos").select("numero")
                         .eq("id", ped["laudo_id"]).single().execute().data)
            numero = laudo_row["numero"]
            nome = f"Laudo-{numero.replace('/', '-')}"
            destino = Path(tempfile.mkdtemp(prefix="geracao-")) / f"{nome}.docx"
            print(f"[{gid}] gerando {nome} ...")
            docx = Path(gerar_do_supabase(numero, destino))

            atualiza: dict = {"status": "pronto", "erro": None}
            formatos = ped.get("formatos") or ["docx", "pdf"]
            if "docx" in formatos:
                caminho = f"{ped['laudo_id']}/{gid}/{nome}.docx"
                storage.upload(caminho, docx.read_bytes(),
                               {"content-type": CT_DOCX, "upsert": "true"})
                atualiza["docx_path"] = caminho
            if "pdf" in formatos:
                pdf = _converter_pdf(docx)
                caminho = f"{ped['laudo_id']}/{gid}/{nome}.pdf"
                storage.upload(caminho, pdf.read_bytes(),
                               {"content-type": "application/pdf",
                                "upsert": "true"})
                atualiza["pdf_path"] = caminho

            db.table("geracoes").update(atualiza).eq("id", gid).execute()
            print(f"[{gid}] pronto.")
        except Exception as exc:  # noqa: BLE001 — fila não pode morrer
            falhas += 1
            detalhe = str(exc)
            if isinstance(exc, subprocess.CalledProcessError):
                detalhe += f"\n{exc.stderr or exc.stdout or ''}"
            traceback.print_exc()
            db.table("geracoes").update(
                {"status": "erro", "erro": detalhe[:2000]}).eq("id", gid).execute()
    return falhas


if __name__ == "__main__":
    sys.exit(1 if processar_fila() else 0)
