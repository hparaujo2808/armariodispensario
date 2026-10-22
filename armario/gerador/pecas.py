"""Construtores de peça — um por tipo de componente do armário v2.

Convenção de juntas usada em todo o projeto (ver geometria.py):

  * Canto estrutural perpendicular (lateral<->base/tampo/fundo) -> pente de
    dentes (comb): lado MACHO no tamanho nominal, lado FÊMEA alargado em
    `c.FOLGA` (largura e profundidade) pra sempre entrar.
  * Prateleira -> lateral, e prateleira -> fundo falso -> rebaixo simples
    (um único rasgo aberto até a borda da lateral / fechado no fundo falso,
    também com `c.FOLGA`), sem pente: a prateleira desliza e cola.
  * Fundo falso -> lateral: dentes de posição (stub tabs) nos dois lados,
    5 pontos ao longo da altura — não é só colado de topo.
  * Divisória / perfis do dispensador / retentor -> base e teto do
    gaveteiro: dentes de posição (stub tabs) casados com furos em BASE e
    TETO_GAV (ver `montagem.py`, que calcula as posições e repassa).
  * Fundo de gaveta -> caixa da gaveta: painel liso capturado num rasgo
    fechado (frame_slot) perto da borda inferior de frente/trás/laterais.
  * Pista do dispensador -> perfis laterais: apoio colado ao longo de toda
    a rampa (junta de topo, área de cola generosa — não dá pra fazer dente
    numa aresta inclinada com as primitivas retas deste projeto).

Frame local de cada peça: origem no canto inferior-esquerdo, X para a
direita, Y para cima. O significado físico de X/Y depende do tipo de peça
(documentado em cada função).
"""
from __future__ import annotations

from geometria import Peca
import config as c


# ---------------------------------------------------------------------
# LATERAIS (2x, esquerda/direita) — peça única (altura cabe numa chapa só)
# Frame local: X = profundidade (Y global, 0=frente..700=fundo), Y = altura (Z global)
# ---------------------------------------------------------------------

def _shelf_zones():
    """(nome, z0, z1) das 4 prateleiras largas, na ordem de baixo pra cima."""
    return [
        ("TETO_GAV", *c.TETO_GAV_Z),
        ("PRAT_2", *c.PRAT2_Z),
        ("PRAT_1", *c.PRAT1_Z),
        ("P_CAM", *c.PCAM_Z),
    ]


def _fundo_falso_tab_zs():
    """5 alturas de fixação do fundo falso nas laterais (meio de cada banda)."""
    bandas = [c.GAVETEIRO_Z, c.BAY1_Z, c.BAY2_Z, c.BAY3_Z, c.BAY4_Z]
    return [(z0 + z1) / 2 for z0, z1 in bandas]


def lateral(lado: str) -> Peca:
    """lado: 'E'/'D'."""
    w, h = c.EXT_D, c.EXT_H
    codigo = f"LAT_{lado}"
    p = Peca(codigo, f"Lateral {'esquerda' if lado=='E' else 'direita'}", w, h)

    # canto com a base (y=0) e com o tampo (y=h) — fêmea, alargada por FOLGA
    p.edge_notches("bottom", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    p.edge_notches("top", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    # canto com o fundo/traseiro (borda direita local, x=700=fundo) — fêmea
    p.edge_notches("right", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)

    # rasgos de prateleira, abertos na borda frontal (x=0 local) — fêmea
    # v2.3: sem rasgo de prateleira. As prateleiras usadas são as da v2,
    # sem aba (retângulo 874 x 494): elas colam de topo nas faces das laterais.
    pass

    # furos de fixação do fundo falso (5 pontos, ao longo da profundidade
    # FALSE_BACK_Y0..Y1) — fêmea, recebe os stub tabs de FUNDO_FALSO
    y0, y1 = c.FALSE_BACK_Y0, c.FALSE_BACK_Y1
    for z in _fundo_falso_tab_zs():
        p.hole_rect(cx=(y0 + y1) / 2, cy=z, w=y1 - y0, h=20.0, folga=c.FOLGA)

    return p


# ---------------------------------------------------------------------
# BASE / TAMPO — peça única (874 largura x 700 profundidade), sem emenda
# Frame local: X = largura (X global), Y = profundidade (Y global)
# ---------------------------------------------------------------------

def base_ou_tampo(tipo: str, holes: list[tuple[float, float, float, float]] | None = None) -> Peca:
    """tipo: 'BASE' ou 'TAMPO'. `holes`: lista de (cx, cy, w, h) — furos que
    recebem os dentes de posição das peças verticais do gaveteiro (só usado
    para BASE; TAMPO não tem nada por cima que precise fixação nela)."""
    w, h = c.INNER_W, c.EXT_D
    p = Peca(tipo, "Base" if tipo == "BASE" else "Tampo", w, h)
    # dentes que penetram nas laterais (bordas esquerda/direita) — MACHO, nominal
    p.edge_tabs("left", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    p.edge_tabs("right", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    for cx, cy, hw, hh in (holes or []):
        p.hole_rect(cx=cx, cy=cy, w=hw, h=hh, folga=c.FOLGA)
    return p


# ---------------------------------------------------------------------
# PRATELEIRAS LARGAS (P_CAM, PRAT_1, PRAT_2, TETO_GAV) — peça única
# Frame local: X = largura (X global), Y = profundidade (Y global, 0=frente)
# ---------------------------------------------------------------------

def prateleira(codigo: str, nome: str, holes: list[tuple[float, float, float, float]] | None = None) -> Peca:
    """Prateleira larga. Entra pela frente deslizando: as duas abas laterais
    correm dentro dos rasgos das laterais (abertos na borda da frente, 494mm
    de profundidade) e a aba traseira entra no rasgo do fundo falso.

    Na v2 original a prateleira era um retângulo de 874×494 — exatamente o vão
    livre entre as laterais e até a face do fundo falso. Ou seja: não entrava
    em rasgo nenhum. Os 12 rasgos já cortados (4 em cada lateral, 4 no fundo
    falso) ficavam vazios, passantes, e a prateleira dependia só de cola de
    topo. As abas abaixo têm exatamente a medida desses rasgos, que não mudam.
    """
    from shapely.geometry import box as _box
    from shapely.ops import unary_union as _uni
    T = c.MATERIAL_T
    w, h = c.INNER_W, c.SHELF_DEPTH
    p = Peca(codigo, nome, w, h)
    # o rasgo do fundo falso vai de 30 a INNER_W-30; a aba fica 0,2mm dentro disso
    m = 30.0 + 0.2
    p.poly = _uni([
        p.poly,
        _box(-T, 0.0, 0.0, h),                  # aba que entra na lateral esquerda
        _box(w, 0.0, w + T, h),                 # aba que entra na lateral direita
        _box(m, h, w - m, h + T),               # aba que entra no fundo falso
    ])
    for cx, cy, hw, hh in (holes or []):
        p.hole_rect(cx=cx, cy=cy, w=hw, h=hh, folga=c.FOLGA)
    return p


# ---------------------------------------------------------------------
# NERVURAS sob as 3 prateleiras (P_CAM, PRAT_1, PRAT_2) — peça única
# Frame local: X = largura (X global), Y = altura do perfil (38mm)
# ---------------------------------------------------------------------

def nervura(codigo: str, nome: str) -> Peca:
    w, h = c.INNER_W, c.NERVURA_H
    p = Peca(codigo, nome, w, h)
    return p


# ---------------------------------------------------------------------
# FUNDO (traseiro real) e FUNDO FALSO — peça única cada
# Frame local: X = largura (X global), Y = altura (Z global)
# ---------------------------------------------------------------------

def _dentes_na_grade_da_lateral(p: Peca, z0: float):
    """Dentes MACHO nas bordas esquerda/direita de uma peça que ocupa a faixa
    de altura z0..z0+p.h do móvel, posicionados na MESMA grade de dentes que a
    LATERAL usa na altura cheia (EXT_H) e recortados a essa faixa. Sem isso,
    uma peça mais baixa que 880mm geraria sua própria divisão de dentes e eles
    não cairiam nos rasgos já cortados das laterais.
    """
    from shapely.geometry import box as _box
    from shapely.ops import unary_union
    from geometria import finger_segments

    tabs = []
    for (a, b, is_a) in finger_segments(c.EXT_H, c.FINGER_PITCH, phase_a=True):
        if not is_a:
            continue
        lo, hi = max(a, z0) - z0, min(b, z0 + p.h) - z0
        if hi - lo <= 1e-9:
            continue
        tabs.append(_box(-c.MATERIAL_T, lo, 0.0, hi))
        tabs.append(_box(p.w, lo, p.w + c.MATERIAL_T, hi))
    if tabs:
        p.poly = unary_union([p.poly, *tabs])
    return p


def fundo(tipo: str) -> Peca:
    """tipo: 'FUNDO' (traseiro real, y=697..700 global) ou 'FUNDO_FALSO' (y=494..497).

    Os dois painéis vão ENTRE a base e o tampo (z=3..877), não do chão ao teto:
    BASE e TAMPO ocupam os 700mm de profundidade inteiros, então um painel de
    880mm de altura ocuparia o mesmo espaço que eles nos 3mm de cima e de baixo.
    Na v2 original os dois tinham 880mm — o traseiro ainda por cima tinha pente
    de dentes nas bordas de cima e de baixo, sem rasgo correspondente em lugar
    nenhum (a borda traseira de BASE/TAMPO é lisa).
    """
    w = c.INNER_W
    z0, z1 = c.BASE_Z[1], c.TOP_Z[0]       # 3 .. 877
    h = z1 - z0                             # 874
    nome = "Traseiro" if tipo == "FUNDO" else "Fundo falso"
    p = Peca(tipo, nome, w, h)

    if tipo == "FUNDO":
        # traseiro real: canto pleno só com as laterais; apoia e cola de topo
        # na base e no tampo.
        _dentes_na_grade_da_lateral(p, z0)
    else:
        # fundo falso: dentes de posição nas 2 laterais (5 pontos cada,
        # casados com os furos cortados em lateral()) — MACHO, nominal
        zs = [z - z0 for z in _fundo_falso_tab_zs()]
        p.edge_stub_tabs("left", zs, tab_w=20.0, protrusion=c.MATERIAL_T)
        p.edge_stub_tabs("right", zs, tab_w=20.0, protrusion=c.MATERIAL_T)
        # rasgos fechados para receber a borda traseira das 4 prateleiras — fêmea
        for nome_prat, zz0, zz1 in _shelf_zones():
            p.frame_slot("bottom", offset=zz0 - z0, slot_depth=c.MATERIAL_T + c.FOLGA,
                         span=(30.0, w - 30.0))
    return p


# ---------------------------------------------------------------------
# DIVISÓRIAS do gaveteiro (DIV_AB, DIV_BC, DIV_DISP) — peça única
# Frame local: X = profundidade (Y global, 0=frente), Y = altura (Z global, banda do gaveteiro)
# ---------------------------------------------------------------------

def divisoria(codigo: str, nome: str) -> Peca:
    """Divisória do gaveteiro: dentes de posição só na BASE.

    Os dentes de topo da v2 original travavam a montagem: com eles, TETO_GAV
    só podia descer de cima, e aí as abas laterais dele (que agora enchem os
    rasgos das laterais) não teriam como entrar — rasgo de prateleira é aberto
    na frente, não em cima. Agora as 4 prateleiras entram todas do mesmo jeito,
    deslizando pela frente, e TETO_GAV encosta e cola sobre o topo das
    divisórias. Quem posiciona a divisória continua sendo o furo da BASE.
    """
    h = c.GAVETEIRO_Z[1] - c.GAVETEIRO_Z[0]
    w = c.SHELF_DEPTH
    p = Peca(codigo, nome, w, h)
    centers = [w * 0.25, w * 0.75]
    # v2.2: sem dente embaixo — a BASE reaproveitada da v2 tem os furos
    # girados 90°. A divisória apoia e cola sobre a base; os furos antigos
    # (mesmo centro) servem de marca de posição.
    return p


# ---------------------------------------------------------------------
# GAVETAS — frente/trás/laterais com dentes de caixa; fundo liso capturado
# ---------------------------------------------------------------------

def gaveta_caixa(prefixo: str, largura_frente: float, altura_frente: float):
    """Devolve as 5 peças de uma gaveta: FRENTE, TRAS, LAT_E, LAT_D, FUNDO."""
    L = c.DRAWER_SLIDE_LEN  # profundidade da gaveta (lateral)
    Wf = largura_frente
    Hf = altura_frente
    T = c.MATERIAL_T
    groove_offset = c.DRAWER_GROOVE_Z
    groove_depth = T + c.FOLGA
    inset = c.DRAWER_GROOVE_INSET

    # FRENTE / TRAS: frame local X=largura, Y=altura da frente. Recebem os
    # dentes das laterais (fêmea) e o fundo capturado num rasgo (fêmea).
    frente = Peca(f"{prefixo}_FRENTE", f"Gaveta {prefixo} frente", Wf, Hf)
    frente.edge_notches("left", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    frente.edge_notches("right", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    frente.frame_slot("bottom", offset=groove_offset, slot_depth=groove_depth, inset=inset)

    tras = Peca(f"{prefixo}_TRAS", f"Gaveta {prefixo} traseira", Wf, Hf)
    tras.edge_notches("left", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    tras.edge_notches("right", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    tras.frame_slot("bottom", offset=groove_offset, slot_depth=groove_depth, inset=inset)

    # LATERAIS: frame local X=profundidade (0=frente..L=fundo), Y=altura. Dão
    # os dentes (macho) que entram nas notches de FRENTE/TRAS.
    # o rasgo das laterais vai até a ponta de trás (span termina além de L, o
    # difference recorta na borda): é por ele que o fundo entra deslizando.
    lat_e = Peca(f"{prefixo}_LAT_E", f"Gaveta {prefixo} lateral esquerda", L, Hf)
    lat_e.edge_tabs("left", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    lat_e.edge_tabs("right", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    lat_e.frame_slot("bottom", offset=groove_offset, slot_depth=groove_depth, span=(inset, L + 1.0))

    lat_d = Peca(f"{prefixo}_LAT_D", f"Gaveta {prefixo} lateral direita", L, Hf)
    lat_d.edge_tabs("left", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    lat_d.edge_tabs("right", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    lat_d.frame_slot("bottom", offset=groove_offset, slot_depth=groove_depth, span=(inset, L + 1.0))

    # FUNDO: painel com abas, não retângulo. Referência (caixa montada vista de
    # cima): FRENTE ocupa Y 0..T, as laterais X 0..T e Wf-T..Wf, TRAS Y T+L..T+L+T.
    #   * corpo       — encosta nas 4 faces internas, com folga;
    #   * abas laterais — entram nos rasgos das laterais, só no trecho em que
    #     esses rasgos existem (de inset até a ponta de trás);
    #   * abas frente/trás — entram nos rasgos de FRENTE e TRAS, só na largura
    #     em que esses rasgos existem (inset a Wf-inset).
    # Fora desses trechos o painel recua para dentro da caixa, senão bate na
    # madeira cheia da parede — que era exatamente o problema da v2 original,
    # onde o fundo era um retângulo 26mm mais largo que o vão do rasgo.
    from shapely.geometry import box as _box
    from shapely.ops import unary_union as _uni
    e = c.DRAWER_BOTTOM_ENGAGE
    r = c.DRAWER_BOTTOM_CLEAR
    corpo = _box(T + r, T + r, Wf - T - r, T + L - r)
    abas_lat = _box(T - e, T + inset + r, Wf - T + e, T + L)
    abas_ft = _box(inset + r, T - e, Wf - inset - r, T + L + e)
    poly = _uni([corpo, abas_lat, abas_ft])
    minx, miny, maxx, maxy = poly.bounds
    fundo_p = Peca(f"{prefixo}_FUNDO", f"Gaveta {prefixo} fundo", maxx - minx, maxy - miny)
    from shapely.affinity import translate as _tr
    fundo_p.poly = _tr(poly, xoff=-minx, yoff=-miny)

    return [frente, tras, lat_e, lat_d, fundo_p]


# ---------------------------------------------------------------------
# DISPENSADOR — rampa inclinada por gravidade (3 peças)
# ---------------------------------------------------------------------

def geometria_dispensador():
    """Rampa v2.2. A pista (já cortada, comprimento fixo) começa logo atrás do
    retentor, que agora é um painel frontal em y=0..T, e termina no fundo
    falso (y=494). Devolve (y_ini, z_ini, y_fim, z_fim, sen, cos) da face de
    BAIXO da pista, z medido a partir do topo da base."""
    import math
    T = c.MATERIAL_T
    L = c.DISP_PISTA_L
    s = 0.15
    for _ in range(50):
        y_ini = T + T * s + 0.2          # canto de cima da ponta da frente fica atrás do retentor
        horiz = c.SHELF_DEPTH - 0.2 - y_ini
        queda = math.sqrt(L * L - horiz * horiz)
        s = queda / L
    cs = horiz / L
    topo_tras = (c.GAVETEIRO_Z[1] - c.GAVETEIRO_Z[0]) - c.DISP_FOLGA_TRAS   # face de cima, no fundo
    z_fim = topo_tras - T / cs           # face de baixo, no fundo
    z_ini = z_fim - queda
    return y_ini, z_ini, y_ini + horiz, z_fim, s, cs


def dispensador():
    """v2.2 — DISP_LATERAL (2x, sem dente: a base reaproveitada não tem furo
    pra eles), DISP_APOIO (2x, tira colada na face interna de cada perfil,
    rente à borda inclinada: é nela que a pista apoia), DISP_RETENTOR (painel
    frontal entre os perfis, da base até acima da pista: é o batente dos
    rolos e fecha a frente do vão sob a rampa)."""
    from shapely.geometry import Polygon as ShPolygon
    T = c.MATERIAL_T
    h_bay = c.GAVETEIRO_Z[1] - c.GAVETEIRO_Z[0]
    depth = c.SHELF_DEPTH
    y0, z0, y1, z1, s, cs = geometria_dispensador()
    k = (z1 - z0) / (y1 - y0)
    zf = z0 - k * y0                 # linha da rampa estendida até y=0
    zt = z0 + k * (depth - y0)       # ... e até y=494
    lateral_disp = Peca("DISP_LATERAL", "Lateral do dispensador (rampa)", depth, h_bay)
    lateral_disp.poly = lateral_disp.poly.difference(
        ShPolygon([(0, zf), (depth, zt), (depth, h_bay + 1), (0, h_bay + 1)]))

    pista = Peca("DISP_PISTA", "Pista inclinada do dispensador", c.DISP_CLEAR_W, c.DISP_PISTA_L)

    apoio = Peca("DISP_APOIO", "Tira de apoio da pista", c.DISP_APOIO_L, c.DISP_APOIO_H)

    topo_ret = z0 + T / cs + c.DISP_LABIO      # acima da face de cima da pista, na ponta da frente
    retentor = Peca("DISP_RETENTOR", "Retentor frontal do dispensador", c.DISP_CLEAR_W, round(topo_ret, 1))
    return [lateral_disp, pista, retentor, apoio]


# ---------------------------------------------------------------------
# CUPOM DE TESTE — kerf (7 ranhuras) + par finger-joint de QC
# ---------------------------------------------------------------------

def cupom_kerf():
    p = Peca("CUPOM_KERF", "Cupom de teste de kerf 3mm", 120.0, 60.0)
    larguras = [2.8, 2.9, 3.0, 3.1, 3.2, 3.3, 3.4]
    x = 10.0
    for lg in larguras:
        p.hole_rect(cx=x, cy=40.0, w=lg, h=20.0)
        x += 15.0
    return p


def cupom_qc():
    """Par de finger-joint de QC (substitui o antigo par quebra-cabeça).
    Fêmea alargada por FOLGA, igual a todo encaixe do projeto."""
    macho = Peca("CUPOM_QC_M", "Cupom finger-joint macho", 68.0, 60.0)
    macho.edge_tabs("right", c.MATERIAL_T, c.FINGER_PITCH, which=True)
    femea = Peca("CUPOM_QC_F", "Cupom finger-joint fêmea", 60.0, 60.0)
    femea.edge_notches("left", c.MATERIAL_T, c.FINGER_PITCH, which=True, folga=c.FOLGA)
    return [macho, femea]
