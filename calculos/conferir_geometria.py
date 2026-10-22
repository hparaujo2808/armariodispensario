"""Calcula, a partir do config.py da V2.3, as posições que o LIGACOES.md e a
simulação usam, e aponta onde eles não batem.

    python calculos/conferir_geometria.py [pasta/do/gerador]

Por padrão lê armario/gerador/config.py.
Coordenadas: olhando o armário de frente, a partir do canto externo de baixo
à esquerda. X para a direita, Y para o fundo, Z para cima. Em mm.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "armario", "gerador")
sys.path.insert(0, pasta)
import config as c  # noqa: E402

T = c.MATERIAL_T
problemas = []


def faixa(z):
    return f"{z[0]:.1f} a {z[1]:.1f}"


def ext_x(x_interno):
    return x_interno + T     # X do config começa na face interna da lateral esquerda


print("== Alturas (Z) ==")
for nome in ("BASE_Z", "GAVETEIRO_Z", "TETO_GAV_Z", "BAY1_Z", "PRAT2_Z", "BAY2_Z", "PRAT1_Z", "BAY3_Z", "PCAM_Z", "BAY4_Z", "TOP_Z"):
    print(f"  {nome:12s} {faixa(getattr(c, nome))}")

print("\n== Colunas do gaveteiro (X externo) ==")
for nome in ("X_COL_A", "X_DIV_AB", "X_COL_B", "X_DIV_BC", "X_COL_C", "X_DIV_DISP", "X_DISP_BAY"):
    x0, x1 = getattr(c, nome)
    print(f"  {nome:11s} {ext_x(x0):.1f} a {ext_x(x1):.1f}")
centro_c = ext_x(sum(c.X_COL_C) / 2)
print(f"  centro da coluna C: {centro_c:.1f}")

# --- gavetas C: posição pela tabela de corrediças do LEIA_PRIMEIRO da V2.3 ---
# centro do membro fixo na DIV_BC (medido da borda de baixo da divisória) e
# centro do membro da gaveta (medido da borda de baixo da lateral da gaveta)
div_z0 = c.GAVETEIRO_Z[0]        # divisória apoiada na base (dentes de baixo cortados)
corredica = {"C1": (147.0, 145.0), "C2": (222.0, 23.0)}
print("\n== Gavetas da coluna C (pela tabela de corrediças da V2.3) ==")
gav = {}
for g, (fixo, membro) in corredica.items():
    z0 = div_z0 + fixo - membro
    gav[g] = (z0, z0 + c.DRAWER_BC_FRONT_H)
    print(f"  {g}: Z {faixa(gav[g])}  (centro {sum(gav[g]) / 2:.0f})")
for g, z in {"C1": 298, "C2": 101}.items():
    dono = [k for k, (a, b) in gav.items() if a <= z <= b]
    if dono != [g]:
        problemas.append(f"LIGACOES.md põe a Peltier da {g} a {z} mm, que fica atrás da {dono[0]} (C1/C2 trocadas)")

# --- nervuras x rota dos cabos da porta ---
print("\n== Nervuras (de lateral a lateral) ==")
for nome, zp in (("P_CAM", c.PCAM_Z[0]), ("PRAT_1", c.PRAT1_Z[0]), ("PRAT_2", c.PRAT2_Z[0])):
    z = (zp - c.NERVURA_H, zp)
    ys = [c.SHELF_DEPTH * (i + 0.5) / c.N_NERVURAS_POR_PRATELEIRA for i in range(c.N_NERVURAS_POR_PRATELEIRA)]
    print(f"  sob {nome}: Z {faixa(z)}, Y = " + ", ".join(f"{y:.0f}" for y in ys))
    furo = (660 - 5, 660 + 5)
    if furo[0] < z[1] and furo[1] > z[0]:
        problemas.append(f"Rota dos cabos da porta a 660 mm (Ø10) cruza as 3 nervuras sob {nome} (Z {faixa(z)}) "
                         f"e encosta na prateleira {nome} ({faixa((zp, zp + T))})")

# --- conferências gerais ---
print("\n== Medidas gerais ==")
print(f"  externo {c.EXT_W:.0f} x {c.EXT_H:.0f} x {c.EXT_D:.0f}; vão entre laterais {c.INNER_W:.0f}; "
      f"profundidade útil {c.SHELF_DEPTH:.0f}; vão de trás Y {c.CABLE_CAVITY_Y0:.0f} a {c.CABLE_CAVITY_Y1:.0f} "
      f"({c.CABLE_CAVITY_Y1 - c.CABLE_CAVITY_Y0:.0f} mm)")
if abs(centro_c - 595) > 1:
    problemas.append(f"Peltier a 595 mm da esquerda, mas a coluna C está centrada em {centro_c:.1f}")
if not (c.BAY4_Z[0] < 835 < c.BAY4_Z[1]):
    problemas.append("Câmera a 835 mm fora do compartimento de cima")

print("\n== Divergências ==")
for p in problemas:
    print("  - " + p)
print(f"\n{len(problemas)} divergência(s)")
