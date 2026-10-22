# Ligações

rogi: Como cada peça se liga no Arduino Mega e por onde cada fio passa dentro do armário. O diagrama mostra o circuito, as tabelas mostram os pinos e o caminho físico. A simulação 3D (`docs/simulacao.html`, botão Fios) mostra os mesmos cabos dentro da caixa.

![Diagrama de ligações](diagrama-ligacoes.svg)

O diagrama é gerado por `python docs/gerar_diagrama.py`. Para mudar um pino, mude no script e gere de novo.

## Mapa de pinos do Mega

| Pino | Liga em |
|---|---|
| 7 | Buzzer ativo (+) |
| 8 | IN1 do módulo de relés: trava solenoide |
| 9 | IN2: Peltier da gaveta C1 |
| 10 | IN3: Peltier da gaveta C2 |
| 11 | IN4: livre |
| 38 · 40 | RS e E do LCD 16x1 |
| 42 · 44 · 46 · 48 | D4, D5, D6 e D7 do LCD |
| 22 · 24 · 26 · 28 | Linhas L1 a L4 do teclado |
| 30 · 32 · 34 · 36 | Colunas C1 a C4 do teclado |
| 5V | VDD do LCD, e o A (luz de fundo) por um resistor de 220 Ω |
| Vin | 12 V da fonte (depois do fusível) |
| GND | GND comum |

O módulo de relés comum liga com nível baixo: no código, `LOW` liga e `HIGH` desliga.

rogi: O LCD é um 16x1 sem placa I2C, ligado em paralelo com 4 bits de dados (D0 a D3 ficam soltos). No próprio LCD, dentro da caixa da porta: VSS, RW e K no GND, VDD no 5V, A no 5V pelo resistor de 220 Ω e V0 no pino do meio de um potenciômetro de 10 kΩ, com as pontas dele no 5V e no GND. Se a tela ligar e não mostrar nada, gire o potenciômetro: é o contraste. Muitos 16x1 são por dentro duas metades de 8 caracteres, então o código inicia como `lcd.begin(8, 2)` e escreve os 8 primeiros caracteres na linha 0 e os 8 seguintes na linha 1. Se o de vocês mostrar só a metade esquerda, é isso.

## Cabos e caminhos

| Cabo | Liga | Fios | Bitola | Caminho |
|---|---|---|---|---|
| Teclado | Teclado 4x4 → Mega 22 a 36 (pares) | 8 | cabo de rede 1 | Por dentro da porta até a dobradiça, laço de folga de 15 cm por fora, furo na lateral esquerda, lateral por dentro (embaixo da prateleira de cima) até o fundo falso, furo, Arduino |
| LCD | LCD → 38, 40, 42, 44, 46, 48, 5V e GND | 8 de 8 | cabo de rede 2 | O mesmo caminho do teclado, lado a lado |
| Buzzer | Buzzer + → 7 (o − vai no GND do LCD, dentro da caixa da porta) | 1 | 0,5 mm² (sobra do fio da trava) | Junto dos dois cabos de rede |
| Trava | Trava → NA do relé 1 e GND | 2 | 0,5 mm² | Parede direita por dentro, a 600 mm, até o fundo falso, furo, relés. Diodo 1N4007 nos terminais da trava, faixa no + |
| Peltier C1 e C2 | Pastilha → NA dos relés 2 e 3 e GND | 2 cada | 1,5 mm² | A pastilha fica no próprio fundo falso, então os fios já saem no vão de trás. Sem cooler: só dissipador de alumínio no lado quente |
| 12 V | Fonte → fusível 10 A → COM 1 → COM 2 → COM 3, de parafuso em parafuso. No COM 3 entra também o fio do IN+ do LM2596, e o Vin do Mega sai do IN+ do LM2596 | 1 por trecho | 1,5 mm² até os COM, 0,5 mm² pro LM2596 e o Vin | Só no vão de trás |
| GND | Direto nos parafusos V− da fonte, 2 fios por parafuso: Peltier C1 e C2 no 1º, trava e IN− do LM2596 no 2º, GND do Mega no 3º | 1 por carga | 1,5 mm² (0,5 mm² pro Mega) | Só no vão de trás. GND da fonte e do Mega ligados juntos |
| 5 V dos relés | LM2596 (ajustado em 5,0 V) → VCC do módulo de relés | 1 | 0,5 mm² | Só no vão de trás |
| Controle | Mega 8, 9, 10 → IN1, IN2, IN3 | 3 | jumper | Só no vão de trás |
| Tomada | Tomada → fonte (fase, neutro, terra) | 3 | cabo de força | Furo no traseiro, embaixo à esquerda |
| Câmera | Webcam USB → notebook, fora do armário | 1 | o próprio cabo USB da webcam (+ extensor de 2 m) | Compartimento de cima até o fundo falso, furo de 16 mm, sobe no vão de trás, furo de 16 mm no traseiro, notebook |

rogi: Não há sensor de porta. A lingueta chanfrada tranca sozinha quando a porta fecha, e quem encerra a sessão é a tecla D do teclado (ou 60 s sem apertar nada).

## Furos para fazer antes de colar

| Peça | Onde | Para |
|---|---|---|
| Lateral esquerda | 660 mm de altura, 28 mm da frente | Cabos da porta |
| Fundo falso | 660 mm, rente à esquerda | Cabos da porta |
| Fundo falso | 600 mm, rente à direita | Trava |
| Traseiro | 28 mm de altura, 95 mm da esquerda | Cabo de força |
| Fundo falso | Ø 38 mm, centro a 298 mm de altura e 595 mm da esquerda | Peltier da gaveta C1 |
| Fundo falso | Ø 38 mm, centro a 101 mm de altura e 595 mm da esquerda | Peltier da gaveta C2 |
| Fundo falso | Ø 16 mm, 835 mm de altura, 440 mm da esquerda (centro) | Cabo USB da câmera |
| Traseiro | Ø 16 mm, 835 mm de altura, 440 mm da esquerda (centro) | Cabo USB da câmera |
| Porta (nova) | Ø 15 mm, 835 mm de altura, 440 mm da esquerda | Lente da câmera |

rogi: Os furos são de 10 mm, menos os dois das Peltier e os três da câmera. Os da câmera são de 16 mm (o plugue USB tem 12 mm e precisa passar) e de 15 mm na porta para a lente. Os das Peltier são de 38 mm, feitos com serra copo na furadeira. O MDF já está todo cortado, então não há recorte nenhum. A pastilha fica no vão de trás, tampando o furo (38 mm deixa 1 mm de borda pra ela vedar), com a face fria virada para a gaveta e o dissipador encostado na face quente com pasta térmica. Quem segura tudo é uma abraçadeira de nylon: dois furinhos de 5 mm, um de cada lado do furo grande, e ela laça o dissipador e aperta o conjunto contra o MDF. Um filete de cola quente na borda da pastilha veda a fresta. Medidas olhando o armário de frente. Do jeito que o manual de montagem está, o vão da eletrônica fica fechado depois da cola, então os furos precisam ser feitos antes. Se a caixa já estiver colada, dá para furar pela frente, com a gaveta tirada.

## Câmera

rogi: Uma webcam USB comum, ligada num notebook do lado de fora. Ela não conversa com o Arduino: só filma quem chega na porta, e o notebook mostra a imagem na apresentação.

| Item | Como fica |
|---|---|
| Lugar | Compartimento de cima (piso a 794 mm, uns 80 mm de vão até o tampo), encostada na frente, no meio da largura |
| Para onde olha | Para fora, para quem está na frente do teclado. Com a porta fechada, enxerga por um furo de 15 mm na porta, a 835 mm de altura; com a porta aberta, vê direto |
| Fixação | Fita dupla face ou abraçadeira no piso do compartimento, com a lente alinhada ao furo da porta e a 1 ou 2 cm dele |
| Cabo | Corre pelo piso do compartimento até o fundo falso, passa por um furo de 16 mm, cruza o vão de trás e sai por um furo de 16 mm no traseiro, na mesma altura. Se não alcançar o notebook, um extensor USB de 2 m resolve |
| Energia | Vem pelo próprio USB do notebook. Nada da fonte de 12 V |

rogi: Os furos da câmera podem ser feitos com a caixa já colada: o do fundo falso pela frente, com a porta aberta e a mão dentro do compartimento de cima; o do traseiro por fora. Antes de furar a porta, ponham a webcam no lugar, liguem no notebook e marquem o furo onde a lente fica centralizada na imagem.

## Antes de ligar na tomada

- Conferir a chave 127/220 V da fonte.
- Ajustar o LM2596 para 5,0 V com o multímetro, sem nada ligado na saída.
- Conferir que nenhum fio de 12 V encosta no Arduino.
- Onde dois fios dividem um parafuso, torcer as pontas juntas (8 mm descascados), apertar e puxar cada fio com a mão. Se um sair, apertar de novo.
- Testar a trava e as Peltier primeiro sem o Arduino, ligando o relé direto (IN em GND).
