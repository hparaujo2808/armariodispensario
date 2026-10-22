"""Checagem de colisão da porta (fechada, entreaberta e aberta) com o armário,
as gavetas, a trava, as câmeras, a dobradiça e os coolers.

O movimento da porta é uma rotação em torno de um eixo vertical, então a
checagem é feita em planta (XY) para cada faixa de altura (Z) em que as duas
peças coexistem. As medidas marcadas [est] em config.py (trava, reed,
câmera) entram como caixas aproximadas.
"""
from __future__ import annotations

import math

from shapely.affinity import rotate
from shapely.geometry import box

import config as c
import porta as P

L = P.L
T = c.MATERIAL_T


def _caixa(nome, x0, x1, y0, y1, z0, z1):
    return dict(nome=nome, poly=box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), z=(min(z0, z1), max(z0, z1)))


def obstaculos():
    o = []
    H, D = c.EXT_H, c.EXT_D
    o.append(_caixa("lateral esquerda", 0, T, 0, D, 0, H))
    o.append(_caixa("lateral direita", c.EXT_W - T, c.EXT_W, 0, D, 0, H))
    o.append(_caixa("base", 0, c.EXT_W, 0, D, 0, T))
    o.append(_caixa("tampo", 0, c.EXT_W, 0, D, H - T, H))
    for nome, (z0, z1) in (("teto do gaveteiro", c.TETO_GAV_Z), ("prateleira 2", c.PRAT2_Z),
                           ("prateleira 1", c.PRAT1_Z), ("piso da câmera", c.PCAM_Z)):
        o.append(_caixa(nome, T, c.EXT_W - T, 0, c.SHELF_DEPTH, z0, z1))
    for nome, (x0, x1) in (("divisória A/B", c.X_DIV_AB), ("divisória B/C", c.X_DIV_BC), ("divisória C/disp.", c.X_DIV_DISP)):
        o.append(_caixa(nome, x0 + T, x1 + T, 0, c.SHELF_DEPTH, c.GAVETEIRO_Z[0], c.GAVETEIRO_Z[1]))
    # frentes das gavetas fechadas (A3 e A4 viraram baia fria)
    yf = c.FRENTE_GAVETA_Y
    cols = {"A": (c.X_COL_A, c.DRAWER_A_FRONT_H), "B": (c.X_COL_B, c.DRAWER_BC_FRONT_H), "C": (c.X_COL_C, c.DRAWER_BC_FRONT_H)}
    zs = {"A1": 53.4 - 48, "A2": 151.8 - 48, "B1": 5.0, "B2": 202.0, "C1": 5.0, "C2": 202.0}
    for g, z0 in zs.items():
        (x0, x1), h = cols[g[0]]
        o.append(_caixa(f"frente da gaveta {g}", x0 + T + c.DRAWER_SIDE_CLEARANCE, x1 + T - c.DRAWER_SIDE_CLEARANCE,
                        yf, yf + T, z0, z0 + h))
    o.append(_caixa("tampa da baia fria", T, T + c.COL_A_W, 0, T, c.BAIA_PISO_Z + T, c.GAVETEIRO_Z[1] - 2))
    # trava, lingueta, reed e câmera interna (medidas [est])
    tx, ty, tz = c.TRAVA_CORPO
    xi = c.EXT_W - T
    o.append(_caixa("corpo da trava", xi - tx, xi, c.TRAVA_Y0, c.TRAVA_Y0 + ty, c.TRAVA_Z - tz / 2, c.TRAVA_Z + tz / 2))
    lx, ly, lz = c.TRAVA_LINGUETA
    o.append(_caixa("lingueta", xi - tx - lx, xi - tx, c.TRAVA_Y0, c.TRAVA_Y0 + ly, c.TRAVA_Z - lz / 2, c.TRAVA_Z + lz / 2))
    o.append(_caixa("reed", xi - 12, xi, 6, 34, c.REED_Z - 7, c.REED_Z + 7))
    yc, zc, _ = L.CAMERA_INTERNA
    o.append(_caixa("câmera interna", xi - 32, xi, yc - 40, yc + 10, zc - 20, zc + 20))
    # bloco da dobradiça e coolers com berço
    o.append(_caixa("bloco da dobradiça", -c.BLOCO_DOB_CAMADAS * T, 0, -c.AFASTAMENTO_PORTA,
                    c.BLOCO_DOB_LARGURA - c.AFASTAMENTO_PORTA, c.DOB_Z0, c.DOB_Z0 + c.DOB_COMPRIMENTO))
    for i in range(2):
        x0, x1, y0, y1, z0, z1 = L.cooler_caixa(i)
        o.append(_caixa(f"cooler {i + 1}", x0, x1, y0, y1, z0, z1))
        yc = L.PELTIER_Y[i]
        o.append(_caixa(f"berço {i + 1}", -(L.COOLER_A + 15), 0, yc - (L.COOLER_L + 24) / 2, yc + (L.COOLER_L + 24) / 2,
                        min(L.SUPORTE_PARAFUSOS_Z) - 12, L.berco_z() + T))
    # tampo: caixa da eletrônica e câmera externa (por cima)
    W, Dp, Hc = (d + 2 * T for d in c.CAIXA_INT)
    o.append(_caixa("caixa da eletrônica", c.CAIXA_XY[0], c.CAIXA_XY[0] + W, c.CAIXA_XY[1], c.CAIXA_XY[1] + Dp, H, H + Hc))
    cx, cy = L.CAMERA_EXTERNA_XY
    o.append(_caixa("câmera externa", cx - 35, cx + 35, cy - 20, cy + 20, H, H + 45))
    return o


def partes_porta():
    """Partes que giram com a porta, na posição fechada."""
    yi = P.Y_PORTA_INT
    p = [_caixa("porta", P.X_PORTA0, P.X_PORTA1, P.Y_PORTA_EXT, yi, c.PORTA_Z0, c.PORTA_Z0 + c.PORTA_H)]
    for z0, z1 in ((c.PORTA_Z0, c.TRAVA_Z - 38), (c.TRAVA_Z + 38, c.PORTA_Z0 + c.PORTA_H)):
        p.append(_caixa("mata-junta", c.EXT_W - 30, c.EXT_W, yi, yi + 2 * T, z0, z1))
    x0, x1, z0, z1 = c.JANELA_INT
    m = P.TAMPA_MARGEM
    p.append(_caixa("tampa traseira", x0 - m, x1 + m, yi, yi + c.CAIXA_TRASEIRA_PROF + T, z0 - m, z1 + m))
    bx0, bx1 = c.BATENTE_X
    zb0, zb1 = c.TRAVA_Z - 35, c.TRAVA_Z + 35
    p.append(_caixa("placa do batente", bx0 - 5, P.X_PORTA1 - 2, yi, yi + 2 * T, zb0, zb1))
    jy, jz = c.BATENTE_JANELA
    yj = c.TRAVA_Y0 + c.TRAVA_LINGUETA[1] / 2
    ya = yi + 2 * T
    p.append(_caixa("braço do batente (baixo)", bx0, bx1, ya, c.BATENTE_Y1, zb0, c.TRAVA_Z - jz / 2))
    p.append(_caixa("braço do batente (cima)", bx0, bx1, ya, c.BATENTE_Y1, c.TRAVA_Z + jz / 2, zb1))
    p.append(_caixa("braço do batente (antes da janela)", bx0, bx1, ya, yj - jy / 2, c.TRAVA_Z - jz / 2, c.TRAVA_Z + jz / 2))
    p.append(_caixa("braço do batente (depois da janela)", bx0, bx1, yj + jy / 2, c.BATENTE_Y1, c.TRAVA_Z - jz / 2, c.TRAVA_Z + jz / 2))
    p.append(_caixa("ímã do reed", c.EXT_W - 22, c.EXT_W - 8, yi + 2 * T, yi + 2 * T + 7, c.REED_Z - 7, c.REED_Z + 7))
    return p


def girar(parte, angulo):
    """Abrir a porta = girar no sentido horário visto de cima (a borda direita vem para −Y)."""
    q = dict(parte)
    q["poly"] = rotate(parte["poly"], -angulo, origin=P.EIXO)
    return q


def checar(angulos=None):
    angulos = angulos if angulos is not None else list(range(0, 16)) + list(range(20, 91, 5))
    obs = obstaculos()
    resultado = []
    for a in angulos:
        for parte in partes_porta():
            g = girar(parte, a)
            for ob in obs:
                if ob["nome"] == "lingueta" and a > 0:
                    continue        # para abrir, a trava recolhe a lingueta; fechada, ela tem que caber na janela
                if g["z"][0] >= ob["z"][1] or g["z"][1] <= ob["z"][0]:
                    continue
                area = g["poly"].intersection(ob["poly"]).area
                if area > 1e-6:
                    resultado.append(dict(angulo=a, parte=parte["nome"], obstaculo=ob["nome"], area=area))
    return resultado


def folgas(angulo):
    """Menor distância de cada parte da porta aos obstáculos na mesma faixa de altura."""
    obs = obstaculos()
    out = {}
    for parte in partes_porta():
        g = girar(parte, angulo)
        melhor = (math.inf, None)
        for ob in obs:
            if g["z"][0] >= ob["z"][1] or g["z"][1] <= ob["z"][0]:
                continue
            d = g["poly"].distance(ob["poly"])
            if d < melhor[0]:
                melhor = (d, ob["nome"])
        out[parte["nome"]] = melhor
    return out


def folga_gavetas():
    """Folga entre a face de dentro da porta fechada e as frentes das gavetas."""
    return P.Y_PORTA_INT * -1 + c.FRENTE_GAVETA_Y


def figura(caminho):
    """Planta (vista de cima) com a porta a 0°, 45° e 90° na altura da trava."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    fig, ax = plt.subplots(figsize=(9, 9))
    zc = c.TRAVA_Z
    for ob in obstaculos():
        if ob["z"][0] <= zc <= ob["z"][1] or ob["nome"].startswith(("cooler", "berço", "bloco")):
            ax.add_patch(MP(list(ob["poly"].exterior.coords), closed=True, facecolor="#dfe6e9", edgecolor="#636e72", lw=0.8))
    cores = {0: "#c0392b", 45: "#e67e22", 90: "#27ae60"}
    for a, cor in cores.items():
        for parte in partes_porta():
            if not (parte["z"][0] <= zc <= parte["z"][1]) and parte["nome"] != "porta":
                continue
            g = girar(parte, a)
            ax.add_patch(MP(list(g["poly"].exterior.coords), closed=True, facecolor="none", edgecolor=cor, lw=1.4))
        ax.text(-60 if a == 90 else 420, -60 - a * 4 if a else -70, f"porta a {a}°", color=cor, fontsize=10)
    ax.plot(*P.EIXO, "ko", ms=4)
    ax.set_xlim(-250, 950)
    ax.set_ylim(-950, 750)
    ax.set_aspect("equal")
    ax.set_title(f"Vista de cima na altura da trava (Z {zc:.0f} mm) — coolers e bloco da dobradiça em todas as alturas",
                 fontsize=10, loc="left")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm) — frente da caixa em Y = 0, porta para Y negativo")
    fig.tight_layout()
    fig.savefig(caminho, dpi=110)
    plt.close(fig)
