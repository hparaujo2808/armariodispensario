# Decisões do projeto

Cada decisão tem data, quem decidiu e de onde vêm os números. Para mudar uma decisão, acrescente uma linha nova; não apague a antiga.

## DECISÃO 1 — Arquitetura (22/10/2026, aprovada pelo grupo)

**Híbrida: Arduino Mega + notebook.**

- **Mega:** tempo real e segurança física. Cuida do teclado, do LCD, do leitor de digital AS608 (Serial1), da trava, do sensor de porta (reed), dos sensores de temperatura DS18B20, do controle da gaveta fria, do buzzer e do watchdog. Funciona sozinho se o notebook cair.
- **Notebook:** quiosque com CPF, MV simulado, registro de auditoria (SQLite), gravação das 2 webcams e painel da logística. Reaproveita o software do legado, com uma camada nova (`hal/serial_mega.py`) que conversa com o Mega pela USB.

Descartadas: "só o Mega" (deixa RF03, RF04, RF07 e RF10, que são Must, sem atender) e "Raspberry Pi do legado" (~R$ 2.800 e prazo apertado). Comparação completa em `docs/AUDITORIA.md`.


## 1.0 Pior caso de montagem (pedido do grupo em 22/10)

O grupo não sabe com certeza o que já está colado. Por isso o projeto supõe o **pior caso**: caixa, traseiro, fundo falso e corrediças já colados ou parafusados. Regras que valem daqui em diante:
- Todo furo é feito com a peça montada, **por fora ou pela frente**, usando gabarito cortado a laser.
- Nada exige desmontar ou recortar o contorno de uma peça já cortada.

**Consequência: o vão de trás não é mais usado.** Com o traseiro colado não há como pôr lá dentro um cooler de 124 × 73 × 152 mm, nem o Mega, os relés e a fonte. A versão de 22/10 de manhã (coolers no vão de trás e 16 furos de 38 mm no traseiro) foi para `legado/`. Ficou assim:
- **As Peltier atravessam a lateral esquerda**, que é a parede esquerda da baia na coluna A, e **os coolers ficam do lado de fora**, apoiados em berços.
- **A eletrônica fica numa caixa cortada a laser em cima do tampo.** A caixa também fecha o borne da fonte colmeia.
- **Não há nenhum furo no fundo falso nem no traseiro.** A pergunta sobre a resistência do traseiro com 16 furos deixa de existir.

## 1.1 Gaveta fria

### Opções comparadas

`python calculos/gaveta_fria.py` (mesmo modelo térmico do legado, com a TEC1-12703, medidas do `config.py`, 6 aberturas por hora). Temperatura mínima que a baia consegue manter com as Peltier ligadas o tempo todo:

| Baia | Pastilhas | Isolamento | Volume da bandeja | 25 °C | 28 °C | 32 °C | Dá para montar com o armário colado? |
|---|---:|---|---:|---:|---:|---:|---|
| C2 (coluna C, em cima) | 1 | XPS 50 mm | 1,4 L | −0,4 | 2,1 | 5,4 | **Não**: a coluna C não encosta em parede externa, então o cooler teria que ficar no vão de trás |
| A3+A4, cooler no vão de trás | 2 | EPS 50 mm | 6,7 L | −0,4 | 2,1 | 5,5 | **Não**: vão de trás fechado |
| **A3+A4, cooler fora da lateral esquerda** | **2** | **EPS 50 mm** | **5,8 L** | **−1,4** | **1,2** | **4,6** | **Sim**: tudo por fora ou pela frente |

As resistências térmicas dos coolers são estimativas [est] e serão medidas na bancada. O EPS escolhido tem 10 kg/m³; usamos condutividade 0,044 W/m·K [est]. Do lado de fora, o cooler pega o ar da sala; no vão de trás o ar ficaria 2 K mais quente. Por isso a opção escolhida é até um pouco melhor.

### Escolha

**Baia fria fixa no lugar das gavetas A3 e A4 (coluna A, metade de cima), com as duas TEC1-12703 atravessando a lateral esquerda e isolamento de EPS de 50 mm em todas as faces.**

- **Volume:** bandeja de **186 × 82 × 382 mm (5,8 L)**. Cabem ~100 frascos de 10 mL em pé (Ø ~25 mm, ~50 mm de altura [est]: 7 × 15), ou canetas deitadas.
- **Medidas da baia** [calc, `hardware/layout.py`]:
  - por fora: X 3 a 346, Z 205 a 399, Y 0 a 494;
  - por dentro do EPS: 243 × 94 × 394 mm;
  - os dissipadores frios ocupam 45 mm na parede esquerda.
- **O que não precisa desmontar:**
  - As corrediças de A3 e A4, se já estiverem presas, **ficam onde estão**. O EPS das paredes leva um entalhe de 13 mm onde passa cada corrediça (sobram 37 mm de isolamento ali).
  - As gavetas A3 e A4 ficam de reserva. A1 e A2 continuam normais.
- **Piso da baia:** placa de MDF de 343 × 494 a 205–208 mm (a gaveta A2 vai até 199,8). Fica apoiada em taquinhos de MDF colados pela frente na lateral esquerda e na divisória A/B, longe dos parafusos. O piso será cortado a laser junto com a porta (Fase 5).
- **Como abre:** **baia fixa**, com **tampa frontal isolada** e **bandeja deslizante**, sem corrediça (a corrediça metálica atravessaria o isolamento e não cabe com 50 mm de EPS).
  1. Abre-se a porta do armário.
  2. Tira-se a tampa: um bloco de EPS de 50 mm colado atrás de uma frente de MDF, com fita de espuma em volta e uma alça.
  3. Puxa-se a bandeja de MDF, que corre sobre o piso.
- **Peltier:**
  - Duas, com centro em Y = 160 e Y = 330 (da frente) e Z = 300. Ficam entre a corrediça de A3 (até 272,7) e a de A4 (a partir de 326,1), com 5,6 mm de folga.
  - Cada uma entra num furo **quadrado de 41 mm** feito por fora na lateral esquerda, com gabarito.
  - A pilha, de dentro para fora: dissipador frio 65 × 46 × 24 com ventoinha de 60 mm (dentro da baia) → espaçador de alumínio 38,1 × 38,1 × 50 mm atravessando o EPS → pastilha no furo da lateral → cooler do lado de fora.
  - Duas barras roscadas M3 por Peltier (Y ± 35 mm) apertam a pilha. Elas **só apertam**: o peso do cooler fica no berço.
- **Água de condensação:** o dissipador frio pode passar de 0 °C (−6 °C calculado a 32 °C de ambiente). Forma gelo fino nas aletas, que derrete no tempo desligado.
  - A água pinga numa **bandejinha removível** (pote raso com papel absorvente) apoiada no piso da baia, embaixo de cada dissipador frio.
  - Pelo cálculo do legado são ~0,08 g por abertura da porta, menos de 2 g por dia: basta trocar o papel uma vez por semana.
  - Toda a eletrônica fica fora da baia e acima dela.

### Controle de temperatura (vai para o firmware na Fase 3)

| Parâmetro | Valor |
|---|---|
| Setpoint | 5,0 °C |
| Faixa aceitável | 2,0 a 8,0 °C |
| Liga as Peltier | sensor da baia ≥ 6,0 °C |
| Desliga | sensor da baia ≤ 4,0 °C (histerese de 2 K) |
| Corte contra congelamento | ≤ 2,0 °C: desliga e só religa acima de 4,0 °C. O setpoint aceito pelo firmware fica entre 3,0 e 7,0 °C |
| Tempo mínimo ligado / desligado | 60 s / 120 s |
| Alarme de temperatura | fora de 2–8 °C por mais de 10 min seguidos (abrir a porta aquece o ar por pouco tempo) |
| Corte por sensor | leitura com erro de CRC, sensor ausente, abaixo de −20 °C ou acima de 60 °C: Peltier desligadas e alarme |
| Corte do lado quente (software) | DS18B20 em qualquer cooler acima de 60 °C: desliga as duas Peltier |
| Corte do lado quente (hardware) | fusível térmico de 85 °C em série com cada Peltier, **encostado na base do cooler** com pasta térmica, coberto com termo-retrátil (o corpo dele é ligado eletricamente a um dos terminais) e preso com abraçadeira de metal. Terminais emendados com **luva de crimpar**, sem solda. Trabalho esperado: ~46 °C no pior caso [calc] |
| Durante o pulso da trava | as duas Peltier desligadas (intertravamento, ver 1.4) |

## 1.2 Coolers do lado de fora da lateral esquerda

`python calculos/coolers_externos.py`

- **Cooler:** Cooler Master Hyper 212 Spectrum V3, com **124 × 73 × 152 mm**, ventoinha de 120 × 120 × 25 mm 12 V 0,26 A e 0,65 kg [ds KaBuM, 22/10]. Não há cooler de PC velho, então são comprados os dois.
- **Posição** [calc]:
  - Base encostada na face de fora da lateral esquerda, heat pipes para fora.
  - Cooler 1 em Y 98–222 e cooler 2 em Y 268–392, os dois em Z 238–336. Saem **153 mm** para o lado.
  - O bloco da dobradiça vai até Y 37: sobram 61 mm até o primeiro cooler.
- **Apoio (não depende da lateral só pelos parafusos da Peltier):**
  - Cada cooler fica num **berço** cortado a laser: uma placa vazada (grade) por baixo da ventoinha, sustentada por duas mãos-francesas encaixadas numa placa de base.
  - A placa de base é presa na lateral por **4 parafusos M4 passantes** com arruela larga, em Z 102 e Z 200. Essas alturas são livres de corrediça (entre A1 e A2, e entre A2 e A3).
  - Conta [calc]: peso de 7,8 N com o berço; momento de 0,60 N·m; tração de 3,1 N em cada parafuso de cima; corte de 2,0 N por parafuso. Muito abaixo do que um M4 com arruela larga segura em MDF de 3 mm.
- **Sentido do ar:**
  - A ventoinha fica **embaixo** do bloco de aletas e **sopra para cima**.
  - O ar entra por baixo, pela grade do berço e por um vão de 12 mm entre a grade e a ventoinha. Sai livre por cima, no ar da sala.
  - Ar quente subindo do lado de fora não passa por nenhuma eletrônica: a caixa da eletrônica fica no tampo, afastada da lateral esquerda.
- **Cuidado de segurança:** a ventoinha fica protegida por baixo pela grade do berço. Por cima, as aletas ficam expostas e mornas (~46 °C [calc]).
- **A porta abre até 90°**, para o lado oposto aos coolers (para a frente). A checagem de colisão da Fase 5 confere a porta a 0°, 45° e 90°.

## 1.3 Mega alimentado pela USB do notebook

**Decisão: sim, o Mega é alimentado pela USB do notebook, e o Vin fica desligado.**

| Critério | USB do notebook | Vin a 12 V (como estava) |
|---|---|---|
| Queda de energia de ~15 s (RNF07.1) | O Mega continua ligado pela bateria do notebook e registra a queda | O Mega reinicia junto com a fonte |
| Regulador do Mega | Não é usado | Dissipa (12 − 5) × ~0,3 A ≈ 2 W [calc], esquenta demais |
| Corrente disponível | 500 mA (fusível do Mega e porta USB 2.0 [ds Arduino]); consumo previsto ~0,3 A [est] → [medir] | Limitada pelo regulador |
| Sem notebook | Precisa de um carregador USB de celular (5 V, 1 A) como reserva | Funciona sozinho |

Cuidados:
- Os relés continuam alimentados pelo LM2596, nunca pelo 5 V do Mega (0,21 A só das bobinas).
- O GND do Mega vai ao GND do módulo de relés **por um fio só** (ponto único de terra), e nenhuma corrente de carga passa pelo Mega. Não vale a pena isolar pelo jumper JD-VCC do módulo: o divisor que mede o 12 V já precisa do terra comum.
- O Mega mede o 12 V por um divisor (4,7 kΩ / 2,2 kΩ → 3,8 V numa entrada analógica). Assim registra "falta de energia" e "energia voltou" no log de auditoria.
- A abertura da porta serial reinicia o Mega (DTR). O firmware inicia com tudo desligado e só libera a trava com um comando novo (item 4 da auditoria).

## 1.4 Energia: pior caso na fonte de 10 A

| Carga (12 V) | Corrente | Origem |
|---|---:|---|
| 2 × TEC1-12703, partida | 6,10 A | [calc] 12 V / 3,93 Ω cada |
| 2 × ventoinha do Hyper 212 | 0,52 A | [ds KaBuM] |
| 2 × ventoinha 60 mm do lado frio | 0,36 A | [ds Eletrogate, 180 mA] |
| Trava FE-91 | 0,50 A (2,0 A se a bobina medir ~6 Ω) | [ds Eletrogate] / [medir] |
| LM2596 → relés | ~0,10 A | [calc] |
| **Tudo junto, sem intertravamento** | **7,6 A** (9,1 A com a trava de 2 A) | [calc] |
| **Com intertravamento** | **7,1 A** | [calc] |

- **Intertravamento obrigatório no firmware.** Antes de energizar a trava, o firmware desliga os relés das duas Peltier. Elas só voltam depois que a trava é desligada (pulso de no máximo 3 s). Isso também conta como tempo desligado na histerese.
- **Partida escalonada:** as duas Peltier nunca ligam no mesmo instante; a segunda liga 2 s depois da primeira.
- Margem de 29% na fonte de 10 A, mesmo com uma trava de 2 A.
- As ventoinhas dos coolers ficam **ligadas direto no 12 V** (sempre giram com a fonte ligada), então nenhuma Peltier funciona sem ventoinha.
- Fios: as Peltier ficam a ~1,2 m da caixa da eletrônica. Em 1,5 mm², a queda de ida e volta é de 0,08 V a 3 A [calc].

## 1.5 Caixa da eletrônica no tampo

- Caixa de MDF cortada a laser (Fase 5), de ~360 × 250 × 95 mm, em cima do tampo, atrás da câmera externa.
- Dentro ficam a fonte, F1, F2, o módulo de relés, o LM2596, o Mega e os conectores de alavanca.
- A tampa é parafusada. Há rasgos de ventilação nas laterais e um furo com passa-fio para cada grupo de cabos.
- **Se a fonte for a colmeia, a caixa é a proteção dos terminais de 127/220 V.** A caixa só pode ser aberta com a fonte fora da tomada.
- O cabo de força sai pela traseira da caixa. O USB do Mega vai direto ao notebook.

## 1.6 Componentes da porta escolhidos

| Peça | Modelo | Medidas usadas no projeto | Origem |
|---|---|---|---|
| Dobradiça | Dobradiça contínua tipo piano, aço bicromatizado, 3 m, 25 mm de largura aberta, furos intercalados a cada 73 mm | 25 mm aberta; passo de 73 mm. Espessura da aba, Ø do furo e Ø do pino: [medir] no cupom | [ds Amazon B0FZLKCS2P, 22/10] |
| Leitor de digital | AS608 (MakerHero) | Módulo 44 × 23 × 20 mm; janela de leitura 15 × 21 mm; 3,8–7 V; < 60 mA | [ds MakerHero, 22/10] |
| LCD | 16x2 HD44780 (o do grupo) | Placa 80 × 36 mm, furos a 75 × 31 mm, moldura 71 × 24 mm, área visível 64,5 × 14,5 mm | [ds padrão 1602A] → conferir no cupom |
| Teclado | Membrana 4x4 (o do grupo) | 69 × 77 mm, cabo flat de ~20 mm de largura | [ds padrão] → conferir no cupom |

A dobradiça é cortada no comprimento com serra de arco. Os 2,1 m que sobram dão para um pedaço de teste no cupom.

## Ainda em aberto

1. A fonte colmeia chegou? Se não chegou, comprar a fonte fechada (linha condicional da lista).
2. Há uma segunda webcam? Se não houver, comprar a Fortrek (linha condicional).
3. Medidas da trava FE-91 (corpo e furos de fixação) e do reed MC-38: medir quando chegarem e ajustar `hardware/layout.py`.
