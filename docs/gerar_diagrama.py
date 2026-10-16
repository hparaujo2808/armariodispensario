"""Gera docs/diagrama-ligacoes.svg (esquema de ligações do armário, no estilo das apostilas de Sistemas Embarcados).

  python docs/gerar_diagrama.py

Coordenadas em px. Pinos do Mega à esquerda, componentes à direita, 12 V em vermelho, GND comum.
"""
from pathlib import Path

W, H = 1500, 1140
FONTE = "Archivo, Helvetica, Arial, sans-serif"
MONO = "'IBM Plex Mono', Consolas, monospace"
C = {
    "v12": "#d0312d", "v5": "#2e8b57", "gnd": "#1e1e1e", "rele": "#8e5cc7", "lcd": "#2f7fd1", "lcd2": "#59a8f0",
    "lin": "#e8892a", "col": "#b8641a", "reed": "#d4b106", "buz": "#139aa0", "ac": "#7d868c",
}
el = []


def add(s):
    el.append(s)


def texto(x, y, t, tam=13, cor="#1f2a26", anc="start", peso=400, fam=FONTE, rot=None):
    r = f' transform="rotate({rot} {x} {y})"' if rot else ""
    add(f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{tam}" font-weight="{peso}" fill="{cor}" text-anchor="{anc}"{r}>{t}</text>')


def fio(pts, cor, w=3):
    p = " ".join(f"{x},{y}" for x, y in pts)
    add(f'<polyline points="{p}" fill="none" stroke="{cor}" stroke-width="{w}" stroke-linejoin="round" stroke-linecap="round"/>')


def ponto(x, y, cor="#1e1e1e"):
    add(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{cor}"/>')


def pino(x, y):
    add(f'<rect x="{x - 5}" y="{y - 5}" width="10" height="10" fill="#141414"/>')


def terra(x, y):
    add(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + 10}" stroke="#1e1e1e" stroke-width="2.5"/>')
    for i, w in enumerate((18, 12, 6)):
        add(f'<line x1="{x - w / 2}" y1="{y + 10 + i * 4}" x2="{x + w / 2}" y2="{y + 10 + i * 4}" stroke="#1e1e1e" stroke-width="2.5"/>')


def caixa(x, y, w, h, cor, rx=6, borda="none"):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{cor}" stroke="{borda}" stroke-width="1.5"/>')


add(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
texto(40, 34, "Ligações do Armário Dispensador", 22, peso=700)
texto(40, 52, "Arduino Mega 2560 · porta com LCD e teclado · trava e Peltier por relé · posição dos pinos simplificada", 12.5, "#5b6862")

# ---------------- Arduino Mega ----------------
AX, AY, AW, AH = 40, 80, 210, 1040
caixa(AX, AY, AW, AH, "#0b8a8a", 12)
texto(AX + AW / 2, AY + 22, "posição dos pinos simplificada", 11, "#d8f3f1", "middle")
texto(AX + 70, AY + AH / 2, "ARDUINO MEGA 2560", 30, "#ffffff", "middle", 800, rot=-90)
P = {"5V": 110, "GND": 140, "Vin": 210, "D7": 310, "D8": 380, "D9": 460, "D10": 540, "D20 SDA": 660, "D21 SCL": 700}
TECL = ["D22", "D24", "D26", "D28", "D30", "D32", "D34", "D36"]
for i, n in enumerate(TECL):
    P[n] = 806 + i * 36
for n, y in P.items():
    pino(AX + AW, y)
    texto(AX + AW - 14, y + 5, n, 15, "#ffffff", "end", 700)
PX = AX + AW + 5

# ---------------- fonte, fusível e barramento de 12 V ----------------
caixa(1170, 70, 230, 70, "#aab2b7", 4, "#7d868c")
texto(1285, 101, "FONTE 12 V 20 A", 15, "#1f2a26", "middle", 700)
texto(1285, 121, "chaveada (colmeia)", 11.5, "#3d4844", "middle")
pino(1220, 140); texto(1210, 158, "+12V", 11, "#d0312d", "end", 700)
pino(1360, 140); texto(1370, 158, "GND", 11, "#1e1e1e", "start", 700)
fio([(1400, 105), (1470, 105)], C["ac"], 4)
texto(1470, 96, "tomada", 11, "#5b6862", "end")
fio([(1220, 145), (1220, 210)], C["v12"], 4)
caixa(1211, 160, 18, 34, "#ffffff", 3, "#1e1e1e")
texto(1200, 182, "fusível 15 A", 11.5, "#1f2a26", "end")
fio([(PX, 210), (1220, 210)], C["v12"], 4)
texto(560, 202, "12 V", 12, "#d0312d", "middle", 700)
ponto(1000, 210, C["v12"]); ponto(1050, 210, C["v12"])

# trilho de GND da fonte
fio([(1360, 145), (1360, 170), (1440, 170), (1440, 568)], C["gnd"], 4)
texto(1462, 380, "GND da fonte (comum)", 11.5, "#5b6862", "middle", rot=90)

# Mega GND
fio([(PX, 140), (285, 140)], C["gnd"])
terra(285, 140)

# ---------------- buzzer ----------------
fio([(PX, 310), (747, 310)], C["buz"])
add('<circle cx="765" cy="310" r="18" fill="#222426"/><circle cx="765" cy="310" r="5" fill="#55595d"/>')
texto(742, 296, "+", 14, peso=700, anc="middle"); texto(790, 296, "-", 14, peso=700, anc="middle")
fio([(783, 310), (830, 310)], C["gnd"]); terra(830, 310)
texto(765, 280, "buzzer ativo (na porta)", 12, anc="middle", peso=600)

# ---------------- LM2596 ----------------
fio([(1050, 210), (1050, 250)], C["v12"], 3)
caixa(1030, 250, 110, 50, "#1f4fa8", 4)
texto(1085, 271, "LM2596", 13, "#ffffff", "middle", 700)
texto(1085, 289, "12 V → 5 V", 11, "#d6e2ff", "middle")
fio([(1140, 285), (1165, 285)], C["gnd"]); terra(1165, 285)
fio([(1120, 300), (1120, 318), (940, 318), (940, 332)], C["v5"])

# ---------------- módulo de relés ----------------
RX, RY, RW, RH = 700, 332, 260, 238
caixa(RX, RY, RW, RH, "#1f4fa8", 6)
pino(940, RY); texto(940, RY + 16, "VCC", 10.5, "#d6e2ff", "middle")
pino(930, RY + RH); texto(918, RY + RH - 8, "GND", 10.5, "#d6e2ff", "end")
fio([(930, RY + RH + 5), (930, RY + RH + 14)], C["gnd"]); terra(930, RY + RH + 14)
rotulos = [("D8", "IN1", "R1 · trava"), ("D9", "IN2", "R2 · Peltier C1"), ("D10", "IN3", "R3 · Peltier C2")]
for pin, inn, nome in rotulos:
    y = P[pin]
    fio([(PX, y), (RX, y)], C["rele"])
    pino(RX, y)
    texto(RX + 12, y + 4, inn, 11, "#d6e2ff", peso=700)
    caixa(RX + 60, y - 22, 120, 44, "#163c82", 4)
    texto(RX + 120, y + 4, nome, 11.5, "#ffffff", "middle", 600)
    pino(RX + RW, y - 12); texto(RX + RW - 10, y - 8, "COM", 10, "#d6e2ff", "end")
    pino(RX + RW, y + 12); texto(RX + RW - 10, y + 16, "NA", 10, "#d6e2ff", "end")
    fio([(RX + RW + 5, y - 12), (1000, y - 12)], C["v12"])
    ponto(1000, y - 12, C["v12"])
texto(RX + 12, RY + 16, "MÓDULO DE RELÉS · liga com LOW", 11.5, "#ffffff", peso=700)
fio([(1000, 210), (1000, P["D10"] - 12)], C["v12"], 3)

# cargas: trava (com diodo), Peltier C1 e C2 (sem cooler, só dissipador)
def carga(y, nome, sub, escura):
    fio([(RX + RW + 5, y + 12), (1080, y + 12)], "#a3221d")
    caixa(1080, y - 6, 160, 36, "#3b4247" if escura else "#eef2f5", 4, "#1e1e1e")
    texto(1160, y + 9, nome, 12, "#ffffff" if escura else "#1f2a26", "middle", 700)
    texto(1160, y + 23, sub, 10, "#c9d0d4" if escura else "#5b6862", "middle")
    fio([(1240, y + 12), (1440, y + 12)], C["gnd"])
    ponto(1440, y + 12)


carga(P["D8"], "trava solenoide", "12 V · 0,5 a 1 A", True)
carga(P["D9"], "Peltier C1", "12 V · ~6 A · 1,5 mm²", False)
carga(P["D10"], "Peltier C2", "12 V · ~6 A · 1,5 mm²", False)
# diodo de proteção na trava (faixa/catodo no lado +)
y = P["D8"] + 12
fio([(1060, y), (1060, y - 46), (1132, y - 46)], "#5b6862", 2.5)
add(f'<polygon points="1168,{y - 56} 1168,{y - 36} 1138,{y - 46}" fill="#1e1e1e"/>')
add(f'<line x1="1136" y1="{y - 57}" x2="1136" y2="{y - 35}" stroke="#1e1e1e" stroke-width="3"/>')
fio([(1168, y - 46), (1258, y - 46), (1258, y)], "#5b6862", 2.5)
ponto(1060, y, "#5b6862"); ponto(1258, y, "#5b6862")
texto(1152, y - 64, "diodo 1N4007 (faixa no +)", 11, anc="middle", peso=600)

# ---------------- LCD 16x2 I2C ----------------
fio([(PX, 110), (300, 110), (300, 636), (700, 636)], C["v5"])
fio([(PX, 660), (700, 660)], C["lcd"])
fio([(PX, 700), (700, 700)], C["lcd2"])
caixa(700, 622, 260, 116, "#1e5a2f", 6)
caixa(748, 642, 196, 70, "#9fc23a", 3)
texto(756, 670, "Digite a senha", 16, "#1f2a12", fam=MONO, peso=500)
texto(756, 698, "Senha: ____", 16, "#1f2a12", fam=MONO, peso=500)
for n, yy in (("VCC", 636), ("SDA", 660), ("SCL", 700)):
    pino(700, yy); texto(711, yy + 4, n, 9.5, "#cfe9d6", peso=700)
pino(960, 680); fio([(965, 680), (990, 680)], C["gnd"]); terra(990, 680)
texto(830, 614, "LCD 16x2 com I2C (na porta)", 12, anc="middle", peso=600)

# ---------------- teclado 4x4 ----------------
KX, KY = 700, 788
caixa(KX, KY, 280, 302, "#1c1d1f", 8)
texto(KX + 140, KY - 10, "teclado 4x4 de membrana (na porta)", 12, anc="middle", peso=600)
nomes = ["L1", "L2", "L3", "L4", "C1", "C2", "C3", "C4"]
for i, n in enumerate(TECL):
    yy = P[n]
    fio([(PX, yy), (KX, yy)], C["lin"] if i < 4 else C["col"])
    pino(KX, yy)
    texto(KX + 12, yy + 4, nomes[i], 10, "#e7e7e2", peso=700)
TEC = ["1", "2", "3", "A", "4", "5", "6", "B", "7", "8", "9", "C", "*", "0", "#", "D"]
for i, k in enumerate(TEC):
    cx, cy = KX + 60 + (i % 4) * 52, KY + 22 + (i // 4) * 68
    caixa(cx, cy, 44, 56, "#b8352b" if k in "ABCD" else "#34373b", 5)
    texto(cx + 22, cy + 35, k, 18, "#f2f2ee", "middle", 700)

# ---------------- legenda ----------------
LX, LY = 1050, 660
texto(LX, LY, "Legenda", 14, peso=700)
leg = [
    (C["v12"], "12 V (fonte, Vin do Mega, COM dos relés)"),
    ("#a3221d", "12 V chaveado pelo relé (vai para a carga)"),
    (C["v5"], "5 V"),
    (C["gnd"], "GND · o símbolo de terra é o mesmo ponto em tudo"),
    (C["rele"], "controle dos relés (D8, D9, D10)"),
    (C["lcd"], "LCD I2C (SDA e SCL)"),
    (C["lin"], "teclado: linhas"),
    (C["col"], "teclado: colunas"),
    (C["buz"], "buzzer"),
]
for i, (cor, t) in enumerate(leg):
    yy = LY + 24 + i * 24
    fio([(LX, yy - 4), (LX + 34, yy - 4)], cor, 4)
    texto(LX + 46, yy, t, 12)
notas = [
    "GND da fonte, do Mega, do LM2596 e dos relés ligados juntos.",
    "Fios de 12 V das Peltier em 1,5 mm²; sinais em cabo de rede.",
    "Ajustar o LM2596 para 5,0 V com o multímetro antes de ligar os relés.",
]
for i, t in enumerate(notas):
    texto(LX, LY + 24 + len(leg) * 24 + 16 + i * 20, t, 11.5, "#5b6862")

svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Diagrama de ligações do Armário Dispensador">\n' + "\n".join(el) + "\n</svg>\n"
saida = Path(__file__).with_name("diagrama-ligacoes.svg")
saida.write_text(svg, encoding="utf-8")
print("ok", saida, len(svg), "bytes")
