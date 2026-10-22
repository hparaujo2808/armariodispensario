"""Exporta os DXFs de corte/gravação e os mapas PNG por chapa."""
from __future__ import annotations

import os
import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MplPolygon

import config as c
from nesting import PecaNaChapa

LABEL_H = 18.0      # altura mínima do texto gravado (mm) — bem maior que o R2 original
LABEL_MARGIN = 6.0  # distância do texto ao canto de referência da peça


def _rings(poly):
    """Devolve todos os anéis fechados (exterior + interiores) de um Polygon."""
    rings = [list(poly.exterior.coords)]
    for interior in poly.interiors:
        rings.append(list(interior.coords))
    return rings


def _add_closed_polyline(msp, coords, color):
    pts = [(x, y) for x, y in coords]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"color": color})


def _orientation_mark(minx, miny):
    """Pequeno triângulo no canto inferior-esquerdo local da peça — referência
    de orientação única e consistente em toda peça (marca sempre o canto que
    corresponde a X=0,Y=0 no frame local: 'frente-baixo' da peça)."""
    s = 8.0
    return [(minx, miny), (minx + s, miny), (minx, miny + s), (minx, miny)]


def gerar_dxfs(colocados: list[PecaNaChapa], pasta_corte: str, pasta_gravacao: str):
    os.makedirs(pasta_corte, exist_ok=True)
    os.makedirs(pasta_gravacao, exist_ok=True)

    por_chapa: dict[int, list[PecaNaChapa]] = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p)

    for chapa, pecas in sorted(por_chapa.items()):
        doc_corte = ezdxf.new(setup=True)
        doc_corte.header["$INSUNITS"] = 4
        msp_corte = doc_corte.modelspace()

        doc_grav = ezdxf.new(setup=True)
        doc_grav.header["$INSUNITS"] = 4
        msp_grav = doc_grav.modelspace()

        for p in pecas:
            for ring in _rings(p.poly_global):
                _add_closed_polyline(msp_corte, ring, c.COLOR_CUT)

            minx, miny, maxx, maxy = p.poly_global.bounds
            codigo = p.item.peca.codigo
            texto = codigo if p.item.quantidade == 1 else f"{codigo} ({p.instancia}/{p.item.quantidade})"
            msp_grav.add_text(
                texto,
                dxfattribs={"height": LABEL_H, "color": c.COLOR_ENGRAVE, "layer": "0"},
            ).set_placement((minx + LABEL_MARGIN, miny + LABEL_MARGIN))
            _add_closed_polyline(msp_grav, _orientation_mark(minx, miny), c.COLOR_ENGRAVE)

        doc_corte.saveas(os.path.join(pasta_corte, f"CHAPA_{chapa:02d}.dxf"))
        doc_grav.saveas(os.path.join(pasta_gravacao, f"CHAPA_{chapa:02d}_NOMES.dxf"))


def gerar_mapas(colocados: list[PecaNaChapa], pasta_mapas: str):
    os.makedirs(pasta_mapas, exist_ok=True)
    por_chapa: dict[int, list[PecaNaChapa]] = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p)

    for chapa, pecas in sorted(por_chapa.items()):
        fig, ax = plt.subplots(figsize=(8, 8.6))
        ax.add_patch(Rectangle((0, 0), c.SHEET_W, c.SHEET_H, fill=False, edgecolor="black", linewidth=1))
        ax.add_patch(Rectangle((c.USABLE_MIN, c.USABLE_MIN), c.USABLE_SPAN, c.USABLE_SPAN,
                                fill=False, edgecolor="lightgray", linewidth=0.7, linestyle="--"))

        legenda = []
        for idx, p in enumerate(pecas, start=1):
            for ring in _rings(p.poly_global):
                ax.add_patch(MplPolygon(ring, closed=True, fill=True, facecolor="#eef3f8",
                                         edgecolor="#c0392b", linewidth=1.1))
            minx, miny, maxx, maxy = p.poly_global.bounds
            cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
            ax.text(cx, cy, str(idx), ha="center", va="center", fontsize=11, fontweight="bold", color="#1a2b4c")
            nome = p.item.peca.nome
            if p.item.quantidade > 1:
                nome += f" ({p.instancia}/{p.item.quantidade})"
            legenda.append((idx, p.item.peca.codigo, nome, maxx - minx, maxy - miny))

        ax.set_xlim(-20, c.SHEET_W + 20)
        ax.set_ylim(-20 - 22 * len(legenda), c.SHEET_H + 20)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(f"V2.3 · CHAPA {chapa:02d} · Área útil {int(c.USABLE_SPAN)}×{int(c.USABLE_SPAN)} mm",
                     loc="left", fontsize=13, fontweight="bold")

        y_txt = -10
        for idx, codigo, nome, w, h in legenda:
            ax.text(0, y_txt, f"{idx:02d}  {codigo}", fontsize=9, fontweight="bold", family="monospace")
            ax.text(220, y_txt, f"{nome} | {w:.0f} × {h:.0f}", fontsize=9)
            y_txt -= 20

        fig.tight_layout()
        fig.savefig(os.path.join(pasta_mapas, f"CHAPA_{chapa:02d}.png"), dpi=110)
        plt.close(fig)
