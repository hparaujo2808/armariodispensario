"""Posições globais (X,Y,Z em mm, a partir do canto externo inferior
esquerdo da frente do móvel) das nervuras — para `MONTAGEM_REFORCOS.md` e
`POSICOES_MONTAGEM.json`.

Não há mais reforço colado de emenda: com a altura reduzida a 880mm, base,
tampo, laterais e fundos cabem todos numa peça única — o projeto inteiro
ficou sem nenhuma emenda de painel.

X aumenta para a direita, Y para o fundo, Z para cima.
"""
from __future__ import annotations

import config as c


def nervuras_posicao():
    zonas = [
        ("P_CAM", c.PCAM_Z[0]),
        ("PRAT_1", c.PRAT1_Z[0]),
        ("PRAT_2", c.PRAT2_Z[0]),
    ]
    itens = []
    for nome, z_prateleira in zonas:
        for i in range(c.N_NERVURAS_POR_PRATELEIRA):
            y_centro = c.SHELF_DEPTH * (i + 0.5) / c.N_NERVURAS_POR_PRATELEIRA
            itens.append({
                "codigo": f"NERV_{nome}_{i+1}",
                "descricao": f"Nervura sob {nome}, linha {i+1}",
                "x_mm": [c.MATERIAL_T, c.EXT_W - c.MATERIAL_T],
                "y_mm": [y_centro - c.MATERIAL_T / 2, y_centro + c.MATERIAL_T / 2],
                "z_mm": [z_prateleira - c.NERVURA_H, z_prateleira],
            })
    return itens


def montagem_markdown() -> str:
    linhas = [
        "# Posição das nervuras — v2",
        "",
        "Olhe o armário de frente. Medidas em milímetros, a partir do canto externo",
        "inferior esquerdo da frente: X aumenta para a direita, Y para o fundo, Z para",
        "cima. As faixas incluem a espessura de 3mm da peça de referência.",
        "",
        "Não há reforço colado de emenda nesta revisão: com a altura reduzida a",
        f"{c.EXT_H:.0f}mm, base, tampo, as duas laterais e os dois fundos cabem cada um",
        "numa peça única — o projeto inteiro ficou sem nenhuma emenda de painel. A",
        "única colagem estrutural que resta é nos cantos (dente reto) e nas nervuras",
        "abaixo.",
        "",
        "| Código | X: esquerda → direita | Y: frente → fundo | Z: baixo → cima |",
        "|---|---:|---:|---:|",
    ]
    for it in nervuras_posicao():
        linhas.append(
            f"| {it['codigo']} | {it['x_mm'][0]:.1f} a {it['x_mm'][1]:.1f} | "
            f"{it['y_mm'][0]:.1f} a {it['y_mm'][1]:.1f} | {it['z_mm'][0]:.1f} a {it['z_mm'][1]:.1f} |"
        )
    linhas += [
        "",
        "As nervuras NERV entram nos rasgos da prateleira correspondente e são",
        "coladas por baixo dela.",
        "",
        "A tabela descreve posições calculadas parametricamente. Não substitui o",
        "ensaio de montagem, a escolha das ferragens ou a avaliação de resistência e",
        "estabilidade do conjunto.",
    ]
    return "\n".join(linhas) + "\n"
