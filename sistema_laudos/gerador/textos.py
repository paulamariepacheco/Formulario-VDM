"""
Textos técnicos padrão do laudo.

Estes são os *defaults* embutidos no motor. Quando existir um registro
correspondente em `laudos.capitulos_fixos` (versionado no Supabase), ele tem
precedência — assim a Paula edita os textos sem mexer no código.

A redação técnica corrida de cada anomalia (transformar campos estruturados em
texto pericial) segue as diretrizes da skill `elaborador-de-laudo` e é aplicada
na etapa de "redação assistida" (Fase 3); aqui o motor apenas monta o que já
está redigido/aprovado nos campos.
"""
from __future__ import annotations

CREA = "CREA/MG 173201"
IBAPE = "IBAPE/MG 1221"
PERITA = "Paula Marie Siqueira Pacheco"
PERITA_TITULO = "Engenheira Civil · Perita em Engenharia Diagnóstica"

# ---------------------------------------------------------------------------
# Capítulos fixos (defaults). Chave -> (título, corpo).
# ---------------------------------------------------------------------------
CAPITULOS_FIXOS = {
    "pressupostos": (
        "Pressupostos e Ressalvas",
        "O presente Laudo de Engenharia foi elaborado com base nos elementos "
        "disponibilizados e nas constatações realizadas em vistoria in loco, "
        "adotando-se metodologia de engenharia diagnóstica reconhecida. As "
        "conclusões restringem-se às condições observadas nas datas das "
        "diligências, aos ambientes efetivamente acessados e aos documentos "
        "apresentados à Perita. Ensaios laboratoriais, aberturas destrutivas e "
        "levantamentos complementares não integraram o escopo, salvo menção "
        "expressa. Eventuais limitações de acesso, de documentação ou de "
        "condições de contorno constituem ressalva técnica e são registradas "
        "nos pontos pertinentes deste laudo.",
    ),
    "motivacao": (
        "Motivação",
        "A presente vistoria foi motivada pela necessidade de identificação, "
        "caracterização e classificação das anomalias e manifestações "
        "patológicas incidentes na edificação, com vistas à orientação técnica "
        "quanto às medidas de intervenção e à mitigação dos riscos associados.",
    ),
    "metodos": (
        "Métodos e Procedimentos",
        "Os trabalhos observaram os procedimentos consagrados da engenharia "
        "diagnóstica: (i) inspeção visual sistemática dos sistemas construtivos; "
        "(ii) registro fotográfico das anomalias; (iii) análise fenomenológica "
        "(descrição, mecanismo, causa provável e consequências); (iv) "
        "classificação do grau de risco segundo a metodologia IBAPE; e (v) "
        "priorização das intervenções por meio da Matriz GUT (Gravidade, "
        "Urgência e Tendência). A voz adotada é impessoal, em terceira pessoa, "
        "conforme praxe pericial.",
    ),
    "referencial": (
        "Referencial Técnico",
        "Foram observadas, no que couber, as normas e referências técnicas "
        "aplicáveis, com destaque para a ABNT NBR 16747 (Inspeção Predial), "
        "a ABNT NBR 5674 (Manutenção de Edificações), a ABNT NBR 6118 "
        "(Projeto de Estruturas de Concreto), a ABNT NBR 9575 "
        "(Impermeabilização) e a Norma de Inspeção Predial Nacional do IBAPE, "
        "além da doutrina consolidada em engenharia diagnóstica.",
    ),
    "especificacoes": (
        "Especificações de Materiais e Aceite",
        "As intervenções recomendadas deverão empregar materiais e sistemas "
        "compatíveis com as normas técnicas vigentes e com as condições de "
        "exposição de cada elemento, mediante projeto executivo específico e "
        "acompanhamento de responsável técnico habilitado. O aceite dos "
        "serviços fica condicionado à verificação de desempenho, à emissão das "
        "respectivas ARTs e à entrega da documentação técnica correspondente.",
    ),
}

# ---------------------------------------------------------------------------
# Parágrafos gerados por regra de negócio
# ---------------------------------------------------------------------------
ALERTA_JURIDICO = (
    "Alerta de Responsabilidade Jurídico-Técnica — A anomalia ora classificada "
    "apresenta grau de risco elevado (GR3), com potencial de dano a pessoas e a "
    "bens e/ou comprometimento de elemento estrutural. Nos termos dos artigos "
    "186, 927 e 1.348, inciso V, do Código Civil, a ciência inequívoca da "
    "condição de risco impõe ao responsável pela administração e conservação da "
    "edificação o dever de adoção imediata das providências cabíveis, sob pena "
    "de responsabilização civil por omissão. Recomenda-se, portanto, a "
    "intervenção prioritária e a devida documentação das medidas adotadas."
)

RESSALVA_VICIO = (
    "Ressalva técnica — Não foram disponibilizados dados suficientes "
    "(projetos, memoriais, histórico de manutenção e registros de execução) "
    "que permitam diferenciar, com segurança, vício construtivo de falha de "
    "manutenção quanto a esta anomalia, constituindo ressalva técnica do "
    "presente laudo. A definição de responsabilidades demanda a apresentação "
    "da referida documentação."
)


def encerramento(qtd_paginas: int, numero: str) -> list[str]:
    """Parágrafos do capítulo de Encerramento."""
    return [
        "Declara a signatária, para os devidos fins, independência e "
        "imparcialidade em relação às partes e ao objeto da presente perícia, "
        "inexistindo impedimento ou suspeição de qualquer natureza.",
        "O presente laudo encontra-se apto à emissão da respectiva Anotação de "
        "Responsabilidade Técnica (ART) perante o CREA/MG.",
        f"Este Laudo de Engenharia Nº {numero} é composto por {qtd_paginas} "
        "(páginas numeradas sequencialmente) e segue assinado pela profissional "
        "responsável.",
        "Nada mais havendo a consignar, encerra-se o presente laudo.",
    ]


def bloco_credenciais() -> list[str]:
    return [
        PERITA,
        PERITA_TITULO,
        f"{CREA}   ·   {IBAPE}",
    ]
