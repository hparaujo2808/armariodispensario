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
| 20 (SDA) · 21 (SCL) | LCD 16x2 I2C |
| 22 · 24 · 26 · 28 | Linhas L1 a L4 do teclado |
| 30 · 32 · 34 · 36 | Colunas C1 a C4 do teclado |
| 5V | VCC do LCD |
| Vin | 12 V da fonte (depois do fusível) |
| GND | GND comum |

O módulo de relés comum liga com nível baixo: no código, `LOW` liga e `HIGH` desliga.

## Cabos e caminhos

| Cabo | Liga | Fios | Bitola | Caminho |
|---|---|---|---|---|
| Teclado | Teclado 4x4 → Mega 22 a 36 (pares) | 8 | cabo de rede 1 | Por dentro da porta até a dobradiça, laço de folga de 15 cm por fora, furo na lateral esquerda, lateral por dentro (embaixo da prateleira de cima) até o fundo falso, furo, Arduino |
| LCD e buzzer | LCD I2C → 20, 21, 5V, GND · buzzer → 7 e GND | 6 de 8 | cabo de rede 2 | O mesmo caminho do teclado, lado a lado. Sobram 2 fios de reserva |
| Trava | Trava → NA do relé 1 e GND | 2 | 0,5 mm² | Parede direita por dentro, a 600 mm, até o fundo falso, furo, relés. Diodo 1N4007 nos terminais da trava, faixa no + |
| Peltier C1 e C2 | Pastilha → NA dos relés 2 e 3 e GND | 2 cada | 1,5 mm² | A pastilha fica no próprio fundo falso, então os fios já saem no vão de trás. Sem cooler: só dissipador de alumínio no lado quente |
| 12 V | Fonte → fusível 15 A → bornes → COM dos relés, LM2596, Vin | 1 por ramal | 1,5 mm² | Só no vão de trás |
| GND | Fonte → bornes → todos os negativos | 1 por ramal | 1,5 mm² | Só no vão de trás. GND da fonte e do Mega ligados juntos |
| 5 V dos relés | LM2596 (ajustado em 5,0 V) → VCC do módulo de relés | 1 | 0,5 mm² | Só no vão de trás |
| Controle | Mega 8, 9, 10 → IN1, IN2, IN3 | 3 | jumper | Só no vão de trás |
| Tomada | Tomada → fonte (fase, neutro, terra) | 3 | cabo de força | Furo no traseiro, embaixo à esquerda |

rogi: Não há sensor de porta. A lingueta chanfrada tranca sozinha quando a porta fecha, e quem encerra a sessão é a tecla D do teclado (ou 60 s sem apertar nada).

## Furos para fazer antes de colar

| Peça | Onde | Para |
|---|---|---|
| Lateral esquerda | 660 mm de altura, 28 mm da frente | Cabos da porta |
| Fundo falso | 660 mm, rente à esquerda | Cabos da porta |
| Fundo falso | 600 mm, rente à direita | Trava |
| Traseiro | 28 mm de altura, 95 mm da esquerda | Cabo de força |

rogi: Os furos são de 10 mm. As Peltier entram em recortes de 40 × 40 mm no fundo falso, atrás das gavetas C1 e C2. Do jeito que o manual de montagem está, o vão da eletrônica fica fechado depois da cola, então tudo isso precisa ser feito antes.

## Antes de ligar na tomada

- Conferir a chave 127/220 V da fonte.
- Ajustar o LM2596 para 5,0 V com o multímetro, sem nada ligado na saída.
- Conferir que nenhum fio de 12 V encosta no Arduino.
- Testar a trava e as Peltier primeiro sem o Arduino, ligando o relé direto (IN em GND).
