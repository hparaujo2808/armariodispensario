"""Manual de montagem ilustrado (PDF) — armário dispensador v2.

Ilustrações esquemáticas simples (projeção oblíqua, não é desenho técnico)
pra dar noção espacial de cada etapa. As medidas reais e os DXFs de
fabricação estão nos outros arquivos do pacote (LEIA_PRIMEIRO.md,
MONTAGEM_REFORCOS.md, corte/, gravacao/).
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, FancyArrowPatch
from matplotlib.backends.backend_pdf import PdfPages

import config as c
from oblique import proj, xy_quad, yz_quad, xz_quad

PAGE = (8.27, 11.69)  # A4 retrato
COR_PECA = "#eef3f8"
COR_BORDA = "#33475b"
COR_NOVA = "#fde9c8"
COR_NOVA_BORDA = "#b5772b"
COR_GAVETA = "#f4e3c1"
COR_GAVETA_BORDA = "#a9762f"
COR_SETA = "#c0392b"

W, H, D = c.EXT_W, c.EXT_H, c.EXT_D


def _fig():
    return plt.figure(figsize=PAGE)


def _canvas(fig, rect=(0.06, 0.30, 0.88, 0.62)):
    ax = fig.add_axes(rect)
    ax.axis("off")
    ax.set_aspect("equal")
    return ax


def panel(ax, quad, facecolor=COR_PECA, edgecolor=COR_BORDA, lw=1.3, alpha=1.0, zorder=2, ls="-"):
    pts = [proj(p) for p in quad]
    ax.add_patch(MplPolygon(pts, closed=True, facecolor=facecolor, edgecolor=edgecolor,
                             linewidth=lw, alpha=alpha, zorder=zorder, linestyle=ls))


def rotulo(ax, quad, texto, dx=0, dy=0, fontsize=8, color="#1a2b4c", weight="bold"):
    xs = [proj(p)[0] for p in quad]
    ys = [proj(p)[1] for p in quad]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    ax.text(cx + dx, cy + dy, texto, ha="center", va="center", fontsize=fontsize,
             fontweight=weight, color=color, zorder=10)


def seta(ax, p_de, p_para, color=COR_SETA, lw=2.0, style="-|>", mutation=14):
    a, b = proj(p_de), proj(p_para)
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, mutation_scale=mutation,
                                  color=color, linewidth=lw, zorder=9))


def _fit(ax, quads, pad=60):
    xs, ys = [], []
    for q in quads:
        for p in q:
            sx, sy = proj(p)
            xs.append(sx)
            ys.append(sy)
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


def _titulo(fig, numero, titulo):
    if numero is not None:
        fig.text(0.06, 0.955, f"PASSO {numero}", fontsize=11, fontweight="bold", color="#b5772b")
        fig.text(0.06, 0.925, titulo, fontsize=17, fontweight="bold", color="#1a2b4c")
    else:
        fig.text(0.06, 0.94, titulo, fontsize=17, fontweight="bold", color="#1a2b4c")


def _texto(fig, itens, y0=0.22, largura=78):
    """`itens`: lista de parágrafos/títulos/"" (linha em branco). Cada item
    que comece com '•' é quebrado automaticamente com indentação
    suspensa (hanging indent), tudo numa única chamada de texto pra ficar
    alinhado."""
    import textwrap
    y = y0
    for item in itens:
        if item == "":
            y -= 0.012
            continue
        if item.startswith("•"):
            corpo = item[1:].strip()
            quebrado = textwrap.wrap(corpo, largura)
            texto = "\n".join(["• " + quebrado[0]] + ["  " + l for l in quebrado[1:]])
            n_linhas = len(quebrado)
            fig.text(0.07, y, texto, fontsize=9.5, color="#222", linespacing=1.6, va="top")
        else:
            quebrado = textwrap.wrap(item, largura + 3) or [item]
            texto = "\n".join(quebrado)
            n_linhas = len(quebrado)
            fig.text(0.06, y, texto, fontsize=9.5, color="#222", linespacing=1.6, va="top")
        y -= 0.026 * n_linhas + 0.006


# ---------------------------------------------------------------------
# Página 1 — capa
# ---------------------------------------------------------------------

def pagina_capa(pdf):
    fig = _fig()
    fig.text(0.5, 0.88, "Manual de Montagem", ha="center", fontsize=24, fontweight="bold")
    fig.text(0.5, 0.845, "Armário dispensador — v2.1", ha="center", fontsize=15, color="#444")

    ax = fig.add_axes([0.12, 0.40, 0.76, 0.38])
    ax.axis("off")
    ax.set_aspect("equal")
    base = xy_quad(0, W, 0, D, 0)
    tampo = xy_quad(0, W, 0, D, H)
    lat_e = yz_quad(0, 0, D, 0, H)
    lat_d = yz_quad(W, 0, D, 0, H)
    fundo = xz_quad(D, 0, W, 0, H)
    panel(ax, fundo, facecolor="#f3f3f3", zorder=1)
    panel(ax, base)
    panel(ax, lat_e)
    panel(ax, lat_d)
    panel(ax, tampo)
    for z0, z1 in (c.TETO_GAV_Z, c.PRAT2_Z, c.PRAT1_Z, c.PCAM_Z):
        panel(ax, xy_quad(3, W - 3, 0, c.SHELF_DEPTH, z0), facecolor="#dfe9f2", alpha=0.9)
    _fit(ax, [base, tampo, lat_e, lat_d, fundo])

    fig.text(0.5, 0.30, "Guia ilustrado passo a passo — do encaixe da caixa\n"
                        "às gavetas e ao porta-ataduras.",
             ha="center", fontsize=10.5, color="#555")
    fig.text(0.5, 0.10, "Leia junto com LEIA_PRIMEIRO.md e MONTAGEM_REFORCOS.md\n"
                        "(medidas exatas e posições de colagem).",
             ha="center", fontsize=8.5, color="#888")
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Página 2 — antes de começar
# ---------------------------------------------------------------------

def pagina_antes(pdf):
    fig = _fig()
    _titulo(fig, None, "Antes de começar")
    folga_str = f"{c.FOLGA:.2f}".replace(".", ",")
    linhas = [
        "Ferramentas e materiais",
        "• Cola branca para MDF (madeira crua) — ver referência de compatibilidade em LEIA_PRIMEIRO.md.",
        "• Esquadro ou fita métrica (pra conferir as diagonais).",
        "• Grampos/sargentos ou peso, pra manter as peças esquadrejadas enquanto a cola cura.",
        "• Martelo de borracha (ajuda a assentar os dentes sem forçar a peça).",
        "• Lixa fina, pra tirar rebarba de corte antes de colar.",
        "",
        "Antes de cortar tudo",
        "• Corte primeiro 00_TESTES_CORTE.dxf (cupom de kerf + par macho/fêmea de teste).",
        "• Calibre a compensação de kerf na sua máquina com esse cupom, no material real.",
        "• Confira se o par macho/fêmea entra com leve esforço — nem solto, nem travado.",
        "",
        "Organizando as peças",
        "• Separe as peças por grupo antes de começar: carcaça, prateleiras, gaveteiro, "
        "dispensador, gavetas (ver LISTA_PECAS.csv).",
        "• Cada peça tem o código gravado num canto fixo + uma marquinha triangular "
        "indicando esse canto de referência — use ela pra não montar peça invertida.",
        "",
        "Sistema de encaixe (vale pro móvel inteiro)",
        "• Dente reto: o macho é do tamanho exato; o rasgo fêmea é levemente maior "
        f"(folga de {folga_str}mm por lado) — a peça deve entrar com leve esforço, nunca à força.",
        "• O encaixe por si só não trava: a fixação definitiva é sempre a cola.",
    ]
    _texto(fig, linhas, y0=0.87)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Página 3 — visão geral explodida
# ---------------------------------------------------------------------

def pagina_visao_geral(pdf):
    fig = _fig()
    _titulo(fig, None, "Visão geral das peças principais")
    ax = _canvas(fig)

    EXP = 260
    FALSO_Y = c.FALSE_BACK_Y0 + 220
    FUNDO_Y = D + 480
    base = xy_quad(0, W, 0, D, 0)
    lat_e = yz_quad(-EXP, 0, D, 0, H)
    lat_d = yz_quad(W + EXP, 0, D, 0, H)
    fundo = xz_quad(FUNDO_Y, 0, W, 0, H)
    fundo_falso = xz_quad(FALSO_Y, 0, W, 0, H)
    tampo = xy_quad(0, W, 0, D, H + EXP)

    panel(ax, base)
    panel(ax, lat_e)
    panel(ax, lat_d)
    panel(ax, fundo, facecolor="#f3f3f3")
    panel(ax, fundo_falso, facecolor="#f3f3f3", alpha=0.85)
    panel(ax, tampo)

    rotulo(ax, base, "BASE")
    rotulo(ax, lat_e, "LAT_E", dx=-15)
    rotulo(ax, lat_d, "LAT_D", dx=15)
    rotulo(ax, fundo, "FUNDO\n(traseiro)", dy=40)
    rotulo(ax, fundo_falso, "FUNDO_FALSO", dy=-45)
    rotulo(ax, tampo, "TAMPO")

    # setas de montagem convergindo pra posição real (eixo que cada peça percorre)
    seta(ax, (-EXP * 0.55, D * 0.5, H * 0.5), (-15, D * 0.5, H * 0.5))
    seta(ax, (W + EXP * 0.55, D * 0.5, H * 0.5), (W + 15, D * 0.5, H * 0.5))
    seta(ax, (W * 0.15, FUNDO_Y - 20, H * 0.7), (W * 0.15, D + 15, H * 0.7))
    seta(ax, (W * 0.85, FALSO_Y - 20, H * 0.3), (W * 0.85, c.FALSE_BACK_Y0 + 15, H * 0.3))
    seta(ax, (W * 0.5, D * 0.5, H + EXP * 0.55), (W * 0.5, D * 0.5, H + 15))

    _fit(ax, [base, lat_e, lat_d, fundo, fundo_falso, tampo], pad=90)
    _texto(fig, [
        "6 painéis formam a caixa: BASE, TAMPO, 2 LATERAIS, FUNDO (traseiro real) e "
        "FUNDO_FALSO (painel interno que separa a cavidade de cabos). Todos peça única, "
        "sem emenda — só resta encaixar os dentes de canto e colar.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Passo 1 — bandeja (base + laterais + fundos, sem tampo)
# ---------------------------------------------------------------------

def pagina_passo1(pdf):
    fig = _fig()
    _titulo(fig, 1, "Monte a base, as laterais e os fundos")
    ax = _canvas(fig)

    base = xy_quad(0, W, 0, D, 0)
    lat_e = yz_quad(0, 0, D, 0, H)
    lat_d = yz_quad(W, 0, D, 0, H)
    fundo = xz_quad(D, 0, W, 0, H)
    fundo_falso = xz_quad(c.FALSE_BACK_Y0, 0, W, 0, H)

    panel(ax, fundo, facecolor="#f3f3f3")
    panel(ax, fundo_falso, facecolor="#f3f3f3", alpha=0.8)
    panel(ax, base)
    panel(ax, lat_e, alpha=0.95)
    panel(ax, lat_d, alpha=0.95)

    rotulo(ax, lat_e, "LAT_E", dx=-10)
    rotulo(ax, lat_d, "LAT_D", dx=10)
    rotulo(ax, fundo, "FUNDO", dy=30)
    rotulo(ax, base, "BASE")

    _fit(ax, [base, lat_e, lat_d, fundo], pad=70)
    _texto(fig, [
        "Ainda SEM o tampo — deixe o topo aberto pra facilitar o próximo passo.",
        "",
        "• Encaixe as duas laterais na base (dentes de canto) e o fundo falso + fundo "
        "traseiro entre elas, formando uma bandeja aberta em cima e na frente. Os dois "
        "fundos apoiam SOBRE a base, não ao lado dela — têm 874mm de altura.",
        "• Confira o esquadro: meça as duas diagonais da abertura frontal — devem dar "
        "a mesma medida. Corrija antes de colar.",
        "• Cole as uniões de canto e mantenha grampeado até secar.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Passo 2 — divisórias do gaveteiro + dispensador sobre a base
# ---------------------------------------------------------------------

def pagina_passo2(pdf):
    fig = _fig()
    _titulo(fig, 2, "Divisórias do gaveteiro e dispensador")
    ax = _canvas(fig)

    base = xy_quad(0, W, 0, D, 0)
    lat_e = yz_quad(0, 0, D, 0, H)
    lat_d = yz_quad(W, 0, D, 0, H)
    z0, z1 = c.GAVETEIRO_Z
    div_ab = xz_quad(sum(c.X_DIV_AB) / 2, 0, c.SHELF_DEPTH, z0, z1)
    div_bc = xz_quad(sum(c.X_DIV_BC) / 2, 0, c.SHELF_DEPTH, z0, z1)
    div_disp = xz_quad(sum(c.X_DIV_DISP) / 2, 0, c.SHELF_DEPTH, z0, z1)
    disp_esq = xz_quad(c.X_DISP_LAT_ESQ_MID, 0, c.SHELF_DEPTH, z0, z0 + (z1 - z0) * 0.85)
    disp_dir = xz_quad(c.X_DISP_LAT_DIR_MID, 0, c.SHELF_DEPTH, z0, z0 + (z1 - z0) * 0.85)

    panel(ax, base, alpha=0.9)
    panel(ax, lat_e, alpha=0.5)
    panel(ax, lat_d, alpha=0.5)
    for q, nome, cor in ((div_ab, "DIV_AB", COR_NOVA), (div_bc, "DIV_BC", COR_NOVA),
                          (div_disp, "DIV_DISP", COR_NOVA)):
        panel(ax, q, facecolor=cor, edgecolor=COR_NOVA_BORDA)
        rotulo(ax, q, nome, dy=-20, fontsize=7.5, color=COR_NOVA_BORDA)
    for q in (disp_esq, disp_dir):
        panel(ax, q, facecolor="#dcefe3", edgecolor="#2f7a4d")
    rotulo(ax, disp_dir, "DISP_\nLATERAL", dx=25, fontsize=7, color="#2f7a4d")

    seta(ax, (sum(c.X_DIV_AB) / 2, c.SHELF_DEPTH * 0.5, z1 + 120), (sum(c.X_DIV_AB) / 2, c.SHELF_DEPTH * 0.5, z1 + 5))

    _fit(ax, [base, lat_e, lat_d, div_ab, div_bc, div_disp, disp_esq, disp_dir], pad=70)
    _texto(fig, [
        "Com o topo aberto, é mais fácil posicionar e colar as peças verticais do "
        "gaveteiro — faça isso ANTES de fechar com o tampo.",
        "",
        "• Encaixe os dentes de posição de DIV_AB, DIV_BC e DIV_DISP nos furos da base. "
        "A divisória tem dente só embaixo: o topo dela encosta e cola no TETO_GAV depois.",
        "• Cole os dois perfis DISP_LATERAL de encontro à DIV_DISP e à lateral direita.",
        "• Encaixe DISP_PISTA apoiada sobre os dois perfis (colagem de topo ao longo de "
        "toda a rampa) e o DISP_RETENTOR na frente.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Passo 3 — prateleiras + nervuras
# ---------------------------------------------------------------------

def pagina_passo3(pdf):
    fig = _fig()
    _titulo(fig, 3, "Deslize as prateleiras e cole as nervuras")
    ax = _canvas(fig)

    lat_e = yz_quad(0, 0, D, 0, H)
    lat_d = yz_quad(W, 0, D, 0, H)
    fundo_falso = xz_quad(c.FALSE_BACK_Y0, 0, W, 0, H)

    panel(ax, lat_e, alpha=0.5)
    panel(ax, lat_d, alpha=0.5)
    panel(ax, fundo_falso, facecolor="#f3f3f3", alpha=0.7)

    zonas = [("TETO_GAV", c.TETO_GAV_Z), ("PRAT_2", c.PRAT2_Z), ("PRAT_1", c.PRAT1_Z), ("P_CAM", c.PCAM_Z)]
    for nome, (z0, z1) in zonas:
        prat_fora = xy_quad(3, W - 3, -180, c.SHELF_DEPTH - 180, z0)
        panel(ax, prat_fora, facecolor=COR_NOVA, edgecolor=COR_NOVA_BORDA, alpha=0.9)
        rotulo(ax, prat_fora, nome, fontsize=7.5, color=COR_NOVA_BORDA)
        seta(ax, (W / 2, -100, z0 + 15), (W / 2, c.SHELF_DEPTH * 0.3, z0 + 15))

    _fit(ax, [lat_e, lat_d, fundo_falso, xy_quad(3, W - 3, -180, c.SHELF_DEPTH, c.PCAM_Z[0])], pad=70)
    _texto(fig, [
        "As 4 prateleiras (TETO_GAV, PRAT_2, PRAT_1, P_CAM) entram pela frente aberta, "
        "deslizando de frente pra trás, de baixo pra cima. Comece pelo TETO_GAV: ela "
        "assenta sobre o topo das divisórias.",
        "",
        "• Encaixe as duas abas laterais da prateleira nos rasgos das laterais.",
        "• Empurre até a aba traseira entrar no rasgo do fundo falso.",
        "• Cole 3 nervuras por baixo de cada prateleira (exceto TETO_GAV), nas posições "
        "de MONTAGEM_REFORCOS.md — ainda acessíveis por baixo, pela frente aberta.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Passo 4 — fechar com o tampo
# ---------------------------------------------------------------------

def pagina_passo4(pdf):
    fig = _fig()
    _titulo(fig, 4, "Feche com o tampo")
    ax = _canvas(fig)

    base = xy_quad(0, W, 0, D, 0)
    lat_e = yz_quad(0, 0, D, 0, H)
    lat_d = yz_quad(W, 0, D, 0, H)
    fundo = xz_quad(D, 0, W, 0, H)
    tampo_fora = xy_quad(0, W, 0, D, H + 200)
    tampo_pos = xy_quad(0, W, 0, D, H)

    panel(ax, fundo, facecolor="#f3f3f3")
    panel(ax, base)
    panel(ax, lat_e)
    panel(ax, lat_d)
    panel(ax, tampo_pos, facecolor=COR_PECA, edgecolor="#9aa5b1", alpha=0.35, ls="--")
    panel(ax, tampo_fora, facecolor=COR_NOVA, edgecolor=COR_NOVA_BORDA)
    rotulo(ax, tampo_fora, "TAMPO", color=COR_NOVA_BORDA)
    seta(ax, (W / 2, D / 2, H + 190), (W / 2, D / 2, H + 10))

    _fit(ax, [base, lat_e, lat_d, fundo, tampo_fora], pad=70)
    _texto(fig, [
        "Só depois que as prateleiras e as divisórias do gaveteiro já estão no lugar:",
        "",
        "• Encaixe o TAMPO nos dentes de canto das duas laterais e do fundo.",
        "• Confira o esquadro de novo e mantenha grampeado até a cola curar.",
        "• A partir daqui a caixa principal está estruturalmente pronta.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Passo 5 — montar uma gaveta
# ---------------------------------------------------------------------

def pagina_passo5(pdf):
    fig = _fig()
    _titulo(fig, 5, "Monte cada gaveta")
    ax = _canvas(fig)

    L = c.DRAWER_SLIDE_LEN
    Hf = c.DRAWER_BC_FRONT_H
    Wf = c.COL_B_W - 2 * c.DRAWER_SIDE_CLEARANCE

    EXP = 90
    fundo_g = xy_quad(6, Wf - 6, 6, L - 6, 0)
    frente = xz_quad(0, 0, Wf, 0, Hf)
    tras = xz_quad(L + EXP, 0, Wf, 0, Hf)
    lat_e = yz_quad(-EXP * 0.6, 0, L, 0, Hf)
    lat_d = yz_quad(Wf + EXP * 0.6, 0, L, 0, Hf)

    panel(ax, fundo_g, facecolor="#f3f3f3")
    panel(ax, frente, facecolor=COR_GAVETA, edgecolor=COR_GAVETA_BORDA)
    panel(ax, tras, facecolor=COR_GAVETA, edgecolor=COR_GAVETA_BORDA)
    panel(ax, lat_e, facecolor=COR_GAVETA, edgecolor=COR_GAVETA_BORDA)
    panel(ax, lat_d, facecolor=COR_GAVETA, edgecolor=COR_GAVETA_BORDA)

    rotulo(ax, frente, "FRENTE", fontsize=7.5, color=COR_GAVETA_BORDA)
    rotulo(ax, tras, "TRÁS", fontsize=7.5, color=COR_GAVETA_BORDA)
    rotulo(ax, lat_e, "LAT_E", dx=-12, fontsize=7.5, color=COR_GAVETA_BORDA)
    rotulo(ax, lat_d, "LAT_D", dx=12, fontsize=7.5, color=COR_GAVETA_BORDA)
    rotulo(ax, fundo_g, "FUNDO\n(liso)", fontsize=7, color="#666")

    seta(ax, (Wf / 2, L + EXP * 0.7, Hf / 2), (Wf / 2, L - 5, Hf / 2))
    seta(ax, (-EXP * 0.3, L / 2, Hf / 2), (2, L / 2, Hf / 2))
    seta(ax, (Wf + EXP * 0.3, L / 2, Hf / 2), (Wf - 2, L / 2, Hf / 2))

    _fit(ax, [fundo_g, frente, tras, lat_e, lat_d], pad=60)
    _texto(fig, [
        "Toda gaveta usa o mesmo esquema: 5 peças (frente, trás, 2 laterais e 1 fundo), "
        "independente do tamanho — só mudam as dimensões por coluna (A, B ou C). A ORDEM "
        "importa:",
        "",
        "• Cole a FRENTE nas duas laterais primeiro (dente reto nos cantos), deixando a "
        "traseira aberta.",
        "• Deslize o fundo por trás: as abas dele correm nos rasgos das laterais, que são "
        "abertos nessa ponta, até a aba da frente entrar no rasgo da FRENTE.",
        "• Só então feche com a TRAS, que captura a aba de trás do fundo. Depois dela "
        "colada o fundo não entra mais. Confira o esquadro da caixinha.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Passo 6 — instalar corrediças e gavetas
# ---------------------------------------------------------------------

def pagina_passo6(pdf):
    fig = _fig()
    _titulo(fig, 6, "Instale corrediças e gavetas")
    ax = _canvas(fig)

    lat_e = yz_quad(0, 0, D, 0, H)
    lat_d = yz_quad(W, 0, D, 0, H)
    base = xy_quad(0, W, 0, D, 0)
    panel(ax, base, alpha=0.6)
    panel(ax, lat_e, alpha=0.4)
    panel(ax, lat_d, alpha=0.4)

    z0, z1 = c.GAVETEIRO_Z
    x0, x1 = c.X_COL_A
    for k in range(c.N_DRAWERS_A):
        zz0 = z0 + k * c.DRAWER_A_FRONT_H + 3
        zz1 = zz0 + c.DRAWER_A_FRONT_H - 3
        fora = xy_quad(x0 + 6, x1 - 6, -140, c.DRAWER_SLIDE_LEN - 140, (zz0 + zz1) / 2)
        panel(ax, fora, facecolor=COR_GAVETA, edgecolor=COR_GAVETA_BORDA, alpha=0.9)
        seta(ax, (x0 + (x1 - x0) / 2, -80, (zz0 + zz1) / 2), (x0 + (x1 - x0) / 2, 40, (zz0 + zz1) / 2))
    rotulo(ax, xy_quad(x0, x1, -140, c.DRAWER_SLIDE_LEN - 140, z0 + 20), "Coluna A\n(4 gavetas)",
           fontsize=8, color=COR_GAVETA_BORDA)

    _fit(ax, [base, lat_e, lat_d, xy_quad(x0, x1, -140, D, z1)], pad=70)
    _texto(fig, [
        "Ferragens (corrediças, câmera, fechadura) não são cortadas no DXF — dependem "
        "do modelo real. Confira compatibilidade antes de furar.",
        "",
        f"• Corrediças compatíveis com caixa de {c.DRAWER_SLIDE_LEN:.0f}mm, folga lateral de "
        f"{c.DRAWER_SIDE_CLEARANCE:.0f}mm por lado já prevista na largura de cada coluna.",
        "• Fixe as corrediças nas divisórias/laterais de cada coluna antes de testar "
        "o curso da gaveta.",
        "• Teste cada gaveta vazia primeiro, sem forçar, antes de carregar o móvel.",
    ], y0=0.22)
    pdf.savefig(fig)
    plt.close(fig)


# ---------------------------------------------------------------------
# Última página — checklist final
# ---------------------------------------------------------------------

def pagina_checklist(pdf):
    fig = _fig()
    _titulo(fig, None, "Checklist final")
    linhas = [
        "☐ Cupom de teste cortado e conferido antes das chapas numeradas.",
        "☐ Caixa principal (base + laterais + fundos) esquadrejada e colada.",
        "☐ Divisórias do gaveteiro e dispensador colados sobre a base.",
        "☐ 4 prateleiras encaixadas e nervuras coladas nas posições certas.",
        "☐ Tampo fechado e esquadrejado.",
        "☐ Todas as gavetas montadas e testadas vazias.",
        "☐ Corrediças instaladas e alinhadas.",
        "☐ Conjunto em cura, esquadrejado, por pelo menos o tempo indicado pela cola.",
        "",
        "Carga de uso prevista: até 1kg por módulo. Os testes deste projeto são",
        "geométricos — não certificam resistência, flecha, estabilidade ou vida útil.",
        "Valide um módulo completo com o responsável pela fabricação antes de dar uso",
        "definitivo ao móvel.",
    ]
    _texto(fig, linhas, y0=0.85)
    pdf.savefig(fig)
    plt.close(fig)


def gerar_manual(caminho: str):
    with PdfPages(caminho) as pdf:
        pagina_capa(pdf)
        pagina_antes(pdf)
        pagina_visao_geral(pdf)
        pagina_passo1(pdf)
        pagina_passo2(pdf)
        pagina_passo3(pdf)
        pagina_passo4(pdf)
        pagina_passo5(pdf)
        pagina_passo6(pdf)
        pagina_checklist(pdf)


if __name__ == "__main__":
    import os
    destino = os.path.join(os.path.dirname(__file__), "..", "MANUAL_DE_MONTAGEM.pdf")
    gerar_manual(destino)
    print("PDF gerado:", destino)
