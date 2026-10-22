"""Distribui as peças nas chapas 1000x1000mm (área útil 900x900, regra de
coordenadas 10-890mm, separação mínima de 6mm) — empacotamento em
prateleiras (shelf packing), sem rotacionar peça (mantém a gravação legível
na orientação de montagem).
"""
from __future__ import annotations

from dataclasses import dataclass
from shapely.affinity import translate

import config as c
from montagem import ItemBOM


@dataclass
class PecaNaChapa:
    item: ItemBOM
    instancia: int          # 1..quantidade, para peças com quantidade>1 (ex.: DISP_LATERAL espelhada)
    chapa: int
    x: float                # deslocamento aplicado ao polígono local (canto inf-esq do bbox nominal)
    y: float
    poly_global: object      # shapely Polygon já deslocado para a posição na chapa
    rotacionada: bool = False  # True = peça girada 90° para melhor aproveitamento da chapa


class _Shelf:
    __slots__ = ("chapa", "y0", "altura", "usado_x")

    def __init__(self, chapa, y0, altura):
        self.chapa = chapa
        self.y0 = y0
        self.altura = altura
        self.usado_x = 0.0


def descontar_ja_cortadas(itens: list[ItemBOM], ja_cortadas: dict[str, int]) -> list[ItemBOM]:
    """Remove do lote a cortar as peças que já saíram da máquina em chapas
    anteriores e continuam válidas. Devolve uma lista nova; a BOM original
    (LISTA_PECAS.csv) continua listando o móvel inteiro."""
    restantes = []
    sobra = dict(ja_cortadas)
    for item in itens:
        feitas = min(sobra.get(item.peca.codigo, 0), item.quantidade)
        if feitas:
            sobra[item.peca.codigo] -= feitas
        falta = item.quantidade - feitas
        if falta > 0:
            restantes.append(ItemBOM(item.peca, item.grupo, falta))
    pendentes = {k: v for k, v in sobra.items() if v}
    if pendentes:
        raise ValueError(f"PECAS_JA_CORTADAS cita peça/quantidade que não existe na BOM: {pendentes}")
    return restantes


def empacotar(itens: list[ItemBOM], primeira_chapa: int = 1) -> list[PecaNaChapa]:
    """Shelf-BFDH (best-fit decreasing height): mantém várias prateleiras
    abertas (inclusive em chapas diferentes) e coloca cada peça na que sobra
    menos espaço de largura, só abrindo prateleira/chapa nova quando
    necessário. Bem mais denso que um shelf-packing ingênuo de uma
    prateleira por vez.
    """
    span = c.USABLE_SPAN
    gap = c.MIN_GAP

    unidades = []
    for item in itens:
        minx, miny, maxx, maxy = item.peca.poly.bounds
        w, h = maxx - minx, maxy - miny
        for inst in range(1, item.quantidade + 1):
            unidades.append((item, inst, w, h, minx, miny))
    unidades.sort(key=lambda u: u[3], reverse=True)  # por altura desc

    shelves: list[_Shelf] = []
    n_chapas_abertas = 0

    def abrir_chapa():
        nonlocal n_chapas_abertas
        n_chapas_abertas += 1
        s = _Shelf(primeira_chapa - 1 + n_chapas_abertas, 0.0, 0.0)
        shelves.append(s)
        return s

    colocados: list[PecaNaChapa] = []

    for (item, inst, w, h, minx, miny) in unidades:
        if w > span or h > span:
            raise ValueError(
                f"{item.peca.codigo}: {w:.1f}x{h:.1f}mm excede o vão máximo de peça única ({span}mm)."
            )
        # procura, entre as prateleiras já abertas, a que tem altura suficiente
        # e sobra menos largura depois de colocar (best fit)
        melhor = None
        melhor_folga = None
        for s in shelves:
            if h <= s.altura + 1e-9 and s.usado_x + w <= span + 1e-9:
                folga = span - (s.usado_x + w)
                if melhor is None or folga < melhor_folga:
                    melhor, melhor_folga = s, folga

        if melhor is None:
            # nenhuma prateleira aberta serve: tenta abrir uma prateleira nova
            # em QUALQUER chapa já usada que ainda tenha altura livre (não só
            # a última) — escolhe a que sobra menos altura depois de colocar,
            # pra preencher chapas parcialmente ocupadas antes de abrir uma nova
            chapas_usadas = sorted({s.chapa for s in shelves})
            melhor_chapa, melhor_sobra_v = None, None
            for chapa_id in chapas_usadas:
                topo = max(s.y0 + s.altura for s in shelves if s.chapa == chapa_id)
                y_livre = topo + gap
                if y_livre + h <= span + 1e-9:
                    sobra_v = span - (y_livre + h)
                    if melhor_sobra_v is None or sobra_v < melhor_sobra_v:
                        melhor_chapa, melhor_sobra_v, melhor_y_livre = chapa_id, sobra_v, y_livre

            if melhor_chapa is not None:
                melhor = _Shelf(melhor_chapa, melhor_y_livre, h)
                shelves.append(melhor)
            else:
                s = abrir_chapa()
                s.altura = h
                melhor = s

        dx = c.USABLE_MIN + melhor.usado_x - minx
        dy = c.USABLE_MIN + melhor.y0 - miny
        poly_global = translate(item.peca.poly, xoff=dx, yoff=dy)
        colocados.append(PecaNaChapa(item, inst, melhor.chapa, dx, dy, poly_global))
        melhor.usado_x += w + gap

    return colocados


def n_chapas(colocados: list[PecaNaChapa]) -> int:
    return len({p.chapa for p in colocados}) if colocados else 0


def validar_sem_sobreposicao(colocados: list[PecaNaChapa]) -> list[str]:
    """Confere, por chapa, que nenhuma peça se sobrepõe/encosta a menos de
    MIN_GAP de outra, e que todas as coordenadas ficam em 10..890mm."""
    problemas = []
    por_chapa: dict[int, list[PecaNaChapa]] = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p)

    for chapa, pecas_chapa in por_chapa.items():
        for p in pecas_chapa:
            minx, miny, maxx, maxy = p.poly_global.bounds
            if minx < c.USABLE_MIN - 1e-6 or maxx > c.USABLE_MAX + 1e-6 or \
               miny < c.USABLE_MIN - 1e-6 or maxy > c.USABLE_MAX + 1e-6:
                problemas.append(
                    f"chapa {chapa}: {p.item.peca.codigo} fora da faixa 10-890mm ({minx:.1f},{miny:.1f},{maxx:.1f},{maxy:.1f})"
                )
        for i in range(len(pecas_chapa)):
            for j in range(i + 1, len(pecas_chapa)):
                a, b = pecas_chapa[i], pecas_chapa[j]
                dist = a.poly_global.distance(b.poly_global)
                if dist < c.MIN_GAP - 1e-6:
                    problemas.append(
                        f"chapa {chapa}: {a.item.peca.codigo} a {dist:.2f}mm de {b.item.peca.codigo} (mínimo {c.MIN_GAP}mm)"
                    )
    return problemas
