"""
Render de páginas-template (Claude Design) em imagem A4 de alta resolução.

Pipeline da decisão "fidelidade visual total": os capítulos que possuem
template pixel-perfect no projeto **Paula Pacheco Design System** (Claude
Design) são renderizados como página-imagem (PNG ~300 dpi) e inseridos no
`.docx` — em vez de texto nativo do Word. Capítulos de tamanho variável
(diagnóstico, plano, conclusões) continuam nativos.

Duas peças:

  * `renderizar_pagina_png(html, destino)` — genérico: recebe um documento
    HTML **já resolvido** (string) e devolve um PNG de página A4 (794×1123 px
    CSS) em ~300 dpi, via Chromium headless (Playwright). O Chromium já vem
    pré-instalado no ambiente (`CHROMIUM_PATH`, padrão
    `/opt/pw-browsers/chromium`) — NÃO rodar `playwright install`.

  * `montar_html_capa(laudo, tokens)` — resolve o template da capa
    (`design/canva_templates/templates/laudo-capa/LaudoCapa.dc.html`) com os
    dados reais do laudo. Os templates são tratados como markup estático
    (formato `.dc.html` do Claude Design): extrai-se o conteúdo de
    `<x-dc>…</x-dc>`, removem-se os `<script>` do runtime e substituem-se
    apenas os nós de dado, via contrato de anotação:

      - `{{campo}}`                      → texto/atributo variável;
      - `<!-- dc:variante:X --> … <!-- /dc:variante:X -->`
                                         → blocos condicionais (o único `sc-if`
                                           real do design é o fundo da capa:
                                           `azul-marinho` × `foto-com-overlay`).

    Cores e fontes NUNCA são hardcodadas aqui: viram CSS custom properties
    (`--pp-*`) geradas de `design/tokens.json` e injetadas no `<head>`.

Assets (fontes, logo, CSS) são espelhados em `design/canva_templates/` para o
render funcionar sem rede; um `<base href>` aponta os caminhos relativos do
template para esse diretório.
"""
from __future__ import annotations

import html as _html
import os
import re
import tempfile
from datetime import date
from pathlib import Path

from . import textos

# --------------------------------------------------------------------------
# Constantes de página
# --------------------------------------------------------------------------
# A4 a 96 dpi (contrato dos templates do Claude Design: 794×1123 px CSS).
PAGINA_LARGURA_PX = 794
PAGINA_ALTURA_PX = 1123

# Fator de escala do Chromium para ~300 dpi (alvo 2480×3508 px).
# 2480/794 ≈ 3.1234; validado empiricamente: 3.1235 produz 2480×3508.
ESCALA_300DPI = 3.1235

# Espelho local do projeto Claude Design (mesma estrutura de paths do projeto:
# templates/<nome>/<Nome>.dc.html, assets/, tokens/, styles.css).
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "design" / "canva_templates"

_CHROMIUM_PADRAO = "/opt/pw-browsers/chromium"

_MESES_PT = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


class RenderIndisponivel(RuntimeError):
    """Playwright/Chromium ou o template não estão disponíveis neste ambiente.

    O chamador (gerar_laudo) usa isto para degradar graciosamente para a
    versão nativa (texto Word) do capítulo.
    """


# --------------------------------------------------------------------------
# Renderer genérico: HTML (string) -> PNG A4 em alta resolução
# --------------------------------------------------------------------------
class SessaoRender:
    """Sessão de Chromium reutilizável para renderizar várias páginas.

    Um launch por laudo (não por página). Uso:

        with SessaoRender() as sr:
            png, rects = sr.render(html, destino, medir=["pagina"])

    `medir` lista valores de `data-dc-medir`; devolve {nome: (x, y, w, h)} em
    px CSS da página 794×1123 — usado para posicionar overlays de campo do
    Word (nº de página vivo) exatamente onde o design os desenha.
    """

    def __init__(self, escala: float = ESCALA_300DPI):
        self.escala = escala
        self._pw = None
        self._browser = None

    def __enter__(self) -> "SessaoRender":
        try:
            from playwright.sync_api import Error as PWError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover
            raise RenderIndisponivel(
                "playwright não instalado — pip install -r requirements-render.txt"
            ) from exc
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(
                executable_path=os.environ.get("CHROMIUM_PATH",
                                               _CHROMIUM_PADRAO) or None)
        except PWError as exc:
            self._pw.stop()
            self._pw = None
            raise RenderIndisponivel(f"Chromium indisponível: {exc}") from exc
        return self

    def __exit__(self, *exc):
        if self._browser is not None:
            self._browser.close()
        if self._pw is not None:
            self._pw.stop()
        return False

    def render(self, html: str, destino: str | Path,
               medir: list[str] | None = None) -> tuple[Path, dict]:
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)
        # goto(file://) em vez de set_content: origem file:// pode carregar
        # subrecursos file:// (fontes/imagens locais); about:blank não pode.
        fd, tmp = tempfile.mkstemp(suffix=".html")
        rects: dict = {}
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(html)
            page = self._browser.new_page(
                viewport={"width": PAGINA_LARGURA_PX,
                          "height": PAGINA_ALTURA_PX},
                device_scale_factor=self.escala,
            )
            try:
                page.goto(Path(tmp).as_uri(), wait_until="load")
                # ícones lucide (injetados por montar_pagina_html) + fontes
                page.evaluate(
                    "window.lucide && window.lucide.createIcons && "
                    "window.lucide.createIcons()")
                page.evaluate("document.fonts ? document.fonts.ready : true")
                if medir:
                    med = page.evaluate(
                        "Array.from(document.querySelectorAll('[data-dc-medir]'))"
                        ".map(e => { const r = e.getBoundingClientRect();"
                        " return [e.getAttribute('data-dc-medir'),"
                        " [r.x, r.y, r.width, r.height]]; })")
                    rects = {nome: tuple(r) for nome, r in med if nome in medir}
                page.screenshot(
                    path=str(destino),
                    clip={"x": 0, "y": 0,
                          "width": PAGINA_LARGURA_PX,
                          "height": PAGINA_ALTURA_PX},
                )
            finally:
                page.close()
        finally:
            Path(tmp).unlink(missing_ok=True)
        return destino, rects


def renderizar_pagina_png(html: str, destino: str | Path,
                          escala: float = ESCALA_300DPI) -> Path:
    """Renderiza um documento HTML resolvido como página A4 em PNG ~300 dpi.

    Atalho de página única (abre e fecha uma SessaoRender); para vários
    capítulos, use a sessão diretamente e reutilize o browser.
    """
    with SessaoRender(escala) as sr:
        caminho, _ = sr.render(html, destino)
    return caminho


# --------------------------------------------------------------------------
# Resolução de templates .dc.html (markup estático + anotações)
# --------------------------------------------------------------------------
def _extrair_xdc(texto: str) -> str:
    """Extrai o markup de <x-dc>…</x-dc> e descarta o runtime (<script>)."""
    # descarta comentários de cabeçalho ANTES do parse (podem citar tokens
    # do contrato — placeholders, x-dc — sem quebrar a extração)
    texto = re.sub(r"^\s*(<!--.*?-->\s*)+", "", texto, flags=re.S)
    m = re.search(r"<x-dc\b[^>]*>(.*)</x-dc>", texto, flags=re.S)
    corpo = m.group(1) if m else texto
    corpo = re.sub(r"<script\b.*?</script>", "", corpo, flags=re.S)
    return corpo


def _resolver_variantes(corpo: str, ativas: str | set[str]) -> str:
    """Mantém só os blocos <!-- dc:variante:X -->…<!-- /dc:variante:X --> ativos.

    `ativas` aceita um nome único ou um conjunto — um template pode combinar
    dimensões independentes (ex.: fundo da capa × moldura de foto).
    """
    if isinstance(ativas, str):
        ativas = {ativas}
    def _sub(m: re.Match) -> str:
        return m.group(2) if m.group(1) in ativas else ""
    return re.sub(
        r"<!--\s*dc:variante:([\w-]+)\s*-->(.*?)<!--\s*/dc:variante:\1\s*-->",
        _sub, corpo, flags=re.S)


def _substituir_campos(corpo: str, campos: dict[str, str],
                       raw: dict[str, str] | None = None) -> str:
    """Substitui placeholders: {{{campo}}} recebe HTML cru (montado pelo
    motor, com valores individualmente escapados); {{campo}} é escapado."""
    for chave, valor in (raw or {}).items():
        corpo = corpo.replace("{{{%s}}}" % chave, valor or "")
    for chave, valor in campos.items():
        corpo = corpo.replace("{{%s}}" % chave, _html.escape(valor or "", quote=True))
    # placeholder não preenchido nunca vaza para a página
    return re.sub(r"\{?\{\{[\w-]+\}\}\}?", "", corpo)


def _css_tokens(tokens: dict) -> str:
    """design/tokens.json -> CSS custom properties (nunca hardcodar cores)."""
    t = tokens
    stack = lambda fam, fbs: ", ".join([f'"{fam}"'] + [
        f'"{f}"' if " " in f else f for f in fbs])
    linhas = [f"--pp-{nome}: {cor};" for nome, cor in t["marca"].items()]
    linhas += [f"--pp-texto-{nome}: {cor};" for nome, cor in t["texto"].items()]
    linhas += [f"--pp-linha-{nome}: {cor};" for nome, cor in t["linhas"].items()]
    for gr, spec in t["grau_risco"].items():
        linhas.append(f"--pp-{gr.lower()}: {spec['cor']};")
        linhas.append(f"--pp-{gr.lower()}-superficie: {spec['superficie']};")
    tip = t["tipografia"]
    linhas.append(f"--pp-fonte-titulo: {stack(tip['titulo'], tip['fallback_titulo'])};")
    linhas.append(f"--pp-fonte-corpo: {stack(tip['corpo'], tip['fallback_corpo'])};")
    return ":root{" + "".join(linhas) + "}"


# Fontes espelhadas em design/canva_templates/assets/fonts/ (sincronizadas do
# projeto Claude Design). Visia Pro: os 5 pesos que os templates de laudo usam
# (200/300/400/600/900). IBM Plex Mono (códigos/cotas — o styles.css do design
# a importa do Google Fonts, inviável offline): servida local (google/fonts,
# OFL). Montserrat variável: fallback de corpo. URLs absolutas file:// para
# não depender do <base href> do documento.
_FONTES_VISIA = [(200, "ExtraLight"), (300, "Light"), (400, "Regular"),
                 (600, "SemiBold"), (900, "Heavy")]
_FONTES_MONO = [(400, "Regular"), (500, "Medium"), (600, "SemiBold")]


def _css_fontes(assets_dir: Path | None = None) -> str:
    fontes = (assets_dir or TEMPLATES_DIR / "assets" / "fonts").resolve()
    if not fontes.is_dir():  # espelho ausente: fallback declarado em tokens.json
        return ""
    uri = lambda nome: (fontes / nome).as_uri()
    css = [
        f'@font-face{{font-family:"Montserrat";src:url("{uri("Montserrat-wght.ttf")}") '
        'format("truetype");font-weight:100 900;font-style:normal;}',
    ]
    for peso, nome in _FONTES_VISIA:
        arq = fontes / f"VisiaPro-{nome}.otf"
        if arq.exists():
            css.append(
                f'@font-face{{font-family:"Visia Pro";src:url("{uri(arq.name)}") '
                f'format("opentype");font-weight:{peso};font-style:normal;}}')
    for peso, nome in _FONTES_MONO:
        arq = fontes / f"IBMPlexMono-{nome}.ttf"
        if arq.exists():
            css.append(
                f'@font-face{{font-family:"IBM Plex Mono";src:url("{uri(arq.name)}") '
                f'format("truetype");font-weight:{peso};font-style:normal;}}')
    return "".join(css)

_CSS_PAGINA = (
    "*{margin:0;padding:0;box-sizing:border-box}"
    "html,body{width:%dpx;height:%dpx;overflow:hidden;"
    "-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}"
    % (PAGINA_LARGURA_PX, PAGINA_ALTURA_PX)
)


def montar_pagina_html(fragmento: str, tokens: dict,
                       base_dir: Path = TEMPLATES_DIR) -> str:
    """Envelopa um fragmento de template resolvido num documento HTML A4.

    `base_dir` deve ser o diretório do PRÓPRIO template (ex.:
    templates/laudo-capa/) para os caminhos relativos do markup original
    (`../../assets/...`) resolverem como no projeto Claude Design.
    """
    base = base_dir.resolve().as_uri() + "/"
    # lucide espelhado (assets/js): os templates de miolo usam <i data-lucide>;
    # a SessaoRender chama lucide.createIcons() antes do screenshot.
    lucide = TEMPLATES_DIR / "assets" / "js" / "lucide.min.js"
    script = (f'<script src="{lucide.resolve().as_uri()}"></script>'
              if lucide.exists() else "")
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<base href=\"{base}\">"
        f"<style>{_CSS_PAGINA}{_css_fontes()}{_css_tokens(tokens)}</style>"
        f"{script}</head><body>{fragmento}</body></html>"
    )


# --------------------------------------------------------------------------
# Capa (prova de conceito da fidelidade visual)
# --------------------------------------------------------------------------
def _data_extenso(iso: str) -> str:
    """'2026-07-09' -> '9 de julho de 2026' (mantém o original se não-ISO)."""
    try:
        d = date.fromisoformat(iso)
        return f"{d.day} de {_MESES_PT[d.month - 1]} de {d.year}"
    except (ValueError, TypeError):
        return iso or ""


def _mes_ano(iso: str) -> str:
    """'2026-07-09' -> 'Julho de 2026' (formato da capa no design original)."""
    try:
        d = date.fromisoformat(iso)
        return f"{_MESES_PT[d.month - 1].capitalize()} de {d.year}"
    except (ValueError, TypeError):
        return iso or ""


def montar_html_capa(laudo, tokens: dict) -> str:
    """Resolve o template da capa com os dados reais do laudo.

    Variantes de fundo (prop `fundo` do template original):
      * `foto-com-overlay` — foto do imóvel com gradiente da marca por cima;
      * `azul-marinho`     — fundo sólido navy (fallback quando não há foto).
    `laudo.capa_fundo` força a escolha; vazio = automático pela foto.
    """
    caminho = TEMPLATES_DIR / "templates" / "laudo-capa" / "LaudoCapa.dc.html"
    if not caminho.exists():
        raise RenderIndisponivel(f"template da capa não encontrado: {caminho}")

    corpo = _extrair_xdc(caminho.read_text(encoding="utf-8"))

    foto = Path(laudo.foto_capa) if getattr(laudo, "foto_capa", "") else None
    tem_foto = bool(foto and foto.exists())
    fundo = getattr(laudo, "capa_fundo", "") or (
        "foto-com-overlay" if tem_foto else "azul-marinho")
    if fundo == "foto-com-overlay" and not tem_foto:
        fundo = "azul-marinho"  # fallback obrigatório: sem foto, navy sólido
    # fundo azul-marinho + foto disponível => foto emoldurada (cantoneiras),
    # como no preview padrão do template original.
    ativas = {fundo}
    if fundo == "azul-marinho" and tem_foto:
        ativas.add("foto-moldura")
    corpo = _resolver_variantes(corpo, ativas)

    cliente_linha = laudo.cliente_nome
    if laudo.cliente_cnpj_cpf:
        cliente_linha += f" · CNPJ/CPF {laudo.cliente_cnpj_cpf}"

    campos = {
        "numero": laudo.numero,
        "nome_imovel": laudo.nome_imovel or laudo.cliente_nome,
        "endereco": laudo.endereco,
        "tipo_rotulo": textos.TIPO_ROTULO.get(laudo.tipo, laudo.tipo),
        "cliente_linha": cliente_linha,
        "emissao": _mes_ano(laudo.data_emissao),
        "emissao_linha": (f"Emitido em {_data_extenso(laudo.data_emissao)}"
                          if laudo.data_emissao else ""),
        "diligencias_linha": (
            "Diligências: " + " · ".join(laudo.datas_diligencia)
            if laudo.datas_diligencia else ""),
        "foto_capa": foto.resolve().as_uri() if tem_foto else "",
        "perita": textos.PERITA,
        "perita_capa": textos.PERITA_CAPA,
        "perita_titulo": textos.PERITA_TITULO,
        "credenciais_linha": f"{textos.CREA} · {textos.IBAPE}",
    }
    corpo = _substituir_campos(corpo, campos)
    return montar_pagina_html(corpo, tokens, base_dir=caminho.parent)


def renderizar_capa(laudo, tokens: dict, destino: str | Path) -> Path:
    """Atalho: monta o HTML da capa e o renderiza em PNG A4 ~300 dpi."""
    return renderizar_pagina_png(montar_html_capa(laudo, tokens), destino)


# --------------------------------------------------------------------------
# Capítulos de miolo (templates 1:1 do Claude Design)
# --------------------------------------------------------------------------
# Nº de página dos miolos: o template desenha o slot ("NN | Pág.") vazio e
# marcado com data-dc-medir="pagina"; o motor sobrepõe uma caixa de texto do
# Word com o campo PAGE na posição medida — numeração viva, visual do design.

_ARQ_TEMPLATE = {
    "motivacao": ("laudo-motivacao", "LaudoMotivacao.dc.html"),
    "vistoria": ("laudo-vistoria", "LaudoVistoria.dc.html"),
    "metodos": ("laudo-metodos", "LaudoMetodos.dc.html"),
    "especificacoes": ("laudo-especificacoes", "LaudoEspecificacoes.dc.html"),
    "referencial": ("laudo-referencial", "LaudoReferencial.dc.html"),
    "encerramento": ("laudo-encerramento", "LaudoEncerramento.dc.html"),
}

# Defaults de redação = texto do design (padrão consolidado da Paula).
# `{nome_imovel}` é interpolado pelo motor.
OBJETIVOS_P1 = ("O presente trabalho tem por objetivo elaborar Laudo Técnico "
                "do {nome_imovel}, mediante inspeção técnica das áreas comuns "
                "acessíveis, análise documental e emprego de inspeção visual, "
                "não destrutiva.")
OBJETIVOS_P2 = ("O laudo deverá identificar, registrar, analisar e classificar "
                "as anomalias, falhas, manifestações patológicas e não "
                "conformidades aparentes, buscando determinar suas possíveis "
                "origens, causas, mecanismos de ocorrência e consequências.")
METODO_P1 = ("O trabalho foi desenvolvido com base em diligência ao local, com "
             "inspeção predominantemente visual e não destrutiva, e na análise "
             "da documentação e das informações disponibilizadas pelo "
             "solicitante.")
FOLHAS_FRASE = ("Este Laudo Técnico, elaborado com observância aos princípios "
                "dos códigos de ética profissional do CONFEA e de acordo com "
                "as normas técnicas da ABNT, consta das folhas numeradas no "
                "rodapé, impressas de um só lado, sendo esta última datada e "
                "assinada.")
NORMAS_PADRAO = [
    ("ABNT NBR 13752", "Perícias de engenharia na construção civil."),
    ("ABNT NBR 16747", "Inspeção predial — diretrizes, conceitos, terminologia "
                       "e procedimentos."),
    ("IBAPE", "Diretrizes do IBAPE aplicáveis à inspeção predial, perícias e "
              "avaliações técnicas."),
    ("ABNT NBR 5674", "Manutenção de edificações — requisitos para o sistema "
                      "de gestão de manutenção."),
    ("ABNT NBR 9050", "Acessibilidade a edificações, mobiliário, espaços e "
                      "equipamentos urbanos, no que couber."),
    ("ABNT NBR 15575", "Edificações habitacionais — desempenho."),
]

# Fragmentos-linha (verbatim do design) para os slots raw {{{...}}}
_LINHA_NORMA = (
    '<div style="display:flex;align-items:flex-start;gap:14px">'
    '<span style="flex-shrink:0;width:128px;font-family:\'IBM Plex Mono\','
    'monospace;font-size:9.5px;letter-spacing:0.04em;color:#3d6675;'
    'background:#eef4f6;border:1px solid #dde9ed;padding:5px 8px;'
    'text-align:center">{codigo}</span>'
    '<span style="font-weight:300;font-size:11.5px;line-height:1.6;'
    'color:#45494a;padding-top:3px">{descricao}</span></div>')
_LINHA_CARACT = (
    '<div style="display:flex;justify-content:space-between;align-items:'
    'baseline;gap:12px;padding:9px 0;border-bottom:1px solid #eef0ef">'
    '<span style="font-weight:300;font-size:11px;color:#767a7a">{rotulo}'
    '</span><span style="font-weight:400;font-size:12px;color:#292929;'
    'text-align:right">{valor}</span></div>')


def _esc(v: str) -> str:
    return _html.escape(v or "", quote=True)


def montar_html_capitulo(chave: str, laudo, tokens: dict, cap_numero: int,
                         campos_extra: dict[str, str] | None = None,
                         raw: dict[str, str] | None = None,
                         variantes: set[str] | None = None) -> str:
    """Resolve um template de capítulo com os campos comuns + específicos."""
    nome_dir, arquivo = _ARQ_TEMPLATE[chave]
    caminho = TEMPLATES_DIR / "templates" / nome_dir / arquivo
    if not caminho.exists():
        raise RenderIndisponivel(f"template não encontrado: {caminho}")
    corpo = _extrair_xdc(caminho.read_text(encoding="utf-8"))
    corpo = _resolver_variantes(corpo, variantes or set())
    campos = {
        "numero": laudo.numero,
        "cap_numero": str(cap_numero),
        "pagina_rotulo": "",   # slot vazio: o Word sobrepõe o campo PAGE
    }
    campos.update(campos_extra or {})
    corpo = _substituir_campos(corpo, campos, raw)
    return montar_pagina_html(corpo, tokens, base_dir=caminho.parent)


def campos_motivacao(laudo) -> dict[str, str]:
    nome = laudo.nome_imovel or laudo.cliente_nome
    return {"objetivos_p1": OBJETIVOS_P1.format(nome_imovel=nome),
            "objetivos_p2": OBJETIVOS_P2}


def campos_metodos() -> tuple[dict[str, str], dict[str, str]]:
    linhas = "".join(_LINHA_NORMA.format(codigo=_esc(c), descricao=_esc(d))
                     for c, d in NORMAS_PADRAO)
    return {"metodo_p1": METODO_P1}, {"normas": linhas}


def campos_vistoria(laudo, mapa_uri: str, fachada_uri: str,
                    fig_mapa: int, fig_fachada: int) -> tuple[dict, dict]:
    nome = laudo.nome_imovel or laudo.cliente_nome
    caract = list(getattr(laudo, "caracteristicas", []) or [])
    if laudo.endereco:
        caract = caract + [{"rotulo": "Endereço", "valor": laudo.endereco}]
    linhas = "".join(_LINHA_CARACT.format(rotulo=_esc(c["rotulo"]),
                                          valor=_esc(c["valor"]))
                     for c in caract)
    campos = {
        "diligencias": ", ".join(laudo.datas_diligencia) or "—",
        "acompanhamento": laudo.acompanhamento or "—",
        "mapa": mapa_uri,
        "fachada": fachada_uri,
        "fig_mapa": f"{fig_mapa:02d}",
        "fig_fachada": f"{fig_fachada:02d}",
        "legenda_mapa": getattr(laudo, "legenda_mapa", "") or
                        f"Localização do {nome} (Fonte: Google Maps)",
        "legenda_fachada": getattr(laudo, "legenda_fachada", "") or
                           "Fachada principal do edifício",
    }
    return campos, {"caracteristicas": linhas}


def campos_referencial(fig_a: int, fig_b: int, fig_c: int) -> dict[str, str]:
    return {"fig_a": f"{fig_a:02d}", "fig_b": f"{fig_b:02d}",
            "fig_c": f"{fig_c:02d}"}


def campos_encerramento(laudo) -> tuple[dict[str, str], set[str]]:
    cidade = getattr(laudo, "cidade_emissao", "") or "Belo Horizonte"
    data = _data_extenso(laudo.data_emissao)
    campos = {"local_data": f"{cidade}, {data}." if data else f"{cidade}.",
              "folhas_frase": FOLHAS_FRASE}
    assinatura = getattr(laudo, "assinatura", "")
    variantes: set[str] = set()
    if assinatura and Path(assinatura).exists():
        campos["assinatura"] = Path(assinatura).resolve().as_uri()
        variantes.add("com-assinatura")
    return campos, variantes
