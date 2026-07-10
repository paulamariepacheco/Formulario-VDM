"""
Regras de negócio de classificação de risco — IBAPE + Matriz GUT.

Tudo aqui é CALCULADO, nunca digitado (requisito da especificação):
  * GUT = G × U × T
  * Faixa de prioridade a partir do GUT
  * Prazo sugerido derivado da faixa (quando não informado)
  * Gatilho do alerta jurídico e da ressalva técnica automática
"""
from __future__ import annotations

# --- IBAPE: Grau de Risco -------------------------------------------------
GR_ROTULO = {1: "GR1 · Baixo", 2: "GR2 · Médio", 3: "GR3 · Alto"}
GR_HEX = {1: "4C8C4A", 2: "D9A441", 3: "B23A32"}          # sem '#', p/ python-docx
GR_SUPERFICIE = {1: "E9F2E9", 2: "F9F0DD", 3: "F5E5E3"}

# --- Matriz GUT: faixas de prioridade sobre GUT (1..125) ------------------
# Faixa -> (gut_minimo, prazo sugerido correspondente)
FAIXAS = [
    ("Imediata",      100, "imediato"),
    ("Alta",           60, "curto prazo"),
    ("Média",          30, "médio prazo"),
    ("Programada",     10, "longo prazo"),
    ("Monitoramento",   1, "monitoramento"),
]
FAIXA_HEX = {
    "Imediata": "B23A32",
    "Alta": "C25A34",
    "Média": "D9A441",
    "Programada": "4A7A8C",
    "Monitoramento": "5E6161",
}


def calcular_gut(g: int, u: int, t: int) -> int:
    """G × U × T (1..125)."""
    return int(g) * int(u) * int(t)


def faixa_prioridade(gut: int) -> str:
    for nome, minimo, _prazo in FAIXAS:
        if gut >= minimo:
            return nome
    return "Monitoramento"


def prazo_da_faixa(faixa: str) -> str:
    for nome, _minimo, prazo in FAIXAS:
        if nome == faixa:
            return prazo
    return "monitoramento"


def prazo_sugerido(g: int, u: int, t: int, informado: str | None = None) -> str:
    """Usa o prazo digitado se houver; senão deriva de G×U×T."""
    if informado:
        return informado
    return prazo_da_faixa(faixa_prioridade(calcular_gut(g, u, t)))


def deve_gerar_alerta_juridico(anomalia) -> bool:
    """
    Alerta de Responsabilidade Jurídico-Técnica:
    quando marcado explicitamente OU quando GR3 (alto risco a pessoas/bens
    ou elemento estrutural comprometido).
    """
    if getattr(anomalia, "alerta_juridico", False):
        return True
    return int(getattr(anomalia, "gr", 1)) >= 3


def deve_gerar_ressalva_vicio(anomalia) -> bool:
    """Ressalva técnica automática quando não há como diferenciar
    vício construtivo de falha de manutenção."""
    return str(getattr(anomalia, "vicio_ou_falha_manutencao", "indeterminado")) == "indeterminado"
