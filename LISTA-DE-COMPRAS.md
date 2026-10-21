# Lista de compras

rogi: Tudo o que falta comprar para a tranca e as duas gavetas frias, com o link do produto exato. A parte da porta o grupo já tem desde 21/10: Arduino Mega, LCD, teclado e buzzer. Protoboard, jumpers, potenciômetro e resistor costumam vir no kit, então confiram antes.

rogi: Links e preços conferidos em 21/10/2026. Preço muda toda semana e estoque acaba, então olhem de novo na hora de fechar o carrinho. Se um item sumir, a coluna "o que procurar" diz o que serve no lugar.

## Já temos

| Peça | Observação |
|---|---|
| Arduino Mega 2560 + cabo USB | |
| Display LCD 16x1, sem I2C | Potenciômetro de 10 kΩ e resistor de 220 Ω vêm do kit |
| Teclado de membrana 4x4 | |
| Buzzer | Conferir se é ativo: ligado direto em 5 V e GND, ele apita sozinho |

## Carrinho 1: Eletrogate

rogi: Seis itens na mesma loja, um frete só.

| Qtd | Peça | Link | Preço (21/10) | O que procurar se acabar |
|---|---|---|---|---|
| 1 | Mini trava elétrica solenoide FE-91, 12 V 0,5 A | [eletrogate.com/mini-trava-eletrica-solenoide](https://www.eletrogate.com/mini-trava-eletrica-solenoide) | R$ 48,90 | Trava 12 V de **lingueta chanfrada** (a que tem um lado inclinado), nunca a de pino reto |
| 1 | Módulo relé 4 canais 5 V com optoacoplador, 10 A | [eletrogate.com/modulo-rele-4-canais-5v](https://www.eletrogate.com/modulo-rele-4-canais-5v) | R$ 22,90 | Relé 5 V, contato 10 A, que **liga com sinal LOW** (esse liga) |
| 1 | Regulador step-down LM2596 | [eletrogate.com/modulo-regulador-de-tensao-step-down-lm2596](https://www.eletrogate.com/modulo-regulador-de-tensao-step-down-lm2596) | R$ 8,90 | Qualquer LM2596 que receba 12 V e ajuste para 5 V |
| 1 | Porta-fusível de meio de fio 5x20 | [eletrogate.com/porta-fusivel-meio-de-fio-5x20](https://www.eletrogate.com/porta-fusivel-meio-de-fio-5x20) | R$ 1,90 | Porta-fusível 5x20 de meio de fio |
| 2 | Fusível de vidro 5x20 **10 A** (1 de reserva) | [eletrogate.com/fusivel-de-vidro-5x20-10a](https://www.eletrogate.com/fusivel-de-vidro-5x20-10a) | R$ 0,35 cada | Fusível 5x20 de 10 A |
| 1 pct | Diodo 1N4007 (pacote com 10) | [eletrogate.com/diodo-retificador-1n4007-10-unidades](https://www.eletrogate.com/diodo-retificador-1n4007-10-unidades) | R$ 1,00 | Qualquer 1N4004 a 1N4007 |
| 1 pct | Jumpers macho-fêmea 20 cm (pacote com 40) | [eletrogate.com/jumpers-macho-femea-40-unidades-de-20-cm](https://www.eletrogate.com/jumpers-macho-femea-40-unidades-de-20-cm) | R$ 8,60 | Pular se o kit do grupo já tiver. Ligam Mega 8, 9 e 10 nos IN dos relés |

**Subtotal:** R$ 92,90 + frete.

rogi: Sobre os relés: o módulo de 4 canais sai mais barato que três de 1 canal e já vem numa placa só, então é o que vale comprar. Só três canais são usados (trava, gaveta C1 e gaveta C2), e o quarto fica sobrando. Se ainda assim comprarem módulos de 1 canal, precisam ser três, todos de 5 V com contato de 10 A, com o jumper `H/L` em **L**.

## Carrinho 2: Usinainfo

| Qtd | Peça | Link | Preço (21/10) | O que procurar se acabar |
|---|---|---|---|---|
| 1 | Fonte chaveada colmeia 12 V **10 A** 120 W, bivolt automática | [usinainfo.com.br/…/fonte-chaveada-colmeia-12v-10a-120w-bivolt](https://www.usinainfo.com.br/fonte-colmeia/fonte-chaveada-colmeia-12v-10a-120w-bivolt-fn12012-2610.html) | R$ 61,55 no Pix | Fonte colmeia 12 V de 10 A ou mais |
| 1 | Cabo de força tripolar 1,8 m 10 A | [usinainfo.com.br/…/cabo-de-forca-tripolar](https://www.usinainfo.com.br/outros-cabos/cabo-de-forca-tripolar-16m-250v-10a-c13-8038.html) | conferir | Qualquer cabo de força com plugue de tomada. A ponta de encaixe (C13) é cortada e os 3 fios vão nos parafusos L, N e terra da fonte |
| 2 | Dissipador de alumínio 65 × 46 × 24 mm | [usinainfo.com.br/…/dissipador-65x46x24mm](https://www.usinainfo.com.br/dissipador-de-calor/dissipador-de-calor-em-aluminio-65x46x24mm-6181.html) | ~R$ 9 cada | **Melhor ainda: o dissipador de processador de um PC velho** (só o metal). Qualquer alumínio maior que 40 × 40 mm serve, quanto maior melhor |
| 1 | Pasta térmica | [usinainfo.com.br/pasta-termica-343](https://www.usinainfo.com.br/pasta-termica-343) | ~R$ 10 | Qualquer pasta térmica de processador |

## Avulsos

| Qtd | Peça | Link | Preço (21/10) | O que procurar se acabar |
|---|---|---|---|---|
| 2 | Pastilha Peltier **TEC1-12703 40 × 40 mm** | [mixtou.com.br/…/tec1-12703-40x40mm](https://www.mixtou.com.br/pastilha-termoeletrica-peltier-tec1-12703-40x40mm-15-5v-27w-1/p) | R$ 41 a 51 cada | TEC1-12703 de **40 × 40**. A de 30 × 30 não tampa o furo de 38 mm |
| 1 | Serra copo 38 mm Stamaco (madeira, encaixa em furadeira comum) | [leroymerlin.com.br/serra-copo-bi-metal-38mm-1355-stamaco](https://www.leroymerlin.com.br/serra-copo-bi-metal-38mm-1355-stamaco_91032263) | conferir | Pular se alguém do grupo já tiver uma |
| 3 m + 3 m | Cabo flexível 1,5 mm², vermelho e preto | loja de material elétrico do bairro, vendido por metro | ~R$ 2 o metro | Fonte, fusível, COM dos relés, Peltier e GND. Rolo de 100 m não compensa. Fio de jumper não aguenta a corrente da Peltier |
| 5 m + 5 m | Cabo flexível 0,5 mm², vermelho e preto | mesma loja, por metro | ~R$ 1 o metro | Trava, buzzer, LM2596, 5 V dos relés e Vin/GND do Mega |
| 2 × 2,5 m | Cabo de rede (UTP Cat5e, 8 fios) | mesma loja ou de informática, por metro | ~R$ 2 o metro | Um para o teclado, um para o LCD, da porta até o fundo falso. Cabo velho de internet serve, cortando os plugues |
| — | Termo-retrátil, fita isolante, abraçadeiras | qualquer loja | R$ 10 a 20 | |

**Total estimado:** de R$ 320 a R$ 380 somando tudo, sem frete.

rogi: Este é o kit sem cooler, decidido em 16/10. A TEC1-12703 puxa uns 3 A e solta metade do calor da 12706, por isso o dissipador sem ventoinha dá conta por mais tempo e a fonte de 10 A sobra: duas pastilhas (6 A), a trava (0,5 A) e o Mega com os relés (menos de 0,5 A) somam uns 7 A. O fusível de 10 A fica acima disso e abaixo do limite da fonte. O frio é fraco, mas mostra o funcionamento. Liguem só pelo tempo da demonstração. Se a mão não aguentar ficar encostada no dissipador, desliguem.

rogi: Não tem bornes (decisão de 19/10, por tempo e dinheiro). O 12 V passa de um COM do relé para o outro e o GND vai direto nos parafusos V− da fonte, dois fios por parafuso. O passo a passo está em `docs/LIGACOES.md`.

## Cuidados

- **A fonte colmeia tem os terminais da tomada (127/220 V) expostos.** Ligar o cabo de força com ela desligada da tomada e não encostar neles com ela ligada. Na primeira vez, de preferência com o professor junto.
- **Nunca ligar a Peltier sem o dissipador preso nela, com pasta térmica.** Sem cooler, ligar só pelo tempo da demonstração.
- **A trava solenoide esquenta se ficar ligada muito tempo.** O código só energiza a trava pelos segundos de abertura.
