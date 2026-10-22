"""Gera um PDF único e detalhado com o mapa de corte de todas as chapas
(capa + índice + uma página por chapa, incluindo o cupom de teste),
pra conferência visual antes de importar os DXFs na máquina.
"""
from __future__ import annotations

import datetime
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon as MplPolygon

import config as c
import montagem as M
import nesting as N
from exportar import _rings

PALETTE = [
    "#eef3f8", "#f7ecdf", "#e9f5ec", "#f6e9ee", "#eee9f6", "#fdf3d8",
]


def _sheet_axes(fig, rect, titulo, subtitulo=None):
    ax = fig.add_axes(rect)
    ax.add_patch(Rectangle((0, 0), c.SHEET_W, c.SHEET_H, fill=False, edgecolor="black", linewidth=1.1))
    ax.add_patch(Rectangle((c.USABLE_MIN, c.USABLE_MIN), c.USABLE_SPAN, c.USABLE_SPAN,
                            fill=False, edgecolor="#9aa5b1", linewidth=0.7, linestyle="--"))
    ax.text(0, c.SHEET_H + 34, titulo, fontsize=13, fontweight="bold", color="#1a2b4c")
    if subtitulo:
        ax.text(0, c.SHEET_H + 16, subtitulo, fontsize=8.5, color="#555")
    # réguas no canto superior direito (fora da área de peças, nunca colide)
    ax.text(c.SHEET_W, c.SHEET_H + 34, f"chapa física {c.SHEET_W:.0f}×{c.SHEET_H:.0f} mm", fontsize=7,
            ha="right", color="#9aa5b1")
    ax.text(c.SHEET_W, c.SHEET_H + 20, f"área útil {c.USABLE_SPAN:.0f}×{c.USABLE_SPAN:.0f} mm "
            f"({c.USABLE_MIN:.0f}–{c.USABLE_MAX:.0f})", fontsize=7, ha="right", color="#9aa5b1")
    return ax


def _pagina_capa(pdf, stats):
    fig = plt.figure(figsize=(8.27, 11.69))  # A4 retrato
    fig.text(0.5, 0.90, "Armário dispensador — v2", ha="center", fontsize=22, fontweight="bold")
    fig.text(0.5, 0.865, "Mapa de corte detalhado", ha="center", fontsize=14, color="#444")
    fig.text(0.5, 0.83, datetime.date.today().strftime("%d/%m/%Y"), ha="center", fontsize=9, color="#888")

    linhas = [
        ("Dimensões externas (L × A × P)", f"{stats['ext_w']:.0f} × {stats['ext_h']:.0f} × {stats['ext_d']:.0f} mm"),
        ("Vão interno", f"{stats['inner_w']:.0f} mm"),
        ("Material nominal", f"MDF {stats['mat_t']:.0f} mm"),
        ("Chapa física / área útil", f"{stats['sheet']:.0f}×{stats['sheet']:.0f} mm / {stats['usable']:.0f}×{stats['usable']:.0f} mm"),
        ("Sistema de junta", "dente reto único (finger joint) — sem emenda de painel em todo o projeto"),
        ("Total de peças", f"{stats['n_pecas']}"),
        ("Total de chapas numeradas", f"{stats['n_chapas']}"),
        ("Cupom de teste", "1 folha separada (00_TESTES) — kerf + par finger-joint de QC"),
    ]
    import textwrap
    y = 0.75
    for rotulo, valor in linhas:
        fig.text(0.10, y, rotulo, fontsize=10, fontweight="bold", color="#1a2b4c")
        linhas_valor = textwrap.wrap(valor, 40) or [valor]
        for lv in linhas_valor:
            fig.text(0.58, y, lv, fontsize=10, color="#222")
            y -= 0.024
        y -= 0.011

    fig.text(0.10, y - 0.02, "Como usar este mapa", fontsize=11, fontweight="bold", color="#1a2b4c")
    instrucoes = [
        "1. Corte primeiro a folha de teste (00_TESTES) e calibre o kerf no material real.",
        "2. Cada página seguinte corresponde a um arquivo corte/CHAPA_NN.dxf — confira o",
        "   número antes de importar. A área tracejada é o limite útil (10–890mm).",
        "3. Os números dentro de cada peça batem com a legenda ao final da própria página",
        "   (código, nome e dimensão nominal, sem compensação de kerf).",
        "4. Os nomes gravados (arquivos gravacao/) não aparecem aqui — este PDF é só o",
        "   contorno de corte, pra conferência de leiaute antes da máquina.",
    ]
    y -= 0.06
    for linha in instrucoes:
        fig.text(0.10, y, linha, fontsize=9, color="#333")
        y -= 0.028

    pdf.savefig(fig)
    plt.close(fig)


def _pagina_indice(pdf, por_chapa):
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.text(0.5, 0.95, "Índice das chapas", ha="center", fontsize=16, fontweight="bold")
    y = 0.90
    fig.text(0.08, y, "Chapa", fontsize=9, fontweight="bold")
    fig.text(0.16, y, "Peças (código × posição)", fontsize=9, fontweight="bold")
    fig.text(0.80, y, "Aprov.", fontsize=9, fontweight="bold")
    y -= 0.018
    fig.add_artist(plt.Line2D([0.08, 0.94], [y, y], color="#ccc", linewidth=0.8, transform=fig.transFigure))
    y -= 0.02
    for chapa, pecas in sorted(por_chapa.items()):
        codigos = ", ".join(p.item.peca.codigo for p in pecas)
        if len(codigos) > 78:
            codigos = codigos[:75] + "..."
        fig.text(0.08, y, f"{chapa:02d}", fontsize=8.5, family="monospace")
        fig.text(0.16, y, codigos, fontsize=8.2)
        fig.add_artist(plt.Rectangle((0.80, y - 0.006), 0.02, 0.014, transform=fig.transFigure,
                                      fill=False, edgecolor="#888", linewidth=0.8))
        y -= 0.022
        if y < 0.06:
            pdf.savefig(fig)
            plt.close(fig)
            fig = plt.figure(figsize=(8.27, 11.69))
            y = 0.95
    pdf.savefig(fig)
    plt.close(fig)


def _pagina_chapa(pdf, chapa_label, pecas, subtitulo=""):
    fig = plt.figure(figsize=(8.27, 11.69))
    ax = _sheet_axes(fig, [0.08, 0.34, 0.86, 0.56], f"CHAPA {chapa_label}", subtitulo)

    legenda = []
    area_pecas = 0.0
    for idx, p in enumerate(pecas, start=1):
        cor = PALETTE[idx % len(PALETTE)]
        rings = _rings(p.poly_global)
        for j, ring in enumerate(rings):
            if j == 0:
                ax.add_patch(MplPolygon(ring, closed=True, fill=True, facecolor=cor,
                                         edgecolor="#c0392b", linewidth=1.2, zorder=2))
            else:
                ax.add_patch(MplPolygon(ring, closed=True, fill=True, facecolor="white",
                                         edgecolor="#c0392b", linewidth=1.0, zorder=3))
        minx, miny, maxx, maxy = p.poly_global.bounds
        area_pecas += p.poly_global.area
        cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
        ax.text(cx, cy, str(idx), ha="center", va="center", fontsize=10, fontweight="bold",
                color="#1a2b4c", zorder=5)
        # cota de largura/altura discretas nos cantos da peça
        ax.text(minx + 2, miny + 2, f"{maxx-minx:.0f}×{maxy-miny:.0f}", fontsize=5.2, color="#7a3b3b",
                ha="left", va="bottom", zorder=5)
        nome = p.item.peca.nome
        if p.item.quantidade > 1:
            nome += f" ({p.instancia}/{p.item.quantidade})"
        legenda.append((idx, p.item.peca.codigo, nome, p.item.grupo, maxx - minx, maxy - miny))

    ax.set_xlim(-25, c.SHEET_W + 25)
    ax.set_ylim(-15, c.SHEET_H + 55)
    ax.set_aspect("equal")
    ax.axis("off")

    aproveitamento = 100.0 * area_pecas / (c.USABLE_SPAN * c.USABLE_SPAN)
    fig.text(0.08, 0.315, f"{len(pecas)} peça(s) nesta chapa · aproveitamento ≈ {aproveitamento:.0f}% "
             f"da área útil", fontsize=8.5, color="#444")

    # legenda em tabela
    y = 0.29
    fig.text(0.08, y, "#", fontsize=8, fontweight="bold")
    fig.text(0.12, y, "Código", fontsize=8, fontweight="bold")
    fig.text(0.34, y, "Nome", fontsize=8, fontweight="bold")
    fig.text(0.72, y, "Grupo", fontsize=8, fontweight="bold")
    fig.text(0.85, y, "Dimensão (mm)", fontsize=8, fontweight="bold")
    y -= 0.014
    fig.add_artist(plt.Line2D([0.08, 0.96], [y, y], color="#ccc", linewidth=0.7, transform=fig.transFigure))
    y -= 0.018
    for idx, codigo, nome, grupo, w, h in legenda:
        if y < 0.03:
            break
        fig.text(0.08, y, str(idx), fontsize=7.6, family="monospace")
        fig.text(0.12, y, codigo, fontsize=7.6, family="monospace")
        fig.text(0.34, y, nome[:46], fontsize=7.6)
        fig.text(0.72, y, grupo, fontsize=7.6, color="#666")
        fig.text(0.85, y, f"{w:.0f} × {h:.0f}", fontsize=7.6)
        y -= 0.016

    pdf.savefig(fig)
    plt.close(fig)


def gerar_mapa_pdf(caminho: str):
    itens = M.montar_pecas()
    itens_cupom = [i for i in itens if i.grupo == "cupom"]
    itens_moveis = [i for i in itens if i.grupo != "cupom"]

    a_cortar = N.descontar_ja_cortadas(itens_moveis, M.resolver_ja_cortadas(itens))
    colocados = N.empacotar(a_cortar, primeira_chapa=c.PRIMEIRA_CHAPA)
    colocados_cupom = N.empacotar(itens_cupom)

    por_chapa: dict[int, list] = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p)

    stats = {
        "ext_w": c.EXT_W, "ext_h": c.EXT_H, "ext_d": c.EXT_D, "inner_w": c.INNER_W,
        "mat_t": c.MATERIAL_T, "sheet": c.SHEET_W, "usable": c.USABLE_SPAN,
        "n_pecas": sum(i.quantidade for i in itens),
        "n_chapas": len(por_chapa),
        "chapa_ini": c.PRIMEIRA_CHAPA,
    }

    with PdfPages(caminho) as pdf:
        _pagina_capa(pdf, stats)
        _pagina_indice(pdf, por_chapa)
        _pagina_chapa(pdf, "00 · TESTE", colocados_cupom,
                      "Cupom de kerf (7 ranhuras 2,8–3,4mm) + par finger-joint de QC — corte antes de tudo")
        for chapa, pecas in sorted(por_chapa.items()):
            _pagina_chapa(pdf, f"{chapa:02d}", pecas)


if __name__ == "__main__":
    destino = os.path.join(os.path.dirname(__file__), "..", "MAPA_DE_CORTE.pdf")
    gerar_mapa_pdf(destino)
    print("PDF gerado:", destino)
