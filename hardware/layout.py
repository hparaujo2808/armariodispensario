"""Posição de tudo o que se prende no armário já montado. Fonte única usada
por hardware/furos.py, calculos/coolers_externos.py e pelo gerador da porta.

Coordenadas olhando o armário de frente, a partir do canto externo de baixo à
esquerda, em mm: X para a direita, Y da frente para o fundo, Z para cima.
Na face de fora da lateral esquerda, "Y" é a distância da borda da frente.

Pior caso assumido (pedido do grupo, 22/10): caixa, traseiro, fundo falso e
corrediças já colados ou parafusados. Nada aqui exige desmontar ou recortar
contorno de peça cortada; os furos são feitos por fora, com gabarito.
"""
from __future__ import annotations

import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "armario", "gerador"))
import config as c  # noqa: E402

T = c.MATERIAL_T

# --- corrediças já presas na LAT_E (LEIA_PRIMEIRO da V2.3): centro em Z, altura 45 mm
CORREDICA_ALTURA = 45.0
CORREDICAS_LAT_E = {"A1": 53.4, "A2": 151.8, "A3": 250.2, "A4": 348.6}
CORREDICA_ESPESSURA = 12.7


def faixas_corredicas():
    return [(z - CORREDICA_ALTURA / 2, z + CORREDICA_ALTURA / 2) for z in CORREDICAS_LAT_E.values()]


# --- gaveta: frente nominal (calc a partir do config) -------------------------
# Corrediça de 457 mm começa a 3 mm da frente; a lateral da gaveta (457 + 2 dentes
# de 3 mm) começa logo atrás da frente de 3 mm -> frente da gaveta rente à caixa.
FRENTE_GAVETA_Y = c.FRENTE_GAVETA_Y            # 0,0 mm [calc] = 3,0 (início da corrediça) − 3,0 (frente); medir

# --- baia fria (coluna A, metade de cima) -------------------------------------
BAIA_X = (T, T + c.COL_A_W)                   # 3 a 346
BAIA_Z = (c.BAIA_PISO_Z, c.GAVETEIRO_Z[1])     # piso novo a 205 (gaveta A2 vai até 199,8)
EPS = 50.0

# --- Peltier, atravessando a LAT_E -------------------------------------------
PELTIER_LADO = 40.0
PELTIER_Y = (160.0, 330.0)                     # centros, da frente
PELTIER_Z = 300.0                              # entre as corrediças A3 (até 272,7) e A4 (desde 326,1)
FURO_PELTIER = 41.0                            # quadrado, 0,5 mm de folga por lado
PRENSA_DY = 35.0                               # barras roscadas M3 em Y ± 35, mesma altura
FURO_M3 = 3.5
FURO_M4 = 4.5

# --- cooler Hyper 212 Spectrum V3 [ds KaBuM 22/10] --------------------------
COOLER_L, COOLER_P, COOLER_A = 124.0, 73.0, 152.0   # C x L x A
COOLER_MASSA = 0.65                                 # kg
VENTOINHA_ESP = 25.0
PELTIER_ESP = 3.8                                   # [est] medir com paquímetro
# Montado de lado: base na LAT_E, heat pipes para fora (−X), ventoinha embaixo
# soprando para cima (+Z). Na face da lateral ocupa 124 (Y) x 73 (Z) + ventoinha.


def cooler_caixa(i: int):
    """(x0, x1, y0, y1, z0, z1) do cooler i, incluindo a ventoinha."""
    y = PELTIER_Y[i]
    x1 = -(PELTIER_ESP - T)                     # pastilha 3,8 mm num furo de 3 mm: sobra 0,8 para fora
    return (x1 - COOLER_A, x1, y - COOLER_L / 2, y + COOLER_L / 2,
            PELTIER_Z - COOLER_P / 2 - VENTOINHA_ESP, PELTIER_Z + COOLER_P / 2)


# --- berço do cooler (cortado a laser) ----------------------------------------
BERCO_FOLGA = 12.0                 # mm entre a grade do berço e a ventoinha (ar entra por baixo)
BERCO_ESPESSURA = T


def berco_z():
    return cooler_caixa(0)[4] - BERCO_FOLGA - BERCO_ESPESSURA   # face de baixo da placa do berço


BERCO_X = -(COOLER_A + 10.0)                     # até onde o berço vai para fora
# Parafusos M4 da placa de base do suporte, na LAT_E: Z livres de corrediça
SUPORTE_PARAFUSOS_Z = (102.0, 200.0)             # entre A1 (até 75,9) e A2 (129,3); entre A2 (174,3) e A3 (227,7)
SUPORTE_PARAFUSOS_DY = (-55.0, 55.0)             # em relação ao centro do cooler, em Y

# --- furo dos fios da baia (DS18B20 + ventoinhas frias), entre os coolers -----
FURO_FIOS_BAIA = ((PELTIER_Y[0] + PELTIER_Y[1]) / 2, PELTIER_Z, 10.0)   # (Y, Z, Ø)

# --- dobradiça da porta (lado esquerdo) -------------------------------------
# Dobradiça piano e bloco de reforço: parâmetros em armario/gerador/config.py
# (seção v2.4). O bloco (3 camadas, a do meio prende porcas M3) avança
# AFASTAMENTO_PORTA para a frente da caixa, para a porta ficar longe das gavetas.
BLOCO_DOB_LARGURA = c.BLOCO_DOB_LARGURA
BLOCO_DOB_Z = (c.DOB_Z0, c.DOB_Z0 + c.DOB_COMPRIMENTO)
AFASTAMENTO_PORTA = c.AFASTAMENTO_PORTA
BLOCO_DOB_PARAFUSO_Y = c.BLOCO_DOB_PARAFUSO_Y
BLOCO_DOB_PARAFUSOS_Z = c.BLOCO_DOB_PARAFUSOS_Z

# --- trava e reed (lateral direita, por dentro, perto da frente) -------------
TRAVA_Z = c.TRAVA_Z                # entre a Prateleira 2 (533,7) e as nervuras da Prateleira 1 (624,3)
TRAVA_CORPO = c.TRAVA_CORPO        # [est] medir a FE-91
TRAVA_FUROS_DY = c.TRAVA_FUROS_DY
REED_Z = c.REED_Z
FURO_FIOS_TRAVA = (40.0, 580.0, 10.0)            # (Y, Z, Ø) na LAT_D
CAMERA_INTERNA = (60.0, 460.0, 38.0)             # (Y, Z, Ø) na LAT_D, cabo com plugue USB passa

# --- tampo: câmera externa e caixa da eletrônica -----------------------------
CAMERA_EXTERNA_XY = (440.0, 30.0)
CAIXA_ELETRONICA = tuple(d + 2 * T for d in c.CAIXA_INT)   # externos
CAIXA_ELETRONICA_XY = c.CAIXA_XY
