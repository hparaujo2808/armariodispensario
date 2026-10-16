# Lista de compras

rogi: Tudo o que a eletrônica do protótipo precisa: senha, display, tranca e as duas gavetas frias. Antes de comprar, confiram o kit de Arduino do grupo. Mega, protoboard, jumpers, buzzer e às vezes o LCD e o teclado já vêm nele.

rogi: Os preços são uma faixa de referência de lojas online brasileiras, só pra ter noção do total. Mudam toda semana, então confiram na hora de comprar.

## Controle e porta

| Qtd | Peça | Para quê | Faixa (R$) |
|---|---|---|---|
| 1 | Arduino Mega 2560 R3 (compatível serve) + cabo USB | O cérebro: lê o teclado, mostra no LCD, decide quando abrir | 80 a 130 |
| 1 | Display LCD 16x2 **com módulo I2C já soldado** (PCF8574) | Mostra `Digite a senha` e os `*` na porta | 25 a 40 |
| 1 | Teclado matricial de membrana 4x4 | O pinpad da porta | 8 a 15 |
| 1 | Buzzer **ativo** 5 V | Bipe de tecla, de senha certa e de senha errada | 3 a 6 |

## Tranca

| Qtd | Peça | Para quê | Faixa (R$) |
|---|---|---|---|
| 1 | Trava solenoide 12 V de **lingueta chanfrada** (não a de pino reto) | Segura a porta, recolhe quando recebe 12 V e tranca sozinha quando a porta fecha | 35 a 70 |
| 2 | Diodo 1N4007 | Protege o circuito do pico de tensão quando a trava desliga (1 vai na trava, 1 é reserva) | 1 a 2 |

## Frio (duas gavetas)

| Qtd | Peça | Para quê | Faixa (R$) |
|---|---|---|---|
| 2 | Pastilha Peltier TEC1-12706 | Um lado gela, o outro esquenta. Uma por gaveta | 15 a 30 cada |
| 2 | Dissipador de alumínio, **sem cooler** (o de um processador velho serve, só o metal) | Tira o calor do lado quente. **Sem ele a pastilha queima em segundos** | 0 a 25 cada |
| 1 | Pasta térmica | Entre a pastilha e os dissipadores | 10 a 20 |

rogi: O grupo decidiu em 16/10 não comprar cooler, por dinheiro e por tempo. A pastilha continua precisando de um pedaço de alumínio no lado quente: é ele que segura o calor que ela bombeia, e uma TEC1-12706 solta uns 70 W ali. Sem ventoinha esse dissipador perde calor devagar, então o frio fica mais fraco e a pastilha deve ficar ligada só na hora de mostrar, alguns minutos. Se a mão não aguentar ficar encostada no dissipador, desliga.

## Energia e acionamento

| Qtd | Peça | Para quê | Faixa (R$) |
|---|---|---|---|
| 1 | Fonte chaveada 12 V 20 A ("fonte colmeia") | Alimenta tudo. As duas pastilhas sozinhas puxam uns 12 A | 60 a 110 |
| 1 | Cabo de força com plugue de tomada | A fonte colmeia não vem com cabo | 10 a 20 |
| 1 | Módulo relé 4 canais 5 V, com optoacoplador, contatos de 10 A | O Arduino liga a energia forte por ele: trava, Peltier 1, Peltier 2 e 1 sobrando | 20 a 35 |
| 1 | Regulador step-down LM2596 (12 V → 5 V) | Alimenta os relés sem esquentar o regulador do Arduino | 8 a 15 |
| 1 | Porta-fusível com fusível de 15 A | Corta a linha de 12 V se der curto | 10 a 15 |

## Fios e montagem

| Qtd | Peça | Para quê | Faixa (R$) |
|---|---|---|---|
| 3 m + 3 m | Fio de 1,5 mm² (vermelho e preto) | Fonte, pastilhas e trava. Fio de jumper não aguenta a corrente da Peltier | 15 a 30 |
| 1 kit | Jumpers macho-macho e macho-fêmea | Ligações do Arduino | 15 a 25 |
| 1 | Protoboard 830 pontos | Testar antes de fixar no armário | 15 a 25 |
| 1 pacote | Bornes KF301 ou conectores Wago | Emendar os fios grossos sem solda | 10 a 15 |
| — | Termo-retrátil, fita isolante, abraçadeiras | Acabamento e segurança | 10 a 20 |

**Total estimado:** de R$ 340 a R$ 680, menos o que já vier no kit.

## Versão mais barata

rogi: Se o orçamento apertar, troquem as pastilhas por duas TEC1-12703 (uns 3 A cada) e a fonte por uma de 12 V 10 A. Sem cooler essa é a troca que mais vale a pena: a 12703 solta metade do calor da 12706, e o dissipador passivo dá conta por mais tempo. O frio fica mais fraco, mas mostra o funcionamento. O resto da lista continua igual.

## Cuidados

- **A fonte colmeia tem os bornes de tomada (127/220 V) expostos.** Conferir a chave seletora de tensão antes de ligar, ligar o cabo de força com ela desligada da tomada e não encostar nos bornes com ela ligada. Na primeira vez, de preferência com o professor junto.
- **Nunca ligar a Peltier sem o dissipador preso nela, com pasta térmica.** Sem cooler, ligar só pelo tempo da demonstração.
- **A trava solenoide esquenta se ficar ligada muito tempo.** O código só energiza a trava pelos segundos de abertura.
