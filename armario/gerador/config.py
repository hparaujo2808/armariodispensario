"""Configuração paramétrica do armário dispensador — v2.

Todas as dimensões são nominais (sem compensação de kerf: o kerf é
compensado uma única vez no CAM, como no pacote R2 original).
Unidades: milímetros.
"""

# --- Material e chapa -------------------------------------------------
MATERIAL_T = 3.0          # espessura nominal do MDF
SHEET_W = 1000.0          # chapa física
SHEET_H = 1000.0
USABLE_MIN = 10.0         # regra do projeto: coordenadas de peça entre 10 e 890mm
USABLE_MAX = 890.0
USABLE_SPAN = USABLE_MAX - USABLE_MIN   # 880mm -> vão máximo de peça única
MIN_GAP = 6.0              # separação mínima entre caixas de peças na chapa

# --- Junta tipo dedo (finger joint) — sistema único usado em todo o projeto
FINGER_PITCH = 24.0        # passo nominal do dente (mm)
# Folga geométrica normal às faces do encaixe (mesmo princípio do R2: 0,10mm
# normal a cada face do quebra-cabeça). O lado MACHO (dente) fica exatamente
# no tamanho nominal; o lado FÊMEA (rasgo/entalhe) é cortado FOLGA maior em
# largura e em profundidade — assim o dente sempre entra, mesmo com pequena
# variação de kerf/calibração, sem depender só da compensação no CAM.
FOLGA = 0.10

# --- Dimensões externas do móvel ---------------------------------------
# BASE/TAMPO/FUNDO têm dentes que protuberam MATERIAL_T além do contorno
# nominal (entram nas laterais) -> o retângulo que precisa caber na chapa é
# INNER_W + 2*MATERIAL_T, não só INNER_W. Por isso o vão interno é
# USABLE_SPAN menos essa folga, não USABLE_SPAN inteiro.
INNER_W = USABLE_SPAN - 2 * MATERIAL_T   # 874mm — vão entre laterais
# ALTURA reduzida de 1100 para caber em uma única chapa também (LATERAL e
# FUNDO não têm dentes que protuberam na própria altura -> o limite aqui é
# o USABLE_SPAN inteiro, não INNER_W). Isso elimina a última emenda do
# projeto (laterais/fundos) e a tira de reforço colada que ela ainda exigia.
EXT_H = USABLE_SPAN                 # 880mm — ALTURA (reduzida de 1100)
EXT_D = 700.0                        # PROFUNDIDADE (mantida do R2)

EXT_W = INNER_W + 2 * MATERIAL_T   # 880mm — largura externa (reduzida de 1000)
assert INNER_W + 2 * MATERIAL_T <= USABLE_SPAN + 1e-9, "BASE/TAMPO/FUNDO com dentes não cabem numa única chapa"
assert EXT_H <= USABLE_SPAN + 1e-9, "LATERAL/FUNDO não cabem numa única chapa"

# --- Zoneamento em profundidade (Y, frente -> fundo) — mantido do R2 ----
SHELF_DEPTH = 494.0                       # profundidade útil de prateleiras/gavetas
FALSE_BACK_Y0 = SHELF_DEPTH                # 494
FALSE_BACK_Y1 = FALSE_BACK_Y0 + MATERIAL_T  # 497
CABLE_CAVITY_Y0 = FALSE_BACK_Y1             # 497
CABLE_CAVITY_Y1 = EXT_D - MATERIAL_T        # 697
BACK_Y0 = CABLE_CAVITY_Y1                   # 697
BACK_Y1 = EXT_D                             # 700
assert abs(BACK_Y1 - EXT_D) < 1e-9

# --- Zoneamento em altura (Z, base -> topo) -------------------------------
# 6 painéis de MATERIAL_T (base, teto_gav, prat_2, prat_1, p_cam, tampo) +
# banda do gaveteiro (fixa, com folga de segurança pras gavetas) + banda da
# câmera (compacta) + 3 vãos livres iguais, repartindo o que sobra.
GAVETEIRO_H = 396.0   # >= 2*DRAWER_BC_FRONT_H (390mm) e 4*DRAWER_A_FRONT_H (384mm)
CAMERA_BAY_H = 80.0    # compartimento da câmera — compacto, não precisa de prateleira alta

_painel_sum = 6 * MATERIAL_T
_sobra = EXT_H - _painel_sum - GAVETEIRO_H - CAMERA_BAY_H
BAY_H = _sobra / 3
assert BAY_H > 60.0, "altura livre por prateleira ficou pequena demais — revise GAVETEIRO_H/CAMERA_BAY_H"

# banda: (nome, z0, z1)
BASE_Z = (0.0, MATERIAL_T)
GAVETEIRO_Z = (BASE_Z[1], BASE_Z[1] + GAVETEIRO_H)
TETO_GAV_Z = (GAVETEIRO_Z[1], GAVETEIRO_Z[1] + MATERIAL_T)
BAY1_Z = (TETO_GAV_Z[1], TETO_GAV_Z[1] + BAY_H)
PRAT2_Z = (BAY1_Z[1], BAY1_Z[1] + MATERIAL_T)
BAY2_Z = (PRAT2_Z[1], PRAT2_Z[1] + BAY_H)
PRAT1_Z = (BAY2_Z[1], BAY2_Z[1] + MATERIAL_T)
BAY3_Z = (PRAT1_Z[1], PRAT1_Z[1] + BAY_H)
PCAM_Z = (BAY3_Z[1], BAY3_Z[1] + MATERIAL_T)
BAY4_Z = (PCAM_Z[1], PCAM_Z[1] + CAMERA_BAY_H)
TOP_Z = (BAY4_Z[1], BAY4_Z[1] + MATERIAL_T)

assert abs(TOP_Z[1] - EXT_H) < 1e-6

# --- Zoneamento em largura (X) do gaveteiro/dispensador ------------------
# DISP_BAY_W é o vão livre entre a divisória DIV_DISP e a face interna da
# lateral direita. As duas peças DISP_LATERAL (perfil da rampa) são coladas
# de encontro a essas duas faces, cada uma consumindo mais MATERIAL_T de
# largura -> o espaço realmente livre pros rolos é DISP_BAY_W - 2*MATERIAL_T,
# não -1*MATERIAL_T (esse era um erro da primeira versão: contava só 1 peça).
DISP_ROLLER_MAX = 190.0
DISP_CLEAR_W = 192.0                                  # meta de vão livre (margem sobre o rolo)
DISP_BAY_W = DISP_CLEAR_W + 2 * MATERIAL_T             # 198mm
assert DISP_CLEAR_W >= DISP_ROLLER_MAX

# 3 colunas de gavetas (A largas/rasas x4, B e C estreitas/fundas x2) + 2 divisórias + 1 divisória do dispensador
_gaveteiro_w = INNER_W - DISP_BAY_W - MATERIAL_T   # largura restante para colunas + divisórias
_n_dividers_gav = 2
_cols_material = _n_dividers_gav * MATERIAL_T
_cols_usable = _gaveteiro_w - _cols_material
# proporção herdada do R2 (468 : 221 : 221), normalizada ao novo espaço disponível
_ratio_A, _ratio_B, _ratio_C = 468.0, 221.0, 221.0
_ratio_sum = _ratio_A + _ratio_B + _ratio_C
COL_A_W = round(_cols_usable * _ratio_A / _ratio_sum, 1)
COL_B_W = round(_cols_usable * _ratio_B / _ratio_sum, 1)
COL_C_W = round(_cols_usable * _ratio_C / _ratio_sum, 1)
# ajusta arredondamento na coluna A para fechar a soma exatamente
COL_A_W = round(_cols_usable - COL_B_W - COL_C_W, 1)

# Posições X (a partir da face interna da lateral esquerda, X=0) de cada
# elemento do gaveteiro — usadas tanto para desenhar as peças verticais
# quanto para furar BASE/TETO_GAV nos pontos exatos que as recebem.
X_COL_A = (0.0, COL_A_W)
X_DIV_AB = (X_COL_A[1], X_COL_A[1] + MATERIAL_T)
X_COL_B = (X_DIV_AB[1], X_DIV_AB[1] + COL_B_W)
X_DIV_BC = (X_COL_B[1], X_COL_B[1] + MATERIAL_T)
X_COL_C = (X_DIV_BC[1], X_DIV_BC[1] + COL_C_W)
X_DIV_DISP = (X_COL_C[1], X_COL_C[1] + MATERIAL_T)
X_DISP_BAY = (X_DIV_DISP[1], X_DIV_DISP[1] + DISP_BAY_W)
assert abs(X_DISP_BAY[1] - INNER_W) < 1e-6, "layout do gaveteiro não fecha com INNER_W"

X_DIV_AB_MID = sum(X_DIV_AB) / 2
X_DIV_BC_MID = sum(X_DIV_BC) / 2
X_DIV_DISP_MID = sum(X_DIV_DISP) / 2
X_DISP_LAT_ESQ_MID = X_DISP_BAY[0] + MATERIAL_T / 2   # perfil colado na face esquerda da baia
X_DISP_LAT_DIR_MID = X_DISP_BAY[1] - MATERIAL_T / 2   # perfil colado na face interna da lateral direita
DISP_RETENTOR_Y = 15.0     # distância da frente do móvel até o retentor

DRAWER_SLIDE_LEN = 457.0     # comprimento nominal da corrediça / lateral da gaveta
DRAWER_SIDE_CLEARANCE = 13.0  # folga lateral por lado, prevista para a ferragem real

# --- Fundo capturado da gaveta ------------------------------------------
# O fundo entra num rasgo a GROOVE_Z da borda inferior das 4 paredes. O rasgo
# das DUAS LATERAIS é aberto na ponta de trás: o fundo entra deslizando pela
# traseira com frente+laterais já coladas, e a peça TRAS fecha capturando a
# aba traseira dele. Na v2 original o rasgo era fechado nos 4 lados e o fundo
# era um retângulo maior que o vão dos rasgos — não havia como montar.
DRAWER_GROOVE_Z = 6.0          # altura do rasgo acima da borda inferior
DRAWER_GROOVE_INSET = 14.0     # distância do rasgo aos cantos (frente/trás e ponta dianteira da lateral)
DRAWER_BOTTOM_ENGAGE = 2.0     # quanto a aba do fundo entra em cada rasgo (rasgo tem MATERIAL_T+FOLGA)
DRAWER_BOTTOM_CLEAR = 0.15     # folga do fundo contra as faces internas da caixa

# alturas de frente das gavetas (mantidas do R2: coluna A rasa x4, B/C fundas x2)
DRAWER_A_FRONT_H = 96.0
DRAWER_BC_FRONT_H = 195.0
N_DRAWERS_A = 4
N_DRAWERS_B = 2
N_DRAWERS_C = 2
assert N_DRAWERS_A * DRAWER_A_FRONT_H <= GAVETEIRO_Z[1] - GAVETEIRO_Z[0]
assert N_DRAWERS_B * DRAWER_BC_FRONT_H <= GAVETEIRO_Z[1] - GAVETEIRO_Z[0]
assert N_DRAWERS_C * DRAWER_BC_FRONT_H <= GAVETEIRO_Z[1] - GAVETEIRO_Z[0]

# --- Nervuras de sustentação sob as prateleiras largas -------------------
N_NERVURAS_POR_PRATELEIRA = 3
NERVURA_H = 38.0   # altura (perfil) da nervura, mantida do R2

# --- Produção em andamento: peças que já saíram da máquina ----------------
# Chapas 01 a 07 da revisão v2 original já foram cortadas. Destas, as peças
# abaixo NÃO mudaram com as correções desta revisão e continuam válidas — não
# entram no novo nesting. As outras 12 peças daquelas chapas viraram sucata
# (ver LEIA_PRIMEIRO.md) e são recortadas junto com o resto.
# Formato: código -> quantidade já cortada e aproveitável.
# v2.3: calculado por montagem.resolver_ja_cortadas() a partir de
# CORTAR_NA_MAQUINA (tudo da v2 menos LAT_E/LAT_D). Na entrega da V2.3 ficou
# None e o main.py quebrava.
PECAS_JA_CORTADAS = None
# v2.3: todas as chapas da v2 (01 a 15) já foram cortadas. Só LAT_E e LAT_D
# precisam de corte novo (as antigas foram coladas). O resto é peça da v2,
# usada como está ou com retrabalho manual (ver LEIA_PRIMEIRO.md).
CORTAR_NA_MAQUINA = {"LAT_E", "LAT_D"}
# As chapas novas continuam a numeração de onde a produção parou.
PRIMEIRA_CHAPA = 22   # continua depois das 21 chapas da v2
VERSAO = "v2.3"

# --- Cores DXF (ACI) -------------------------------------------------------
COLOR_CUT = 1    # vermelho — corte
COLOR_ENGRAVE = 5  # azul — gravação


# --- v2.2: dispensador refeito (só peças ainda não cortadas) -------------
# A DISP_PISTA já está cortada (v2): comprimento fixo = hipotenusa de 494 x 60.
DISP_PISTA_L = (SHELF_DEPTH ** 2 + 60.0 ** 2) ** 0.5   # 497,63mm
DISP_FOLGA_TRAS = 60.0      # vão livre entre a face de cima da pista e o TETO_GAV, no fundo
DISP_LABIO = 35.0           # quanto o retentor sobe acima da face de cima da pista, na frente
DISP_APOIO_H = 12.0         # altura das tiras de apoio da pista
DISP_APOIO_L = 470.0        # comprimento das tiras de apoio
