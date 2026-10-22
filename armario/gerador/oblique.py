"""Projeção oblíqua simples (cavalier) pra ilustrações esquemáticas em 2D.

X = largura (direita), Y = profundidade (foge na diagonal), Z = altura (cima).
Não é CAD nem escala fiel de desenho técnico — é só uma ilustração simples
pra dar noção espacial de como as peças se encaixam.
"""
import math

ANGLE = 35.0
K = 0.45


def proj(pt):
    x, y, z = pt
    a = math.radians(ANGLE)
    sx = x + y * math.cos(a) * K
    sy = z + y * math.sin(a) * K
    return sx, sy


def xy_quad(x0, x1, y0, y1, z):
    """Painel horizontal (base/tampo/prateleira), plano Z constante."""
    return [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]


def yz_quad(x, y0, y1, z0, z1):
    """Painel vertical tipo lateral, plano X constante."""
    return [(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)]


def xz_quad(y, x0, x1, z0, z1):
    """Painel vertical tipo fundo, plano Y constante."""
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]


def bbox2d(quads):
    xs, ys = [], []
    for q in quads:
        for p in q:
            sx, sy = proj(p)
            xs.append(sx)
            ys.append(sy)
    return min(xs), max(xs), min(ys), max(ys)
