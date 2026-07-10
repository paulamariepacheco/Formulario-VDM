"""
Camada de acesso a dados do laudo.

Duas fontes intercambiáveis, com o mesmo formato de saída (objeto `Laudo`):

  * `carregar_de_json(caminho)`  — fixture local (Fase 1 / testes).
  * `carregar_do_supabase(numero)` — lê do schema `laudos` (Fase 2+).

O motor de geração (`gerar_laudo.py`) consome apenas o objeto `Laudo`, sem
saber de onde ele veio — assim a Fase 2 pluga o Supabase sem tocar no motor.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .modelos import Ambiente, Anomalia, Foto, Laudo


def carregar_de_json(caminho: str | Path) -> Laudo:
    caminho = Path(caminho)
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    base = caminho.parent

    laudo = Laudo(
        id=dados.get("id", ""),
        numero=dados["numero"],
        tipo=dados.get("tipo", "individual"),
        cliente_nome=dados.get("cliente_nome", ""),
        cliente_cnpj_cpf=dados.get("cliente_cnpj_cpf", ""),
        endereco=dados.get("endereco", ""),
        data_emissao=dados.get("data_emissao", ""),
        status=dados.get("status", "em_redacao"),
        datas_diligencia=dados.get("datas_diligencia", []),
        acompanhamento=dados.get("acompanhamento", ""),
    )

    laudo.ambientes = [
        Ambiente(id=a["id"], nome=a["nome"], pavimento=a.get("pavimento", ""),
                 ordem=a.get("ordem", 0))
        for a in dados.get("ambientes", [])
    ]

    laudo.anomalias = [
        Anomalia(
            id=an["id"], sistema_construtivo=an["sistema_construtivo"],
            titulo=an["titulo"], ordem=an.get("ordem", 0),
            ambiente_id=an.get("ambiente_id"),
            descricao_fenomenologica=an.get("descricao_fenomenologica", ""),
            mecanismo=an.get("mecanismo", ""),
            causa_provavel=an.get("causa_provavel", ""),
            consequencias=an.get("consequencias", ""),
            origem_taxonomia=an.get("origem_taxonomia", ""),
            vicio_ou_falha_manutencao=an.get("vicio_ou_falha_manutencao", "indeterminado"),
            gr=an.get("gr", 1), g=an.get("g", 1), u=an.get("u", 1), t=an.get("t", 1),
            prazo_sugerido=an.get("prazo_sugerido"),
            alerta_juridico=an.get("alerta_juridico", False),
        )
        for an in dados.get("anomalias", [])
    ]

    def resolver(caminho_foto: str) -> str:
        if not caminho_foto:
            return ""
        p = Path(caminho_foto)
        return str(p if p.is_absolute() else (base / p))

    laudo.fotos = [
        Foto(id=f["id"], arquivo=resolver(f.get("arquivo", "")),
             legenda=f.get("legenda", ""), ordem=f.get("ordem", 0),
             anomalia_id=f.get("anomalia_id"), ambiente_id=f.get("ambiente_id"))
        for f in dados.get("fotos", [])
    ]

    return laudo


def carregar_do_supabase(numero: str, client=None) -> Laudo:
    """
    Fase 2+. Espera um cliente supabase-py já autenticado no schema `laudos`.
    Mantém exatamente o mesmo contrato de saída de `carregar_de_json`.
    """
    if client is None:  # pragma: no cover - stub até a Fase 2
        raise NotImplementedError(
            "Passe um cliente supabase-py autenticado (schema 'laudos'). "
            "Na Fase 1 use carregar_de_json()."
        )
    lr = client.table("laudos").select("*").eq("numero", numero).single().execute().data
    laudo = Laudo(
        id=lr["id"], numero=lr["numero"], tipo=lr["tipo"],
        cliente_nome=lr.get("cliente_nome", ""), cliente_cnpj_cpf=lr.get("cliente_cnpj_cpf", ""),
        endereco=lr.get("endereco", ""), data_emissao=lr.get("data_emissao", ""),
        status=lr.get("status", ""), datas_diligencia=lr.get("datas_diligencia", []),
        acompanhamento=lr.get("acompanhamento", ""),
    )
    laudo.ambientes = [Ambiente(**{k: a[k] for k in ("id", "nome", "pavimento", "ordem")})
                       for a in client.table("ambientes").select("*").eq("laudo_id", lr["id"]).execute().data]
    for an in client.table("anomalias").select("*").eq("laudo_id", lr["id"]).execute().data:
        laudo.anomalias.append(Anomalia(
            id=an["id"], sistema_construtivo=an["sistema_construtivo"], titulo=an["titulo"],
            ordem=an["ordem"], ambiente_id=an.get("ambiente_id"),
            descricao_fenomenologica=an.get("descricao_fenomenologica", ""),
            mecanismo=an.get("mecanismo", ""), causa_provavel=an.get("causa_provavel", ""),
            consequencias=an.get("consequencias", ""), origem_taxonomia=an.get("origem_taxonomia", ""),
            vicio_ou_falha_manutencao=an.get("vicio_ou_falha_manutencao", "indeterminado"),
            gr=an["gr"], g=an["g"], u=an["u"], t=an["t"],
            prazo_sugerido=an.get("prazo_sugerido"), alerta_juridico=an.get("alerta_juridico", False),
        ))
    for f in client.table("fotos").select("*").eq("laudo_id", lr["id"]).execute().data:
        laudo.fotos.append(Foto(
            id=f["id"], arquivo=f.get("arquivo_url", ""), legenda=f.get("legenda", ""),
            ordem=f["ordem"], anomalia_id=f.get("anomalia_id"), ambiente_id=f.get("ambiente_id"),
        ))
    return laudo
