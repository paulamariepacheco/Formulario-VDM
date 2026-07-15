"""Modelos de dados do laudo (espelham o schema Supabase `laudos`)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from . import risco


@dataclass
class Ambiente:
    id: str
    nome: str
    pavimento: str = ""
    ordem: int = 0


@dataclass
class Foto:
    id: str
    arquivo: str = ""          # caminho local (ou URL do Storage)
    legenda: str = ""
    ordem: int = 0
    anomalia_id: Optional[str] = None
    ambiente_id: Optional[str] = None
    numero_figura: int = 0     # atribuído no motor (numeração automática)


@dataclass
class Anomalia:
    id: str
    sistema_construtivo: str
    titulo: str
    ordem: int = 0
    ambiente_id: Optional[str] = None
    descricao_fenomenologica: str = ""
    mecanismo: str = ""
    causa_provavel: str = ""
    consequencias: str = ""
    origem_taxonomia: str = ""
    vicio_ou_falha_manutencao: str = "indeterminado"
    gr: int = 1
    g: int = 1
    u: int = 1
    t: int = 1
    prazo_sugerido: Optional[str] = None
    alerta_juridico: bool = False

    # ---- derivados (calculados, nunca digitados) ----
    @property
    def gut(self) -> int:
        return risco.calcular_gut(self.g, self.u, self.t)

    @property
    def faixa(self) -> str:
        return risco.faixa_prioridade(self.gut)

    @property
    def prazo(self) -> str:
        return risco.prazo_sugerido(self.g, self.u, self.t, self.prazo_sugerido)


@dataclass
class Laudo:
    id: str
    numero: str
    tipo: str
    cliente_nome: str = ""
    cliente_cnpj_cpf: str = ""
    endereco: str = ""
    data_emissao: str = ""
    status: str = "em_redacao"
    datas_diligencia: list[str] = field(default_factory=list)
    acompanhamento: str = ""
    # ---- capa renderizada do template do design (fidelidade visual) ----
    # Nome de exibição do imóvel na capa (ex.: "Edifício Comercial Otoni").
    # Distinto de cliente_nome ("Condomínio do Edifício ..."); se vazio, a
    # capa usa cliente_nome como fallback.
    nome_imovel: str = ""
    # Foto de capa (caminho local/URL baixada). Vazio => fundo azul-marinho.
    foto_capa: str = ""
    # Força a variante de fundo do template: "" (automático pela foto),
    # "azul-marinho" ou "foto-com-overlay" (prop `fundo` do LaudoCapa).
    capa_fundo: str = ""
    # ---- página de Vistoria renderizada (template LaudoVistoria) ----
    # Mapa de localização (captura) e foto da fachada — caminhos locais;
    # ausentes => placeholder gerado no pipeline.
    mapa_localizacao: str = ""
    legenda_mapa: str = ""
    foto_fachada: str = ""
    legenda_fachada: str = ""
    # Características gerais do imóvel: [{"rotulo": ..., "valor": ...}, ...]
    # (a linha "Endereço" é acrescentada automaticamente de `endereco`).
    caracteristicas: list[dict] = field(default_factory=list)
    # ---- página de Encerramento renderizada (template LaudoEncerramento) --
    cidade_emissao: str = ""      # vazio => "Belo Horizonte"
    assinatura: str = ""          # assinatura digitalizada (opcional)
    ambientes: list[Ambiente] = field(default_factory=list)
    anomalias: list[Anomalia] = field(default_factory=list)
    fotos: list[Foto] = field(default_factory=list)

    def ambiente(self, ambiente_id: Optional[str]) -> Optional[Ambiente]:
        return next((a for a in self.ambientes if a.id == ambiente_id), None)

    def fotos_da_anomalia(self, anomalia_id: str) -> list[Foto]:
        return sorted(
            (f for f in self.fotos if f.anomalia_id == anomalia_id),
            key=lambda f: f.ordem,
        )
