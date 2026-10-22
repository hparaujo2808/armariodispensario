"""Gera o pacote da v2.4 (porta e peças novas) ao lado do pacote da V2.3.

    cd armario/gerador
    python porta_main.py

Saídas em armario/:
    00_CUPOM_PORTA_CORTE.dxf / 00_CUPOM_PORTA_NOMES.dxf   cortar ANTES de tudo
    corte/CHAPA_24.dxf ...   gravacao/CHAPA_24_NOMES.dxf ...   mapas/CHAPA_24.png ...
    mapas/CUPOM_PORTA.png, mapas/PORTA_FRENTE.png, mapas/PORTA_COLISAO.png
    VALIDACAO_PORTA.json, LISTA_PECAS_PORTA.csv, MANUAL_PORTA.md

Não mexe nas chapas 22 e 23 nem no LEIA_PRIMEIRO.md da V2.3.
"""
from __future__ import annotations

import csv
import json
import os
import sys

import ezdxf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Rectangle
from shapely.affinity import translate
from shapely.geometry import box
from shapely.validation import explain_validity

import config as c
import nesting as N
import porta as P
import porta_colisao as COL
from montagem import ItemBOM

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
TXT_H = 6.0


# ------------------------------------------------------------------ itens --
def itens():
    porta = [ItemBOM(p, "porta") for p in P.pecas_porta()]
    armario = [ItemBOM(p, "armário") for p in P.pecas_armario()]
    cupom = [ItemBOM(p, "cupom") for p in P.cupom()]
    return porta + armario, cupom


# ---------------------------------------------------------------- exportar --
def _rings(poly):
    polys = getattr(poly, "geoms", [poly])
    for g in polys:
        yield list(g.exterior.coords)
        for i in g.interiors:
            yield list(i.coords)


def exportar(colocados, nome_corte, nome_grav):
    por_chapa: dict[int, list] = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p)
    arquivos = []
    for chapa, pecas in sorted(por_chapa.items()):
        dc, dg = ezdxf.new(setup=True), ezdxf.new(setup=True)
        dc.header["$INSUNITS"] = 4
        dg.header["$INSUNITS"] = 4
        mc, mg = dc.modelspace(), dg.modelspace()
        for p in pecas:
            for ring in _rings(p.poly_global):
                mc.add_lwpolyline([(x, y) for x, y in ring], close=True, dxfattribs={"color": c.COLOR_CUT})
            minx, miny, _, _ = p.poly_global.bounds
            peca = p.item.peca
            mg.add_text(peca.codigo, dxfattribs={"height": TXT_H, "color": c.COLOR_ENGRAVE}).set_placement((minx + 3, miny + 3))
            for texto, x, y, h in getattr(peca, "gravar", []):
                mg.add_text(texto, dxfattribs={"height": h, "color": c.COLOR_ENGRAVE}).set_placement((x + p.x, y + p.y))
            for risco in getattr(peca, "riscos", []):
                mg.add_lwpolyline([(x + p.x, y + p.y) for x, y in risco], dxfattribs={"color": c.COLOR_ENGRAVE})
        a = nome_corte(chapa)
        b = nome_grav(chapa)
        os.makedirs(os.path.dirname(a), exist_ok=True)
        os.makedirs(os.path.dirname(b), exist_ok=True)
        dc.saveas(a)
        dg.saveas(b)
        arquivos.append((chapa, a, b))
    return arquivos


def mapa(colocados, caminho, titulo):
    fig, ax = plt.subplots(figsize=(8, 8.8))
    ax.add_patch(Rectangle((0, 0), c.SHEET_W, c.SHEET_H, fill=False, edgecolor="black", lw=1))
    ax.add_patch(Rectangle((c.USABLE_MIN, c.USABLE_MIN), c.USABLE_SPAN, c.USABLE_SPAN, fill=False,
                           edgecolor="lightgray", lw=0.7, ls="--"))
    legenda = []
    for idx, p in enumerate(colocados, 1):
        for ring in _rings(p.poly_global):
            ax.add_patch(MplPolygon(ring, closed=True, facecolor="#eef3f8", edgecolor="#c0392b", lw=0.6))
        minx, miny, maxx, maxy = p.poly_global.bounds
        ax.text((minx + maxx) / 2, (miny + maxy) / 2, str(idx), ha="center", va="center", fontsize=6, color="#1a2b4c")
        legenda.append(f"{idx:02d} {p.item.peca.codigo}")
    ax.set_xlim(-20, c.SHEET_W + 20)
    ax.set_ylim(-20, c.SHEET_H + 20)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(titulo, loc="left", fontsize=12, fontweight="bold")
    col = "   ".join(legenda)
    fig.text(0.02, 0.01, "\n".join(_quebrar(col, 150)), fontsize=5.5, family="monospace", va="bottom")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(caminho, dpi=110)
    plt.close(fig)


def _quebrar(texto, n):
    linhas, atual = [], ""
    for palavra in texto.split("   "):
        if len(atual) + len(palavra) + 3 > n:
            linhas.append(atual)
            atual = palavra
        else:
            atual = (atual + "   " + palavra).strip()
    return linhas + [atual]


def figura_porta(caminho):
    """Frente da porta (vista de fora) com os recortes e a posição dos componentes."""
    pe = P.pele_ext()
    from shapely.affinity import scale
    poly = scale(pe.poly, xfact=-1, origin=(c.PORTA_W / 2, 0))   # desfaz o espelhamento: vista de frente
    fig, ax = plt.subplots(figsize=(8, 8))
    for ring in _rings(poly):
        ax.add_patch(MplPolygon(ring, closed=True, facecolor="#f5e6cc", edgecolor="#8e5b2b", lw=0.8))
    cx, cz = c.TECLADO_CENTRO
    ax.add_patch(Rectangle((P.u(cx) - c.TECLADO[0] / 2, P.v(cz) - c.TECLADO[1] / 2), *c.TECLADO,
                           fill=False, edgecolor="#2c3e50", lw=1, ls="--"))
    ax.text(P.u(cx), P.v(cz), "teclado\n(colado)", ha="center", va="center", fontsize=7)
    for nome, (x, z) in (("LCD", c.LCD_CENTRO), ("leitor", c.AS608_CENTRO), ("buzzer", c.BUZZER_CENTRO),
                         ("puxador", c.PUXADOR_CENTRO)):
        ax.annotate(nome, (P.u(x), P.v(z)), (P.u(x) - 150, P.v(z) + 40), fontsize=7,
                    arrowprops=dict(arrowstyle="-", lw=0.6))
    za, zb = P.furos_dobradica()
    ax.plot([0, 0], [P.v(c.DOB_Z0), P.v(c.DOB_Z0 + c.DOB_COMPRIMENTO)], color="#7f8c8d", lw=3)
    ax.text(8, P.v(c.DOB_Z0) + 10, "dobradiça (por dentro)", fontsize=7, rotation=90)
    ax.set_xlim(-30, c.PORTA_W + 30)
    ax.set_ylim(-30, c.PORTA_H + 30)
    ax.set_aspect("equal")
    ax.set_title(f"Porta vista de frente — {c.PORTA_W:.0f} × {c.PORTA_H:.0f} × {P.PORTA_ESP:.0f} mm", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)


# --------------------------------------------------------------- validação --
def validar_geometria(colocados):
    erros = []
    for p in colocados:
        g = p.poly_global
        if not g.is_valid:
            erros.append(f"{p.item.peca.codigo}: contorno inválido ({explain_validity(g)})")
        if g.geom_type != "Polygon":
            erros.append(f"{p.item.peca.codigo}: a peça saiu em mais de um pedaço")
        for ring in _rings(g):
            if ring[0] != ring[-1]:
                erros.append(f"{p.item.peca.codigo}: contorno aberto")
    return erros + N.validar_sem_sobreposicao(colocados)


def validar_miolo():
    """Peças do miolo da porta não se sobrepõem (planta u × v), fora os
    cruzamentos de meia-madeira entre nervuras horizontais e verticais."""
    T = c.MATERIAL_T
    u0, u1 = c.PORTA_MONT_E, c.PORTA_W - c.PORTA_MONT_D
    x0, x1, z0, z1 = c.JANELA_INT
    m = {
        "montante esquerdo": box(0, 0, u0, c.PORTA_H),
        "montante direito": box(u1, 0, c.PORTA_W, c.PORTA_H),
        "trilho de baixo": box(u0, 0, u1, T),
        "trilho de cima": box(u0, c.PORTA_H - T, u1, c.PORTA_H),
        "moldura da janela (baixo)": box(P.u(x0) - 6, P.v(z0) - 6, u1, P.v(z0) - 6 + T),
        "moldura da janela (cima)": box(P.u(x0) - 6, P.v(z1) + 3, u1, P.v(z1) + 3 + T),
        "moldura da janela (esquerda)": box(P.u(x0) - 6, P.v(z0) - 3, P.u(x0) - 6 + T, P.v(z1) + 3),
    }
    for i, vv in enumerate(c.PORTA_NERV_H, 1):
        m[f"nervura H{i}"] = box(u0, vv - T / 2, u1, vv + T / 2)
    for i, uu in enumerate(c.PORTA_NERV_V, 1):
        m[f"nervura V{i}"] = box(uu - T / 2, T, uu + T / 2, c.PORTA_H - T)
    for nome, (cx, cz), (w, h) in (("moldura do LCD", c.LCD_CENTRO, (c.LCD_PLACA[0] + 28, c.LCD_PLACA[1] + 16)),
                                   ("moldura do leitor", c.AS608_CENTRO, (c.AS608_MODULO[0] + 28, c.AS608_MODULO[1] + 14))):
        m[nome] = box(P.u(cx) - w / 2, P.v(cz) - h / 2, P.u(cx) + w / 2, P.v(cz) + h / 2)
    cx, cz = c.PUXADOR_CENTRO
    cava = box(P.u(cx) - c.PUXADOR[0] / 2, P.v(cz) - c.PUXADOR[1] / 2, P.u(cx) + c.PUXADOR[0] / 2, P.v(cz) + c.PUXADOR[1] / 2)
    erros = []
    nomes = list(m)
    for i, a in enumerate(nomes):
        for b in nomes[i + 1:]:
            cruz = ("nervura H" in a and "nervura V" in b) or ("nervura H" in b and "nervura V" in a)
            if cruz:
                continue
            area = m[a].intersection(m[b]).area
            if area > 1e-6:
                erros.append(f"miolo da porta: {a} e {b} se sobrepõem ({area:.1f} mm²)")
    if not m["montante direito"].contains(cava):
        erros.append("cava do puxador sai do montante direito")
    return erros


def massa_porta(itens_porta):
    area = sum(i.peca.poly.area for i in itens_porta) / 1e6
    return area * c.MATERIAL_T / 1000 * c.MDF_DENSIDADE


# --------------------------------------------------------------- principal --
def main():
    moveis, cupom = itens()
    colocados = N.empacotar(moveis, primeira_chapa=c.PRIMEIRA_CHAPA_PORTA)
    colocados_cupom = N.empacotar(cupom, primeira_chapa=1)
    erros = validar_geometria(colocados) + validar_geometria(colocados_cupom) + validar_miolo()
    if N.n_chapas(colocados_cupom) != 1:
        erros.append("o cupom de teste não coube numa chapa só")
    for p in P.bercos():
        if hasattr(p, "vazado") and p.vazado < 0.60:
            erros.append(f"{p.codigo}: grade com só {p.vazado:.0%} vazado (mínimo 60%)")
    colisoes = COL.checar()
    for col in colisoes:
        erros.append(f"colisão a {col['angulo']}°: {col['parte']} × {col['obstaculo']} ({col['area']:.0f} mm²)")
    folga_gav = COL.folga_gavetas()
    if folga_gav < c.FOLGA_PORTA_GAVETA_MIN:
        erros.append(f"folga porta–gaveta de {folga_gav:.1f} mm, abaixo do mínimo {c.FOLGA_PORTA_GAVETA_MIN}")
    if erros:
        raise SystemExit("Validação da porta falhou:\n  " + "\n  ".join(erros))

    corte = lambda ch: os.path.join(RAIZ, "corte", f"CHAPA_{ch:02d}.dxf")          # noqa: E731
    grav = lambda ch: os.path.join(RAIZ, "gravacao", f"CHAPA_{ch:02d}_NOMES.dxf")   # noqa: E731
    arquivos = exportar(colocados, corte, grav)
    exportar(colocados_cupom, lambda ch: os.path.join(RAIZ, "00_CUPOM_PORTA_CORTE.dxf"),
             lambda ch: os.path.join(RAIZ, "00_CUPOM_PORTA_NOMES.dxf"))

    pasta_mapas = os.path.join(RAIZ, "mapas")
    por_chapa: dict[int, list] = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p)
    for ch, ps in sorted(por_chapa.items()):
        mapa(ps, os.path.join(pasta_mapas, f"CHAPA_{ch:02d}.png"), f"v2.4 · CHAPA {ch:02d}")
    mapa(colocados_cupom, os.path.join(pasta_mapas, "CUPOM_PORTA.png"), "v2.4 · CUPOM DE TESTE DA PORTA")
    figura_porta(os.path.join(pasta_mapas, "PORTA_FRENTE.png"))
    COL.figura(os.path.join(pasta_mapas, "PORTA_COLISAO.png"))

    itens_porta = [i for i in moveis if i.grupo == "porta"]
    massa = massa_porta(itens_porta)
    with open(os.path.join(RAIZ, "LISTA_PECAS_PORTA.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo", "nome", "grupo", "largura_mm", "altura_mm", "chapa"])
        for p in colocados + colocados_cupom:
            minx, miny, maxx, maxy = p.item.peca.poly.bounds
            chapa = "cupom" if p in colocados_cupom else f"{p.chapa:02d}"
            w.writerow([p.item.peca.codigo, p.item.peca.nome, p.item.grupo, f"{maxx - minx:.1f}", f"{maxy - miny:.1f}", chapa])

    fol = {a: COL.folgas(a) for a in (0, 45, 90)}
    validacao = {
        "versao": "v2.4 (porta)",
        "chapas": [ch for ch, _, _ in arquivos],
        "pecas": len(colocados),
        "pecas_cupom": len(colocados_cupom),
        "contornos_fechados_e_validos": True,
        "sem_sobreposicao_e_dentro_da_area_util": True,
        "miolo_da_porta_sem_sobreposicao": True,
        "colisoes_0_a_90_graus": 0,
        "folga_porta_gavetas_mm": round(folga_gav, 1),
        "espessura_porta_mm": P.PORTA_ESP,
        "massa_porta_kg_sem_componentes": round(massa, 2),
        "folgas_mm": {str(a): {k: [round(v[0], 1), v[1]] for k, v in d.items()} for a, d in fol.items()},
    }
    with open(os.path.join(RAIZ, "VALIDACAO_PORTA.json"), "w", encoding="utf-8") as f:
        json.dump(validacao, f, indent=2, ensure_ascii=False)

    import manual_porta
    manual_porta.escrever(os.path.join(RAIZ, "MANUAL_PORTA.md"), arquivos, colocados, colocados_cupom, validacao)
    print(f"OK: {len(colocados)} peças em {len(arquivos)} chapas (CHAPA_{arquivos[0][0]:02d} a "
          f"CHAPA_{arquivos[-1][0]:02d}) + cupom com {len(colocados_cupom)} peças. Porta {massa:.1f} kg sem componentes.")


if __name__ == "__main__":
    main()
