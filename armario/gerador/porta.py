"""v2.4 — porta e peças novas, no mesmo sistema de peças da V2.3.

Todas as peças são `Peca` (geometria.py) com dois atributos extras usados na
exportação:
    gravar: lista de (texto, x, y, altura) em coordenadas locais da peça
    riscos: lista de polilinhas gravadas (marcas de alinhamento)

Sistemas de coordenadas
- Armário: X para a direita, Y para o fundo (frente da caixa em Y = 0), Z para cima.
- Porta: u da borda esquerda da porta (vista de frente), v da borda de baixo.
  u = X − X_PORTA0, v = Z − PORTA_Z0.
- A pele de fora é desenhada ESPELHADA (vista de trás), para a gravação ficar
  na face de dentro, escondida no miolo.
"""
from __future__ import annotations

import math
import os
import sys

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import config as c
from geometria import Peca

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "hardware")))
import layout as L  # noqa: E402

T = c.MATERIAL_T
F = c.FOLGA
FR = c.FOLGA_RECORTE

# --- posição da porta no armário ---------------------------------------------
X_PORTA0 = -(c.BLOCO_DOB_CAMADAS * T + c.DOB_ABA_ESP)      # borda esquerda da porta: −10
Y_PORTA_INT = -(c.AFASTAMENTO_PORTA + c.DOB_ABA_ESP)       # face de dentro da porta fechada: −9
PORTA_ESP = 2 * T + c.PORTA_NUCLEO                          # 30
Y_PORTA_EXT = Y_PORTA_INT - PORTA_ESP                       # −39
EIXO = (X_PORTA0, Y_PORTA_INT)                              # eixo da dobradiça (aprox.: pino na quina)
X_PORTA1 = X_PORTA0 + c.PORTA_W                             # 870


def u(x):
    return x - X_PORTA0


def v(z):
    return z - c.PORTA_Z0


# --- ferramentas --------------------------------------------------------------
def nova(codigo, nome, w, h):
    p = Peca(codigo, nome, w, h)
    p.gravar, p.riscos = [], []
    return p


def furo(p, x, y, d):
    p.hole_circle(x, y, d)


def retangulo(p, x0, x1, y0, y1):
    p.poly = p.poly.difference(box(x0, y0, x1, y1))


def sextavado(p, x, y, chave=5.5):
    """Bolsa sextavada para prender porca M3 (chave 5,5 + folga)."""
    s = chave + 2 * F + 0.2
    r = s / math.sqrt(3)
    pts = [(x + r * math.cos(math.radians(60 * k)), y + r * math.sin(math.radians(60 * k))) for k in range(6)]
    p.poly = p.poly.difference(Polygon(pts))


def rasgo_aba(p, cx, cy, comprimento, vertical):
    """Rasgo que recebe uma aba de 20 mm de outra peça em pé (MDF 3 mm)."""
    w, h = (T + 2 * F, comprimento + 2 * F) if vertical else (comprimento + 2 * F, T + 2 * F)
    p.hole_rect(cx, cy, w, h)


def aba(p, borda, centro, comprimento=20.0):
    p.edge_stub_tabs(borda, [centro], comprimento, T)


def espelhar(p):
    """Espelha a peça em X (desenho visto de trás)."""
    from shapely.affinity import scale
    p.poly = scale(p.poly, xfact=-1, yfact=1, origin=(p.w / 2, 0))


def nota(p, texto, x, y, h=6.0):
    p.gravar.append((texto, x, y, h))


# =====================================================================
# Dobradiça: posições dos furos
# =====================================================================
def furos_dobradica():
    """Z dos furos da aba do armário (A) e da aba da porta (B)."""
    z_a, z_b = [], []
    z = c.DOB_Z0 + c.DOB_PRIMEIRO_FURO
    while z < c.DOB_Z0 + c.DOB_COMPRIMENTO - 5:
        z_a.append(z)
        zb = z + c.DOB_PASSO / 2
        if zb < c.DOB_Z0 + c.DOB_COMPRIMENTO - 5:
            z_b.append(zb)
        z += c.DOB_PASSO
    return z_a, z_b


def y_furo_aba_a():
    """Y dos furos da aba do armário, no bloco (a aba sai do pino para o fundo)."""
    return EIXO[1] + c.DOB_FURO_DA_DOBRA


# =====================================================================
# PORTA
# =====================================================================
def _janela_lcd_ext(p, espelhado):
    def xx(x):
        return c.PORTA_W - u(x) if espelhado else u(x)
    cx, cz = c.LCD_CENTRO
    p.hole_rect(xx(cx), v(cz), c.LCD_JANELA[0], c.LCD_JANELA[1])
    cx, cz = c.AS608_CENTRO
    p.hole_rect(xx(cx), v(cz), c.AS608_JANELA[0], c.AS608_JANELA[1])
    cx, cz = c.TECLADO_CENTRO
    flat_z = cz - c.TECLADO[1] / 2 + 8                 # escondido sob a borda de baixo do teclado
    p.hole_rect(xx(cx), v(flat_z), c.TECLADO_FLAT[0], c.TECLADO_FLAT[1])
    bx, bz = c.BUZZER_CENTRO
    for dx, dz in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)):
        furo(p, xx(bx + dx), v(bz + dz), c.BUZZER_FUROS_D)
    px, pz = c.PUXADOR_CENTRO
    p.hole_rect(xx(px), v(pz), c.PUXADOR[0], c.PUXADOR[1])


def pele_ext():
    p = nova("PORTA_PELE_EXT", "Porta — pele de fora (vista de trás)", c.PORTA_W, c.PORTA_H)
    _janela_lcd_ext(p, espelhado=True)
    nota(p, "PELE DE FORA - esta face fica para DENTRO (miolo)", 40, 430, 10)
    # contorno do teclado gravado (para colar no lugar certo, do lado de fora: só referência)
    return p


def pele_int():
    p = nova("PORTA_PELE_INT", "Porta — pele de dentro", c.PORTA_W, c.PORTA_H)
    x0, x1, z0, z1 = c.JANELA_INT
    retangulo(p, u(x0), u(x1), v(z0), v(z1))
    _, z_b = furos_dobradica()
    for z in z_b:
        furo(p, c.DOB_FURO_DA_DOBRA, v(z), c.DOB_FURO)
    for x, z in batente_parafusos():
        furo(p, u(x), v(z), L.FURO_M4)
    nota(p, "PELE DE DENTRO - esta face fica para o miolo", 60, 430, 10)
    return p


def batente_parafusos():
    px, pz = c.PUXADOR_CENTRO
    return [(px - 6, pz - 15), (px + 6, pz + 15)]


def montantes():
    pecas = []
    _, z_b = furos_dobradica()
    # esquerdo (dobradiça): camada 1 encosta na pele de dentro
    for k in range(1, c.PORTA_CAMADAS_MONT + 1):
        p = nova(f"PORTA_MONT_E_{k}", f"Porta — montante esquerdo, camada {k}", c.PORTA_MONT_E, c.PORTA_H)
        for z in z_b:
            if k == 1:
                furo(p, c.DOB_FURO_DA_DOBRA, v(z), c.DOB_FURO)
            elif k == 2:
                sextavado(p, c.DOB_FURO_DA_DOBRA, v(z))
        pecas.append(p)
    # direito (trava e puxador): camada 1 encosta na pele de dentro
    px, pz = c.PUXADOR_CENTRO
    for k in range(1, c.PORTA_CAMADAS_MONT + 1):
        p = nova(f"PORTA_MONT_D_{k}", f"Porta — montante direito, camada {k}", c.PORTA_MONT_D, c.PORTA_H)
        x_loc = px - (X_PORTA1 - c.PORTA_MONT_D)
        if k > c.PORTA_CAMADAS_MONT // 2:            # cava do puxador (metade de fora)
            p.hole_rect(x_loc, v(pz), c.PUXADOR[0], c.PUXADOR[1])
        else:
            for x, z in batente_parafusos():
                furo(p, x - (X_PORTA1 - c.PORTA_MONT_D), v(z), L.FURO_M4)
        pecas.append(p)
    return pecas


def nervuras():
    """Nervuras em pé (altura = miolo), com meia-madeira nos cruzamentos."""
    pecas = []
    u0, u1 = c.PORTA_MONT_E, c.PORTA_W - c.PORTA_MONT_D
    comp_h = u1 - u0
    H = c.PORTA_NUCLEO
    meia = H / 2
    us = list(c.PORTA_NERV_V)
    # trilhos de cima e de baixo
    for nome, vv in (("PORTA_TRILHO_INF", 0), ("PORTA_TRILHO_SUP", c.PORTA_H - T)):
        p = nova(nome, f"Porta — trilho {'de baixo' if vv == 0 else 'de cima'} (em pé)", comp_h, H)
        if vv:   # saída dos cabos pela borda de cima, junto da dobradiça
            s0, s1 = c.SAIDA_CABOS_U
            retangulo(p, s0 - u0, s1 - u0, -1, 12)
            nota(p, "SAIDA DOS CABOS", s1 - u0 + 4, 14, 5)
        pecas.append(p)
    # horizontais de corpo inteiro, com rasgo de meia-madeira (de cima) nos verticais
    for i, vv in enumerate(c.PORTA_NERV_H, 1):
        p = nova(f"PORTA_NERV_H{i}", f"Porta — nervura horizontal {i} (v {vv:.0f})", comp_h, H)
        for uu in us:
            retangulo(p, uu - u0 - T / 2 - F, uu - u0 + T / 2 + F, meia, H + 1)
        pecas.append(p)
    # verticais de corpo inteiro (entre os trilhos), rasgo de baixo nos cruzamentos
    comp_v = c.PORTA_H - 2 * T
    x0, x1, z0, z1 = c.JANELA_INT
    canal = (v(c.SAIDA_CABOS_Z[0]) - 4, v(c.SAIDA_CABOS_Z[1]) + 4)
    for i, uu in enumerate(us, 1):
        p = nova(f"PORTA_NERV_V{i}", f"Porta — nervura vertical {i} (u {uu:.0f})", comp_v, H)
        for vv in c.PORTA_NERV_H:
            retangulo(p, vv - T - T / 2 - F, vv - T + T / 2 + F, -1, meia)
        # passagem dos cabos (alto da porta), aberta do lado da pele de dentro
        retangulo(p, canal[0] - T, canal[1] - T, -1, 12)
        pecas.append(p)
    # moldura da janela (LCD e leitor): duas horizontais curtas e uma vertical
    ju0, ju1 = u(x0) - 6, u1
    for nome, vv in (("PORTA_JAN_INF", v(z0) - 6), ("PORTA_JAN_SUP", v(z1) + 3)):
        p = nova(nome, f"Porta — moldura da janela ({'baixo' if 'INF' in nome else 'cima'})", ju1 - ju0, H)
        if "INF" in nome:   # passagem do cabo do teclado
            cx = u(c.TECLADO_CENTRO[0]) - ju0
            retangulo(p, cx - 10, cx + 10, -1, 12)
        else:               # passagem dos cabos para o canal do alto
            retangulo(p, 20, 60, H - 12, H + 1)
        pecas.append(p)
    p = nova("PORTA_JAN_ESQ", "Porta — moldura da janela (esquerda)", (v(z1) + 3) - (v(z0) - 3), H)
    pecas.append(p)
    return pecas


ALMA_MIN_PILHA = 2.5     # MDF mínimo entre o furo da presilha e a abertura


def _pilha(prefixo, nome, abertura_frente, n_frente, abertura_meio, n_meio, ext, sobre):
    """Pilha de camadas coladas atrás da pele de fora que segura um componente:
    n_frente camadas com a abertura da frente (moldura do vidro), n_meio com a
    abertura do corpo, e uma presilha de cada lado que cobre `sobre` mm da
    ponta do componente, parafusada com M3 numa porca presa na camada 1."""
    W, H = ext
    larg = W / 2 - (abertura_meio[0] / 2 - sobre)            # largura de cada presilha
    dx = W / 2 - larg / 2                                    # centro do furo da presilha
    alma = dx - L.FURO_M3 / 2 - (abertura_meio[0] / 2 + FR)
    assert alma >= ALMA_MIN_PILHA, f"{prefixo}: só {alma:.1f} mm de MDF entre o furo e a abertura"
    pecas = []
    aberturas = [abertura_frente] * n_frente + [abertura_meio] * n_meio
    for k, ab in enumerate(aberturas, 1):
        p = nova(f"{prefixo}_{k}", f"{nome} — camada {k}", W, H)
        p.hole_rect(W / 2, H / 2, ab[0] + 2 * FR, ab[1] + 2 * FR)
        for sx in (-1, 1):
            if k == 1:
                sextavado(p, W / 2 + sx * dx, H / 2)
            else:
                furo(p, W / 2 + sx * dx, H / 2, L.FURO_M3)
        pecas.append(p)
    for lado in ("E", "D"):
        p = nova(f"{prefixo}_PRESILHA_{lado}", f"{nome} — presilha {lado}", larg, H)
        furo(p, larg / 2, H / 2, L.FURO_M3)
        pecas.append(p)
    return pecas


def pilha_lcd(prefixo="PORTA_LCD"):
    """3 camadas com a moldura do vidro (9 mm > 7 mm do vidro) + 1 com a placa."""
    W, H = c.LCD_PLACA[0] + 28, c.LCD_PLACA[1] + 16
    return _pilha(prefixo, "Moldura do LCD", (c.LCD_MOLDURA[0] + 1, c.LCD_MOLDURA[1] + 1), 3,
                  c.LCD_PLACA, 1, (W, H), sobre=4.0)


def pilha_leitor(prefixo="PORTA_LEITOR"):
    """7 camadas (21 mm) para o corpo de 20 mm; a face do sensor encosta na pele."""
    mx, my, mz = c.AS608_MODULO
    W, H = mx + 28, my + 14
    n = int(math.ceil(mz / T))
    return _pilha(prefixo, "Moldura do leitor AS608", (mx, my), 0, (mx, my), n, (W, H), sobre=3.0)


TAMPA_MARGEM = 18.0      # a tampa passa 18 mm da janela; as colunas ficam no meio dessa faixa


def tampa_traseira():
    """Tampa sobre a janela da pele de dentro + 4 colunas com porca presa."""
    x0, x1, z0, z1 = c.JANELA_INT
    W, H = (x1 - x0) + 2 * TAMPA_MARGEM, (z1 - z0) + 2 * TAMPA_MARGEM
    p = nova("PORTA_TAMPA_TRAS", "Porta — tampa traseira do LCD e do leitor", W, H)
    m = TAMPA_MARGEM / 2
    cantos = [(m, m), (W - m, m), (m, H - m), (W - m, H - m)]
    for x, y in cantos:
        furo(p, x, y, L.FURO_M3)
    nota(p, "TAMPA LCD/LEITOR", 20, H / 2 - 3, 7)
    pecas = [p]
    n_camadas = int(round(c.CAIXA_TRASEIRA_PROF / T))
    for i in range(4):
        for k in range(1, n_camadas + 1):
            q = nova(f"PORTA_COLUNA_{i + 1}_{k}", f"Porta — coluna {i + 1} da tampa, camada {k}", 14, 14)
            if k == 1:      # camada colada na pele: porca presa
                sextavado(q, 7, 7)
            else:
                furo(q, 7, 7, L.FURO_M3)
            pecas.append(q)
    return pecas


def batente():
    """Placa no lado de dentro da porta (2 camadas) + braço em pé (2 camadas) com
    a janela da lingueta. Os 2 parafusos M4 entram pela cava do puxador: soltar
    os dois é a LIBERAÇÃO DE EMERGÊNCIA (a porta abre e o batente fica preso na trava)."""
    bx0, bx1 = c.BATENTE_X
    xs = [bx0 - 5, X_PORTA1 - 2]
    z0, z1 = c.TRAVA_Z - 35, c.TRAVA_Z + 35
    pecas = []
    for k in (1, 2):
        p = nova(f"BATENTE_PLACA_{k}", f"Batente — placa, camada {k}", xs[1] - xs[0], z1 - z0)
        for x, z in batente_parafusos():
            furo(p, x - xs[0], z - z0, L.FURO_M4)
        if k == 2:   # a camada de cima recebe as abas das 2 camadas do braço
            for zc in (z0 + 15, z1 - 15):
                p.hole_rect((bx0 + bx1) / 2 - xs[0], zc - z0, (bx1 - bx0) + 2 * F, 20 + 2 * F)
        pecas.append(p)
    comp = c.BATENTE_Y1 - (Y_PORTA_INT + 2 * T)
    for k in (1, 2):
        p = nova(f"BATENTE_BRACO_{k}", f"Batente — braço, camada {k}", comp, z1 - z0)
        jy, jz = c.BATENTE_JANELA
        # janela da lingueta: centrada na trava, a partir da face da frente do corpo
        y_lin = c.TRAVA_Y0 + c.TRAVA_LINGUETA[1] / 2 - (Y_PORTA_INT + 2 * T)
        p.hole_rect(y_lin, c.TRAVA_Z - z0, jy, jz)
        for zc in (z0 + 15, z1 - 15):
            p.poly = unary_union([p.poly, box(-T, zc - z0 - 10, 0, zc - z0 + 10)])   # abas na placa
        pecas.append(p)
    return pecas


def mata_junta():
    pecas = []
    z_cortes = [(c.PORTA_Z0, c.TRAVA_Z - 38), (c.TRAVA_Z + 38, c.PORTA_Z0 + c.PORTA_H)]
    for i, (z0, z1) in enumerate(z_cortes, 1):
        for k in (1, 2):
            # 30 mm: 20 colados na porta + 10 cobrindo a borda da lateral direita
            pecas.append(nova(f"PORTA_MATA_JUNTA_{i}_{k}", f"Mata-junta {i}, camada {k}", 30, z1 - z0))
    return pecas


def pecas_porta():
    return ([pele_ext(), pele_int()] + montantes() + nervuras() + pilha_lcd() + pilha_leitor()
            + tampa_traseira() + batente() + mata_junta())


# =====================================================================
# ARMÁRIO: bloco da dobradiça, berços, baia, caixa, gabaritos
# =====================================================================
def bloco_dobradica(prefixo="BLOCO_DOB", z_range=None):
    """Camadas no plano YZ (largura = Y, altura = Z). Camada 1 = encostada na
    aba da dobradiça (face de fora); camada 3 = encostada na LAT_E."""
    y0 = -c.AFASTAMENTO_PORTA
    z0, z1 = z_range or (c.DOB_Z0, c.DOB_Z0 + c.DOB_COMPRIMENTO)
    z_a, _ = furos_dobradica()
    ya = y_furo_aba_a() - y0
    pecas = []
    for k in range(1, c.BLOCO_DOB_CAMADAS + 1):
        p = nova(f"{prefixo}_{k}", f"Bloco da dobradiça — camada {k}", c.BLOCO_DOB_LARGURA, z1 - z0)
        for z in z_a:
            if z0 + 6 < z < z1 - 6:
                (sextavado(p, ya, z - z0) if k == 2 else furo(p, ya, z - z0, c.DOB_FURO))
        for z in c.BLOCO_DOB_PARAFUSOS_Z:
            if z0 + 8 < z < z1 - 8:
                furo(p, c.BLOCO_DOB_PARAFUSO_Y - y0, z - z0, L.FURO_M4)
        nota(p, f"FRENTE {k}", 2, 10, 5)
        pecas.append(p)
    return pecas


def bercos():
    pecas = []
    zg = L.berco_z()                          # face de baixo da grade
    zb0 = min(L.SUPORTE_PARAFUSOS_Z) - 12
    for i, yc in enumerate(L.PELTIER_Y, 1):
        largura = L.COOLER_L + 24
        base = nova(f"BERCO_{i}_BASE", f"Berço do cooler {i} — placa na lateral", largura, zg + T - zb0)
        for dy in L.SUPORTE_PARAFUSOS_DY:
            for z in L.SUPORTE_PARAFUSOS_Z:
                furo(base, largura / 2 + dy, z - zb0, L.FURO_M4)
        for dy in (-(L.COOLER_L / 2 + 3), L.COOLER_L / 2 + 3):
            for zc in (zb0 + 25, zg - 25):
                rasgo_aba(base, largura / 2 + dy, zc - zb0, 20, vertical=True)
        nota(base, f"COOLER {i} - FRENTE <", 6, 4, 5)
        pecas.append(base)
        prof = L.COOLER_A + 12
        grade = nova(f"BERCO_{i}_GRADE", f"Berço do cooler {i} — grade", prof, largura)
        passo = c.BERCO_GRADE_FURO + c.BERCO_GRADE_ALMA
        nx, ny = int((prof - 30) // passo), int((L.COOLER_L - 8) // passo)
        ox, oy = (prof - nx * passo) / 2 + passo / 2, (largura - ny * passo) / 2 + passo / 2
        for a in range(nx):
            for b in range(ny):
                grade.hole_rect(ox + a * passo, oy + b * passo, c.BERCO_GRADE_FURO, c.BERCO_GRADE_FURO)
        for dy in (-(L.COOLER_L / 2 + 3), L.COOLER_L / 2 + 3):
            for xc in (35.0, prof - 25):
                rasgo_aba(grade, xc, largura / 2 + dy, 20, vertical=False)
        grade.vazado = nx * ny * c.BERCO_GRADE_FURO ** 2 / (120.0 * 120.0)
        pecas.append(grade)
        for lado in ("A", "B"):
            alt = zg - zb0
            m = nova(f"BERCO_{i}_MAO_{lado}", f"Berço do cooler {i} — mão-francesa {lado}", prof, alt)
            m.poly = Polygon([(0, 0), (12, 0), (prof, alt - 12), (prof, alt), (0, alt)])
            for zc in (25.0, alt - 25):
                m.poly = unary_union([m.poly, box(-T, zc - 10, 0, zc + 10)])          # abas na placa
            for xc in (35.0, prof - 25):
                m.poly = unary_union([m.poly, box(xc - 10, alt, xc + 10, alt + T)])   # abas na grade
            pecas.append(m)
    return pecas


def baia():
    pecas = []
    larg = c.COL_A_W - 1.0
    piso = nova("BAIA_PISO", "Baia fria — piso", larg, c.SHELF_DEPTH - 4)
    nota(piso, "PISO DA BAIA - FRENTE v", 20, 10, 8)
    pecas.append(piso)
    for lado in ("E", "D"):
        for i, _ in enumerate(c.BAIA_TAQUINHO_Y, 1):
            for k in (1, 2, 3):
                pecas.append(nova(f"BAIA_TAQ_{lado}{i}_{k}", f"Taquinho {lado}{i}, camada {k}", *c.BAIA_TAQUINHO))
    alt = c.GAVETEIRO_Z[1] - (c.BAIA_PISO_Z + T) - 2
    tampa = nova("BAIA_TAMPA", "Baia fria — frente da tampa isolada", c.COL_A_W - 2, alt)
    furo(tampa, (c.COL_A_W - 2) / 2, alt - 30, 28)
    nota(tampa, "TAMPA DA BAIA FRIA", 20, 10, 8)
    pecas.append(tampa)
    return pecas


def caixa_eletronica():
    """Caixa de juntas de dente: base, 4 paredes e tampa parafusada."""
    W, D, H = c.CAIXA_INT
    pecas = []
    base = nova("CAIXA_BASE", "Caixa da eletrônica — base", W + 2 * T, D + 2 * T)
    for x in (30, W / 2, W - 30):
        furo(base, x, D / 2, L.FURO_M4)                   # parafusos no tampo
    pecas.append(base)
    paredes = {"FRENTE": W + 2 * T, "TRAS": W + 2 * T, "ESQ": D, "DIR": D}
    for nome, comp in paredes.items():
        p = nova(f"CAIXA_{nome}", f"Caixa da eletrônica — parede {nome.lower()}", comp, H)
        if nome in ("ESQ", "DIR"):
            for k in range(6):
                p.hole_rect(30 + k * (D - 60) / 5, H / 2, 5, 45)        # ventilação
            p.edge_tabs("left", T, c.FINGER_PITCH, which=True)
            p.edge_tabs("right", T, c.FINGER_PITCH, which=True)
        else:
            p.edge_notches("left", T, c.FINGER_PITCH, which=True, folga=F)
            p.edge_notches("right", T, c.FINGER_PITCH, which=True, folga=F)
        if nome == "TRAS":
            for k, d in enumerate((20, 20, 20, 12, 10)):
                furo(p, 40 + k * 65, H / 2 + 10, d)                      # passagem de cabos
        pecas.append(p)
    tampa = nova("CAIXA_TAMPA", "Caixa da eletrônica — tampa", W + 2 * T, D + 2 * T)
    k = T + 8
    for x, y in ((k, k), (W + 2 * T - k, k), (k, D + 2 * T - k), (W + 2 * T - k, D + 2 * T - k)):
        furo(tampa, x, y, L.FURO_M4)
    nota(tampa, "ELETRONICA - SO ABRIR FORA DA TOMADA", 30, D / 2, 9)
    pecas.append(tampa)
    for i in range(4):
        for k in (1, 2, 3):
            q = nova(f"CAIXA_CANTO_{i + 1}_{k}", f"Caixa — canto {i + 1} da tampa, camada {k}", 16, 16)
            (sextavado(q, 8, 8, 7.0) if k == 1 else furo(q, 8, 8, L.FURO_M4))
            pecas.append(q)
    return pecas


GABARITO_REGUA_X = 6.0   # centro dos rasgos da régua de encosto


def gabaritos():
    """Gabaritos de furação: apoiam na mesa (borda de baixo = Z 0) e encostam na
    borda da frente da lateral (régua cortada junto)."""
    import furos as FUROS
    pecas = []
    ofs = GABARITO_REGUA_X + T / 2 + F       # face da régua que encosta na borda da frente da lateral
    for lado, codigo, ymax, zmax in (("lateral esquerda", "GABARITO_LAT_E", 430.0, 345.0),
                                     ("lateral direita", "GABARITO_LAT_D", 110.0, 650.0)):
        p = nova(codigo, f"Gabarito de furação — {lado} (encostar na mesa e na frente)", ymax + ofs, zmax)
        n = 0
        for f in FUROS.furos():
            if f["peca"] != lado or f["a"] > ymax - 5 or f["b"] > zmax - 5:
                continue
            if f["quadrado"]:
                p.hole_rect(f["a"] + ofs, f["b"], f["d"], f["d"])
            else:
                furo(p, f["a"] + ofs, f["b"], f["d"])
            nota(p, f"{f['d']:g}", f["a"] + ofs + f["d"] / 2 + 2, f["b"] + 2, 4)
            n += 1
        p.n_furos = n
        p.ofs = ofs
        for zc in (40.0, zmax - 40):
            rasgo_aba(p, GABARITO_REGUA_X, zc, 20, vertical=True)
        nota(p, "FRENTE", ofs + 4, zmax - 12, 6)
        nota(p, "MESA", (ymax + ofs) / 2, 4, 6)
        pecas.append(p)
        regua = nova(f"{codigo}_REGUA", f"Régua de encosto do {codigo}", zmax, 15)
        for zc in (40.0, zmax - 40):
            regua.poly = unary_union([regua.poly, box(zc - 10, -T, zc + 10, 0)])
        pecas.append(regua)
    return pecas


def pecas_armario():
    return bloco_dobradica() + bercos() + baia() + caixa_eletronica() + gabaritos()


# =====================================================================
# CUPOM DE TESTE (cortar ANTES da porta)
# =====================================================================
def cupom():
    pecas = []
    # 1. amostra da pele de fora com todos os recortes de componente
    xs = [c.LCD_CENTRO[0], c.AS608_CENTRO[0], c.TECLADO_CENTRO[0], c.BUZZER_CENTRO[0]]
    zs = [c.LCD_CENTRO[1], c.AS608_CENTRO[1], c.TECLADO_CENTRO[1], c.BUZZER_CENTRO[1]]
    x0, x1 = min(xs) - 70, max(xs) + 40
    z0, z1 = min(zs) - 50, max(zs) + 30
    p = nova("CP_PELE", "Cupom — pele de fora com LCD, leitor, teclado e buzzer", x1 - x0, z1 - z0)
    cx, cz = c.LCD_CENTRO
    p.hole_rect(cx - x0, cz - z0, c.LCD_JANELA[0], c.LCD_JANELA[1])
    cx, cz = c.AS608_CENTRO
    p.hole_rect(cx - x0, cz - z0, c.AS608_JANELA[0], c.AS608_JANELA[1])
    cx, cz = c.TECLADO_CENTRO
    p.hole_rect(cx - x0, cz - c.TECLADO[1] / 2 + 8 - z0, c.TECLADO_FLAT[0], c.TECLADO_FLAT[1])
    tx0, tx1 = cx - c.TECLADO[0] / 2 - x0, cx + c.TECLADO[0] / 2 - x0
    tz0, tz1 = cz - c.TECLADO[1] / 2 - z0, cz + c.TECLADO[1] / 2 - z0
    p.riscos.append([(tx0, tz0), (tx1, tz0), (tx1, tz1), (tx0, tz1), (tx0, tz0)])
    bx, bz = c.BUZZER_CENTRO
    for dx, dz in ((0, 0), (4, 0), (-4, 0), (0, 4), (0, -4)):
        furo(p, bx + dx - x0, bz + dz - z0, c.BUZZER_FUROS_D)
    for k, d in enumerate((c.DOB_FURO, L.FURO_M3, L.FURO_M4, 10.0)):
        furo(p, 12 + k * 14, 12, d)
        nota(p, f"{d:g}", 8 + k * 14, 20, 3.5)
    nota(p, "TECLADO (contorno)", tx0 + 2, tz1 + 2, 4)
    pecas.append(p)
    # 2. molduras do LCD e do leitor (iguais às da porta)
    pecas += pilha_lcd("CP_LCD") + pilha_leitor("CP_LEITOR")
    # 3. dobradiça: trecho do bloco (150 mm) e da borda da porta
    pecas += bloco_dobradica("CP_BLOCO", (c.DOB_Z0, c.DOB_Z0 + 150))
    _, z_b = furos_dobradica()
    zb = [z for z in z_b if z < c.DOB_Z0 + 150]
    for k, nome in ((0, "PELE"), (1, "MONT1"), (2, "MONT2")):
        q = nova(f"CP_PORTA_{nome}", f"Cupom — borda da porta ({nome.lower()})", 40 if k == 0 else c.PORTA_MONT_E, 150)
        for z in zb:
            (sextavado(q, c.DOB_FURO_DA_DOBRA, z - c.DOB_Z0) if k == 2 else furo(q, c.DOB_FURO_DA_DOBRA, z - c.DOB_Z0, c.DOB_FURO))
        pecas.append(q)
    # 4. batente + placa de teste da trava (faz o papel da lateral direita)
    pecas += [q for q in batente()]
    for q in pecas[-4:]:
        q.codigo = "CP_" + q.codigo
    tp = nova("CP_TRAVA_PLACA", "Cupom — placa da trava (faz o papel da lateral direita)", 100, 110)
    for dy in c.TRAVA_FUROS_DY:
        furo(tp, dy, 55, L.FURO_M4)
    nota(tp, "FRENTE <", 4, 100, 5)
    pecas.append(tp)
    # 5. Peltier e grade do berço
    q = nova("CP_PELTIER", "Cupom — furo da Peltier e da prensa", 110, 60)
    q.hole_rect(55, 30, L.FURO_PELTIER, L.FURO_PELTIER)
    for dx in (-L.PRENSA_DY, L.PRENSA_DY):
        furo(q, 55 + dx, 30, L.FURO_M3)
    pecas.append(q)
    g = nova("CP_GRADE", "Cupom — grade do berço (teste do dedo)", 60, 60)
    passo = c.BERCO_GRADE_FURO + c.BERCO_GRADE_ALMA
    for a in range(3):
        for b in range(3):
            g.hole_rect(30 + (a - 1) * passo, 30 + (b - 1) * passo, c.BERCO_GRADE_FURO, c.BERCO_GRADE_FURO)
    pecas.append(g)
    return pecas
