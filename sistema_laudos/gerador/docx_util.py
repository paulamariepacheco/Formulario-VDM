"""
Utilitários de baixo nível para o documento Word (.docx).

Concentra o "encanamento" que satisfaz os critérios de aceite da Fase 1:
  * Sumário automático (campo TOC que o Word popula ao abrir);
  * Numeração de página contínua (campo PAGE no rodapé) e atualização
    automática de campos na abertura;
  * Compressão de imagem no pipeline (Pillow, máx. 1600px, JPEG ~80%);
  * Legenda de figura numerada automaticamente;
  * Fontes e cores da marca (design tokens).
"""
from __future__ import annotations

import json
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --------------------------------------------------------------------------
# Design tokens
# --------------------------------------------------------------------------
_TOKENS_PATH = Path(__file__).resolve().parent.parent / "design" / "tokens.json"


def carregar_tokens() -> dict:
    return json.loads(_TOKENS_PATH.read_text(encoding="utf-8"))


def hexnum(cor: str) -> str:
    """'#171f3d' -> '171F3D' (formato exigido pelo OOXML)."""
    return cor.lstrip("#").upper()


# --------------------------------------------------------------------------
# Campos do Word (TOC, PAGE, updateFields)
# --------------------------------------------------------------------------
def _campo(paragraph, instrucao: str, placeholder: str = ""):
    """Insere um campo do Word ( { instrucao } ) em um parágrafo."""
    r1 = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    fld_begin.set(qn("w:dirty"), "true")
    r1._r.append(fld_begin)

    r2 = paragraph.add_run()
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = instrucao
    r2._r.append(instr)

    r3 = paragraph.add_run()
    fld_sep = OxmlElement("w:fldChar")
    fld_sep.set(qn("w:fldCharType"), "separate")
    r3._r.append(fld_sep)

    if placeholder:
        paragraph.add_run(placeholder)

    r5 = paragraph.add_run()
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    r5._r.append(fld_end)


def inserir_sumario(paragraph):
    """Campo TOC (níveis 1–3). O Word popula ao abrir / com F9."""
    _campo(
        paragraph,
        ' TOC \\o "1-3" \\h \\z \\u ',
        placeholder="Sumário — atualize os campos (Ctrl+A, F9) ao abrir.",
    )


def atualizar_campos_ao_abrir(document):
    """Faz o Word atualizar TODOS os campos (sumário, paginação) ao abrir."""
    settings = document.settings.element
    if settings.find(qn("w:updateFields")) is None:
        el = OxmlElement("w:updateFields")
        el.set(qn("w:val"), "true")
        settings.append(el)


# --------------------------------------------------------------------------
# Cabeçalho e rodapé (numeração de página contínua)
# --------------------------------------------------------------------------
def configurar_cabecalho_rodape(document, tokens, numero_laudo: str):
    """Cabeçalho fixo (CREA/IBAPE) e rodapé com numeração contínua.
    A primeira página (capa) fica limpa via 'different first page'."""
    section = document.sections[0]
    section.different_first_page_header_footer = True

    fonte_corpo = tokens["tipografia"]["corpo"]
    cinza = hexnum(tokens["marca"]["cinza"])
    terracota = hexnum(tokens["marca"]["terracota"])

    # ---- Cabeçalho (páginas de miolo) ----
    hp = section.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = hp.add_run(f"Laudo de Engenharia Nº {numero_laudo}    ·    "
                     "CREA/MG 173201    ·    IBAPE/MG 1221")
    run.font.name = fonte_corpo
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor.from_string(cinza)
    _linha_inferior(hp, cinza)

    # ---- Rodapé (numeração contínua "Página X") ----
    fp = section.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run("Página ")
    r.font.name = fonte_corpo
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor.from_string(terracota)
    _campo(fp, " PAGE ")
    r2 = fp.add_run(" de ")
    r2.font.name = fonte_corpo
    r2.font.size = Pt(8)
    r2.font.color.rgb = RGBColor.from_string(terracota)
    _campo(fp, " NUMPAGES ")
    # aplica cor/fonte aos runs de campo do rodapé
    for run in fp.runs:
        run.font.name = fonte_corpo
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor.from_string(terracota)


def _linha_inferior(paragraph, cor_hex: str):
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), cor_hex)
    pbdr.append(bottom)
    pPr.append(pbdr)


# --------------------------------------------------------------------------
# Tabelas — sombreamento de célula (matrizes de risco)
# --------------------------------------------------------------------------
def sombrear_celula(cell, cor_hex: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), cor_hex)
    tcPr.append(shd)


# --------------------------------------------------------------------------
# Imagens — compressão no pipeline + placeholder
# --------------------------------------------------------------------------
def comprimir_imagem(origem: str | Path, destino: str | Path,
                     lado_max: int = 1600, qualidade: int = 80) -> Path:
    """Redimensiona (máx. `lado_max` no maior lado) e recomprime JPEG."""
    origem, destino = Path(origem), Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(origem) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((lado_max, lado_max), Image.LANCZOS)
        img.save(destino, "JPEG", quality=qualidade, optimize=True)
    return destino


def gerar_placeholder(destino: str | Path, texto: str,
                      largura: int = 1200, altura: int = 800) -> Path:
    """Gera uma imagem-marcador (para fixture sem foto real)."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (largura, altura), "#e4e5e5")
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, largura - 8, altura - 8], outline="#969a9a", width=3)
    try:
        fonte = ImageFont.truetype("DejaVuSans.ttf", 34)
        fonte_p = ImageFont.truetype("DejaVuSans.ttf", 24)
    except OSError:
        fonte = ImageFont.load_default()
        fonte_p = fonte
    d.text((largura / 2, altura / 2 - 30), "FOTO DE EXEMPLO",
           fill="#5e6161", anchor="mm", font=fonte)
    d.text((largura / 2, altura / 2 + 20), "(substituir pela foto da vistoria)",
           fill="#767a7a", anchor="mm", font=fonte_p)
    d.text((largura / 2, altura - 60), texto[:80],
           fill="#45494a", anchor="mm", font=fonte_p)
    img.save(destino, "JPEG", quality=80, optimize=True)
    return destino
