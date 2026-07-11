"""
Atalho para gerar o .docx de um laudo a partir do Supabase, sem digitar
comandos todas as vezes.

Uso:
    python gerar.py             (pergunta o número do laudo)
    python gerar.py 52/2026     (gera direto)

Lê as credenciais de um arquivo .env na mesma pasta (copie .env.example
para .env e preencha a SUPABASE_SERVICE_KEY uma única vez).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def carregar_env() -> None:
    env_path = BASE / ".env"
    if not env_path.exists():
        print("Arquivo .env não encontrado.")
        print(f"Copie '.env.example' para '.env' nesta mesma pasta e preencha "
              f"a SUPABASE_SERVICE_KEY antes de continuar.")
        sys.exit(1)
    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip())


def main() -> None:
    carregar_env()
    chave = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not chave or "cole_aqui" in chave:
        print("Preencha a SUPABASE_SERVICE_KEY no arquivo .env antes de continuar.")
        print("Onde encontrar: painel do Supabase -> Settings -> API -> service_role key.")
        sys.exit(1)

    numero = sys.argv[1] if len(sys.argv) > 1 else input("Número do laudo (ex.: 52/2026): ").strip()
    if not numero:
        print("Número do laudo é obrigatório.")
        sys.exit(1)

    sys.path.insert(0, str(BASE))
    from gerador.gerar_do_supabase import gerar_do_supabase  # noqa: E402

    destino = BASE / "saida" / f"Laudo-{numero.replace('/', '-')}.docx"
    print(f"\nGerando {destino} ...\n")
    try:
        caminho = gerar_do_supabase(numero, destino)
    except Exception as e:  # mensagem amigável para quem não programa
        msg = str(e)
        print(f"\nNão foi possível gerar o laudo: {msg}")
        if "401" in msg or "403" in msg or "Invalid API key" in msg:
            print("Isso costuma indicar que a SUPABASE_SERVICE_KEY no .env está "
                  "errada, incompleta ou expirada. Confira no painel do Supabase "
                  "em Settings -> API -> service_role key.")
        elif "PGRST" in msg or "does not exist" in msg or "0 rows" in msg:
            print(f"Confira se o número do laudo '{numero}' está exatamente "
                  "igual ao cadastrado no app (mesma grafia, com a barra).")
        sys.exit(1)

    print(f"\nPronto! Laudo salvo em:\n  {caminho.resolve()}")


if __name__ == "__main__":
    main()
    input("\nPressione Enter para fechar...")
