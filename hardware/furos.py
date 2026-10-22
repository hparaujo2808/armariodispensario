"""Furos feitos à mão nas peças já cortadas, calculados a partir do config.py
da V2.3 e das decisões em docs/DECISOES.md. Também confere se algum furo
cai em cima de rasgo, prateleira, nervura, borda ou outro furo.

    python hardware/furos.py

Coordenadas olhando o armário DE FRENTE, a partir do canto externo de baixo à
esquerda, em mm: X para a direita, Y da frente para o fundo, Z para cima.
- Laterais: posição em Y (distância da frente) e Z (altura).
- Fundo falso e traseiro: posição em X e Z. Furando o traseiro por trás, a
  medida a partir da borda esquerda de quem está atrás é 880 − X.
"""
from __future__ import annotations

import math
import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "armario", "gerador"))
sys.path.insert(0, os.path.join(RAIZ, "calculos"))
import config as c  # noqa: E402

T = c.MATERIAL_T

# Faixas que um furo não pode tocar, por peça: (nome, eixo1 min, max, eixo2 min, max)
# Laterais: eixo1 = Y, eixo2 = Z. Fundo falso e traseiro: eixo1 = X, eixo2 = Z.
_rasgos_ff = [z for z in (c.TETO_GAV_Z, c.PRAT2_Z, c.PRAT1_Z, c.PCAM_Z)]
PROIBIDO = {
    "fundo falso": [(f"rasgo da prateleira em Z {z0:.0f}", T, c.EXT_W - T, z0 - 1, z1 + 1) for z0, z1 in _rasgos_ff],
    "lateral esquerda": [(f"prateleira em Z {z0:.0f}", 0, c.SHELF_DEPTH, z0, z1) for z0, z1 in _rasgos_ff]
                        + [("fundo falso", c.FALSE_BACK_Y0, c.FALSE_BACK_Y1, 0, c.EXT_H)],
    "traseiro": [],
}
PROIBIDO["lateral direita"] = PROIBIDO["lateral esquerda"]
LIMITES = {  # (eixo1 min, max, eixo2 min, max) da peça, já descontando as peças vizinhas
    "lateral esquerda": (0, c.EXT_D, c.BASE_Z[1], c.TOP_Z[0]),
    "lateral direita": (0, c.EXT_D, c.BASE_Z[1], c.TOP_Z[0]),
    "fundo falso": (T, c.EXT_W - T, c.BASE_Z[1], c.TOP_Z[0]),
    "traseiro": (T, c.EXT_W - T, c.BASE_Z[1], c.TOP_Z[0]),
}
BORDA_MIN = 8.0
ALMA_MIN = 10.0

# Rotas de cabo por dentro das prateleiras: não podem cruzar as nervuras.
NERVURAS_Z = [(z - c.NERVURA_H, z) for z in (c.PRAT2_Z[0], c.PRAT1_Z[0], c.PCAM_Z[0])]


def furos() -> list[dict]:
    from vao_de_tras import X_PELTIER, Z_PELTIER   # mesma posição usada no cálculo dos coolers
    lista = []

    def add(peca, a, b, diam, para, quadrado=False):
        lista.append(dict(peca=peca, a=a, b=b, d=diam, para=para, quadrado=quadrado))

    # cabos da porta: 3 cabos de rede, um por furo, abaixo das nervuras da Prateleira 1
    for z in (560.0, 580.0, 600.0):
        add("lateral esquerda", 28.0, z, 10, "cabo de rede da porta (um por furo)")
        add("fundo falso", 20.0, z, 10, "cabo de rede da porta (um por furo)")
    # trava e reed (mesma rota pela lateral direita)
    add("fundo falso", 860.0, 580.0, 10, "fios da trava e do reed")
    # Peltier: furo quadrado de 40 mm e 4 furos da prensa (barra roscada M3) em volta
    for x in X_PELTIER:
        add("fundo falso", x, Z_PELTIER, 40, f"Peltier em X {x:.0f} (quadrado 40 × 40)", quadrado=True)
        for dx in (-35, 35):
            for dz in (-35, 35):
                add("fundo falso", x + dx, Z_PELTIER + dz, 3.5, "prensa da Peltier (M3)")
    # sensor da baia e fios das ventoinhas frias, entre as duas Peltier, em cima
    add("fundo falso", (X_PELTIER[0] + X_PELTIER[1]) / 2, Z_PELTIER + 55, 10, "DS18B20 da baia e ventoinhas frias")
    # câmera interna (cabo com plugue USB passa por furo de 38 mm)
    add("fundo falso", 840.0, 460.0, 38, "cabo USB da câmera interna")
    add("traseiro", 840.0, 460.0, 38, "cabo USB da câmera interna")
    # cabo de força perto da fonte (fonte no lado direito do vão, em cima da base)
    add("traseiro", 840.0, 28.0, 10, "cabo de força")
    # ventilação (calculos/vao_de_tras.py)
    for x in (75.0, 135.0, 215.0, 275.0):
        for z in (164.0, 218.0):
            add("traseiro", x, z, 38, "entrada de ar dos coolers")
        for z in (382.0, 436.0):
            add("traseiro", x, z, 38, "saída de ar dos coolers")
    return lista


def _caixa(f):
    r = f["d"] / 2
    return f["a"] - r, f["a"] + r, f["b"] - r, f["b"] + r


def conferir(lista=None) -> list[str]:
    lista = lista if lista is not None else furos()
    erros = []
    for f in lista:
        a0, a1, b0, b1 = _caixa(f)
        lim = LIMITES[f["peca"]]
        if a0 - lim[0] < BORDA_MIN or lim[1] - a1 < BORDA_MIN or b0 - lim[2] < BORDA_MIN or lim[3] - b1 < BORDA_MIN:
            erros.append(f"{f['peca']} ({f['a']:.0f}, {f['b']:.0f}): menos de {BORDA_MIN:.0f} mm da borda útil")
        for nome, p0, p1, q0, q1 in PROIBIDO[f["peca"]]:
            if a0 < p1 and a1 > p0 and b0 < q1 and b1 > q0:
                erros.append(f"{f['peca']} ({f['a']:.0f}, {f['b']:.0f}) Ø{f['d']}: cai em {nome}")
    for i, f in enumerate(lista):
        for g in lista[i + 1:]:
            if f["peca"] != g["peca"]:
                continue
            if f["quadrado"] or g["quadrado"]:
                fa = _caixa(f)
                ga = _caixa(g)
                gap = max(ga[0] - fa[1], fa[0] - ga[1], ga[2] - fa[3], fa[2] - ga[3])
            else:
                gap = math.dist((f["a"], f["b"]), (g["a"], g["b"])) - (f["d"] + g["d"]) / 2
            if gap < ALMA_MIN:
                erros.append(f"{f['peca']}: furos em ({f['a']:.0f}, {f['b']:.0f}) e ({g['a']:.0f}, {g['b']:.0f}) "
                             f"com {gap:.0f} mm de MDF entre eles")
    # rotas pelas laterais (Z do cabo) não cruzam nervuras
    for z in (560.0, 580.0, 600.0, 470.0):
        for z0, z1 in NERVURAS_Z:
            if z0 - 5 < z < z1 + 5:
                erros.append(f"rota de cabo a Z {z:.0f} cruza nervuras ({z0:.0f}–{z1:.0f})")
    return erros


def bloco_markdown() -> str:
    linhas = ["| Peça | Posição | Tamanho | Para | Como medir |", "|---|---|---|---|---|"]
    como = {"lateral esquerda": "Y da frente, Z da base", "lateral direita": "Y da frente, Z da base",
            "fundo falso": "X da esquerda, Z da base, olhando de frente",
            "traseiro": "X da esquerda olhando de frente (por trás: 880 − X), Z da base"}
    for f in furos():
        eixo = "Y" if f["peca"].startswith("lateral") else "X"
        tam = f"{f['d']:g} × {f['d']:g} mm" if f["quadrado"] else f"Ø {f['d']:g} mm".replace(".", ",")
        linhas.append(f"| {f['peca']} | {eixo} {f['a']:.0f} · Z {f['b']:.0f} | {tam} | {f['para']} | {como[f['peca']]} |")
    return "\n".join(linhas)


if __name__ == "__main__":
    e = conferir()
    print(bloco_markdown())
    print("\n" + ("\n".join(e) if e else "Sem conflitos."))
    sys.exit(1 if e else 0)
