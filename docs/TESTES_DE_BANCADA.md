# Testes de bancada

Roteiro para montar e testar a eletrônica **por partes**, do passo mais seguro ao mais arriscado. Não pule passos: cada um confere uma coisa que o próximo supõe que está certa.

**Regras para todos os passos**
- Leia `docs/SEGURANCA.md` antes do passo 2 (o primeiro que liga a fonte na tomada).
- Anote cada medição na coluna "Medido" de uma cópia impressa ou num arquivo. Os números medidos substituem os [est] e [calc] da documentação.
- Se der diferente do esperado: **pare**, desligue da tomada e siga a coluna "Se der diferente". Não passe para o próximo passo.
- Multímetro: na escala de **corrente** (10 A ou mA), as ponteiras vão em **série**. Na de **tensão**, em paralelo. Antes de medir tensão, confira que a ponta vermelha está no borne V/Ω, não no de 10 A.

## Passo 0 — Tudo desligado: conferências com o multímetro em Ω

| # | O que medir | Como | Esperado | Medido | Se der diferente |
|---|---|---|---|---|---|
| 0.1 | Bobina da trava | Ω nos dois fios da trava solta | ~24 Ω (FE-91 de 0,5 A) [calc] | | Se der ~6 Ω, a trava puxa 2 A: troque o F2 por 4 A (`hardware/potencia.yaml`) e avise antes de seguir |
| 0.2 | Peltier 1 e 2 | Ω nos fios, pastilha na mesa, parada há 5 min | 3,5 a 4,5 Ω [calc: ACR 3,88 Ω no datasheet; o multímetro DC lê um pouco diferente] | | 0 Ω = em curto; aberto = queimada. Não usar |
| 0.3 | Fusível térmico (cada) | Ω nos dois terminais | ~0 Ω (fechado) | | Aberto: já queimou, trocar |
| 0.4 | F1 e F2 | Ω no porta-fusível com o fusível dentro | ~0 Ω | | Trocar o fusível |
| 0.5 | Curto no 12 V | Ω entre B12 e GND, com as cargas ligadas e **sem** a fonte | Valor que sobe devagar (capacitores do LM2596) e passa de 1 kΩ | | Menos de 10 Ω: tem curto. Desfazer conector por conector até achar |
| 0.6 | Reed | Ω nos dois fios, com e sem o ímã encostado | Com ímã: ~0 Ω. Sem ímã: aberto | | Ao contrário: o reed é NF, não NA. Trocar ou inverter a lógica no `pinos.yaml` |
| 0.7 | Face fria da Peltier | Pastilha **sem** cooler, 5 V de um carregador USB cortado, **no máximo 2 s** | Um lado esfria, o outro esquenta | | Marque a face fria com caneta |

## Passo 1 — Fonte e LM2596 sozinhos

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 1.1 | Fonte ligada na tomada **sem nada** nos bornes de saída. Medir V+ e V− | 12,0 V (11,4 a 12,6) | | Fora disso: ajustar o trimpot da fonte (se tiver). Se não mudar, não usar a fonte |
| 1.2 | LM2596 ligado no 12 V, **sem nada na saída**. Girar o trimpot até a saída dar 5,0 V | 4,95 a 5,05 V | | Se não chega a 5 V ou não muda: módulo com defeito |
| 1.3 | Saída do LM2596 com o módulo de relés ligado (sem nenhum IN ativo) | Ainda 4,9 a 5,1 V | | Caiu muito: módulo de relés em curto ou LM2596 fraco |
| 1.4 | Proteção da fonte: **só a fonte**, sem nada ligado. Com a fonte na tomada, encostar por 1 s um fio de 1,5 mm² entre V+ e V− (o professor segura o fio; usem óculos) | A fonte corta e volta sozinha ao soltar ("hiccup"), sem cheiro nem estalo | | Não corta (a tensão não cai), aquece ou estala: **não usar essa fonte**; comprar a fechada da lista. É essa proteção que salva os fios de 0,5 mm² das ventoinhas frias (o F1 de 10 A não abre rápido com uma fonte de 10 A) |

## Passo 2 — Relés sem carga

Fonte → F1 → B12 → F2 → LM2596 → módulo de relés. **Nada** ligado nos contatos dos relés. Mega ainda desligado. Neste passo, e só nele, o jumper JD-VCC–VCC do módulo fica **no lugar** (os LEDs precisam de 5 V para o teste).

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 2.1 | Jumper do IN1 ao GND do módulo | Clique, LED aceso, COM–NA em ~0 Ω (medir com a fonte desligada e o jumper no lugar) | | Sem clique: VCC não chega ao módulo ou o módulo aciona em nível alto (conferir o jumper H/L) |
| 2.2 | Repetir para IN2, IN3 e IN4 | Igual | | |
| 2.3 | Corrente do LM2596 com 3 relés acionados (multímetro em série no 5 V) | ~0,21 a 0,25 A [ds: bobina 70 Ω] | | Bem maior: algum relé em curto |

## Passo 3 — Mega pela USB e relés no reset

**Tire o jumper JD-VCC–VCC do módulo** (DECISOES 1.3). LM2596 no JD-VCC; 5 V e GND do Mega no VCC e no GND do conector dos IN. IN1–IN4 nos pinos 8 a 11. Mega ligado pela USB do notebook. Ainda **sem carga** nos relés.

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 3.1 | Gravar o firmware (`firmware/LEIA_ME.md`). Apertar o reset do Mega 10 vezes | Nenhum relé estala | | Algum estala: o firmware faz `pinMode` antes de `digitalWrite(HIGH)`. Corrigir antes de seguir (auditoria, item 3) |
| 3.2 | Abrir e fechar o Monitor Serial 10 vezes | Nenhum relé estala | | Idem |
| 3.3 | Tirar e pôr o cabo USB 5 vezes | Nenhum relé estala | | Idem |
| 3.4 | Corrente do Mega na USB (adaptador USB com bornes ou multímetro em série no 5 V do cabo), com LCD aceso e AS608 ligado | 0,15 a 0,35 A [est] | | Acima de 0,45 A: perto do limite da USB (0,5 A). Tirar a luz de fundo do LCD do 5 V do Mega |
| 3.5 | Medir o 12 V no pino A0 (multímetro entre A0 e GND) | 3,7 a 3,9 V [calc: 12 × 2,2 / 6,9] | | Acima de 5 V: divisor invertido. **Desligar já** |
| 3.6 | Com o 12 V ligado, **tirar a USB** do Mega. Esperar 10 s. Depois pôr a USB e fechar o app (notebook "dormindo") | Nenhum relé arma, nenhum LED de relé acende | | Algum arma: o VCC dos LEDs ainda está no LM2596 (jumper JD-VCC no lugar). **Não ligar a trava nem as Peltier** até corrigir |
| 3.7 | Com a USB fora, medir a tensão no 5 V do Mega (pino 5V ao GND) | Abaixo de 1 V | | Acima: alguma ligação alimenta o Mega por trás (divisor sem o 4,7 kΩ em série, ou fio do lado de 12 V no 5 V) |

## Passo 4 — Porta: LCD, teclado, leitor, buzzer, reed

Com os cabos de rede **no comprimento final** (2,5 m), antes de passar pelo armário.

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 4.1 | LCD com texto que muda a cada 100 ms, por 5 min | Nenhum caractere errado | | Caracteres trocados: usar par trançado (cada sinal com um GND no mesmo par) ou o adaptador I²C (linha condicional da lista) |
| 4.2 | Teclado: apertar as 16 teclas | As 16 aparecem certas no LCD | | Linhas e colunas trocadas: conferir a ordem do flat |
| 4.3 | Tensão no TX do AS608 (multímetro entre TX e GND, leitor ligado e parado) | Acima de 3,0 V | | Abaixo de 3,0 V: o Mega pode não ler. Avisar; a solução é um conversor de nível |
| 4.4 | Tensão no RX do AS608 (depois do divisor), com o Mega mandando dados | No máximo 3,5 V | | Acima: divisor errado |
| 4.5 | Cadastrar e ler uma digital | Leitor reconhece o dedo em menos de 1 s | | |
| 4.6 | Buzzer no volume mínimo e no máximo | Mínimo: audível a 1 m num lugar quieto. Máximo: incomoda a 1 m | | |
| 4.7 | Reed: ímã perto e longe; depois soltar um fio | Fechada / aberta / aberta | | Fio solto lendo "fechada" é erro grave: conferir o `INPUT_PULLUP` |

## Passo 5 — Trava sozinha

Relé 1 com a trava e o diodo D3 (faixa no +). Multímetro em série na escala de 10 A.

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 5.1 | Pulso de 2 s pelo firmware (ou jumper IN1–GND por 2 s) | Lingueta recolhe; ~0,5 A [ds] (2 A se o passo 0.1 deu 6 Ω) | | Não recolhe: tensão chegando na trava (medir com ela ligada) |
| 5.2 | 5 pulsos de 3 s com 10 s de intervalo, depois pôr o dedo na trava | Morna | | Quente demais para segurar: diminuir o tempo de pulso no firmware |
| 5.3 | Liberação mecânica de emergência (Fase 5) | A lingueta recolhe puxando o cordão, sem energia | | Refazer antes de fechar a porta |

## Passo 6 — Ventoinhas

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 6.1 | Ventoinha de cada cooler direto no T12 | Gira; 0,2 a 0,3 A [ds 0,26 A] | | Não gira: conferir pino 1 (GND) e pino 2 (+12 V) |
| 6.2 | Ventoinha fria de cada ramo, com o relé acionado | Gira; ~0,18 A [ds] | | |

## Passo 7 — Uma Peltier com cooler, na mesa (2 minutos)

Pastilha montada **fora do armário** (antes de ir para a lateral): cooler + pasta + pastilha + pasta + espaçador + pasta + dissipador frio com a ventoinha, apertados pela prensa. Ventoinha do cooler girando **antes** de ligar a pastilha. DS18B20 (ou termômetro de cozinha) na base do cooler e outro no dissipador frio. Multímetro em série (10 A).

| # | O que medir | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 7.1 | Corrente ao ligar | ~3,0 A [calc 12 / 3,93], caindo devagar | | Acima de 3,5 A: desligar. Pastilha errada ou em curto |
| 7.2 | Base do cooler depois de 2 min | Menos de 45 °C [calc ~30–48 °C] | | Acima de 60 °C: **desligar já**. Pasta mal passada, cooler frouxo ou ventoinha parada |
| 7.3 | Dissipador frio depois de 2 min | Pelo menos 10 °C abaixo do ambiente [est] | | Esquentando: pastilha invertida (face quente para o lado frio). Desligar e virar |
| 7.4 | Corrente depois de 2 min | 2,3 a 2,9 A [calc] | | |

Repetir para a segunda pastilha.

## Passo 8 — Proteção térmica

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 8.1 | Com as Peltier ligadas, pôr o DS18B20 de um cooler num copo de água quente da torneira (> 60 °C, conferir com termômetro) | Relés 2 e 3 desligam; evento `CORTE_QUENTE` no notebook; só religam abaixo de 45 °C | | Conferir o mapa dos sensores (`SET mapa=`) |
| 8.2 | Soltar o fio de dados (amarelo) dos DS18B20 | Peltier desligadas; evento `SENSOR_FALHA` | | Corrigir o firmware |
| 8.3 | **Não** testar o fusível térmico queimando: ele não volta. Conferir a continuidade (0.3), que a luva de crimpar não sai puxando com a mão e que ele está encostado na base do cooler | — | | |
| 8.4 | Intertravamento: pedir abertura da trava com as duas Peltier ligadas | Relés 2 e 3 desligam antes do relé 1 ligar (20 ms antes); voltam depois (segunda Peltier 2 s após a primeira) | | Corrigir o firmware |
| 8.5 | Baia que não esfria: com a baia acima de 6 °C, tirar o fio de uma Peltier do conector P1 e P2 (relés ligam, pastilhas não) e esperar 20 min | Evento `FRIO_SEM_EFEITO`, relés 2 e 3 desligam, alarme "baia não esfria" no painel; nova tentativa em 30 min | | Corrigir o firmware |

## Passo 9 — Tudo junto no armário, 30 minutos

Baia fria montada e fechada com a tampa isolada. Porta do armário fechada. Ambiente anotado. Notebook registrando as temperaturas (o firmware manda `TEMP` a cada 2 s).

| # | O que medir | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 9.1 | Corrente total no F1 com as duas Peltier ligadas | 5,5 a 7,0 A [calc] | | Acima de 8 A: desligar e procurar a carga errada |
| 9.2 | Temperatura da baia em 30 min | Cai pelo menos 10 K [calc aproximado: ~1000 J/K de massa fria e ~10 W líquidos dão ~0,6 K/min] | | Caiu menos de 5 K: isolamento com fresta, tampa mal vedada ou pastilha invertida |
| 9.3 | Base dos coolers em 30 min | Abaixo de 50 °C [calc ~46 °C a 32 °C de ambiente] | | Acima de 55 °C: falta ar. Conferir se a ventoinha sopra para cima e se nada tampa a grade do berço |
| 9.4 | Ar saindo por cima dos coolers | Morno, nunca quente | | |
| 9.5 | Deixar mais 30–60 min | A baia chega a 5 °C e as Peltier começam a ligar e desligar (histerese 4–6 °C) | | Não chega a 6 °C em 90 min com ambiente abaixo de 28 °C: refazer as contas com os valores medidos |
| 9.6 | Temperatura do ar **dentro da caixa da eletrônica**, em cima da fonte, depois de 60 min (DS18B20 de reserva ou termômetro) | Até 20 K acima do ambiente [est: ~15 W de perda da fonte] | | Mais: abrir mais rasgos ou trocar pela fonte fechada metálica, com 3 cm de ar livre acima dela. MDF é combustível e o borne de 127/220 V está ali |
| 9.7 | Em 1 h de funcionamento, olhar o furo das Peltier por dentro da baia | Seco: sem água escorrendo no MDF | | Água ou gelo: vedar a borda da pastilha e do espaçador com silicone neutro (RTV) por dentro e conferir a manta de vedação. MDF molhado incha e a água corrói a pastilha |

## Passo 10 — Queda de energia (RNF07.1)

| # | O que fazer | Esperado | Medido | Se der diferente |
|---|---|---|---|---|
| 10.1 | No meio de uma retirada (porta aberta), tirar a fonte da tomada por 15 s e religar | Mega não reinicia (está na USB); registro "falta de energia" e "energia voltou" na auditoria; porta continua registrada como aberta; Peltier voltam a obedecer o controle | | |
| 10.2 | Tirar também a USB do Mega por 5 s | Mega reinicia com tudo desligado, lê o estado da EEPROM e reenvia os eventos pendentes | | |
