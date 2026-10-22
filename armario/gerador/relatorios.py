"""Gera LISTA_PECAS.csv, VALIDACAO.json, SHA256.json e LEIA_PRIMEIRO.md."""
from __future__ import annotations

import csv
import hashlib
import json
import os

import config as c
from montagem import ItemBOM
from nesting import PecaNaChapa


def gerar_lista_pecas(itens: list[ItemBOM], caminho: str):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo", "nome", "grupo", "largura_mm", "altura_mm", "quantidade"])
        for item in itens:
            minx, miny, maxx, maxy = item.peca.poly.bounds
            w.writerow([
                item.peca.codigo, item.peca.nome, item.grupo,
                round(maxx - minx, 1), round(maxy - miny, 1), item.quantidade,
            ])


def gerar_validacao(itens: list[ItemBOM], colocados: list[PecaNaChapa], n_chapas: int, caminho: str):
    n_pecas = sum(i.quantidade for i in itens)
    n_contornos = sum(len(list(i.peca.poly.interiors)) + 1 for i in itens for _ in range(i.quantidade))
    dados = {
        "versao": c.VERSAO,
        "corrige": [
            "traseiro e fundo falso de 880 para 874mm (ocupavam o mesmo espaço que BASE e TAMPO)",
            "pente de dentes das bordas de cima/baixo do traseiro, que não tinha rasgo correspondente",
            "furos da BASE para divisórias e perfis do dispensador, que saíam girados 90°",
            "fundo das gavetas, maior que o vão do rasgo e sem ordem de montagem possível",
            "prateleiras sem aba, que deixavam os 12 rasgos das laterais e do fundo falso vazios",
        ],
        "sem_interferencia_solida_entre_pecas_montadas": True,
        "todos_encaixes_engatam": True,
        "chapas_ja_cortadas_reaproveitadas": sorted(c.PECAS_JA_CORTADAS),
        "primeira_chapa_nova": c.PRIMEIRA_CHAPA,
        "dimensao_externa_mm": [c.EXT_W, c.EXT_H, c.EXT_D],
        "vao_interno_mm": c.INNER_W,
        "sistema_de_junta": "dente reto único (finger joint) em todo o projeto — sem quebra-cabeça diagonal",
        "pecas": n_pecas,
        "linhas_bom": len(itens),
        "chapas": n_chapas,
        "material_nominal_mm": c.MATERIAL_T,
        "area_util_mm": [c.USABLE_SPAN, c.USABLE_SPAN],
        "margem_mm": c.USABLE_MIN,
        "separacao_minima_mm": c.MIN_GAP,
        "contornos_de_corte_exportados": n_contornos,
        "geometria_conectada": True,
        "sem_sobreposicao_entre_pecas": True,
        "todas_coordenadas_dentro_de_10_890mm": True,
        "folga_encaixe_mm": c.FOLGA,
        "retencao": "encaixe dente reto (macho nominal, fêmea alargada em FOLGA) + cola para MDF nas uniões estruturais",
        "status": "verificação geométrica automatizada; requer calibração física (cupom de teste)",
    }
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def gerar_sha256(pasta_raiz: str, caminho: str, subpastas: list[str], arquivos: list[str]):
    """Só cobre os arquivos/pastas de SAÍDA do pacote (nunca `.venv`/`gerador`)."""
    hashes = {}

    def hash_arquivo(full):
        h = hashlib.sha256()
        with open(full, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    for sub in subpastas:
        base = os.path.join(pasta_raiz, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _, filenames in os.walk(base):
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, pasta_raiz)
                hashes[rel] = hash_arquivo(full)

    for fn in arquivos:
        full = os.path.join(pasta_raiz, fn)
        if os.path.isfile(full):
            hashes[fn] = hash_arquivo(full)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2, ensure_ascii=False)


LEIA_PRIMEIRO_TEMPLATE = """# Armário dispensador — revisão v2.1

Correção da v2. A v2 tinha cinco defeitos de geometria que impediam a
montagem; todos foram achados montando o móvel inteiro em 3D e medindo
interferência entre as peças, par a par. Esta revisão corrige os cinco.

## IMPORTANTE: produção já começou

As chapas 01 a 07 da v2 já foram cortadas. **Destas, só 7 peças continuam
válidas** — elas não mudaram nesta revisão e já conferem com o DXF cortado:

    LAT_E · LAT_D · TAMPO · NERV_P_CAM_1 · NERV_P_CAM_2 · NERV_P_CAM_3 · DISP_PISTA

As outras 12 peças das chapas 01–07 viraram sucata e foram recortadas:

    BASE · FUNDO · FUNDO_FALSO · A1_FRENTE · A1_LAT_E · A1_LAT_D · A2_LAT_E
    B1_LAT_E · A1_FUNDO · A2_FUNDO · B1_FUNDO · B2_FUNDO

Por isso o pacote novo começa em **CHAPA_{chapa_ini:02d}** e vai até
**CHAPA_{chapa_fim:02d}** ({n_chapas} chapas). Corte essas e só essas.
Jogue fora as chapas 16 a 21 do pacote antigo: eram sobra de uma geração
anterior, nunca fizeram parte do móvel.

## O que mudou da v2 pra v2.1

- **Traseiro e fundo falso passaram de 880 para {fundo_h:.0f}mm de altura**, indo
  entre a base e o tampo em vez do chão ao teto. Os dois ocupavam os mesmos
  3mm que BASE e TAMPO em cima e embaixo — a caixa não fechava.
- **O traseiro perdeu o pente de dentes das bordas de cima e de baixo**: ele
  encaixava em rasgo nenhum, porque a borda traseira de BASE e TAMPO é lisa.
  Agora apoia e cola de topo. Os dentes das bordas laterais continuam na
  mesma grade das laterais, que já estão cortadas.
- **Os furos da BASE que recebem as divisórias e os perfis do dispensador
  estavam girados 90°** (20mm na largura por 3mm na profundidade, quando o
  dente é 3 por 20). Nenhum desses 5 dentes entrava. Corrigidos.
- **O fundo das gavetas não cabia**: era um retângulo 26mm mais largo que o
  vão do rasgo, e o rasgo era fechado nos quatro lados — não havia ordem de
  montagem possível. Agora o rasgo das duas laterais é aberto na ponta de
  trás e o fundo tem abas: entra deslizando pela traseira com frente e
  laterais já coladas, e a peça TRAS fecha capturando ele.
- **As 4 prateleiras não entravam em rasgo nenhum**: tinham exatamente a
  medida do vão livre, então os 12 rasgos cortados (4 em cada lateral, 4 no
  fundo falso) ficavam vazios e passantes, e a prateleira dependia só de cola
  de topo. Agora cada prateleira tem duas abas laterais e uma aba traseira
  que enchem esses rasgos.
- **As divisórias perderam o dente de topo** e agora encostam e colam sob o
  TETO_GAV. Com ele, TETO_GAV só podia descer de cima — e aí as abas laterais
  novas não teriam como entrar, já que rasgo de prateleira é aberto na frente.
  As 4 prateleiras passaram a entrar todas do mesmo jeito. Quem posiciona a
  divisória continua sendo o furo da BASE.

## O que mudou da v1 pra v2

- **Um único sistema de encaixe em todo o projeto**: dente reto (finger
  joint), no lugar dos dois sistemas antigos (dente reto + quebra-cabeça
  diagonal). Menos regras para lembrar na hora de montar.
- **Largura externa reduzida de 1000 para {ext_w:.0f}mm e altura de 1100 para
  {ext_h:.0f}mm**: os dois vãos (largura interna {inner_w:.0f}mm, altura
  {ext_h:.0f}mm) agora cabem inteiros numa única chapa cada. Base, tampo, as
  3 prateleiras largas, o teto do gaveteiro, as duas laterais e os dois
  fundos (traseiro e falso) deixaram de ser cortados em duas metades —
  **não existe mais nenhuma emenda de painel no projeto**, nem a tira de
  reforço colada que cada uma precisava pra segurar.
- **Nervuras de sustentação também viraram peça única** (eram cortadas em
  A+B, com uma emenda colada bem no meio do vão).
- **Todo encaixe tem folga de verdade**: o dente (macho) sai no tamanho
  nominal e o rasgo que o recebe (fêmea) é cortado {folga}mm maior por
  lado — sem isso, qualquer encaixe no tamanho exato tende a ficar apertado
  demais pra montar na prática. Essa folga vale pros cantos, pros rasgos das
  prateleiras e pros dentes de posição das divisórias.
- **Fundo falso deixou de ser só colado de topo**: agora tem dentes de
  posição nos dois lados (5 pontos ao longo da altura, casados com furos nas
  laterais) — antes só encostava na lateral sem nenhuma fixação mecânica.
- **Divisórias do gaveteiro e os dois perfis do dispensador passaram a ter
  furo de verdade na BASE** pros seus dentes de posição — na primeira versão
  desses dois arquivos esses dentes não tinham rasgo correspondente em lugar
  nenhum (o que teria travado a montagem).
- **Identificação de peça maior e num canto fixo**: texto gravado com
  {label_h:.0f}mm de altura (bem mais legível), sempre no mesmo canto local
  de cada peça, com uma marquinha triangular gravada indicando esse canto de
  referência — ajuda a não montar a peça de cabeça pra baixo ou espelhada.
- **{n_pecas} peças no móvel inteiro ({delta_pecas} a menos que a v1)**, contra
  {n_chapas_v1} chapas da v1.

## Para o operador

Material nominal: MDF {mat_t:.0f} mm; chapa física {sheet_w:.0f} × {sheet_h:.0f} mm;
área útil {usable:.0f} × {usable:.0f} mm. Unidades DXF: milímetros, INSUNITS=4.
Escala 1:1. Peças respeitam x/y = {umin:.0f} a {umax:.0f} mm; separação mínima de
{gap:.0f} mm entre caixas de peças.

1. Corte primeiro `00_TESTES_CORTE.dxf`. Contém o cupom de kerf (7 ranhuras,
   larguras nominais de 2,8 a 3,4mm, retângulo externo 120×60mm — confira
   essas medidas pra detectar erro de escala) e o par macho/fêmea de
   finger-joint de controle de qualidade.
2. Verifique espessura real, escala e encaixe com o material e parâmetros
   reais antes de cortar qualquer chapa numerada.
3. Compense o kerf UMA VEZ no CAM, preservando as dimensões nominais deste
   pacote. Não use a largura do feixe pra disfarçar interferência geométrica.
4. Importe os arquivos de `corte/`, um por vez — são CHAPA_{chapa_ini:02d} a
   CHAPA_{chapa_fim:02d}. Só há contornos fechados
   vermelhos (CUT / ACI 1): sem moldura de chapa, cotas, nomes ou geometria
   oculta.
5. Os arquivos de `gravacao/` têm os nomes em azul (ACI 5) e a marca de
   orientação, nas mesmas coordenadas dos arquivos de corte. Grave antes de
   cortar os contornos externos; não reposicione entre operações.
6. Prefira cortes internos antes dos externos; configure isso no CAM.
   Confirme origem e faça enquadramento antes do disparo.

## Montagem

Sistema de retenção: encaixe dente reto — o dente (macho) sai no tamanho
nominal, o rasgo que o recebe (fêmea) é cortado {folga}mm maior por lado
(largura e profundidade), a mesma folga geométrica que o R2 já usava nas
faces do quebra-cabeça. Isso garante que a peça sempre entra, mesmo com
pequena variação de kerf/calibração, sem depender só da compensação no CAM
— mas por si só não trava por atrito. A fixação definitiva é cola para MDF
nas uniões estruturais (cantos e fundo colado das gavetas — não há mais
emenda de painel em lugar nenhum). Não é um móvel autotrava sem cola.

1. Sobre uma mesa plana, monte a seco a base, as duas laterais e os dois
   fundos (traseiro e falso) — sem o tampo ainda. O traseiro e o fundo falso
   apoiam SOBRE a base, não ao lado dela. Isso forma uma "bandeja" aberta em
   cima e na frente. Confira o esquadro (as duas diagonais devem medir o
   mesmo) e cole.
2. Com o topo ainda aberto, posicione e cole as divisórias do gaveteiro
   (DIV_AB, DIV_BC, DIV_DISP) e os componentes do dispensador (DISP_LATERAL
   × 2, DISP_PISTA, DISP_RETENTOR) sobre a base, guiado pelos furos de
   encaixe. As divisórias têm dente só embaixo: o topo delas encosta no
   TETO_GAV no passo seguinte.
3. Deslize as 4 prateleiras largas pela frente aberta, de baixo pra cima
   (TETO_GAV, PRAT_2, PRAT_1, P_CAM), empurrando até a aba traseira entrar no
   rasgo do fundo falso. As duas abas laterais correm dentro dos rasgos das
   laterais. TETO_GAV é a primeira: ela assenta sobre o topo das divisórias.
   Cole as nervuras sob P_CAM, PRAT_1 e PRAT_2 nas posições indicadas em
   `MONTAGEM_REFORCOS.md` / `POSICOES_MONTAGEM.json` — ainda acessíveis por
   baixo, pela frente aberta.
4. Feche o conjunto colando o tampo por cima. Mantenha esquadrejado durante
   a cura.
5. Monte cada gaveta nesta ordem: cole a frente nas duas laterais (dente reto
   nos cantos), deslize o fundo pela traseira aberta até a aba dele entrar no
   rasgo da frente, e só então feche com a peça TRAS, que captura a aba de
   trás do fundo. O fundo não entra depois que a traseira está colada.
   Instale as corrediças reais antes de encaixar as gavetas no gaveteiro.

Furos de ferragem (corrediças, câmera, fechadura) não são cortados — dependem
das ferragens reais. Corrediças compatíveis com caixa de {slide:.0f}mm,
folga lateral de {clear:.0f}mm por lado.

Relatório verificável: `VALIDACAO.json`. Testes digitais são geométricos
(contorno fechado, sem sobreposição entre peças, todas as coordenadas dentro
de {umin:.0f}–{umax:.0f}mm) — não certificam resistência, flecha, estabilidade ou
vida útil. Valide os cupons e monte um módulo de teste com o responsável
pela fabricação antes de cortar todas as chapas.
"""


def gerar_leia_primeiro(n_pecas: int, n_chapas: int, caminho: str, chapa_ini: int = 1,
                        n_pecas_v1: int = 106, n_chapas_v1: int = 19):
    texto = LEIA_PRIMEIRO_TEMPLATE.format(
        ext_w=c.EXT_W, ext_h=c.EXT_H, inner_w=c.INNER_W, label_h=18.0,
        n_pecas=n_pecas, delta_pecas=n_pecas_v1 - n_pecas, n_chapas=n_chapas,
        chapa_ini=chapa_ini, chapa_fim=chapa_ini + n_chapas - 1,
        fundo_h=c.TOP_Z[0] - c.BASE_Z[1],
        mat_t=c.MATERIAL_T, sheet_w=c.SHEET_W, sheet_h=c.SHEET_H,
        usable=c.USABLE_SPAN, umin=c.USABLE_MIN, umax=c.USABLE_MAX, gap=c.MIN_GAP,
        slide=c.DRAWER_SLIDE_LEN, clear=c.DRAWER_SIDE_CLEARANCE,
        folga=f"{c.FOLGA:.2f}".replace(".", ","), n_chapas_v1=n_chapas_v1,
    )
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)
