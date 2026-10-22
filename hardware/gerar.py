"""Gera tudo o que sai de hardware/pinos.yaml e hardware/potencia.yaml.

    python hardware/gerar.py              grava os arquivos
    python hardware/gerar.py --verificar  só confere; sai com erro se algo divergir

Também confere os furos de hardware/furos.py.

Saídas:
    firmware/armario_dispensador/pinos.h
    docs/LIGACOES.md        (só os trechos entre <!-- gerado:... --> e <!-- /gerado:... -->)
    docs/diagrama-ligacoes.svg
    docs/diagrama-potencia.svg
"""
from __future__ import annotations

import os
import re
import sys
from html import escape

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import furos as FUROS  # noqa: E402

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PINOS_YAML = os.path.join(RAIZ, "hardware", "pinos.yaml")
POTENCIA_YAML = os.path.join(RAIZ, "hardware", "potencia.yaml")
PINOS_H = os.path.join(RAIZ, "firmware", "armario_dispensador", "pinos.h")
LIGACOES = os.path.join(RAIZ, "docs", "LIGACOES.md")
SVG_SINAIS = os.path.join(RAIZ, "docs", "diagrama-ligacoes.svg")
SVG_POTENCIA = os.path.join(RAIZ, "docs", "diagrama-potencia.svg")

# Recursos dos pinos do Mega 2560 [ds] docs.arduino.cc/hardware/mega-2560
MEGA_PWM = set(range(2, 14)) | {44, 45, 46}
MEGA_INTERRUPCAO = {2, 3, 18, 19, 20, 21}
MEGA_SERIAL1 = {18, 19}
MEGA_DIGITAIS = set(range(0, 54))
MEGA_ANALOGICOS = {f"A{i}" for i in range(16)}


def carregar():
    with open(PINOS_YAML, encoding="utf-8") as f:
        pinos = yaml.safe_load(f)
    with open(POTENCIA_YAML, encoding="utf-8") as f:
        potencia = yaml.safe_load(f)
    return pinos, potencia


# ---------------------------------------------------------------- validação --
def validar(pinos: dict, potencia: dict) -> list[str]:
    erros = []
    usados: dict = {}
    nomes = set()
    reservados = set(pinos["reservados"])
    for p in pinos["pinos"]:
        n, pino = p["nome"], p["pino"]
        if n in nomes:
            erros.append(f"nome repetido: {n}")
        nomes.add(n)
        if pino in usados:
            erros.append(f"pino {pino} usado por {usados[pino]} e {n}")
        usados[pino] = n
        if pino in reservados:
            erros.append(f"{n} usa o pino reservado {pino}: {pinos['reservados'][pino]}")
        if isinstance(pino, str):
            if pino not in MEGA_ANALOGICOS:
                erros.append(f"{n}: pino {pino} não existe no Mega")
            if p["modo"] != "analogico":
                erros.append(f"{n}: pino analógico com modo {p['modo']}")
        elif pino not in MEGA_DIGITAIS:
            erros.append(f"{n}: pino {pino} não existe no Mega")
        for req in p.get("exige", []):
            ok = {"pwm": MEGA_PWM, "interrupcao": MEGA_INTERRUPCAO, "serial1": MEGA_SERIAL1}[req]
            if pino not in ok:
                erros.append(f"{n}: precisa de {req}, mas o pino {pino} não tem")
        if p["modo"] in ("saida", "entrada_pullup", "entrada") and p.get("ativo") not in ("alto", "baixo"):
            erros.append(f"{n}: falta 'ativo' (alto/baixo)")
        if p["cabo"] not in pinos["cabos"]:
            erros.append(f"{n}: cabo {p['cabo']} não está em 'cabos'")

    cap = {float(k): v for k, v in potencia["capacidade_fio_a"].items()}
    fus = potencia["fusiveis"]
    ids = set()
    for t in potencia["trechos"]:
        if t["id"] in ids:
            erros.append(f"trecho repetido: {t['id']}")
        ids.add(t["id"])
        b = float(t["bitola_mm2"])
        if b == 0:
            continue
        if b not in cap:
            erros.append(f"{t['id']}: bitola {b} sem capacidade definida")
            continue
        if t["corrente_a"] > cap[b]:
            erros.append(f"{t['id']}: {t['corrente_a']} A em fio de {b} mm² (máx. {cap[b]} A)")
        prot = t["protegido_por"]
        if prot in fus and fus[prot]["corrente_a"] > cap[b] and not t.get("curto_ok"):
            erros.append(f"{t['id']}: fio de {b} mm² ({cap[b]} A) atrás do {prot} de {fus[prot]['corrente_a']} A")
        if not str(t.get("origem", "")).startswith("["):
            erros.append(f"{t['id']}: corrente sem origem [ds]/[calc]/[medir]")
    return erros


# ----------------------------------------------------------------- pinos.h --
def gerar_pinos_h(pinos: dict) -> str:
    linhas = [
        "// GERADO por hardware/gerar.py a partir de hardware/pinos.yaml. Não editar à mão.",
        "#pragma once",
        "#include <Arduino.h>",
        "",
    ]
    for p in pinos["pinos"]:
        valor = p["pino"] if isinstance(p["pino"], int) else p["pino"]
        linhas.append(f"// {p['liga_em']}")
        linhas.append(f"const uint8_t PINO_{p['nome']} = {valor};")
        if p.get("ativo"):
            nivel = "LOW" if p["ativo"] == "baixo" else "HIGH"
            linhas.append(f"const uint8_t ATIVO_{p['nome']} = {nivel};")
    linhas.append("")
    linhas.append("// Saídas em ordem de inicialização segura: nível inativo antes de pinMode(OUTPUT)")
    saidas = [p for p in pinos["pinos"] if p["modo"] == "saida"]
    linhas.append(f"const uint8_t SAIDAS[{len(saidas)}] = {{" + ", ".join(f"PINO_{p['nome']}" for p in saidas) + "};")
    linhas.append(f"const uint8_t SAIDAS_INATIVO[{len(saidas)}] = {{"
                  + ", ".join(("HIGH" if p["ativo"] == "baixo" else "LOW") for p in saidas) + "};")
    return "\n".join(linhas) + "\n"


# ------------------------------------------------------------ LIGACOES.md --
def _num(v):
    return f"{v:g}".replace(".", ",")


def bloco_pinos(pinos: dict) -> str:
    modos = {"saida": "saída", "entrada_pullup": "entrada com pull-up", "entrada": "entrada",
             "barramento": "1-Wire", "serial": "serial", "analogico": "analógica"}
    linhas = ["| Pino | Nome no firmware | Tipo | Liga em | Cabo | Observação |", "|---|---|---|---|---|---|"]
    for p in pinos["pinos"]:
        tipo = modos[p["modo"]] + (f", ativo em {p['ativo']}" if p.get("ativo") else "")
        cabo = pinos["cabos"][p["cabo"]]["tipo"]
        linhas.append(f"| {p['pino']} | `PINO_{p['nome']}` | {tipo} | {p['liga_em']} | {cabo} | {p.get('nota', '')} |")
    linhas += ["", "| Do Mega | Liga em | Cabo | Observação |", "|---|---|---|---|"]
    for a in pinos["alimentacao_mega"]:
        linhas.append(f"| {a['de']} | {a['liga_em']} | {a['cabo']} | {a.get('nota', '')} |")
    linhas += ["", "Pinos reservados: " + "; ".join(f"{k} ({v})" for k, v in pinos["reservados"].items()) + "."]
    return "\n".join(linhas)


def bloco_potencia(potencia: dict) -> str:
    cap = {float(k): v for k, v in potencia["capacidade_fio_a"].items()}
    linhas = ["| Trecho | De | Para | Fio | Corrente (pior caso) | Capacidade do fio | Protegido por | Observação |",
              "|---|---|---|---|---|---|---|---|"]
    for t in potencia["trechos"]:
        b = float(t["bitola_mm2"])
        fio = "do próprio componente" if b == 0 else f"{_num(b)} mm²"
        capac = "—" if b == 0 else f"{_num(cap[b])} A"
        obs = t.get("nota", "") or t.get("curto_ok", "")
        linhas.append(f"| `{t['id']}` | {t['de']} | {t['para']} | {fio} | {_num(t['corrente_a'])} A {t['origem']} | "
                      f"{capac} | {t['protegido_por']} | {obs} |")
    linhas += ["", "| Fusível | Corrente | Tipo | Onde |", "|---|---|---|---|"]
    for k, f in potencia["fusiveis"].items():
        extra = f", abre a {f['temperatura_c']} °C" if "temperatura_c" in f else ""
        linhas.append(f"| {k} | {f['corrente_a']} A{extra} | {f['tipo']} | {f['onde']}{('. ' + f['nota']) if f.get('nota') else ''} |")
    linhas += ["", "| Diodo | Tipo | Entre | Por quê |", "|---|---|---|---|"]
    for d in potencia["diodos"]:
        linhas.append(f"| {d['id']} | {d['tipo']} | {d['entre']} | {d['motivo']} |")
    linhas += ["", "| Ponto de emenda | O que é |", "|---|---|"]
    for k, v in potencia["nos"].items():
        linhas.append(f"| {k} | {v} |")
    return "\n".join(linhas)


def aplicar_blocos(texto: str, blocos: dict[str, str]) -> str:
    for nome, conteudo in blocos.items():
        padrao = re.compile(rf"(<!-- gerado:{nome} -->\n)(?:.*?\n)?(<!-- /gerado:{nome} -->)", re.S)
        if not padrao.search(texto):
            raise SystemExit(f"LIGACOES.md não tem os marcadores do bloco '{nome}'")
        texto = padrao.sub(lambda m: m.group(1) + conteudo + "\n" + m.group(2), texto)
    return texto


# ------------------------------------------------------------------- SVGs --
FONTE = "Helvetica, Arial, sans-serif"
CORES = {"porta_1": "#e8892a", "porta_2": "#2f7fd1", "porta_3": "#139aa0", "reed": "#b8960c",
         "sensores": "#7a4fc2", "jumper": "#5b6862", "medicao": "#d0312d"}


def _t(x, y, s, tam=12, cor="#1f2a26", anc="start", peso=400):
    return (f'<text x="{x}" y="{y}" font-family="{FONTE}" font-size="{tam}" font-weight="{peso}" '
            f'fill="{cor}" text-anchor="{anc}">{escape(str(s))}</text>')


def svg_sinais(pinos: dict) -> str:
    lista = pinos["pinos"]
    por_grupo: dict[str, list] = {}
    for p in lista:
        g = p.get("grupo") or ("reles" if p["nome"].startswith("RELE") else p["cabo"])
        por_grupo.setdefault(g, []).append(p)
    grupos = list(por_grupo.items())
    titulos = {"jumper": "Módulo de relés (caixa da eletrônica)", "reles": "Módulo de relés (caixa da eletrônica)",
               "porta_1": "Teclado 4x4 (porta) · cabo de rede 1", "porta_2": "LCD 16x2 (porta) · cabo de rede 2",
               "porta_3": "AS608 e buzzer (porta) · cabo de rede 3", "reed": "Reed MC-38 (batente da porta)",
               "sensores": "3 × DS18B20 (baia fria e coolers)", "medicao": "Divisor 4,7 kΩ / 2,2 kΩ do +12 V"}
    lin, topo, passo = [], 110, 26
    y = topo
    caixas = []
    for g, ps in grupos:
        y0 = y
        for p in ps:
            p["_y"] = y
            y += passo
        caixas.append((g, y0 - 32, y - passo + 14, ps))
        y += 40
    altura = y + 30
    W = 1180
    lin.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {altura}" width="{W}" height="{altura}">')
    lin.append(f'<rect width="{W}" height="{altura}" fill="#ffffff"/>')
    lin.append(_t(30, 34, "Ligações de sinal do Arduino Mega", 20, peso=700))
    lin.append(_t(30, 56, "Gerado de hardware/pinos.yaml por hardware/gerar.py. Potência em diagrama-potencia.svg.", 12, "#5b6862"))
    lin.append(f'<rect x="30" y="{topo - 30}" width="230" height="{y - topo + 10}" rx="10" fill="#0b8a8a"/>')
    lin.append(_t(145, topo - 10, "ARDUINO MEGA 2560", 13, "#ffffff", "middle", 700))
    for g, ya, yb, ps in caixas:
        cor = CORES.get(g, "#5b6862")
        lin.append(f'<rect x="560" y="{ya}" width="590" height="{yb - ya}" rx="6" fill="#f4f6f5" stroke="{cor}" stroke-width="2"/>')
        lin.append(_t(575, ya + 13, titulos.get(g, g), 11, cor, "start", 700))
        for p in ps:
            yy = p["_y"]
            lin.append(_t(240, yy + 4, f"{p['pino']}", 13, "#ffffff", "end", 700))
            lin.append(_t(185, yy + 4, p["nome"], 10, "#d8f3f1", "end"))
            lin.append(f'<line x1="260" y1="{yy}" x2="560" y2="{yy}" stroke="{cor}" stroke-width="2.5"/>')
            lin.append(f'<rect x="255" y="{yy - 4}" width="8" height="8" fill="#141414"/>')
            lin.append(_t(575, yy + 4, p["liga_em"], 11))
    lin.append("</svg>")
    return "\n".join(lin) + "\n"


def svg_potencia(potencia: dict) -> tuple[str, set[str]]:
    """Diagrama em escada: trilho +12 V à esquerda, GND à direita.
    Devolve o SVG e o conjunto de trechos desenhados (o teste confere com o YAML)."""
    t = {x["id"]: x for x in potencia["trechos"]}
    cap = {float(k): v for k, v in potencia["capacidade_fio_a"].items()}
    desenhados: set[str] = set()
    el = []
    W, H = 1500, 1010
    X12, XG = 300, 1420

    def rot(tid):
        x = t[tid]
        b = float(x["bitola_mm2"])
        fio = "fio do componente" if b == 0 else f"{_num(b)} mm²"
        return f"{fio} · {_num(x['corrente_a'])} A"

    def fio(tid, x1, y1, x2, y2, cor="#d0312d", rotulo=True, desce_antes=False):
        """Fio em L. desce_antes=True faz primeiro o trecho vertical (em x1)."""
        desenhados.add(tid)
        meio = f"{x1},{y2}" if desce_antes else f"{x2},{y1}"
        el.append(f'<polyline points="{x1},{y1} {meio} {x2},{y2}" fill="none" stroke="{cor}" stroke-width="3"/>')
        if rotulo:
            yr = y2 if desce_antes else y1
            el.append(_t((x1 + x2) / 2, yr - 6, rot(tid), 10, "#5b6862", "middle"))

    def comp(x, y, w, nome, sub="", cor="#e9ece6", borda="#7d868c"):
        el.append(f'<rect x="{x}" y="{y - 18}" width="{w}" height="36" rx="5" fill="{cor}" stroke="{borda}" stroke-width="1.5"/>')
        el.append(_t(x + w / 2, y - 2 if sub else y + 4, nome, 11, anc="middle", peso=700))
        if sub:
            el.append(_t(x + w / 2, y + 12, sub, 9, "#3d4844", "middle"))

    el.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')
    el.append(_t(30, 34, "Potência: 12 V, 5 V dos relés e GND", 20, peso=700))
    el.append(_t(30, 56, "Gerado de hardware/potencia.yaml por hardware/gerar.py. Vermelho = +12 V, laranja = +12 V comutado, "
                 "verde = 5 V, preto = GND.", 12, "#5b6862"))

    # entrada
    comp(30, 110, 100, "Tomada", "127/220 V")
    fio("tomada", 130, 110, 170, 110, "#7d868c", rotulo=False)
    comp(170, 110, 110, "Fonte 12 V 10 A", "V+ / V−")
    fio("fonte_f1", 280, 100, 300, 100, rotulo=False)
    comp(300, 100, 70, "F1 10 A")
    fio("f1_b12", 370, 100, 400, 140, rotulo=False)
    el.append(_t(410, 135, "B12  +12 V  " + rot("f1_b12"), 11, "#d0312d", peso=700))
    el.append(f'<line x1="{X12}" y1="140" x2="{X12}" y2="900" stroke="#d0312d" stroke-width="5"/>')
    el.append(f'<line x1="400" y1="140" x2="{X12}" y2="140" stroke="#d0312d" stroke-width="5"/>')
    el.append(f'<line x1="{XG}" y1="140" x2="{XG}" y2="960" stroke="#1e1e1e" stroke-width="5"/>')
    el.append(_t(XG, 130, "GND", 12, "#1e1e1e", "middle", 700))
    fio("gnd_fonte", XG, 960, 225, 960, "#1e1e1e")
    el.append(f'<line x1="225" y1="960" x2="225" y2="128" stroke="#1e1e1e" stroke-width="2" stroke-dasharray="6 4"/>')
    el.append(_t(235, 950, "parafuso V− 3 da fonte", 10, "#1e1e1e"))

    # ramos das Peltier
    for n, y in ((1, 200), (2, 400)):
        fio(f"b12_rele{n + 1}", X12, y, 420, y)
        comp(420, y, 130, f"Relé {n + 1}", f"COM → NA (pino {8 + n})", "#dfe6f7", "#1f4fa8")
        fio(f"rele{n + 1}_p{n}", 550, y, 640, y, "#e07020")
        el.append(f'<circle cx="640" cy="{y}" r="7" fill="#e07020"/>')
        el.append(_t(640, y - 14, f"P{n}", 11, "#e07020", "middle", 700))
        fio(f"p{n}_tf{n}", 640, y, 760, y, "#e07020")
        comp(760, y, 120, f"TF{n} 85 °C", "no cooler", "#fbe9d0", "#e07020")
        fio(f"tf{n}_peltier{n}", 880, y, 960, y, "#e07020", rotulo=False)
        el.append(_t(920, y + 30, "fio da pastilha", 9, "#5b6862", "middle"))
        comp(960, y, 170, f"Peltier {n} TEC1-12703", "3,93 Ω [calc]", "#f2f2f2")
        fio(f"peltier{n}_gnd", 1130, y, XG, y, "#1e1e1e")
        el.append(_t(1275, y + 16, f"parafuso V− {n} da fonte", 9, "#1e1e1e", "middle"))
        fio(f"p{n}_vf{n}", 640, y, 960, y + 60, "#e07020", desce_antes=True)
        comp(960, y + 60, 170, f"Ventoinha fria {n}", "60 mm 12 V 0,18 A")
        fio(f"vf{n}_gnd", 1130, y + 60, XG, y + 60, "#1e1e1e")
        el.append(f'<polyline points="640,{y} 640,{y + 120} 960,{y + 120}" fill="none" stroke="#7a4fc2" stroke-width="2"/>')
        comp(960, y + 120, 170, f"D{n} 1N4007", "faixa em P" + str(n), "#efe7fb", "#7a4fc2")
        el.append(f'<line x1="1130" y1="{y + 120}" x2="{XG}" y2="{y + 120}" stroke="#1e1e1e" stroke-width="2"/>')

    # ramo fino
    y = 620
    fio("b12_f2", X12, y, 400, y)
    comp(400, y, 80, "F2 2 A")
    fio("f2_t12", 480, y, 560, y)
    el.append(f'<line x1="560" y1="{y}" x2="560" y2="830" stroke="#d0312d" stroke-width="4"/>')
    el.append(_t(570, y - 22, "T12", 11, "#d0312d", peso=700))
    fio("t12_vq1", 560, y, 960, y)
    comp(960, y, 170, "Ventoinha cooler 1", "120 mm 0,26 A, sempre ligada")
    fio("t12_vq2", 560, y, 960, y + 50, desce_antes=True)
    comp(960, y + 50, 170, "Ventoinha cooler 2", "120 mm 0,26 A, sempre ligada")
    fio("vq_gnd", 1130, y + 25, XG, y + 25, "#1e1e1e")
    el.append(f'<line x1="1130" y1="{y}" x2="1150" y2="{y + 25}" stroke="#1e1e1e" stroke-width="2"/>'
              f'<line x1="1130" y1="{y + 50}" x2="1150" y2="{y + 25}" stroke="#1e1e1e" stroke-width="2"/>')
    y = 740
    fio("t12_rele1", 560, y, 640, y)
    comp(640, y, 130, "Relé 1", "COM → NA (pino 8)", "#dfe6f7", "#1f4fa8")
    fio("rele1_trava", 770, y, 960, y, "#e07020")
    comp(960, y, 170, "Trava FE-91 12 V", "0,5 A [ds] · D3 nos terminais")
    fio("trava_gnd", 1130, y, XG, y, "#1e1e1e")
    y = 830
    fio("t12_lm", 560, y, 640, y)
    comp(640, y, 130, "LM2596", "ajustado em 5,0 V", "#e1f3e8", "#2e8b57")
    fio("lm_gnd", 705, y + 18, 705, 960, "#1e1e1e", rotulo=False)
    fio("lm_reles", 770, y, 960, y, "#2e8b57")
    comp(960, y, 170, "Módulo de relés", "VCC 5 V · IN1–IN4 do Mega", "#dfe6f7", "#1f4fa8")
    fio("lm_reles_gnd", 1045, y + 18, 1045, 960, "#1e1e1e", rotulo=False)
    fio("mega_gnd", 1130, y + 10, 1260, y + 10, "#1e1e1e", rotulo=False)
    comp(1180, y + 50, 160, "GND do Mega", "ponto único de terra")
    el.append(f'<line x1="1260" y1="{y + 10}" x2="1260" y2="{y + 32}" stroke="#1e1e1e" stroke-width="2"/>')
    fio("divisor_12v", X12, 900, 400, 900, rotulo=False)
    comp(400, 900, 140, "Divisor 4,7k / 2,2k", "→ A0 do Mega")

    el.insert(0, f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    el.append("</svg>")
    return "\n".join(el) + "\n", desenhados


# ---------------------------------------------------------------- principal --
def saidas() -> dict[str, str]:
    pinos, potencia = carregar()
    erros = validar(pinos, potencia) + FUROS.conferir()
    if erros:
        raise SystemExit("Erros nos YAML:\n  " + "\n  ".join(erros))
    svg_p, desenhados = svg_potencia(potencia)
    faltando = {t["id"] for t in potencia["trechos"]} ^ desenhados
    if faltando:
        raise SystemExit(f"Diagrama de potência e potencia.yaml divergem: {sorted(faltando)}")
    with open(LIGACOES, encoding="utf-8") as f:
        lig = f.read()
    lig = aplicar_blocos(lig, {"pinos": bloco_pinos(pinos), "potencia": bloco_potencia(potencia),
                                "furos": FUROS.bloco_markdown()})
    return {PINOS_H: gerar_pinos_h(pinos), LIGACOES: lig, SVG_SINAIS: svg_sinais(pinos), SVG_POTENCIA: svg_p}


def main():
    verificar = "--verificar" in sys.argv
    divergentes = []
    for caminho, conteudo in saidas().items():
        atual = open(caminho, encoding="utf-8").read() if os.path.exists(caminho) else None
        if atual == conteudo:
            continue
        if verificar:
            divergentes.append(os.path.relpath(caminho, RAIZ))
        else:
            os.makedirs(os.path.dirname(caminho), exist_ok=True)
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(conteudo)
            print("gerado:", os.path.relpath(caminho, RAIZ))
    if divergentes:
        raise SystemExit("Desatualizado em relação aos YAML (rode python hardware/gerar.py): " + ", ".join(divergentes))
    print("OK")


if __name__ == "__main__":
    main()
