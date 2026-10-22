"""Monta a lista completa de peças do armário v2, com metadados para os
relatórios (BOM, validação) e para o nesting.
"""
from __future__ import annotations

from dataclasses import dataclass
from geometria import Peca
import config as c
import pecas as P


@dataclass
class ItemBOM:
    peca: Peca
    grupo: str
    quantidade: int = 1


def _furos_gaveteiro():
    """Furos na BASE que recebem os dentes de posição das peças verticais do
    gaveteiro: 3 divisórias, 2 perfis do dispensador (cada um com 2 pontos,
    nas mesmas frações 0.25/0.75 da profundidade) e o retentor frontal.
    TETO_GAV não leva furo nesta revisão."""
    y_a, y_b = c.SHELF_DEPTH * 0.25, c.SHELF_DEPTH * 0.75
    base_holes = []
    teto_holes = []
    # Divisórias e perfis do dispensador são chapas em pé no plano X=const: o
    # dente delas mede MATERIAL_T na direção X (a espessura da chapa) por 20mm
    # na direção Y (ao longo da profundidade). O furo tem que ter essa mesma
    # orientação — na v2 original ele saía 20mm em X por MATERIAL_T em Y, ou
    # seja, girado 90°, e nenhum desses dentes entrava.
    for x_mid in (c.X_DIV_AB_MID, c.X_DIV_BC_MID, c.X_DIV_DISP_MID,
                  c.X_DISP_LAT_ESQ_MID, c.X_DISP_LAT_DIR_MID):
        for y in (y_a, y_b):
            base_holes.append((x_mid, y, c.MATERIAL_T, 20.0))
    # TETO_GAV não leva mais furo: as divisórias perderam o dente de topo para
    # que as 4 prateleiras possam entrar deslizando pela frente (ver divisoria()).

    # o retentor é uma chapa em pé no plano Y=const (atravessa o vão na largura):
    # o dente dele mede 20mm em X por MATERIAL_T em Y — orientação oposta à das
    # divisórias, e esta já estava certa.
    clear_x0 = c.X_DISP_BAY[0] + c.MATERIAL_T
    for frac in (0.3, 0.7):
        base_holes.append((clear_x0 + c.DISP_CLEAR_W * frac, c.DISP_RETENTOR_Y, 20.0, c.MATERIAL_T))

    return base_holes, teto_holes


def resolver_ja_cortadas(itens: list[ItemBOM]) -> dict[str, int]:
    """Preenche c.PECAS_JA_CORTADAS com todas as peças do móvel que não estão
    em c.CORTAR_NA_MAQUINA, se o config não trouxer a lista pronta."""
    if c.PECAS_JA_CORTADAS is None:
        ja: dict[str, int] = {}
        for i in itens:
            if i.grupo != "cupom" and i.peca.codigo not in c.CORTAR_NA_MAQUINA:
                ja[i.peca.codigo] = ja.get(i.peca.codigo, 0) + i.quantidade
        c.PECAS_JA_CORTADAS = ja
    return c.PECAS_JA_CORTADAS


def montar_pecas() -> list[ItemBOM]:
    itens: list[ItemBOM] = []

    def add(peca: Peca, grupo: str):
        itens.append(ItemBOM(peca, grupo))

    base_holes, teto_holes = _furos_gaveteiro()

    # --- Carcaça ---------------------------------------------------------
    for lado in ("E", "D"):
        add(P.lateral(lado), "carcaça")

    add(P.base_ou_tampo("BASE", holes=base_holes), "carcaça")
    add(P.base_ou_tampo("TAMPO"), "carcaça")

    add(P.fundo("FUNDO"), "carcaça")
    add(P.fundo("FUNDO_FALSO"), "carcaça")

    # --- Prateleiras e nervuras -------------------------------------------
    prateleiras = [
        ("P_CAM", "Piso do compartimento da câmera", None),
        ("PRAT_1", "Prateleira livre 1", None),
        ("PRAT_2", "Prateleira livre 2", None),
        ("TETO_GAV", "Prateleira 3 / teto do gaveteiro", teto_holes),
    ]
    for codigo, nome, holes in prateleiras:
        add(P.prateleira(codigo, nome, holes=holes), "prateleiras")

    for codigo, _, _h in prateleiras[:3]:  # TETO_GAV não tem nervura (é o teto do gaveteiro)
        for i in range(c.N_NERVURAS_POR_PRATELEIRA):
            add(P.nervura(f"NERV_{codigo}_{i+1}", f"Nervura sob {codigo} linha {i+1}"), "nervuras")

    # --- Divisórias do gaveteiro -------------------------------------------
    add(P.divisoria("DIV_AB", "Divisória gaveteiro A-B"), "gaveteiro")
    add(P.divisoria("DIV_BC", "Divisória gaveteiro B-C"), "gaveteiro")
    add(P.divisoria("DIV_DISP", "Divisória gaveteiro-dispensador"), "gaveteiro")

    # --- Gavetas -------------------------------------------------------
    colunas = [
        ("A", c.COL_A_W, c.DRAWER_A_FRONT_H, c.N_DRAWERS_A),
        ("B", c.COL_B_W, c.DRAWER_BC_FRONT_H, c.N_DRAWERS_B),
        ("C", c.COL_C_W, c.DRAWER_BC_FRONT_H, c.N_DRAWERS_C),
    ]
    for prefixo, col_w, front_h, n in colunas:
        largura_frente = col_w - 2 * c.DRAWER_SIDE_CLEARANCE
        for k in range(1, n + 1):
            for peca in P.gaveta_caixa(f"{prefixo}{k}", largura_frente, front_h):
                add(peca, "gavetas")

    # --- Dispensador -------------------------------------------------------
    lateral_disp, pista, retentor, apoio = P.dispensador()
    itens.append(ItemBOM(lateral_disp, "dispensador", quantidade=2))  # espelhada nos 2 lados do vão
    add(pista, "dispensador")
    add(retentor, "dispensador")
    itens.append(ItemBOM(apoio, "dispensador", quantidade=2))

    # --- Cupons de teste -------------------------------------------------------
    add(P.cupom_kerf(), "cupom")
    for peca in P.cupom_qc():
        add(peca, "cupom")

    return itens


def resumo_larguras():
    """Para debug/relatório: confirma o orçamento de largura do gaveteiro."""
    return {
        "INNER_W": c.INNER_W,
        "DISP_BAY_W": c.DISP_BAY_W,
        "divisoria_disp": c.MATERIAL_T,
        "COL_A_W": c.COL_A_W,
        "div_AB": c.MATERIAL_T,
        "COL_B_W": c.COL_B_W,
        "div_BC": c.MATERIAL_T,
        "COL_C_W": c.COL_C_W,
        "soma": c.DISP_BAY_W + c.MATERIAL_T + c.COL_A_W + c.MATERIAL_T + c.COL_B_W + c.MATERIAL_T + c.COL_C_W,
    }
