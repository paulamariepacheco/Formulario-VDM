"""
Ponte Fase 2: gera o .docx lendo os dados diretamente do Supabase.

O motor (Fase 1) não muda — apenas troca-se a fonte de dados. Este módulo:
  1. cria um cliente supabase-py a partir de variáveis de ambiente;
  2. carrega o laudo pelo número (schema `laudos`);
  3. baixa as fotos do Storage (bucket `laudos-fotos`) para um diretório local;
  4. chama o mesmo `GeradorLaudo` da Fase 1.

Uso:
    export SUPABASE_URL="https://noknoebspmrbigwhyucn.supabase.co"
    export SUPABASE_SERVICE_KEY="<service_role key>"   # roda no computador da Paula
    python -m gerador.gerar_do_supabase 50/2026 saida/Laudo-50-2026.docx

Observação: use a *service role key* apenas em máquina de confiança (ela ignora
RLS). O app de captura no navegador usa a chave pública (anon) + login.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .fonte_dados import carregar_do_supabase
from .gerar_laudo import GeradorLaudo


def _cliente():
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover
        raise SystemExit(
            "Dependência ausente: pip install supabase\n"
            "(ela é opcional — só necessária para gerar a partir do Supabase)."
        ) from e
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise SystemExit("Defina SUPABASE_URL e SUPABASE_SERVICE_KEY no ambiente.")
    return create_client(url, key)


def _baixar_fotos(client, laudo, destino_dir: Path, bucket: str = "laudos-fotos"):
    """Baixa cada foto do Storage e aponta foto.arquivo para o arquivo local.
    Fotos sem objeto no Storage caem no placeholder do motor (arquivo vazio)."""
    destino_dir.mkdir(parents=True, exist_ok=True)
    storage = client.storage.from_(bucket)

    def baixar(caminho_obj: str, prefixo: str) -> str:
        if not caminho_obj:
            return ""
        try:
            conteudo = storage.download(caminho_obj)
        except Exception as e:  # objeto ausente -> placeholder do motor
            print(f"  aviso: não baixou {caminho_obj}: {e}")
            return ""
        local = destino_dir / f"{prefixo}_{Path(caminho_obj).name}"
        local.write_bytes(conteudo)
        return str(local)

    for foto in laudo.fotos:
        # em `arquivo_url` guardamos o path no bucket
        foto.arquivo = baixar(foto.arquivo, foto.id)

    # imagens das páginas-template (migração 0005): capa, vistoria, assinatura
    laudo.foto_capa = baixar(laudo.foto_capa, "capa")
    laudo.mapa_localizacao = baixar(laudo.mapa_localizacao, "mapa")
    laudo.foto_fachada = baixar(laudo.foto_fachada, "fachada")
    laudo.assinatura = baixar(laudo.assinatura, "assinatura")


def gerar_do_supabase(numero: str, saida: str | Path) -> Path:
    client = _cliente()
    laudo = carregar_do_supabase(numero, client=client)
    saida = Path(saida)
    _baixar_fotos(client, laudo, saida.parent / "fotos_supabase")
    return GeradorLaudo(laudo, saida).gerar()


if __name__ == "__main__":
    numero = sys.argv[1] if len(sys.argv) > 1 else "50/2026"
    destino = sys.argv[2] if len(sys.argv) > 2 else f"saida/Laudo-{numero.replace('/', '-')}.docx"
    caminho = gerar_do_supabase(numero, destino)
    print(f"Laudo gerado a partir do Supabase: {caminho}")
