#!/usr/bin/env python3
"""Gera os .dc.html anotados a partir dos .original.dc.html espelhados.

Cada transformação é uma substituição literal verificada: se o trecho do
original não casar (design mudou), o script FALHA — nunca produz um template
silenciosamente errado. Rodar de novo após cada re-sync.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent / "templates"

CAB = """<!--
  Template REAL do Claude Design ("Paula Pacheco Design System"), anotado com
  o contrato de dados de gerador/render_paginas.py. Gerado por
  anotar_templates.py a partir do .original.dc.html ao lado (intocado) —
  apos re-sync do design, rode o script de novo em vez de editar a mao.
  Ver design/canva_templates/README.md para o contrato.
-->
"""


def anotar(nome_dir: str, arquivo: str, trocas: list[tuple[str, str]],
           regexes: list[tuple[str, str, int]] = ()):  # (padrao, repl, n_esperado)
    orig = (RAIZ / nome_dir / arquivo.replace(".dc.html", ".original.dc.html"))
    texto = orig.read_text(encoding="utf-8")
    for velho, novo in trocas:
        assert velho in texto, f"{nome_dir}: trecho não encontrado:\n{velho[:120]}"
        texto = texto.replace(velho, novo)
    for padrao, repl, n in regexes:
        texto, k = re.subn(padrao, repl, texto, flags=re.S)
        assert k == n, f"{nome_dir}: regex casou {k}x (esperado {n}): {padrao[:80]}"
    # descarta wrapper de documento: mantém só o miolo x-dc + cabeçalho nosso
    m = re.search(r"<x-dc>.*</x-dc>", texto, flags=re.S)
    assert m, f"{nome_dir}: x-dc não encontrado"
    (RAIZ / nome_dir / arquivo).write_text(CAB + m.group(0) + "\n", encoding="utf-8")
    print(f"ok  {nome_dir}/{arquivo}")


NUM = ('<span style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
       'letter-spacing:0.08em;color:#5e6161">LAUDO Nº 54/2026</span>',
       '<span style="font-family:\'IBM Plex Mono\',monospace;font-size:10px;'
       'letter-spacing:0.08em;color:#5e6161">LAUDO Nº {{numero}}</span>')

# rodapé: o nº de página vira slot vazio MEDIDO (overlay com campo PAGE no Word)
PAG = [(r'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:11px;'
        r'font-weight:600;color:#BE7C4D">\d+ \| Pág\.</span>',
        '<span data-dc-medir="pagina" style="font-family:\'IBM Plex Mono\','
        'monospace;font-size:11px;font-weight:600;color:#BE7C4D">'
        '{{pagina_rotulo}}</span>', 1)]


def main():
    # ---------------- 2. Motivação ----------------
    anotar("laudo-motivacao", "LaudoMotivacao.dc.html", [
        NUM,
        ('color:#BE7C4D">2</span>', 'color:#BE7C4D">{{cap_numero}}</span>'),
        ('2.1 — Objetivos', '{{cap_numero}}.1 — Objetivos'),
        ('2.2 — Tipos de anomalias', '{{cap_numero}}.2 — Tipos de anomalias'),
        ('2.3 — Níveis de inspeção', '{{cap_numero}}.3 — Níveis de inspeção'),
        ('<p style="margin:0;font-weight:300;font-size:12.5px;line-height:1.75;'
         'color:#45494a;text-wrap:pretty">O presente trabalho tem por objetivo '
         'elaborar Laudo Técnico do Edifício Jardins da Cidade, mediante '
         'inspeção técnica das áreas comuns acessíveis, análise documental e '
         'emprego de inspeção visual, não destrutiva.</p>',
         '<p style="margin:0;font-weight:300;font-size:12.5px;line-height:1.75;'
         'color:#45494a;text-wrap:pretty">{{objetivos_p1}}</p>'),
        ('<p style="margin:8px 0 0;font-weight:300;font-size:12.5px;line-height:'
         '1.75;color:#45494a;text-wrap:pretty">O laudo deverá identificar, '
         'registrar, analisar e classificar as anomalias, falhas, manifestações '
         'patológicas e não conformidades aparentes, buscando determinar suas '
         'possíveis origens, causas, mecanismos de ocorrência e '
         'consequências.</p>',
         '<p style="margin:8px 0 0;font-weight:300;font-size:12.5px;line-height:'
         '1.75;color:#45494a;text-wrap:pretty">{{objetivos_p2}}</p>'),
    ], PAG)

    # ---------------- 3. Vistoria ----------------
    anotar("laudo-vistoria", "LaudoVistoria.dc.html", [
        NUM,
        ('color:#BE7C4D">3</span>', 'color:#BE7C4D">{{cap_numero}}</span>'),
        ('3.1 — Localização do imóvel', '{{cap_numero}}.1 — Localização do imóvel'),
        ('01, 11, 19 e 22 de junho de 2026', '{{diligencias}}'),
        ('Síndica — Sra. [nome de quem acompanhou]', '{{acompanhamento}}'),
        # mapa (image-slot -> img) + FIG dinâmica
        ('<x-import component-from-global-scope="image-slot" '
         'from="../../assets/js/image-slot.js" id="vistoria-mapa" '
         'placeholder="Mapa de localização — captura do Google Maps" '
         'shape="rect" radius="0" fit="cover" '
         'style="width:100%;height:278px;display:block" '
         'hint-size="682px,278px"></x-import>',
         '<img src="{{mapa}}" alt="" style="width:100%;height:278px;'
         'object-fit:cover;display:block" />'),
        ('>FIG. 03</span>', '>FIG. {{fig_mapa}}</span>'),
        ('Localização do Edifício Jardins da Cidade (Fonte: Google Maps)',
         '{{legenda_mapa}}'),
        # fachada
        ('<x-import component-from-global-scope="image-slot" '
         'from="../../assets/js/image-slot.js" id="vistoria-fachada" '
         'placeholder="Foto da fachada" shape="rect" radius="0" fit="cover" '
         'style="width:300px;height:232px;display:block" '
         'hint-size="300px,232px"></x-import>',
         '<img src="{{fachada}}" alt="" style="width:300px;height:232px;'
         'object-fit:cover;display:block" />'),
        ('>FIG. 04</span>', '>FIG. {{fig_fachada}}</span>'),
        ('Fachada principal do edifício', '{{legenda_fachada}}'),
    ], PAG + [
        # bloco inteiro de características (6 linhas de exemplo) -> slot raw,
        # linhas construídas pelo motor a partir de Laudo.caracteristicas
        (r'<div style="display:flex;justify-content:space-between;align-items:'
         r'baseline;gap:12px;padding:9px 0;border-bottom:1px solid #eef0ef">'
         r'.*?Endereço</span>\s*<span[^>]*>R\. Gentios, 273 — Coração de Jesus, '
         r'Belo Horizonte/MG</span>\s*</div>',
         '{{{caracteristicas}}}', 1),
    ])

    # ---------------- 4. Métodos ----------------
    anotar("laudo-metodos", "LaudoMetodos.dc.html", [
        NUM,
        ('color:#BE7C4D">4</span>', 'color:#BE7C4D">{{cap_numero}}</span>'),
        ('4.1 — Método empregado', '{{cap_numero}}.1 — Método empregado'),
        ('4.2 — Normas e legislação aplicável',
         '{{cap_numero}}.2 — Normas e legislação aplicável'),
        ('<p style="margin:0;font-weight:300;font-size:12.5px;line-height:1.75;'
         'color:#45494a;text-wrap:pretty">O trabalho foi desenvolvido com base '
         'em diligência ao local, com inspeção predominantemente visual e não '
         'destrutiva, e na análise da documentação e das informações '
         'disponibilizadas pelo solicitante.</p>',
         '<p style="margin:0;font-weight:300;font-size:12.5px;line-height:1.75;'
         'color:#45494a;text-wrap:pretty">{{metodo_p1}}</p>'),
        # dica de edição do design NÃO é conteúdo do documento
        ('<div style="margin-top:14px;font-family:\'IBM Plex Mono\',monospace;'
         'font-size:8.5px;letter-spacing:0.04em;color:#b9bcbc">// duplique ou '
         'remova linhas conforme o escopo de cada laudo</div>', ''),
    ], PAG + [
        # lista de normas inteira -> slot raw (linhas construídas pelo motor)
        (r'<div style="display:flex;flex-direction:column;gap:10px">\s*<div '
         r'style="display:flex;align-items:flex-start;gap:14px">\s*<span[^>]*>'
         r'ABNT NBR 13752</span>.*?Edificações habitacionais — '
         r'desempenho\.</span>\s*</div>\s*</div>',
         '<div style="display:flex;flex-direction:column;gap:10px">'
         '{{{normas}}}</div>', 1),
    ])

    # ---------------- 7. Especificações ----------------
    anotar("laudo-especificacoes", "LaudoEspecificacoes.dc.html", [
        NUM,
        ('color:#BE7C4D">7</span>', 'color:#BE7C4D">{{cap_numero}}</span>'),
        ('7.1 — Caderno de especificações mínimas',
         '{{cap_numero}}.1 — Caderno de especificações mínimas'),
        ('7.2 — Controle de qualidade · critérios gerais de aceite',
         '{{cap_numero}}.2 — Controle de qualidade · critérios gerais de aceite'),
    ], PAG)

    # ---------------- 9. Referencial técnico ----------------
    anotar("laudo-referencial", "LaudoReferencial.dc.html", [
        NUM,
        ('4.6 — Referencial técnico', '{{cap_numero}} — Referencial técnico'),
        ('4.6.1 — Trincas e fissuras · classificação por direção e origem',
         '{{cap_numero}}.1 — Trincas e fissuras · classificação por direção e origem'),
        ('4.6.2 — Umidade nas edificações',
         '{{cap_numero}}.2 — Umidade nas edificações'),
        ('>FIG. 07 · 08</span>', '>FIG. {{fig_a}} · {{fig_b}}</span>'),
        ('>FIG. 09</span>\n      </div>',
         '>FIG. {{fig_c}}</span>\n      </div>'),
    ], PAG + [
        (r'>FIG\. 07</span>', '>FIG. {{fig_a}}</span>', 1),
        (r'>FIG\. 08</span>', '>FIG. {{fig_b}}</span>', 1),
        (r'>FIG\. 09</span>\s*<span style="font-weight:300;font-size:9px;'
         r'line-height:1\.45',
         '>FIG. {{fig_c}}</span><span style="font-weight:300;font-size:9px;'
         'line-height:1.45', 1),
    ])

    # ---------------- 10. Encerramento ----------------
    anotar("laudo-encerramento", "LaudoEncerramento.dc.html", [
        NUM,
        ('color:#BE7C4D">8</span>', 'color:#BE7C4D">{{cap_numero}}</span>'),
        ('Belo Horizonte, 26 de junho de 2026.', '{{local_data}}'),
        # frase de contagem: sem número fixo — numeração viva fica no rodapé
        ('Este Laudo Técnico, elaborado com observância aos princípios dos '
         'códigos de ética profissional do CONFEA e de acordo com as normas '
         'técnicas da ABNT, consta de <span style="font-family:\'IBM Plex Mono\''
         ',monospace;font-size:10px;color:#292929">175</span> folhas impressas '
         'de um só lado, sendo esta última datada e assinada.',
         '{{folhas_frase}}'),
        # assinatura digitalizada é opcional -> variante
        ('<div style="position:absolute;left:0;right:0;top:8px;height:48px">\n'
         '          <x-import component-from-global-scope="image-slot" '
         'from="../../assets/js/image-slot.js" id="enc-assinatura" '
         'placeholder="Assinatura digitalizada (opcional)" shape="rect" '
         'radius="0" fit="contain" style="width:100%;height:100%" '
         'hint-size="280px,48px"></x-import>\n        </div>',
         '<!-- dc:variante:com-assinatura --><div style="position:absolute;'
         'left:0;right:0;top:8px;height:48px"><img src="{{assinatura}}" alt="" '
         'style="width:100%;height:100%;object-fit:contain" /></div>'
         '<!-- /dc:variante:com-assinatura -->'),
    ], PAG)

    print("todos anotados.")


if __name__ == "__main__":
    sys.exit(main())
