"""Confere os coolers na face de fora da lateral esquerda: posição, choque
com as corrediças já presas, apoio (berço) e fluxo de ar.

    python calculos/coolers_externos.py

Usa hardware/layout.py (fonte única das posições).
"""
from __future__ import annotations

import math
import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware"))
import layout as L  # noqa: E402

G = 9.81


def sobrepoe(a0, a1, b0, b1, folga=0.0):
    return a0 < b1 + folga and a1 > b0 - folga


def main() -> list[str]:
    erros = []
    corr = L.faixas_corredicas()
    print("Corrediças já presas na LAT_E (Z): " + ", ".join(f"{a:.1f}–{b:.1f}" for a, b in corr))

    # 1. Peltier, prensa e furos de fios fora das corrediças (a porca e a corrediça ficam do lado de dentro)
    z0, z1 = L.PELTIER_Z - L.FURO_PELTIER / 2, L.PELTIER_Z + L.FURO_PELTIER / 2
    for a, b in corr:
        if sobrepoe(z0, z1, a, b, 3.0):
            erros.append(f"furo da Peltier (Z {z0:.0f}–{z1:.0f}) a menos de 3 mm da corrediça ({a:.0f}–{b:.0f})")
    folgas = [min(abs(z0 - b), abs(a - z1)) for a, b in corr]
    print(f"Furo da Peltier: Z {z0:.1f}–{z1:.1f}; folga até a corrediça mais próxima {min(folgas):.1f} mm")
    for z in L.SUPORTE_PARAFUSOS_Z:
        for a, b in corr:
            if sobrepoe(z - 7, z + 7, a, b):      # arruela larga Ø14
                erros.append(f"parafuso do suporte em Z {z} bate na corrediça {a:.0f}–{b:.0f}")

    # 2. coolers: posição, distância entre eles e até o bloco da dobradiça
    caixas = [L.cooler_caixa(i) for i in range(2)]
    for i, (x0, x1, y0, y1, zb, zt) in enumerate(caixas, 1):
        print(f"Cooler {i}: X {x0:.0f} a {x1:.1f} (sai {-x0:.0f} mm da lateral), Y {y0:.0f}–{y1:.0f}, Z {zb:.0f}–{zt:.0f}")
    gap = caixas[1][2] - caixas[0][3]
    print(f"Entre os coolers: {gap:.0f} mm (furo dos fios da baia em Y {L.FURO_FIOS_BAIA[0]:.0f})")
    if gap < 20:
        erros.append("coolers perto demais")
    bloco_fim = L.BLOCO_DOB_LARGURA - L.AFASTAMENTO_PORTA
    print(f"Bloco da dobradiça vai até Y {bloco_fim:.0f}; cooler 1 começa em Y {caixas[0][2]:.0f}")
    if caixas[0][2] - bloco_fim < 30:
        erros.append("cooler muito perto do bloco da dobradiça")
    if caixas[1][3] > 494:
        erros.append("cooler passa do fundo falso (não há baia atrás)")

    # 3. apoio: berço + 2 mãos-francesas por cooler, presos na LAT_E por 4 parafusos M4
    massa = L.COOLER_MASSA + 0.15                      # + berço e mãos-francesas [est]
    peso = massa * G
    braco = (L.COOLER_A + L.PELTIER_ESP - L.T) / 2 / 1000   # centro de massa ~ no meio do cooler
    momento = peso * braco
    alavanca = (L.SUPORTE_PARAFUSOS_Z[1] - L.SUPORTE_PARAFUSOS_Z[0]) / 1000
    tracao = momento / alavanca / 2                    # 2 parafusos de cima
    corte = peso / 4
    print(f"\nApoio de cada cooler [calc]: peso {peso:.1f} N, momento {momento:.2f} N·m, "
          f"tração em cada parafuso de cima {tracao:.1f} N, corte por parafuso {corte:.1f} N")
    print("A prensa da Peltier só aperta a pastilha; o peso vai todo para o berço.")
    if tracao > 50:
        erros.append("tração alta nos parafusos do suporte")

    # 4. ar: ventoinha embaixo sopra para cima; entra pelo berço vazado, sai livre por cima
    zb = caixas[0][4]
    print(f"\nVentoinha de {zb:.0f} a {zb + L.VENTOINHA_ESP:.0f} mm; grade do berço em Z {L.berco_z():.0f}–"
          f"{L.berco_z() + L.BERCO_ESPESSURA:.0f}; vão para o ar entrar: {L.BERCO_FOLGA:.0f} mm")
    area_vent = math.pi * (0.120 / 2) ** 2 * 1e4
    print(f"Área da ventoinha {area_vent:.0f} cm²; a grade do berço precisa de pelo menos 60% vazado (gerador da porta confere)")
    if L.berco_z() < 0:
        erros.append("berço abaixo da base do armário")

    print("\n" + ("\n".join("ERRO: " + e for e in erros) if erros else "Sem conflitos."))
    return erros


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
