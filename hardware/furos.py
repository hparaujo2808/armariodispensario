"""Furos feitos à mão nas peças já montadas, calculados a partir do config.py
da V2.3 e de hardware/layout.py. Também confere se algum furo cai em cima de
prateleira, nervura, corrediça, borda ou outro furo.

    python hardware/furos.py

Pior caso: armário todo colado. Por isso só há furos nas duas laterais, feitos
POR FORA com os gabaritos cortados a laser (Fase 5). Nenhum furo no fundo
falso nem no traseiro.

Coordenadas na face de fora de cada lateral: Y = distância da borda da frente,
Z = altura a partir de baixo (a lateral encosta na mesa).
"""
from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import layout as L  # noqa: E402

c = L.c
T = L.T

_prateleiras = [c.TETO_GAV_Z, c.PRAT2_Z, c.PRAT1_Z, c.PCAM_Z]
_nervuras = [(z - c.NERVURA_H, z) for z in (c.PRAT2_Z[0], c.PRAT1_Z[0], c.PCAM_Z[0])]
_nerv_y = [c.SHELF_DEPTH * (i + 0.5) / c.N_NERVURAS_POR_PRATELEIRA for i in range(c.N_NERVURAS_POR_PRATELEIRA)]

# O que está colado ou preso na face de DENTRO de cada lateral: (nome, y0, y1, z0, z1)
_comum = ([(f"prateleira em Z {z0:.0f}", 0, c.SHELF_DEPTH, z0, z1) for z0, z1 in _prateleiras]
          + [(f"nervura Y {y:.0f} Z {z0:.0f}", y - T / 2, y + T / 2, z0, z1) for y in _nerv_y for z0, z1 in _nervuras]
          + [("fundo falso", c.FALSE_BACK_Y0, c.FALSE_BACK_Y1, 0, c.EXT_H),
             ("traseiro", c.BACK_Y0, c.BACK_Y1, 0, c.EXT_H)])
PROIBIDO = {
    "lateral esquerda": _comum + [(f"corrediça Z {a:.0f}–{b:.0f}", 3, 3 + c.DRAWER_SLIDE_LEN, a, b)
                                  for a, b in L.faixas_corredicas()],
    # perfil do dispensador colado na face interna da LAT_D (até 333 mm de altura)
    "lateral direita": _comum + [("perfil do dispensador", 0, c.SHELF_DEPTH, 0, 334)],
}
# o corpo da trava tampa a face de dentro da LAT_D: só os furos de fixação dela podem ficar embaixo
CORPO_TRAVA = ("corpo da trava", c.TRAVA_Y0, c.TRAVA_Y0 + c.TRAVA_CORPO[1],
               c.TRAVA_Z - c.TRAVA_CORPO[2] / 2, c.TRAVA_Z + c.TRAVA_CORPO[2] / 2)
LIMITES = {p: (0, c.EXT_D, c.BASE_Z[1], c.TOP_Z[0]) for p in PROIBIDO}
BORDA_MIN = 8.0
ALMA_MIN = 8.0


def furos() -> list[dict]:
    lista = []

    def add(peca, y, z, d, para, quadrado=False, ignora=()):
        lista.append(dict(peca=peca, a=y, b=z, d=d, para=para, quadrado=quadrado, ignora=ignora))

    E, D = "lateral esquerda", "lateral direita"
    for i, y in enumerate(L.PELTIER_Y, 1):
        add(E, y, L.PELTIER_Z, L.FURO_PELTIER, f"Peltier {i} (quadrado)", quadrado=True)
        for dy in (-L.PRENSA_DY, L.PRENSA_DY):
            add(E, y + dy, L.PELTIER_Z, L.FURO_M3, f"prensa da Peltier {i} (M3)")
        for dy in L.SUPORTE_PARAFUSOS_DY:
            for z in L.SUPORTE_PARAFUSOS_Z:
                add(E, y + dy, z, L.FURO_M4, f"suporte do cooler {i} (M4)")
    y, z, d = L.FURO_FIOS_BAIA
    add(E, y, z, d, "fios do DS18B20 da baia e das ventoinhas frias")
    for z in L.BLOCO_DOB_PARAFUSOS_Z:
        add(E, L.BLOCO_DOB_PARAFUSO_Y, z, L.FURO_M4, "bloco da dobradiça (M4)")

    for y in L.TRAVA_FUROS_Y:
        add(D, y, L.TRAVA_Z, L.FURO_M4, "fixação da trava (M4) [medir na trava]")
    y, z, d = L.FURO_FIOS_TRAVA
    add(D, y, z, d, "fios da trava e do reed")
    y, z, d = L.CAMERA_INTERNA
    add(D, y, z, d, "cabo USB da câmera interna (plugue passa)")
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
            erros.append(f"{f['peca']} (Y {f['a']:.0f}, Z {f['b']:.0f}): menos de {BORDA_MIN:.0f} mm da borda")
        zonas = list(PROIBIDO[f["peca"]])
        if f["peca"] == "lateral direita" and not f["para"].startswith("fixação da trava"):
            zonas.append(CORPO_TRAVA)
        elif f["para"].startswith("fixação da trava"):
            n, p0, p1, q0, q1 = CORPO_TRAVA            # e precisam cair dentro do corpo, com folga da borda
            if a0 < p0 + 3 or a1 > p1 - 3:
                erros.append(f"fixação da trava (Y {f['a']:.0f}): fora do corpo da trava (Y {p0:.0f}–{p1:.0f})")
        for nome, p0, p1, q0, q1 in zonas:
            if a0 < p1 and a1 > p0 and b0 < q1 and b1 > q0:
                erros.append(f"{f['peca']} (Y {f['a']:.0f}, Z {f['b']:.0f}) Ø{f['d']}: cai em {nome}")
    for i, f in enumerate(lista):
        for g in lista[i + 1:]:
            if f["peca"] != g["peca"]:
                continue
            if f["quadrado"] or g["quadrado"]:
                fa, ga = _caixa(f), _caixa(g)
                gap = max(ga[0] - fa[1], fa[0] - ga[1], ga[2] - fa[3], fa[2] - ga[3])
            else:
                gap = math.dist((f["a"], f["b"]), (g["a"], g["b"])) - (f["d"] + g["d"]) / 2
            if gap < ALMA_MIN:
                erros.append(f"{f['peca']}: furos em (Y {f['a']:.0f}, Z {f['b']:.0f}) e (Y {g['a']:.0f}, Z {g['b']:.0f}) "
                             f"com {gap:.1f} mm de MDF entre eles")
    return erros


def bloco_markdown() -> str:
    linhas = ["| Lateral | Y (da frente) | Z (de baixo) | Tamanho | Para |", "|---|---:|---:|---|---|"]
    for f in furos():
        tam = f"{f['d']:g} × {f['d']:g} mm (quadrado)" if f["quadrado"] else f"Ø {f['d']:g} mm"
        linhas.append(f"| {f['peca']} | {f['a']:.0f} | {f['b']:.0f} | {tam.replace('.', ',')} | {f['para']} |")
    return "\n".join(linhas)


if __name__ == "__main__":
    e = conferir()
    print(bloco_markdown())
    print("\n" + ("\n".join(e) if e else "Sem conflitos."))
    sys.exit(1 if e else 0)
