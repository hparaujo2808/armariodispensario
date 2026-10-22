"""Confere o kit de frio que está no README/LISTA-DE-COMPRAS de 21/10:
TEC1-12703 a 12 V, dissipador de alumínio 65 x 46 x 24 mm SEM ventoinha,
pastilha tampando um furo de 38 mm no fundo falso, sem nada do lado frio.

    python calculos/termico_atual.py

Modelo em regime permanente (o mesmo usado no cálculo térmico do legado):
    I  = (V - S (Th - Tc)) / R
    Qc = S Tc I - I² R / 2 - K (Th - Tc)     calor tirado do lado frio
    Qh = Qc + V I                           calor jogado no lado quente
    Th = T_vao + Qh (R_quente + R_pasta)
    Tc = T_gaveta - Qc (R_frio + R_pasta)

Origem dos números:
[ds] Módulo 12703: Beijing Huimao TES1-12703 (Th = 25 °C): Imax 3 A,
     Umax 15,2 V, Qmax 28,3 W, ΔTmax 67 K, ACR 3,88 Ω, temperatura máxima
     de operação 125 °C, solda 138 °C.
     https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/38/PELTIER-HUIMAO-TES1_2D00_12703T125.pdf
     A pastilha anunciada (Mixtou 40 x 40, "15,5 V 27 W") não publica datasheet;
     os números do Huimao são os mais próximos achados.
[calc] S, R e K efetivos pelo método padrão a partir de Imax, Umax, ΔTmax.
[calc] Dissipador quente em convecção natural: resistência volumétrica de
     500 a 800 cm³·K/W (Simons, "Estimating parallel plate-fin heat sink
     thermal resistance", Electronics Cooling, fev/2003). Volume 6,5 x 4,6 x
     2,4 = 71,8 cm³ -> 7 a 11 K/W. Também rodamos 3 K/W como caso otimista.
     [medir] procedimento em docs/AUDITORIA.md.
[calc] Lado frio sem dissipador: só a face de cerâmica exposta pelo furo de
     38 mm (11,3 cm²), convecção natural + radiação h ≈ 10 W/m²K -> ~88 K/W.
[est]  Vão de trás fechado: UA ≈ 5 W/K para fora (paredes de MDF 3 mm,
     ~1,5 m² de área externa, U ≈ 2,3 W/m²K, mais a troca pelo fundo falso).
"""
from __future__ import annotations

K0 = 273.15

# ---- módulo [ds] Huimao TES1-12703, Th = 25 °C --------------------------
TH_REF = 25 + K0
UMAX, IMAX, DTMAX = 15.2, 3.0, 67.0
S = UMAX / TH_REF                                           # V/K
R_MOD = UMAX * (TH_REF - DTMAX) / (IMAX * TH_REF)           # Ω
K_MOD = IMAX * UMAX * (TH_REF - DTMAX) / (2 * TH_REF * DTMAX)  # W/K
V = 12.0
R_PASTA = 0.10          # K/W por face, pasta térmica em 40 x 40 mm [est]

# ---- lado frio sem dissipador -------------------------------------------
A_FRIO = 3.14159 * 0.019 ** 2      # m², face exposta pelo furo de 38 mm
H_FRIO = 10.0                       # W/m²K, convecção natural + radiação
R_FRIO_NU = 1 / (H_FRIO * A_FRIO)   # ≈ 88 K/W

UA_VAO = 5.0      # W/K, vão de trás fechado [est]
UA_GAVETA = 2.5   # W/K, uma gaveta C de MDF 3 mm sem isolamento, com frestas [est]


def _modulo(tc, th):
    i = (V - S * (th - tc)) / R_MOD
    qc = S * (tc + K0) * i - 0.5 * i * i * R_MOD - K_MOD * (th - tc)
    return i, qc, qc + V * i


def _bissecao(f, lo, hi):
    for _ in range(100):
        meio = (lo + hi) / 2
        if f(lo) * f(meio) <= 0:
            hi = meio
        else:
            lo = meio
    return (lo + hi) / 2


def ponto(t_vao, t_gaveta, r_quente, r_frio):
    """Ponto de operação: acha Th e Tc que fecham os dois balanços."""
    def tc_de(th):
        return _bissecao(lambda tc: tc - (t_gaveta - _modulo(tc, th)[1] * (r_frio + R_PASTA)), -80.0, th)

    th = _bissecao(lambda th: th - (t_vao + _modulo(tc_de(th), th)[2] * (r_quente + R_PASTA)), t_vao, t_vao + 400)
    tc = tc_de(th)
    i, qc, qh = _modulo(tc, th)
    return dict(i=i, p=V * i, qc=qc, qh=qh, th=th, tc=tc)


def sistema(t_amb, r_quente, n_pastilhas=2, r_frio=R_FRIO_NU):
    """Resolve junto: o vão de trás esquenta com o calor das pastilhas e a
    gaveta troca calor com a sala e com a pastilha."""
    t_vao, t_gav = t_amb, t_amb
    for _ in range(300):
        p = ponto(t_vao, t_gav, r_quente, r_frio)
        t_vao = 0.8 * t_vao + 0.2 * (t_amb + n_pastilhas * p["qh"] / UA_VAO)
        t_gav = 0.8 * t_gav + 0.2 * (t_amb - p["qc"] / UA_GAVETA)
    return p, t_vao, t_gav


def main():
    print(f"Módulo [calc]: S = {S*1000:.1f} mV/K  R = {R_MOD:.2f} Ω  K = {K_MOD:.3f} W/K")
    i0 = V / R_MOD
    print(f"Partida a 12 V (ΔT = 0): I = {i0:.2f} A, P = {V*i0:.1f} W por pastilha\n")
    print(f"Lado frio sem dissipador: R = {R_FRIO_NU:.0f} K/W\n")
    print("Ambiente 25 °C, 2 pastilhas no mesmo vão de trás fechado")
    print(f"{'R dissip. quente':>17} | {'I (A)':>5} | {'P (W)':>5} | {'Th (°C)':>7} | {'Tc (°C)':>7} | "
          f"{'Qc (W)':>6} | {'vão (°C)':>8} | {'gaveta (°C)':>11}")
    for rq in (3.0, 7.0, 11.0):
        p, tv, tg = sistema(25.0, rq)
        aviso = "  <- passa de 125 °C (máx. do módulo)" if p["th"] > 125 else ""
        print(f"{rq:>13.0f} K/W | {p['i']:5.2f} | {p['p']:5.1f} | {p['th']:7.1f} | {p['tc']:7.1f} | "
              f"{p['qc']:6.2f} | {tv:8.1f} | {tg:11.2f}{aviso}")
    print("\nMesmo caso otimista (3 K/W), mas com dissipador e ventoinha do lado frio (~1 K/W):")
    p, tv, tg = sistema(25.0, 3.0, r_frio=1.0)
    print(f"  Qc = {p['qc']:.1f} W, Th = {p['th']:.0f} °C, Tc = {p['tc']:.0f} °C, gaveta sem isolamento = {tg:.1f} °C")


if __name__ == "__main__":
    main()
