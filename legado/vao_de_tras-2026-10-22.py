"""Confere se os coolers do lado quente cabem no vão de trás e calcula os
furos de ventilação do traseiro.

    python calculos/vao_de_tras.py

Coordenadas olhando o armário de frente, a partir do canto externo de baixo
à esquerda: X para a direita, Y para o fundo, Z para cima, em mm.

Origem dos números:
[ds]   Cooler Master Hyper 212 Spectrum V3 (RR-S4NA-17PA-R1), página da
       KaBuM em 22/10/2026: 124 x 73 x 152 mm (C x L x A), ventoinha
       120 x 120 x 25 mm, 12 V 0,26 A, 0,65 kg.
       https://www.kabum.com.br/produto/532493
[ds]   TEC1-12703: 40 x 40 mm; espessura ~3,8 mm [est, medir com paquímetro].
[calc] Calor no vão: 2 pastilhas x Qh (calculos/gaveta_fria.py, pior caso a
       32 °C) + ventoinhas.
"""
from __future__ import annotations

import math
import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "armario", "gerador"))
import config as c  # noqa: E402

T = c.MATERIAL_T

# ---- cooler e pastilha -----------------------------------------------------
COOLER_L, COOLER_P, COOLER_A = 124.0, 73.0, 152.0   # C x L x A [ds]
VENT_ESP = 25.0                                      # espessura da ventoinha [ds]
PELTIER_LADO, PELTIER_ESP = 40.0, 3.8

# ---- baia fria na coluna A, em cima (docs/DECISOES.md) ----------------------
ISO = 50.0          # EPS 50 mm (docs/DECISOES.md)
BAIA_X = (c.X_COL_A[0] + T, c.X_COL_A[1] + T)        # externo
BAIA_Z = (201.0, c.GAVETEIRO_Z[1])
Z_PELTIER = (BAIA_Z[0] + BAIA_Z[1]) / 2               # centro da baia
X_PELTIER = (110.0, 240.0)                            # centro de cada pastilha

# ---- calor e ar --------------------------------------------------------------
QH_TOTAL = 72.0 + 2 * 3.12        # W: 2 x Qh a 32 °C + 2 ventoinhas [calc]
DT_AR = 5.0                        # K de aumento aceitável no ar que passa
V_FURO = 1.5                       # m/s máximo no furo (ruído e perda de carga) [est]
D_FURO = 38.0                      # serra copo de 38 mm que o grupo já tem


def main():
    vao_y = (c.CABLE_CAVITY_Y0, c.CABLE_CAVITY_Y1)
    prof_vao = vao_y[1] - vao_y[0]
    ocupado = PELTIER_ESP / 2 + COOLER_A      # a pastilha fica metade no furo do fundo falso
    folga = prof_vao - ocupado
    print(f"Vão de trás: Y {vao_y[0]:.0f} a {vao_y[1]:.0f} = {prof_vao:.0f} mm")
    print(f"Pastilha (metade fora do fundo falso) + cooler: {ocupado:.0f} mm -> folga até o traseiro {folga:.0f} mm")
    assert folga > 20, "cooler não cabe no vão de trás"

    # ventoinha embaixo do bloco de aletas, soprando para cima (Z)
    print("\nCoolers (base no fundo falso, ventoinha embaixo soprando para cima):")
    caixas = []
    for i, x in enumerate(X_PELTIER, 1):
        x0, x1 = x - COOLER_L / 2, x + COOLER_L / 2
        z0, z1 = Z_PELTIER - COOLER_P / 2 - VENT_ESP, Z_PELTIER + COOLER_P / 2
        caixas.append((x0, x1, z0, z1))
        print(f"  cooler {i}: X {x0:.0f} a {x1:.0f}, Z {z0:.0f} a {z1:.0f}")
        assert x0 >= BAIA_X[0] - 1e-9 and x1 <= BAIA_X[1] + 1e-9, "cooler sai de trás da coluna A"
    assert caixas[0][1] <= caixas[1][0], "coolers se sobrepõem"
    print(f"  folga entre os dois: {caixas[1][0] - caixas[0][1]:.0f} mm")

    # ar
    vazao = QH_TOTAL / (1.2 * 1005 * DT_AR)            # m³/s
    area_min = vazao / V_FURO * 1e4                    # cm²
    a_furo = math.pi * (D_FURO / 20) ** 2              # cm²
    n = math.ceil(area_min / a_furo)
    print(f"\nCalor no vão: {QH_TOTAL:.0f} W -> vazão para subir {DT_AR:.0f} K: {vazao*1000:.1f} L/s "
          f"({vazao*3600:.0f} m³/h)")
    print(f"Área mínima por lado (entrada e saída) a {V_FURO} m/s: {area_min:.0f} cm² = {n} furos de Ø{D_FURO:.0f} "
          f"({a_furo:.1f} cm² cada)")

    # grade: 2 fileiras x 4 colunas embaixo (entrada) e em cima (saída), no traseiro
    xs = [75.0, 135.0, 215.0, 275.0]
    z_ent = [caixas[0][2] - 75.0, caixas[0][2] - 20.0]
    z_sai = [caixas[0][3] + 45.0, caixas[0][3] + 100.0]
    furos = [("entrada", x, z) for z in z_ent for x in xs] + [("saída", x, z) for z in z_sai for x in xs]
    print(f"\nFuros de Ø{D_FURO:.0f} no traseiro (centro, X e Z):")
    for nome, x, z in furos:
        print(f"  {nome:8s} X {x:5.0f}  Z {z:5.0f}")
    total = {k: sum(1 for f in furos if f[0] == k) * a_furo for k in ("entrada", "saída")}
    print("Área: " + ", ".join(f"{k} {v:.0f} cm²" for k, v in total.items()))
    assert all(v >= area_min for v in total.values())

    # distância mínima entre furos (alma de MDF) e até as bordas
    alma = min(math.dist((a[1], a[2]), (b[1], b[2])) - D_FURO
               for i, a in enumerate(furos) for b in furos[i + 1:])
    print(f"Menor alma de MDF entre furos: {alma:.0f} mm")
    assert alma >= 15
    # outros furos do traseiro: cabo de força (X 95, Z 28, Ø10) e USB da câmera (Z 835)
    for nome, x, z, d in (("cabo de força", 95, 28, 10),):
        dmin = min(math.dist((x, z), (f[1], f[2])) - (d + D_FURO) / 2 for f in furos)
        print(f"Distância até o furo do {nome}: {dmin:.0f} mm")
        assert dmin > 10


if __name__ == "__main__":
    main()
