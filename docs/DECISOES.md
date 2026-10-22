# Decisões do projeto

Cada decisão tem data, quem decidiu e de onde vêm os números. Para mudar uma decisão, acrescente uma linha nova; não apague a antiga.

## DECISÃO 1 — Arquitetura (22/10/2026, aprovada pelo grupo)

**Híbrida: Arduino Mega + notebook.**

- **Mega:** tempo real e segurança física. Cuida do teclado, do LCD, do leitor de digital AS608 (Serial1), da trava, do sensor de porta (reed), dos sensores de temperatura DS18B20, do controle da gaveta fria, do buzzer e do watchdog. Funciona sozinho se o notebook cair.
- **Notebook:** quiosque com CPF, MV simulado, registro de auditoria (SQLite), gravação das 2 webcams e painel da logística. Reaproveita o software do legado, com uma camada nova (`hal/serial_mega.py`) que conversa com o Mega pela USB.

Descartadas: "só o Mega" (deixa RF03, RF04, RF07 e RF10, que são Must, sem atender) e "Raspberry Pi do legado" (~R$ 2.800 e prazo apertado). Comparação completa em `docs/AUDITORIA.md`.

## 1.1 Gaveta fria

### Opções comparadas

`python calculos/gaveta_fria.py` (mesmo modelo térmico do legado, com a TEC1-12703, medidas do `config.py`, 6 aberturas por hora). Temperatura mínima que a baia consegue manter com a Peltier ligada o tempo todo:

| Baia | Pastilhas | Isolamento | Bandeja útil (L × A × P) | Volume | 25 °C | 28 °C | 32 °C |
|---|---:|---|---|---:|---:|---:|---:|
| C2 (coluna C, em cima) | 1 | XPS 25 mm | 100 × 136 × 387 mm | 5,3 L | 9,6 | 12,3 | 15,9 ❌ |
| C2 | 1 | XPS 40 mm | 70 × 106 × 357 mm | 2,6 L | 3,4 | 6,0 | 9,5 ❌ |
| C2 | 1 | XPS 50 mm | 50 × 86 × 337 mm | 1,4 L | −0,4 | 2,1 | 5,4 |
| A3+A4 (coluna A, em cima) | 1 | XPS 50 mm | 231 × 86 × 337 mm | 6,7 L | 7,7 | 10,3 | 13,9 ❌ |
| A3+A4 | 2 | XPS 40 mm | 251 × 106 × 357 mm | 9,5 L | 0,7 | 3,3 | 6,7 |
| **A3+A4** | **2** | **EPS 50 mm** | **231 × 86 × 337 mm** | **6,7 L** | **−0,4** | **2,1** | **5,5** |

As resistências térmicas dos coolers são estimativas [est] e serão medidas na bancada. O EPS escolhido tem 10 kg/m³; usamos condutividade 0,044 W/m·K [est]. O XPS seria um pouco melhor, mas não foi encontrado à venda em loja brasileira com link conferido.

### Escolha

**Baia fria fixa no lugar das gavetas A3 e A4 (coluna A, metade de cima), com as duas TEC1-12703 que o grupo já tem e isolamento de EPS de 50 mm em todas as faces.**

- **Por quê:** é a única opção com espaço útil de verdade que ainda segura 2–8 °C num dia de 32 °C. A bandeja tem 231 × 86 × 337 mm. Cabem ~100 frascos de 10 mL em pé (Ø ~25 mm, ~50 mm de altura [est]: 9 × 13), ou canetas deitadas. A C2 com 50 mm só tem 1,4 L, uns 25 frascos.
- **O que muda no armário:** as gavetas A3 e A4 já cortadas ficam de reserva, e as corrediças delas não são instaladas. A1 e A2 continuam normais embaixo. Nenhuma peça cortada é recortada. Em peças já cortadas só entram dois furos quadrados de 40 mm, feitos à mão no fundo falso, e os furos de ventilação do traseiro.
- **Medidas da baia** [calc, `config.py`]: X 3 a 346, Z 201 a 399, Y 0 a 494. Por dentro do EPS: 243 × 98 × 394 mm.
- **Como abre:** é uma **baia fixa** com **tampa frontal isolada** e **bandeja deslizante**, sem corrediça.
  1. Abre-se a porta do armário.
  2. Tira-se a tampa, um bloco de EPS de 50 mm colado atrás de uma frente de MDF de 3 mm, com fita de espuma em volta e uma alça.
  3. Puxa-se a bandeja de MDF, que corre sobre uma placa de MDF apoiada no EPS do piso.
  Por que não corrediça: a corrediça metálica atravessaria o isolamento, levando calor para dentro, e não cabe com 50 mm de EPS dos lados. Tampa por cima não dá, porque há o teto do gaveteiro.
- **Piso da baia:** placa de MDF 343 × 494 apoiada em sarrafos colados na lateral esquerda e na divisória A/B, a 198–201 mm. Será cortada a laser junto com a porta (Fase 5).
- **Peltier:** duas, nos centros X = 110 e X = 240, Z = 300, em furos quadrados de 40 × 40 mm no fundo falso. Cada uma é presa entre o cooler (no vão de trás) e um espaçador de alumínio de 38,1 × 38,1 × 50 mm, que atravessa o EPS do fundo da baia até o dissipador frio 65 × 46 × 24 (um dos dois já comprados) com ventoinha de 60 mm.

### Controle de temperatura (vai para o firmware na Fase 3)

| Parâmetro | Valor |
|---|---|
| Setpoint | 5,0 °C |
| Faixa aceitável | 2,0 a 8,0 °C |
| Liga as Peltier | sensor da baia ≥ 6,0 °C |
| Desliga | sensor da baia ≤ 4,0 °C (histerese de 2 K) |
| Corte contra congelamento | ≤ 2,0 °C: desliga e só religa acima de 4,0 °C, mesmo que o setpoint seja mudado para baixo. O setpoint aceito pelo firmware fica entre 3,0 e 7,0 °C |
| Tempo mínimo ligado / desligado | 60 s / 120 s |
| Alarme de temperatura | fora de 2–8 °C por mais de 10 min seguidos (abrir a porta aquece o ar por pouco tempo) |
| Corte por sensor | leitura com erro de CRC, sensor ausente, abaixo de −20 °C ou acima de 60 °C: Peltier desligada e alarme |
| Corte do lado quente (software) | DS18B20 no cooler acima de 60 °C: desliga as Peltier |
| Corte do lado quente (hardware) | fusível térmico de 85 °C em série com cada Peltier, preso na base do cooler. Expectativa de trabalho: ~48 °C no pior caso [calc] |
| Durante o pulso da trava | Peltier desligadas (intertravamento de energia, ver 1.4) |

O dissipador frio pode passar de 0 °C (calculado −5 °C a 32 °C de ambiente) com o ar da baia a 5 °C. Pode formar gelo fino nas aletas, que derrete no tempo desligado. A água pinga numa bandejinha com papel absorvente embaixo do dissipador frio.

## 1.2 Coolers no vão de trás e ventilação

`python calculos/vao_de_tras.py`

- **Cooler:** Cooler Master Hyper 212 Spectrum V3, com **124 × 73 × 152 mm**, ventoinha 120 × 120 × 25 mm 12 V 0,26 A e 0,65 kg [ds KaBuM, 22/10].
- **Encaixe:** o vão de trás tem 200 mm (Y 497 a 697). A base do cooler encosta no fundo falso; pastilha (metade no furo) + cooler = 154 mm. **Sobram 46 mm até o traseiro.** [calc]
- **Posição:** cooler 1 em X 48–172, cooler 2 em X 178–302 (6 mm entre eles), os dois em Z 238–336. Ficam de lado, com os heat pipes apontando para trás e a ventoinha embaixo do bloco de aletas, soprando para cima.
- **Apoio:** 0,65 kg em balanço numa chapa de 3 mm é demais só com os parafusos da pastilha. Cada cooler leva um calço de MDF (2 camadas de sobra coladas) entre a borda de baixo do bloco de aletas e o fundo falso, sem tapar a ventoinha. A Fase 2 detalha.
- **Calor a tirar:** 2 × 35,5 W + 6 W das ventoinhas ≈ **78 W** [calc]. Para o ar subir só 5 K são precisos **13 L/s (47 m³/h)**.
- **Furos de ventilação no traseiro**, com a serra copo de 38 mm que já está na lista antiga. Medidas olhando o armário **de frente**, a partir do canto de baixo à esquerda:

| Função | Centros em X (mm) | Centros em Z (mm) | Quantidade | Área |
|---|---|---|---:|---:|
| Entrada de ar (embaixo dos coolers) | 75, 135, 215, 275 | 164 e 218 | 8 | 91 cm² |
| Saída de ar (em cima dos coolers) | 75, 135, 215, 275 | 382 e 436 | 8 | 91 cm² |

  A área mínima por lado é 87 cm² (até 1,5 m/s no furo). A menor alma de MDF entre furos é de 17 mm, e o furo mais próximo fica a 113 mm do furo do cabo de força. Como os furos são feitos pela parte de trás, **a medida em X fica espelhada**: medida pela face de fora do traseiro, a coluna de 75 mm fica a 880 − 75 = 805 mm da borda esquerda de quem olha por trás. A Fase 2 vai gerar um gabarito de papel em escala 1:1.
- **Nada embaixo dos coolers:** a região X 48–302, Z 3–238 do vão de trás fica livre para o ar entrar. Fonte, Mega e relés vão para o lado direito do vão.

## 1.3 Mega alimentado pela USB do notebook

**Decisão: sim, o Mega é alimentado pela USB do notebook, e o Vin fica desligado.**

| Critério | USB do notebook | Vin a 12 V (como estava) |
|---|---|---|
| Queda de energia de ~15 s (RNF07.1) | O Mega continua ligado pela bateria do notebook e registra a queda | O Mega reinicia junto com a fonte |
| Regulador do Mega | Não é usado | Dissipa (12 − 5) × ~0,3 A ≈ 2 W [calc], esquenta demais |
| Corrente disponível | 500 mA (fusível do Mega e porta USB 2.0 [ds Arduino]); consumo previsto ~0,3 A [est] → [medir] | Limitada pelo regulador |
| Sem notebook | Precisa de um carregador USB de celular (5 V, 1 A) como reserva | Funciona sozinho |
| Terra | O GND do notebook fica ligado ao GND do 12 V pelo Mega (ver abaixo) | Mesmo problema |

Cuidados:
- Os relés continuam alimentados pelo LM2596, nunca pelo 5 V do Mega (0,21 A só das bobinas).
- Se o módulo de relés tiver o jumper **JD-VCC** (a página da Eletrogate não diz; olhar a placa), o lado do Mega e o lado de 12 V ficam isolados pelos optoacopladores. Nesse caso: tirar o jumper, ligar JD-VCC no LM2596 e VCC no 5 V do Mega. Sem o jumper, o GND do Mega vai ao ponto de terra único do 12 V **por um fio só**, e nenhuma corrente de carga passa pelo Mega.
- O Mega mede o 12 V por um divisor (4,7 kΩ / 2,2 kΩ → 3,8 V numa entrada analógica). Assim registra "falta de energia" e "energia voltou" no log de auditoria.
- A abertura da porta serial reinicia o Mega (DTR). O firmware inicia com tudo desligado e só libera a trava com um comando novo (item 4 da auditoria).

## 1.4 Energia com a decisão final

| Carga (12 V) | Corrente | Origem |
|---|---:|---|
| 2 × TEC1-12703, partida | 6,10 A | [calc] |
| 2 × ventoinha do Hyper 212 | 0,52 A | [ds KaBuM] |
| 2 × ventoinha 60 mm do lado frio | 0,36 A | [ds Eletrogate, 180 mA] |
| Trava FE-91 | 0,50 A (2,0 A se a bobina medir ~6 Ω) | [ds Eletrogate] / [medir] |
| LM2596 → relés | ~0,10 A | [calc] |
| **Pior caso sem intertravamento** | **7,6 A** (9,1 A) | [calc] |
| **Com intertravamento** (Peltier desligadas durante o pulso da trava, ≤ 3 s) | **7,1 A** | [calc] |

Margem de 29% na fonte de 10 A, mesmo com a trava de 2 A. As ventoinhas dos coolers ficam **ligadas direto no 12 V** (sempre giram com a fonte ligada), então nenhuma Peltier funciona sem ventoinha.

## Ainda em aberto (responder ao Claude)

1. A fonte colmeia chegou? Se não chegou, comprar a fonte fechada (linha condicional da lista).
2. Alguém tem cooler de PC velho, de torre e com ventoinha de 12 V? Cada um tira um Hyper 212 da lista.
3. Há uma segunda webcam? Se não houver, comprar a Fortrek (linha condicional).
