"""Primitivas geométricas para as juntas do armário — v2.

Sistema único de junta usada em todo o projeto: dente retangular (finger
joint). Três operações compõem todas as uniões do móvel:

  * `edge_tabs`    — dentes que PROTUBERAM além do contorno nominal da peça
                      (encaixam num rasgo aberto ou atravessam a peça vizinha).
  * `edge_notches` — rasgos ABERTOS até a borda, cortados para dentro
                      (recebem os dentes da peça vizinha).
  * `edge_splice`  — emenda coplanar: pente de dentes que se intercalam sem
                      ultrapassar o contorno nominal somado das duas metades.
  * `frame_slot`   — rasgo FECHADO (não toca a borda da peça), usado para o
                      fundo encaixado das gavetas (technique de "painel preso
                      em ranhura").

Todas as peças são devolvidas como `shapely.geometry.Polygon` em
coordenadas locais (origem no canto inferior esquerdo do retângulo nominal,
X para a direita, Y para cima).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

import config as c


def finger_segments(length: float, pitch: float, phase_a: bool = True):
    """Divide [0, length] em ~pitch por segmento, alternando A/B.

    O número de segmentos é escolhido para que cada um fique o mais
    próximo possível de `pitch`, sempre com pelo menos 1 segmento.
    """
    n = max(1, round(length / pitch))
    step = length / n
    segs = []
    cur = 0.0
    is_a = phase_a
    for i in range(n):
        nxt = length if i == n - 1 else cur + step
        segs.append((cur, nxt, is_a))
        cur = nxt
        is_a = not is_a
    return segs


def _edge_length(w: float, h: float, edge: str) -> float:
    return w if edge in ("bottom", "top") else h


def _edge_rect(w: float, h: float, edge: str, a: float, b: float, depth: float, outward: bool):
    if edge == "bottom":
        return box(a, -depth, b, 0) if outward else box(a, 0, b, depth)
    if edge == "top":
        return box(a, h, b, h + depth) if outward else box(a, h - depth, b, h)
    if edge == "left":
        return box(-depth, a, 0, b) if outward else box(0, a, depth, b)
    if edge == "right":
        return box(w, a, w + depth, b) if outward else box(w - depth, a, w, b)
    raise ValueError(f"edge inválida: {edge}")


@dataclass
class Peca:
    codigo: str
    nome: str
    w: float
    h: float
    poly: Polygon = field(init=False)

    def __post_init__(self):
        self.poly = box(0, 0, self.w, self.h)

    # -- operações de borda -------------------------------------------------
    def edge_tabs(self, edge: str, protrusion: float, pitch: float, phase_a: bool = True, which: bool = True):
        """Acrescenta dentes que protuberam `protrusion` além da borda `edge`."""
        length = _edge_length(self.w, self.h, edge)
        tabs = [
            _edge_rect(self.w, self.h, edge, a, b, protrusion, outward=True)
            for (a, b, is_a) in finger_segments(length, pitch, phase_a)
            if is_a == which
        ]
        if tabs:
            self.poly = unary_union([self.poly, *tabs])
        return self

    def edge_notches(self, edge: str, depth: float, pitch: float, phase_a: bool = True, which: bool = True,
                      span: tuple[float, float] | None = None, folga: float = 0.0):
        """Corta rasgos abertos até a borda `edge` (lado FÊMEA), opcionalmente
        restritos a `span`. `folga` alarga o rasgo em `folga` por lado (largura
        e profundidade) além do dente nominal que vai entrar nele, pra sempre
        montar mesmo com pequena variação de kerf/calibração."""
        length = _edge_length(self.w, self.h, edge)
        lo, hi = span if span else (0.0, length)
        cuts = [
            _edge_rect(self.w, self.h, edge, a - folga, b + folga, depth + folga, outward=False)
            for (a, b, is_a) in finger_segments(length, pitch, phase_a)
            if is_a == which and a >= lo - 1e-6 and b <= hi + 1e-6
        ]
        if cuts:
            self.poly = self.poly.difference(unary_union(cuts))
        return self

    def edge_splice(self, edge: str, side: str, finger_depth: float, pitch: float, span: tuple[float, float] | None = None):
        """Emenda coplanar: metade 'A' protubera nos segmentos A e recua nos B; metade 'B' o inverso.

        `side` = 'A' ou 'B'. As duas metades, uma vez encostadas na linha de
        emenda nominal, se intercalam formando um pente reto (sem sobrepor
        material da peça oposta, respeitando a folga `SPLICE_CLEARANCE`).
        """
        phase_a = True
        which_tab = side == "A"
        self.edge_tabs(edge, finger_depth, pitch, phase_a=phase_a, which=which_tab)
        self.edge_notches(edge, finger_depth, pitch, phase_a=phase_a, which=(not which_tab), span=span)
        return self

    def frame_slot(self, edge_ref: str, offset: float, slot_depth: float, inset: float = 6.0,
                   span: tuple[float, float] | None = None):
        """Rasgo fechado próximo à borda `edge_ref`, distante `offset` dela,
        usado para capturar um painel (ex.: fundo de gaveta) sem dentes, ou
        para encaixar outra peça numa posição interna (ex.: fundo falso
        recebendo a borda traseira de uma prateleira). `inset` evita colisão
        com os dentes de canto nos dois extremos; `span` substitui o inset
        por limites explícitos (lo, hi) ao longo da borda de referência.
        """
        length = _edge_length(self.w, self.h, edge_ref)
        lo, hi = span if span else (inset, length - inset)
        if edge_ref == "bottom":
            hole = box(lo, offset, hi, offset + slot_depth)
        elif edge_ref == "top":
            hole = box(lo, self.h - offset - slot_depth, hi, self.h - offset)
        elif edge_ref == "left":
            hole = box(offset, lo, offset + slot_depth, hi)
        elif edge_ref == "right":
            hole = box(self.w - offset - slot_depth, lo, self.w - offset, hi)
        else:
            raise ValueError(edge_ref)
        self.poly = self.poly.difference(hole)
        return self

    def edge_slot(self, edge: str, lo: float, hi: float, depth: float, folga: float = 0.0):
        """Um único rasgo retangular aberto até `edge`, entre [lo, hi] ao longo
        dela (lado FÊMEA). Usado para encaixes tipo rebaixo simples (sem pente
        de dentes): prateleira -> lateral, fundo falso -> lateral, etc.
        `folga` alarga o rasgo por lado (largura e profundidade).
        """
        self.poly = self.poly.difference(
            _edge_rect(self.w, self.h, edge, lo - folga, hi + folga, depth + folga, outward=False)
        )
        return self

    def edge_stub_tabs(self, edge: str, centers: list[float], tab_w: float, protrusion: float):
        """Pequenos dentes de posicionamento em posições explícitas (não um
        pente contínuo, lado MACHO, tamanho nominal) — usado para pegar/
        registrar divisórias e outras peças verticais na peça que as recebe.
        """
        tabs = [
            _edge_rect(self.w, self.h, edge, cx - tab_w / 2, cx + tab_w / 2, protrusion, outward=True)
            for cx in centers
        ]
        if tabs:
            self.poly = unary_union([self.poly, *tabs])
        return self

    def edge_stub_notches(self, edge: str, centers: list[float], tab_w: float, depth: float, folga: float = 0.0):
        """Rasgos fêmea que recebem os `edge_stub_tabs` da peça vizinha,
        alargados por `folga` em largura e profundidade."""
        cuts = [
            _edge_rect(self.w, self.h, edge, cx - tab_w / 2 - folga, cx + tab_w / 2 + folga, depth + folga,
                       outward=False)
            for cx in centers
        ]
        if cuts:
            self.poly = self.poly.difference(unary_union(cuts))
        return self

    def hole_rect(self, cx: float, cy: float, w: float, h: float, folga: float = 0.0):
        w, h = w + 2 * folga, h + 2 * folga
        self.poly = self.poly.difference(box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
        return self

    def hole_circle(self, cx: float, cy: float, d: float, segs: int = 64):
        from shapely.geometry import Point
        self.poly = self.poly.difference(Point(cx, cy).buffer(d / 2, resolution=segs // 4))
        return self

    def bbox(self):
        return self.poly.bounds  # (minx, miny, maxx, maxy)
