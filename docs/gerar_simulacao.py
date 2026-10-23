"""Gera docs/simulacao.html: o armário em 3D com as medidas de verdade.

    python docs/gerar_simulacao.py              grava
    python docs/gerar_simulacao.py --verificar  só confere (sai com erro se estiver desatualizado)

Todas as peças saem de armario/gerador/config.py (V2.3 + porta v2.4) e de
hardware/layout.py. A página só desenha e simula o comportamento da porta
(o mesmo fluxo do firmware, de forma simplificada). Ela não é fonte de medida.
"""
from __future__ import annotations

import json
import os
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "armario", "gerador"))
sys.path.insert(0, os.path.join(RAIZ, "hardware"))
import config as c  # noqa: E402
import layout as L  # noqa: E402
import porta as P  # noqa: E402

SAIDA = os.path.join(RAIZ, "docs", "simulacao.html")
T = c.MATERIAL_T


def caixa(nome, x0, x1, y0, y1, z0, z1, cor, detalhe="", grupo="armario", **extra):
    d = {"nome": nome, "detalhe": detalhe, "grupo": grupo, "cor": cor,
         "x": [min(x0, x1), max(x0, x1)], "y": [min(y0, y1), max(y0, y1)], "z": [min(z0, z1), max(z0, z1)]}
    d.update(extra)
    return d


def pecas():
    W, D, H = c.EXT_W, c.EXT_D, c.EXT_H
    mdf, mdf2, metal, preto = "#c9a26b", "#b98d55", "#9aa3a8", "#2f3438"
    p = [
        caixa("Base", T, W - T, 0, D, 0, T, mdf2, "MDF 3 mm"),
        caixa("Tampo", T, W - T, 0, D, H - T, H, mdf2, "MDF 3 mm"),
        caixa("Lateral esquerda", 0, T, 0, D, 0, H, mdf, "furos das Peltier e dos berços feitos por fora, com gabarito"),
        caixa("Lateral direita", W - T, W, 0, D, 0, H, mdf, "trava e reed por dentro; furo da câmera interna"),
        caixa("Fundo falso", T, W - T, c.FALSE_BACK_Y0, c.FALSE_BACK_Y1, T, H - T, mdf2, "sem furos: o vão de trás não é usado"),
        caixa("Traseiro", T, W - T, c.BACK_Y0, c.BACK_Y1, T, H - T, mdf2, "sem furos"),
    ]
    for nome, (z0, z1) in (("Teto do gaveteiro", c.TETO_GAV_Z), ("Prateleira de baixo", c.PRAT2_Z),
                           ("Prateleira do meio", c.PRAT1_Z), ("Piso do compartimento de cima", c.PCAM_Z)):
        p.append(caixa(nome, T, W - T, 0, c.SHELF_DEPTH, z0, z1, mdf))
    for nome, (x0, x1) in (("Divisória A/B", c.X_DIV_AB), ("Divisória B/C", c.X_DIV_BC), ("Divisória do dispensador", c.X_DIV_DISP)):
        p.append(caixa(nome, x0 + T, x1 + T, 0, c.SHELF_DEPTH, c.GAVETEIRO_Z[0], c.GAVETEIRO_Z[1], mdf))
    # gavetas: 1 = a de baixo (V2.3). A3 e A4 viraram a baia fria
    yf = c.FRENTE_GAVETA_Y
    cols = {"A": (c.X_COL_A, c.DRAWER_A_FRONT_H), "B": (c.X_COL_B, c.DRAWER_BC_FRONT_H), "C": (c.X_COL_C, c.DRAWER_BC_FRONT_H)}
    zs = {"A1": 53.4 - 48, "A2": 151.8 - 48, "B1": 5.0, "B2": 202.0, "C1": 5.0, "C2": 202.0}
    for g, z0 in zs.items():
        (x0, x1), h = cols[g[0]]
        p.append(caixa(f"Gaveta {g}", x0 + T + c.DRAWER_SIDE_CLEARANCE, x1 + T - c.DRAWER_SIDE_CLEARANCE, yf, yf + 463,
                       z0, z0 + h, "#e2c08d", "clique para puxar; puxador embutido (nada saliente)", "gaveta", gaveta=g))
    bx0, bx1 = L.BAIA_X
    bz0, bz1 = L.BAIA_Z
    p.append(caixa("Baia fria (piso)", bx0, bx1, 0, c.SHELF_DEPTH, bz0, bz0 + T, mdf2, "piso a 205 mm, apoiado em taquinhos"))
    p.append(caixa("Baia fria — isopor 50 mm", bx0, bx1, T, c.SHELF_DEPTH, bz0 + T, bz1, "#eef2f5",
                   "EPS 50 mm em todas as faces; bandeja de 186 × 79 × 382 mm (5,6 L)", "baia", transparente=True))
    p.append(caixa("Baia fria — tampa isolada", bx0, bx1, 0, T, bz0 + T, bz1 - 2, "#dfe7ee",
                   "frente de MDF + bloco de EPS; sai pela alça", "baia"))
    # dispensador por gravidade (estrutura passiva)
    xd0, xd1 = c.X_DISP_BAY[0] + T, c.X_DISP_BAY[1] + T
    p.append(caixa("Rampa do dispensador", xd0, xd1, 15, c.SHELF_DEPTH, 245.9, 249, mdf2,
                   "estrutura passiva: os rolos descem por gravidade, sem sensor nem motor"))
    # Peltier, coolers e berços (lateral esquerda, por fora)
    for i, yc in enumerate(L.PELTIER_Y):
        x0, x1, y0, y1, z0, z1 = L.cooler_caixa(i)
        p.append(caixa(f"Cooler {i + 1} (Hyper 212)", x0, x1, y0, y1, z0 + L.VENTOINHA_ESP, z1, metal,
                       "lado quente da Peltier; ventoinha embaixo soprando para cima", "frio"))
        p.append(caixa(f"Ventoinha do cooler {i + 1}", x0 + 15, x1 - 15, yc - 60, yc + 60, z0, z0 + L.VENTOINHA_ESP, preto,
                       "120 mm, 12 V, sempre ligada com a fonte", "frio"))
        bz = L.berco_z()
        p.append(caixa(f"Berço do cooler {i + 1}", -(L.COOLER_A + 15), -T, yc - 74, yc + 74, bz, bz + T, mdf,
                       "grade de quadrados de 11 mm; o peso do cooler fica aqui", "frio"))
        p.append(caixa(f"Peltier {i + 1} (TEC1-12703)", -0.8, T, yc - 20, yc + 20, L.PELTIER_Z - 20, L.PELTIER_Z + 20,
                       "#f4f4f4", "no furo quadrado de 41 mm da lateral", "frio"))
        p.append(caixa(f"Dissipador frio {i + 1}", T + 50, T + 50 + 34, yc - 23, yc + 23, L.PELTIER_Z - 32, L.PELTIER_Z + 32,
                       metal, "65 × 46 × 24 + ventoinha de 60 mm, dentro da baia", "frio"))
    # bloco da dobradiça, trava, reed, câmeras, caixa da eletrônica
    p.append(caixa("Bloco da dobradiça", -c.BLOCO_DOB_CAMADAS * T, 0, -c.AFASTAMENTO_PORTA,
                   c.BLOCO_DOB_LARGURA - c.AFASTAMENTO_PORTA, c.DOB_Z0, c.DOB_Z0 + c.DOB_COMPRIMENTO, mdf2,
                   "3 camadas coladas e parafusadas; recebe a dobradiça piano"))
    tx, ty, tz = c.TRAVA_CORPO
    xi = W - T
    p.append(caixa("Trava FE-91", xi - tx, xi, c.TRAVA_Y0, c.TRAVA_Y0 + ty, c.TRAVA_Z - tz / 2, c.TRAVA_Z + tz / 2, preto,
                   "relé 1 do Mega; energizada no máximo 3 s", "trava"))
    lx, ly, lz = c.TRAVA_LINGUETA
    p.append(caixa("Lingueta", xi - tx - lx, xi - tx, c.TRAVA_Y0, c.TRAVA_Y0 + ly, c.TRAVA_Z - lz / 2, c.TRAVA_Z + lz / 2,
                   metal, "recolhe com 12 V; o lado chanfrado fica para a frente", "lingueta"))
    p.append(caixa("Reed (sensor da porta)", xi - 12, xi, 6, 34, c.REED_Z - 7, c.REED_Z + 7, "#ffffff",
                   "pino 3; fio rompido lê porta aberta", "trava"))
    yc, zc, _ = L.CAMERA_INTERNA
    p.append(caixa("Câmera interna", xi - 32, xi, yc - 40, yc + 10, zc - 20, zc + 20, preto, "olha para as gavetas"))
    cx, cy = L.CAMERA_EXTERNA_XY
    p.append(caixa("Câmera externa", cx - 35, cx + 35, cy - 20, cy + 20, H, H + 45, preto, "no tampo: olha quem está no teclado"))
    wx, wy, wz = (d + 2 * T for d in c.CAIXA_INT)
    x0, y0 = c.CAIXA_XY
    p.append(caixa("Caixa da eletrônica", x0, x0 + wx, y0, y0 + wy, H, H + wz, "#3a6ea5",
                   "fonte, fusíveis, relés, LM2596 e Mega; só abrir fora da tomada"))
    return p


def porta():
    """Partes que giram com a porta (na posição fechada) e o eixo."""
    yi, ye = P.Y_PORTA_INT, P.Y_PORTA_EXT
    z0, z1 = c.PORTA_Z0, c.PORTA_Z0 + c.PORTA_H
    p = [caixa("Porta (caixão de 30 mm)", P.X_PORTA0, P.X_PORTA1, ye, yi, z0, z1, "#d9b47c",
               "duas peles de 3 mm + miolo de 24 mm; clique para abrir (só se a trava estiver solta)", "porta")]
    for nome, (cx, cz), (w, h) in (("LCD 16x2", c.LCD_CENTRO, c.LCD_JANELA), ("Leitor de digital AS608", c.AS608_CENTRO, c.AS608_JANELA),
                                   ("Teclado 4x4", c.TECLADO_CENTRO, c.TECLADO), ("Puxador (cava)", c.PUXADOR_CENTRO, c.PUXADOR)):
        cor = {"LCD 16x2": "#7fae3c", "Leitor de digital AS608": "#1d2733", "Teclado 4x4": "#222", "Puxador (cava)": "#5a4026"}[nome]
        p.append(caixa(nome, cx - w / 2, cx + w / 2, ye - 1.5, ye, cz - h / 2, cz + h / 2, cor, "", "porta", tela=nome == "LCD 16x2"))
    x0, x1, zt0, zt1 = c.JANELA_INT
    m = P.TAMPA_MARGEM
    p.append(caixa("Tampa traseira do LCD e do leitor", x0 - m, x1 + m, yi, yi + c.CAIXA_TRASEIRA_PROF + T, zt0 - m, zt1 + m,
                   "#b98d55", "entra 6 mm no compartimento: deixar a frente da prateleira vazia", "porta"))
    bx0, bx1 = c.BATENTE_X
    p.append(caixa("Batente (braço com a janela da lingueta)", bx0, bx1, yi + 2 * T, c.BATENTE_Y1, c.TRAVA_Z - 35, c.TRAVA_Z + 35,
                   "#8c6a3f", "preso por 2 parafusos dentro da cava do puxador: liberação de emergência", "porta"))
    p.append(caixa("Mata-junta", c.EXT_W - 30, c.EXT_W, yi, yi + 2 * T, z0, z1, "#c49a62", "cobre a borda da lateral direita", "porta"))
    return p, {"x": P.EIXO[0], "y": P.EIXO[1]}


PAGINA = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Armário dispensador</title>
<style>
  :root { --bg:#f3f1ec; --card:#fff; --tx:#1f2a26; --mut:#5b6862; --pri:#0b6e4f; --line:#d9d4c8; --lcd:#9ecb3c; --lcdtx:#16310b; }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#1b1f1d; --card:#252b28; --tx:#e8ece9; --mut:#9aa8a1; --line:#3a423e; } }
  :root[data-theme="dark"] { --bg:#1b1f1d; --card:#252b28; --tx:#e8ece9; --mut:#9aa8a1; --line:#3a423e; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--tx); font:16px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
  header { padding:14px 16px; }
  h1 { margin:0; font-size:22px; }
  header p { margin:4px 0 0; color:var(--mut); }
  .grade { display:grid; grid-template-columns:minmax(0,1fr) 330px; gap:14px; padding:0 16px 16px; }
  @media (max-width: 860px) { .grade { grid-template-columns:1fr; } }
  #cena { position:relative; height:640px; background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; }
  @media (max-width: 860px) { #cena { height:420px; } }
  #etq { position:absolute; pointer-events:none; background:#1f2a26; color:#fff; padding:6px 9px; border-radius:6px; font-size:13px; max-width:260px; display:none; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; margin-bottom:12px; }
  .card h2 { margin:0 0 8px; font-size:16px; }
  .lcd { background:var(--lcd); color:var(--lcdtx); font:20px/1.25 ui-monospace,Menlo,Consolas,monospace; padding:8px 10px; border-radius:6px; white-space:pre; letter-spacing:1px; }
  .tec { display:grid; grid-template-columns:repeat(4,1fr); gap:6px; margin-top:8px; }
  button { font:inherit; border:1px solid var(--line); border-radius:8px; padding:8px; background:var(--bg); color:var(--tx); cursor:pointer; }
  button.pri { background:var(--pri); color:#fff; border-color:var(--pri); }
  .linha { display:flex; gap:6px; flex-wrap:wrap; margin-top:8px; }
  .chip { display:inline-block; padding:2px 8px; border-radius:999px; background:var(--bg); border:1px solid var(--line); font-size:13px; margin:2px 2px 0 0; }
  .chip.on { background:#ffe2c2; border-color:#e8a15f; color:#5a2c00; }
  #log { font:12px/1.35 ui-monospace,Menlo,Consolas,monospace; max-height:160px; overflow:auto; color:var(--mut); white-space:pre-wrap; }
  small { color:var(--mut); }
</style>
</head>
<body>
<header>
  <h1>Armário dispensador</h1>
  <p>Medidas geradas de <code>armario/gerador/config.py</code> e <code>hardware/layout.py</code> por <code>docs/gerar_simulacao.py</code>. Passe o mouse numa peça para ver o nome; clique na porta ou numa gaveta para abrir.</p>
</header>
<div class="grade">
  <div id="cena"><div id="etq"></div></div>
  <div>
    <div class="card">
      <h2>Na porta</h2>
      <div class="lcd" id="lcd"></div>
      <div class="tec" id="tec"></div>
      <div class="linha"><button class="pri" id="b-dig">Digital do usuário 1</button><button id="b-dig-x">Dedo desconhecido</button></div>
      <small>Usuário 1 tem a senha 1357 (padrão do firmware). Sem notebook, o Mega libera sozinho depois da autenticação.</small>
    </div>
    <div class="card">
      <h2>Estado</h2>
      <div id="chips"></div>
      <div class="linha"><button id="b-vista-f">Frente</button><button id="b-vista-e">Lado esquerdo</button><button id="b-vista-c">De cima</button><button id="b-raio">Raio-x</button></div>
    </div>
    <div class="card"><h2>Monitor serial</h2><div id="log"></div></div>
  </div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
const DADOS = __DADOS__;
(function () {
  // ---------------------------------------------------------- lógica da porta (resumo do firmware)
  const st = { estado: "OCIOSO", buf: "", id: 0, erros: 0, desde: performance.now(), trava: false, porta: 0, alvo: 0,
               alarme: false, l1: "", l2: "", gav: {}, tela_ate: 0 };
  const TECLAS = ["1","2","3","A","4","5","6","B","7","8","9","C","*","0","#","D"];
  const SENHAS = {1: "1357"};
  const $ = id => document.getElementById(id);
  function log(t) { const l = $("log"); l.textContent = (new Date().toLocaleTimeString() + "  " + t + "\n" + l.textContent).slice(0, 4000); }
  function tela(a, b, ms) { st.l1 = a; st.l2 = b; st.tela_ate = ms ? performance.now() + ms : 0; }
  function ir(e) { st.estado = e; st.desde = performance.now(); st.buf = ""; if (e === "OCIOSO") tela("Digital ou ID+#", "Dispensario"); }
  function ev(t, u, v) { log(`EV t=${t} u=${u || 0} v=${v || 0}`); }
  function autenticado(u, m) { st.erros = 0; st.id = u; ev("AUTH_OK", u, m); ev("MODO_AUTONOMO", u); ev("LIBERADO", u); ir("LIBERADO"); st.trava = true; tela("Pode abrir", "a porta"); }
  function falhou(m) {
    st.erros++; ev("AUTH_FALHA", 0, m);
    if (st.erros >= 3) { ev("BLOQUEIO", 0, 30); ir("BLOQUEADO"); } else { ir("OCIOSO"); tela(m === 1 ? "Digital invalida" : "Senha errada", "Tente de novo", 3000); }
  }
  function tecla(k) {
    if (["BLOQUEADO","LIBERADO"].includes(st.estado)) return;
    if (k === "*") { ir("OCIOSO"); return; }
    const dig = /[0-9]/.test(k);
    if (st.estado === "OCIOSO") { if (!dig) return; ir("ID"); }
    if (st.estado === "PORTA_ABERTA") return;
    if (dig) { if (st.buf.length < (st.estado === "ID" ? 2 : 8)) st.buf += k; }
    else if (k === "#") {
      if (st.estado === "ID") { const id = +st.buf; if (!(id >= 1 && id <= 20)) return falhou(2); st.id = id; ir("SENHA"); }
      else if (st.estado === "SENHA") { return (st.buf.length >= 4 && SENHAS[st.id] === st.buf) ? autenticado(st.id, 2) : falhou(2); }
    }
    tela(st.estado === "ID" ? "ID: " + st.buf : "Senha: " + "*".repeat(st.buf.length), "#=ok  *=apaga");
  }
  function tick() {
    const t = performance.now() - st.desde;
    if (st.tela_ate && performance.now() > st.tela_ate && st.estado === "OCIOSO") { st.tela_ate = 0; tela("Digital ou ID+#", "Dispensario"); }
    if (st.estado === "LIBERADO" && t > 3000) { st.trava = false; ev("LIBERACAO_EXPIROU", st.id); ir("OCIOSO"); }
    if (st.estado === "PORTA_ABERTA" && t > 30000 && !st.alarme) { st.alarme = true; ev("PORTA_ABERTA_TEMPO", st.id, 30); tela("Feche a porta", ""); }
    if (st.estado === "BLOQUEADO") { if (t > 30000) { st.erros = 0; ir("OCIOSO"); } else tela("Bloqueado", "Aguarde " + Math.ceil((30000 - t) / 1000) + "s"); }
    if (["ID","SENHA"].includes(st.estado) && t > 15000) ir("OCIOSO");
  }
  function puxarPorta() {
    if (st.alvo === 0) {                                     // abrir
      if (!st.trava && st.estado !== "PORTA_ABERTA") { log("A lingueta segura a porta (trava sem energia)"); tremer = 12; return; }
      if (st.estado === "LIBERADO") { st.trava = false; ev("PORTA_ABERTA", st.id); ir("PORTA_ABERTA"); tela("Porta aberta", "Feche ao sair"); }
      st.alvo = 90;
    } else {                                                 // fechar: o batente empurra o chanfro e tranca sozinho
      st.alvo = 0;
      setTimeout(() => { if (st.estado === "PORTA_ABERTA") { ev("PORTA_FECHADA", st.id); st.alarme = false; ir("OCIOSO"); } }, 900);
    }
  }
  let tremer = 0;
  TECLAS.forEach(k => { const b = document.createElement("button"); b.textContent = k; b.onclick = () => tecla(k); $("tec").appendChild(b); });
  $("b-dig").onclick = () => { if (st.estado === "OCIOSO") autenticado(1, 1); };
  $("b-dig-x").onclick = () => { if (st.estado === "OCIOSO") falhou(1); };
  function painel() {
    $("lcd").textContent = (st.l1 + " ".repeat(16)).slice(0, 16) + "\n" + (st.l2 + " ".repeat(16)).slice(0, 16);
    const c = [["Estado: " + st.estado, false], ["Trava " + (st.trava ? "energizada" : "sem energia"), st.trava],
               ["Porta " + (st.porta > 2 ? "aberta" : "fechada"), st.porta > 2], ["Alarme", st.alarme]];
    $("chips").innerHTML = c.map(([t, on]) => `<span class="chip ${on ? "on" : ""}">${t}</span>`).join("");
  }
  ir("OCIOSO"); ev("BOOT", 0, 0);

  // ---------------------------------------------------------- cena 3D (X direita, Y fundo, Z cima -> three: x, z=-Y, y=Z)
  setInterval(() => { tick(); painel(); }, 100);       // a lógica não depende da animação (que para com a aba escondida)
  if (!window.THREE) { $("cena").innerHTML = "<p style='padding:12px'>Sem internet para carregar o three.js: a lógica da porta funciona assim mesmo.</p>"; return; }
  const box = $("cena");
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
  box.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 5, 10000);
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x887766, 0.9));
  const sol = new THREE.DirectionalLight(0xffffff, 0.6); sol.position.set(-800, 1600, -1400); scene.add(sol);
  const centro = new THREE.Vector3(440, 440, -300);
  function vista(n) {
    const p = { f: [440, 520, -2100], e: [-1500, 700, -150], c: [440, 2300, -350] }[n];
    camera.position.set(...p); controls.target.copy(centro); controls.update();
  }
  const clicaveis = [], todos = [];
  function malha(d, pai) {
    const w = d.x[1] - d.x[0], h = d.z[1] - d.z[0], p = d.y[1] - d.y[0];
    const mat = new THREE.MeshStandardMaterial({ color: d.cor, roughness: 0.75, transparent: !!d.transparente, opacity: d.transparente ? 0.45 : 1 });
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, p), mat);
    m.position.set((d.x[0] + d.x[1]) / 2, (d.z[0] + d.z[1]) / 2, -(d.y[0] + d.y[1]) / 2);
    m.add(new THREE.LineSegments(new THREE.EdgesGeometry(m.geometry), new THREE.LineBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.25 })));
    m.userData = d; (pai || scene).add(m); todos.push(m); clicaveis.push(m);
    return m;
  }
  DADOS.pecas.forEach(d => { const m = malha(d); if (d.gaveta) { st.gav[d.gaveta] = { m, alvo: 0, pos: 0, z0: m.position.z }; } });
  // a porta gira em torno do eixo da dobradiça (vertical)
  const pivo = new THREE.Group(); pivo.position.set(DADOS.eixo.x, 0, -DADOS.eixo.y); scene.add(pivo);
  DADOS.porta.forEach(d => { const m = malha(d, pivo); m.position.x -= DADOS.eixo.x; m.position.z += DADOS.eixo.y; });
  const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
  function sob(e) {
    const r = renderer.domElement.getBoundingClientRect();
    mouse.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(mouse, camera);
    const hit = ray.intersectObjects(clicaveis, false).find(h => h.object.visible && h.object.material.opacity > 0.3);
    return hit ? hit.object : null;
  }
  renderer.domElement.addEventListener("mousemove", e => {
    const o = sob(e), etq = $("etq");
    if (!o) { etq.style.display = "none"; return; }
    const r = box.getBoundingClientRect();
    etq.innerHTML = `<b>${o.userData.nome}</b>${o.userData.detalhe ? "<br>" + o.userData.detalhe : ""}`;
    etq.style.display = "block"; etq.style.left = (e.clientX - r.left + 12) + "px"; etq.style.top = (e.clientY - r.top + 12) + "px";
  });
  renderer.domElement.addEventListener("click", e => {
    const o = sob(e); if (!o) return;
    if (o.userData.grupo === "porta") puxarPorta();
    else if (o.userData.gaveta) { if (st.porta < 80) { log("Abra a porta antes de puxar a gaveta"); return; } const g = st.gav[o.userData.gaveta]; g.alvo = g.alvo ? 0 : 300; }
  });
  let raio = false;
  $("b-raio").onclick = () => { raio = !raio; todos.forEach(m => { const d = m.userData; if (["Lateral esquerda","Lateral direita","Tampo","Traseiro","Fundo falso"].includes(d.nome) || d.grupo === "porta" && d.nome.startsWith("Porta")) { m.material.transparent = raio || !!d.transparente; m.material.opacity = raio ? 0.15 : (d.transparente ? 0.45 : 1); } }); };
  $("b-vista-f").onclick = () => vista("f"); $("b-vista-e").onclick = () => vista("e"); $("b-vista-c").onclick = () => vista("c");
  function tamanho() { const w = box.clientWidth, h = box.clientHeight; renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix(); }
  window.addEventListener("resize", tamanho); tamanho(); vista("f");
  function quadro() {
    st.porta += (st.alvo - st.porta) * 0.12;
    let a = -st.porta * Math.PI / 180;
    if (tremer > 0) { a += Math.sin(tremer) * 0.004; tremer--; }
    pivo.rotation.y = -a;
    Object.values(st.gav).forEach(g => { g.pos += (g.alvo - g.pos) * 0.15; g.m.position.z = g.z0 + g.pos; });
    renderer.render(scene, camera); requestAnimationFrame(quadro);
  }
  quadro();
})();
</script>
</body>
</html>
"""


def gerar() -> str:
    partes_porta, eixo = porta()
    dados = {"pecas": pecas(), "porta": partes_porta, "eixo": eixo}
    return PAGINA.replace("__DADOS__", json.dumps(dados, ensure_ascii=False, separators=(",", ":")))


def main():
    novo = gerar()
    atual = open(SAIDA, encoding="utf-8").read() if os.path.exists(SAIDA) else ""
    if "--verificar" in sys.argv:
        if atual != novo:
            raise SystemExit("docs/simulacao.html desatualizada: rode python docs/gerar_simulacao.py")
        print("OK")
        return
    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(novo)
    print("gerado: docs/simulacao.html")


if __name__ == "__main__":
    main()
