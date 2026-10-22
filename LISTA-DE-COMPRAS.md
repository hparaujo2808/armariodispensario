# Lista de compras — o que falta (versão final de 22/10)

Preços no Pix e links conferidos em **22/10/2026**. Preço e estoque mudam: confiram de novo na hora de fechar o carrinho. Várias páginas da Usinainfo mostram "Últimas unidades". O porquê de cada escolha está em `docs/DECISOES.md`.

Esta versão já considera o **pior caso de montagem** (armário todo colado): os coolers ficam do lado de fora da lateral esquerda e a eletrônica numa caixa em cima do tampo.

## Já temos (não comprar)

| Peça | Vai servir para |
|---|---|
| Arduino Mega 2560 + cabo USB | Controle. Alimentado pela USB do notebook |
| LCD 16x2 paralelo, potenciômetro 10 kΩ, resistor 220 Ω | Mensagens na porta |
| Teclado de membrana 4x4 | Senha |
| Buzzer ativo | Reserva. O alarme passa a ser o buzzer passivo (volume ajustável, RNF10) |
| Webcam (de alguém do grupo) | Câmera externa (quem abre) |
| Notebook | Quiosque, auditoria, gravação |
| Comprados em 21/10 (lista antiga em `legado/`): trava FE-91, módulo de relés de 4 canais, LM2596, porta-fusível e fusíveis de 10 A, diodos 1N4007, jumpers, dissipadores 65×46×24 (2), pasta térmica, extensor USB, 2 × TEC1-12703, serra copo 38 mm, fios de 1,5 e 0,5 mm², 2 cabos de rede, termo-retrátil, fita isolante, abraçadeiras | Tudo continua em uso. Os dissipadores 65×46×24 vão para o **lado frio**, com ventoinha. O termo-retrátil isola o corpo do fusível térmico |

## Carrinho 1 — Eletrogate (Belo Horizonte, tem entrega por moto)

| Qtd | Peça | Para quê | Link | Pix |
|---:|---|---|---|---:|
| 2 | Ventoinha 12 V 60×60×10 mm, 180 mA | Circula o ar dentro da baia fria, uma por dissipador frio | [link](https://www.eletrogate.com/cooler-ventoinha-dc-12v-60x60x10mm) | 20,22 |
| 1 | Buzzer passivo 5 V | Alarme de volume ajustável por PWM (RNF10) | [link](https://www.eletrogate.com/buzzer-passivo-5v) | 1,80 |
| 1 | Porta-fusível de meio de fio 5×20 | Fusível do ramo fino (trava, LM2596, ventoinhas dos coolers) | [link](https://www.eletrogate.com/porta-fusivel-meio-de-fio-5x20) | 1,80 |
| 2 | Fusível de vidro 5×20 **2 A** (1 de reserva) | Protege os fios de 0,5 mm² | [link](https://www.eletrogate.com/fusivel-de-vidro-5x20-2a) | 0,76 |
| 1 pct | Resistor 4,7 kΩ (10 un.) | Pull-up dos DS18B20 e divisor que mede o 12 V | [link](https://www.eletrogate.com/resistor-4k7-1-4w-10-unidades) | 0,86 |
| 1 pct | Resistor 2,2 kΩ (10 un.) | Divisor do 12 V e divisor do RX do leitor de digital | [link](https://www.eletrogate.com/resistor-2k2-1-4w-10-unidades) | 0,86 |
| 1 pct | Resistor 1 kΩ (10 un.) | Divisor do RX do leitor e resistor do buzzer | [link](https://www.eletrogate.com/resistor-1k-1-4w-10-unidades) | 0,86 |
| | | | **Subtotal** | **27,16** |

## Carrinho 2 — Usinainfo

| Qtd | Peça | Para quê | Link | Pix |
|---:|---|---|---|---:|
| 3 | Sensor DS18B20 à prova d'água, cabo 90 cm | 1 no ar da baia fria, 1 na base de cada cooler | [link](https://www.usinainfo.com.br/sensor-de-temperatura/sensor-de-temperatura-ds-18b20-a-prova-d-agua-2645.html) | 26,97 |
| 1 | Sensor magnético MC-38 (reed + ímã), NA | Porta aberta/fechada (RF05, RF09, RNF03) | [link](https://www.usinainfo.com.br/outros-sensores/sensor-magnetico-na-de-sobrepor-com-fios-2510.html) | 11,39 |
| 4 | Fusível térmico 85 °C 10 A (2 de reserva) | Corta a Peltier por hardware se o cooler parar. Não é rearmável: se queimar, troca | [link](https://www.usinainfo.com.br/fusivel-termico/fusivel-termico-85c-10a-250v-5054.html) | 8,32 |
| 2 kits | Conector de alavanca 3 vias 32 A (5 un.) | Barramento 12 V e GND sem solda | [link](https://www.usinainfo.com.br/conectores-e-adaptadores/conector-de-emenda-rapida-com-alavancas-3-vias-32a-250v-kit-com-5-unidades-5817.html) | 24,98 |
| 1 kit | Conector de alavanca 2 vias 32 A (5 un.) | Emendas simples | [link](https://www.usinainfo.com.br/conectores-e-adaptadores/conector-de-emenda-rapida-com-alavancas-2-vias-32a-250v-kit-com-5-unidades-5818.html) | 9,38 |
| 2 | Conector de alavanca em linha 4 vias 32 A | Ponto único de 12 V e ponto único de GND | [link](https://www.usinainfo.com.br/conectores-e-adaptadores/conector-de-emenda-rapida-em-linha-com-alavancas-4-vias-32a-600v-8641.html) | 13,58 |
| | | | **Subtotal** | **94,62** |

## Carrinho 3 — MakerHero

| Qtd | Peça | Para quê | Link | Pix |
|---:|---|---|---|---:|
| 1 | Leitor de digital AS608 (UART, 240 digitais, 3,8–7 V, < 60 mA, módulo 44 × 23 × 20 mm) | Biometria (RF01). A digital fica guardada no leitor (LGPD). A porta é projetada com estas medidas | [link](https://www.makerhero.com/produto/modulo-leitor-de-impressao-digital/) | 113,90 |

## Carrinho 4 — KaBuM

| Qtd | Peça | Para quê | Link | Pix |
|---:|---|---|---|---:|
| 2 | Cooler Master Hyper 212 Spectrum V3 (124 × 73 × 152 mm, ventoinha 12 V 0,26 A, 0,65 kg) | Lado quente das 2 Peltier, por fora da lateral esquerda | [link](https://www.kabum.com.br/produto/532493) | 139,98 |

## Carrinho 5 — Isolamento

| Qtd | Peça | Para quê | Link | Pix |
|---:|---|---|---|---:|
| 1 pct | Placa de EPS 50 mm, 50 × 100 cm (5 placas, 10 kg/m³) — Magalu | Isolamento da baia fria (~0,5 m²; sobra para errar) | [link](https://www.magazineluiza.com.br/5-placas-de-isopor-antichamas-espessura-50mm-5cm-forro-termico-acustico-eps-envio-imediato-isopro-solucoes-em-eps/p/ab7j4fcg1a/cj/paac/) | 58,41 |
| 1 | Fita adesiva metalizada 48 mm × 50 m — Telhanorte | Fecha as emendas do EPS (barreira de vapor) | [link](https://www.telhanorte.com.br/fita-adesiva-metalizada-48mmx50m-brasfoil-1770403/p) | 19,90 (cartão) |
| | | | **Subtotal** | **78,31** |

## Carrinho 6 — Porta e ligações

| Qtd | Peça | Para quê | Link | Preço |
|---:|---|---|---|---:|
| 1 | Dobradiça contínua tipo piano, aço bicromatizado, **3 m**, 25 mm aberta, furos a cada 73 mm (Amazon, vendedor Multivario, 7 em estoque) | Porta: espalha a carga no MDF de 3 mm. Cortar 840 mm com serra de arco; um pedaço de 150 mm vai para o cupom de teste | [link](https://www.amazon.com.br/Dobradi%C3%A7a-Cont%C3%ADnua-Metros-Bicromatizado-Amarelo/dp/B0FZLKCS2P) | 48,90 + frete |
| 1 pct | Luva de emenda pré-isolada 0,5–1,5 mm², vermelha (100 un.) — Leroy | Emendar os fusíveis térmicos e os fios das Peltier **crimpando**, sem solda | [link](https://www.leroymerlin.com.br/luva-pre-isolada-0,50-1,50-mm2-vermelho-100-pecas_1570203278) | 38,90 + frete |
| | | | **Subtotal** | **87,80** |

## Sem link (loja de ferragens, de material elétrico ou serralheria) — preços estimados [est]

| Qtd | Peça | Para quê | Estimativa |
|---:|---|---|---:|
| 2 pedaços de 50 mm | Barra **quadrada** de alumínio maciça 1 1/2" (38,1 mm). Serve também barra chata 1 1/2" × 1/2" (38,1 × 12,7 mm) cortada em 8 pedaços de 38 mm, empilhados 4 a 4 com pasta térmica | Espaçador que leva o frio da Peltier através do EPS | ~R$ 20 |
| 1 kit | 50 parafusos M3 × 16 com porca e arruela (dobradiça e bloco da dobradiça); 30 parafusos M4 × 20 e 10 M4 × 30 com porca e arruela **larga** (berços, trava, caixa); 1 m de barra roscada M3 com 8 porcas e arruelas; 2 pedaços de 80 mm de barra chata de aço ou alumínio (~20 × 3 mm) | Tudo passante: MDF de 3 mm não segura rosca | ~R$ 40 |
| 2,5 m | Cabo de rede (UTP Cat5e, 8 fios), por metro | Terceiro cabo da porta: leitor de digital e buzzer | ~R$ 5 |
| 2 + 2 m | Cabo flexível 1,5 mm², vermelho e preto | As Peltier ficam a ~1,2 m da caixa da eletrônica | ~R$ 8 |
| 2 m | Fita de espuma EVA adesiva (perfil de vedação de porta) | Vedação da tampa da baia fria e batentes da porta | ~R$ 10 |
| 20 | Bases adesivas para abraçadeira | Prender os cabos por fora do armário até o tampo | ~R$ 15 |
| 4 chapas | MDF 3 mm 1000 × 1000 + corte a laser (porta, caixa da eletrônica, berços, piso e tampa da baia, gabaritos, cupom de teste) | Fase 5. Quantidade exata sai do gerador; confirmar preço com o fornecedor que cortou a V2 | ~R$ 140 + corte |
| | | **Subtotal estimado** | **~R$ 238** |

## Condicionais (comprar só se for o caso)

| Se… | Peça | Link | Preço |
|---|---|---|---:|
| a fonte colmeia **não chegou** | Fonte chaveada 12 V 10 A 120 W (KaBuM). A saída é plugue P4: **cortar o plugue** e ligar os fios nos conectores de alavanca, porque o P4 não é feito para 7 A | [link](https://www.kabum.com.br/produto/736865/fonte-chaveada-12v-10a-para-cftv-e-equipamentos-diversos-120w) | 94,40 |
| não houver segunda webcam | Webcam Fortrek Vision 10, 720p, UVC (sem driver no Windows e no Mac), cabo de 1,5 m (KaBuM) | [link](https://www.kabum.com.br/produto/727410/webcam-vision-10-fortrek-720p-30fps-para-videochamadas) | 66,61 |
| a faculdade não emprestar alicate de crimpar | Alicate para terminal pré-isolado (Leroy) | [link](https://www.leroymerlin.com.br/alicate-para-crimpar-terminal-pre-isolado-olhal-garfo-pino_1572113854) | 78,90 |
| o LCD falhar com os cabos longos (teste 4.1) | Módulo serial I²C para LCD (MakerHero) | [link](https://www.makerhero.com/produto/modulo-serial-i2c-para-display-lcd-arduino/) | 6,55 |

## Total

| | Valor |
|---|---:|
| Itens com preço conferido hoje (carrinhos 1 a 6) | **R$ 541,77** |
| Itens estimados, sem link | ~R$ 238 |
| **Total do que falta** | **~R$ 780 + fretes** |
| Se a fonte colmeia não chegou | + R$ 94,40 |
| Se não houver segunda webcam | + R$ 66,61 |
| Se precisar comprar o alicate | + R$ 78,90 |
| **Pior caso (os três condicionais)** | **~R$ 1.020 + fretes** |

Para economizar frete: a Eletrogate fica em BH e entrega por moto. Antes de pagar a Usinainfo, vejam se a Eletrogate tem os mesmos itens (DS18B20, MC-38, conectores de alavanca) e juntem tudo num carrinho só.

## Cuidados

- **Fonte colmeia, se for usada:** ela fica dentro da caixa da eletrônica, que é a tampa dos terminais de 127/220 V. Cabo de força preso na caixa, fio terra ligado. A primeira vez na tomada, com o professor junto. Checklist completo em `docs/SEGURANCA.md`.
- **Nunca ligar uma Peltier sem o cooler preso e girando.** As ventoinhas dos coolers ficam ligadas direto no 12 V justamente por isso.
- **Fusível térmico:** não soldar (o calor da solda queima ele). Emendar com luva crimpada e prender na base do cooler com pasta térmica e abraçadeira de metal, com termo-retrátil no corpo.
