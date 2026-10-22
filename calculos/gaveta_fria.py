"""Compara opções de gaveta fria: volume útil e temperatura alcançável.

    python calculos/gaveta_fria.py

Mesmo modelo de regime permanente do cálculo térmico do legado
(referencias_externas/.../dispensario_interno/calculos/termico.py), com três
mudanças: o módulo é a TEC1-12703 que o grupo já comprou, as medidas saem do
config.py da V2.3 e o espaçador é uma barra quadrada de alumínio de 38,1 mm.

Origem dos números:
[ds]   TEC1-12703: Beijing Huimao TES1-12703 (Th = 25 °C): Imax 3 A,
       Umax 15,2 V, ΔTmax 67 K (link em docs/AUDITORIA.md).
[ds]   XPS: condutividade 0,030–0,035 W/m·K nas fichas de XPS comercial;
       usamos 0,035 (pior caso). MDF 0,14 W/m·K. Alumínio 6061 ~ 167 W/m·K;
       usamos 160.
[est]  Cooler de torre no lado quente: 0,35 K/W com a ventoinha ligada
       (fabricantes não publicam). Dissipador frio 65x46x24 com ventoinha de
       60 mm: 1,2 K/W. Os dois viram [medir] no roteiro de bancada.
[est]  6 aberturas por hora trocando todo o ar da baia, 1 W da ventoinha
       interna, 1 W de produto que chega da farmácia, +25% por pontes térmicas.
"""
from __future__ import annotations

import math
import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "armario", "gerador"))
import config as c  # noqa: E402

K0 = 273.15

# ---- módulo [ds] -----------------------------------------------------------
TH_REF = 25 + K0
UMAX, IMAX, DTMAX = 15.2, 3.0, 67.0
S = UMAX / TH_REF
R_MOD = UMAX * (TH_REF - DTMAX) / (IMAX * TH_REF)
K_MOD = IMAX * UMAX * (TH_REF - DTMAX) / (2 * TH_REF * DTMAX)
V = 12.0
R_PASTA = 0.05          # K/W por interface, 40 x 40 mm [est]

# ---- materiais --------------------------------------------------------------
K_XPS, K_MDF, K_AL = 0.035, 0.14, 160.0
H_IN, H_OUT = 1 / 0.05, 1 / 0.13
PONTES = 1.25
R_QUENTE = 0.35         # cooler de torre com ventoinha [est]
R_FRIO = 1.2            # dissipador 65x46x24 + ventoinha 60 mm [est]
LADO_ESPACADOR = 0.0381  # barra quadrada de 1 1/2"
PROF_FRIO = 45.0        # mm ocupados no fundo pelo dissipador frio + ventoinha
FOLGA_BANDEJA = 3.0     # mm de folga da bandeja contra o isolamento, por lado
PAREDE_BANDEJA = c.MATERIAL_T

# ---- baias possíveis (medidas do config.py da V2.3) --------------------------
# Z da baia: de 201 (logo acima da gaveta de baixo, que vai até 200) ao teto
# do gaveteiro (399). Ver docs/AUDITORIA.md, seção 2.
Z0, Z1 = 201.0, c.GAVETEIRO_Z[1]
BAIAS = {
    "C2 (coluna C, em cima)": (c.COL_C_W, Z1 - Z0, c.SHELF_DEPTH),
    "A3+A4 (coluna A, em cima)": (c.COL_A_W, Z1 - Z0, c.SHELF_DEPTH),
}


def geometria(w, h, d, t):
    wi, hi, di = w - 2 * t, h - 2 * t, d - 2 * t
    a_in = 2 * (wi * hi + wi * di + hi * di) / 1e6
    a_out = 2 * (w * h + w * d + h * d) / 1e6
    folga = 2 * (FOLGA_BANDEJA + PAREDE_BANDEJA)
    bandeja = (wi - folga, hi - folga, di - PROF_FRIO - folga)   # medidas internas da bandeja
    vol = max(bandeja[0], 0) * max(bandeja[1], 0) * max(bandeja[2], 0) / 1e6
    return dict(wi=wi, hi=hi, di=di, a_med=math.sqrt(a_in * a_out), bandeja=bandeja, vol_l=vol)


def ua(g, t):
    r = 1 / H_IN + (t / 1000) / K_XPS + 0.003 / K_MDF + 1 / H_OUT
    return PONTES * g["a_med"] / r


def carga(g, t, t_in, t_amb, aberturas_h=6):
    vol_m3 = g["wi"] * g["hi"] * g["di"] / 1e9
    sens = vol_m3 * 1.2 * 1005 * (t_amb - t_in)
    lat = vol_m3 * max(0.0, 0.0180 - 0.0068) * 1000 * 2450   # ar a 32 °C/60% condensa a 5 °C
    return ua(g, t) * (t_amb - t_in) + aberturas_h * (sens + lat) / 3600 + 1.0 + 1.0


def modulo(tc, th):
    i = (V - S * (th - tc)) / R_MOD
    qc = S * (tc + K0) * i - 0.5 * i * i * R_MOD - K_MOD * (th - tc)
    return i, qc, qc + V * i


def r_espacador(t):
    return (t / 1000) / (K_AL * LADO_ESPACADOR ** 2) + R_PASTA


def equilibrio(g, t, t_amb, n=1):
    """Menor temperatura interna sustentável com n Peltier 100% ligadas,
    cada uma com seu cooler quente e seu dissipador frio."""
    r_frio = R_FRIO + r_espacador(t) + R_PASTA
    t_ar_quente = t_amb + 2.0      # ar do vão de trás ventilado
    lo, hi = -30.0, t_amb
    for _ in range(60):
        t_in = (lo + hi) / 2
        tc, th = t_in - 10, t_amb + 15
        for _ in range(300):
            i, qc, qh = modulo(tc, th)
            tc_n = t_in - max(qc, 0) * r_frio
            th_n = t_ar_quente + qh * (R_QUENTE + R_PASTA)
            tc, th = 0.7 * tc + 0.3 * tc_n, 0.7 * th + 0.3 * th_n
        if n * qc >= carga(g, t, t_in, t_amb):
            hi = t_in
        else:
            lo = t_in
    i, qc, qh = modulo(tc, th)
    return dict(t_in=hi, i=n * i, qc=n * qc, qh=n * qh, th=th, tc=tc)


def main():
    print(f"Peltier TEC1-12703: S={S*1000:.1f} mV/K R={R_MOD:.2f} Ω K={K_MOD:.3f} W/K")
    print(f"Lado quente {R_QUENTE} K/W [est], lado frio {R_FRIO} K/W [est] + espaçador\n")
    print(f"{'baia':28s} {'XPS':>4} | {'bandeja (L x A x P) mm':>24} | {'vol':>5} | "
          f"{'25°C':>6} {'28°C':>6} {'32°C':>6} | {'carga@5°C,25°C':>14}")
    for n in (1, 2):
      print(f"--- {n} pastilha(s) ---")
      for nome, (w, h, d) in BAIAS.items():
        for t in (25.0, 40.0, 50.0):
            g = geometria(w, h, d, t)
            temps = [equilibrio(g, t, a, n)["t_in"] for a in (25.0, 28.0, 32.0)]
            b = g["bandeja"]
            print(f"{nome:28s} {t:4.0f} | {b[0]:6.0f} x {b[1]:5.0f} x {b[2]:5.0f}     | {g['vol_l']:4.1f}L | "
                  + " ".join(f"{x:6.1f}" for x in temps) + f" | {carga(g, t, 5, 25):11.1f} W")
    e = equilibrio(geometria(*BAIAS["A3+A4 (coluna A, em cima)"], 40.0), 40.0, 32.0, 2)
    print(f"\nA3+A4, 2 pastilhas, 40 mm, a 32 °C: I={e['i']:.2f} A, Qc={e['qc']:.1f} W, Qh={e['qh']:.1f} W, "
          f"Th={e['th']:.0f} °C, Tc={e['tc']:.0f} °C")


if __name__ == "__main__":
    main()
