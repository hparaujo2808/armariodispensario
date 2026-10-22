"""Gera um desenho esquemático (vista frontal em corte) do armário v2,
mostrando gavetas, prateleiras e o porta-ataduras — para conferência visual,
não é desenho de fabricação (esse é o papel dos DXFs de corte/gravação).
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
from matplotlib.backends.backend_pdf import PdfPages

import config as c

COR_PAINEL = "#c9d6e3"
COR_BORDA = "#33475b"
COR_GAVETA = "#f4e3c1"
COR_GAVETA_BORDA = "#a9762f"
COR_DISP = "#d8ecdd"
COR_DISP_BORDA = "#2f7a4d"
COR_VAO = "#fbfbfb"


def _painel(ax, x0, x1, z0, z1, label=None, fontsize=7):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, facecolor=COR_PAINEL,
                            edgecolor=COR_BORDA, linewidth=0.8, zorder=3))


def _gaveta(ax, x0, x1, z0, z1, label):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, facecolor=COR_GAVETA,
                            edgecolor=COR_GAVETA_BORDA, linewidth=1.0, zorder=4))
    # puxador
    pw = (x1 - x0) * 0.5
    ax.add_patch(Rectangle((x0 + (x1 - x0 - pw) / 2, z0 + (z1 - z0) * 0.35), pw, (z1 - z0) * 0.12,
                            facecolor=COR_GAVETA_BORDA, edgecolor="none", zorder=5))
    ax.text((x0 + x1) / 2, (z0 + z1) / 2, label, ha="center", va="center",
            fontsize=7.5, fontweight="bold", color="#4a3410", zorder=6)


def _coluna_gavetas(ax, x0, x1, z0, z1, prefixo, n, altura):
    slack = (z1 - z0) - n * altura
    gap = max(slack / (n + 1), 0.0)
    z = z0 + gap
    for k in range(1, n + 1):
        _gaveta(ax, x0, x1, z, z + altura, f"{prefixo}{k}")
        z += altura + gap


def _prateleira_com_nervura(ax, x0, x1, z_topo, label):
    ax.add_patch(Rectangle((x0, z_topo - c.MATERIAL_T * 6), x1 - x0, c.MATERIAL_T * 6,
                            facecolor=COR_PAINEL, edgecolor=COR_BORDA, linewidth=0.8, zorder=3))
    ax.text(x0 + 6, z_topo - c.MATERIAL_T * 3, label, ha="left", va="center",
            fontsize=7, color=COR_BORDA, zorder=6)


def _dispensador(ax, x0, x1, z0, z1):
    ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, facecolor=COR_DISP,
                            edgecolor=COR_DISP_BORDA, linewidth=1.0, zorder=4))
    # rampa inclinada (linha) + 3 rolos esquemáticos
    rampa_z0 = z0 + (z1 - z0) * 0.22
    rampa_z1 = z0 + (z1 - z0) * 0.55
    ax.plot([x0 + 6, x1 - 6], [rampa_z1, rampa_z0], color=COR_DISP_BORDA, linewidth=1.2, zorder=5)
    for i, frac in enumerate((0.30, 0.55, 0.80)):
        cx = x0 + (x1 - x0) * frac
        cz = rampa_z1 - (rampa_z1 - rampa_z0) * frac + 10
        ax.add_patch(plt.Circle((cx, cz), min((x1 - x0) * 0.11, 12), facecolor="white",
                                 edgecolor=COR_DISP_BORDA, linewidth=1.0, zorder=6))
    ax.text((x0 + x1) / 2, z1 - 10, "PORTA-\nATADURAS", ha="center", va="top",
            fontsize=6.3, fontweight="bold", color="#1f5233", zorder=6)


def _cota_h(ax, x, z0, z1, texto, offset=-24):
    ax.annotate("", xy=(x, z1), xytext=(x, z0),
                arrowprops=dict(arrowstyle="<->", color="#555", linewidth=0.8))
    ax.text(x + offset, (z0 + z1) / 2, texto, ha="center", va="center", rotation=90,
            fontsize=7, color="#555")


def _cota_v(ax, z, x0, x1, texto, offset=-18):
    ax.annotate("", xy=(x1, z), xytext=(x0, z),
                arrowprops=dict(arrowstyle="<->", color="#555", linewidth=0.8))
    ax.text((x0 + x1) / 2, z + offset, texto, ha="center", va="center", fontsize=7, color="#555")


def gerar_pdf(caminho: str):
    ew, eh = c.EXT_W, c.EXT_H
    fig, ax = plt.subplots(figsize=(8.3, 11.7))  # A4 retrato

    # moldura externa (laterais, base, tampo)
    _painel(ax, 0, ew, 0, c.MATERIAL_T)                       # base
    _painel(ax, 0, ew, eh - c.MATERIAL_T, eh)                 # tampo
    _painel(ax, 0, c.MATERIAL_T, 0, eh)                       # lateral esquerda
    _painel(ax, ew - c.MATERIAL_T, ew, 0, eh)                 # lateral direita

    x_in0, x_in1 = c.MATERIAL_T, ew - c.MATERIAL_T

    # prateleiras largas
    _prateleira_com_nervura(ax, x_in0, x_in1, c.TETO_GAV_Z[1], "TETO_GAV")
    _painel(ax, x_in0, x_in1, c.PRAT2_Z[0], c.PRAT2_Z[1])
    ax.text(x_in0 + 6, (c.PRAT2_Z[0] + c.PRAT2_Z[1]) / 2, "PRAT_2", fontsize=7, va="center", color=COR_BORDA)
    _painel(ax, x_in0, x_in1, c.PRAT1_Z[0], c.PRAT1_Z[1])
    ax.text(x_in0 + 6, (c.PRAT1_Z[0] + c.PRAT1_Z[1]) / 2, "PRAT_1", fontsize=7, va="center", color=COR_BORDA)
    _painel(ax, x_in0, x_in1, c.PCAM_Z[0], c.PCAM_Z[1])
    ax.text(x_in0 + 6, (c.PCAM_Z[0] + c.PCAM_Z[1]) / 2, "P_CAM", fontsize=7, va="center", color=COR_BORDA)

    # vãos livres (rótulo)
    for (z0, z1), nome in ((c.BAY1_Z, "prateleira livre"), (c.BAY2_Z, "prateleira livre"), (c.BAY3_Z, "prateleira livre")):
        ax.text((x_in0 + x_in1) / 2, (z0 + z1) / 2, nome, ha="center", va="center",
                fontsize=7.5, color="#8a97a6", style="italic")

    # câmera
    z0, z1 = c.BAY4_Z
    ax.text((x_in0 + x_in1) / 2, (z0 + z1) / 2, "◎  compartimento da câmera", ha="center", va="center",
            fontsize=7.5, color="#8a97a6", style="italic")

    # --- gaveteiro: colunas A / B / C + dispensador ---
    z0, z1 = c.GAVETEIRO_Z
    x = x_in0
    x_end_a = x + c.COL_A_W
    _coluna_gavetas(ax, x, x_end_a, z0, z1, "A", c.N_DRAWERS_A, c.DRAWER_A_FRONT_H)
    x = x_end_a
    ax.add_patch(Rectangle((x, z0), c.MATERIAL_T, z1 - z0, facecolor=COR_BORDA, zorder=4))  # DIV_AB
    x += c.MATERIAL_T
    x_end_b = x + c.COL_B_W
    _coluna_gavetas(ax, x, x_end_b, z0, z1, "B", c.N_DRAWERS_B, c.DRAWER_BC_FRONT_H)
    x = x_end_b
    ax.add_patch(Rectangle((x, z0), c.MATERIAL_T, z1 - z0, facecolor=COR_BORDA, zorder=4))  # DIV_BC
    x += c.MATERIAL_T
    x_end_c = x + c.COL_C_W
    _coluna_gavetas(ax, x, x_end_c, z0, z1, "C", c.N_DRAWERS_C, c.DRAWER_BC_FRONT_H)
    x = x_end_c
    ax.add_patch(Rectangle((x, z0), c.MATERIAL_T, z1 - z0, facecolor=COR_BORDA, zorder=4))  # DIV_DISP
    x += c.MATERIAL_T
    _dispensador(ax, x, x_in1, z0, z1)

    # cotas gerais
    _cota_h(ax, -18, 0, eh, f"{eh:.0f} mm", offset=-16)
    _cota_v(ax, -22, 0, ew, f"{ew:.0f} mm", offset=-14)
    _cota_v(ax, eh + 34, x_in0, x_in1, f"vão interno {x_in1 - x_in0:.0f} mm", offset=12)

    ax.set_xlim(-70, ew + 40)
    ax.set_ylim(-70, eh + 90)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        "Armário dispensador — v2\nVista frontal em corte (esquemática) · "
        f"{ew:.0f} × {eh:.0f} × {c.EXT_D:.0f} mm (L×A×P) · MDF {c.MATERIAL_T:.0f}mm",
        fontsize=11, fontweight="bold", pad=18,
    )
    ax.text(
        ew / 2, -55,
        "Esquema de referência — não é desenho de fabricação. Cortes reais em corte/ e gravacao/.",
        ha="center", fontsize=7.5, color="#777",
    )

    fig.tight_layout()
    with PdfPages(caminho) as pdf:
        pdf.savefig(fig)
    plt.close(fig)


if __name__ == "__main__":
    import os
    gerar_pdf(os.path.join(os.path.dirname(__file__), "..", "ARMARIO_V2_DESENHO.pdf"))
    print("PDF gerado.")
