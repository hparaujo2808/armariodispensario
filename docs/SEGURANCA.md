# Segurança

Leia inteiro antes da primeira vez que a fonte for para a tomada. Na primeira ligação, de preferência com o professor junto.

## Checklist antes de ligar na tomada

Marque cada item **toda vez** que mexer na fiação.

- [ ] Fonte **desligada da tomada** enquanto se mexe em qualquer fio.
- [ ] Chave 127/220 V da fonte na tensão da tomada (fonte colmeia; a fechada é automática).
- [ ] Fonte colmeia: tampa de MDF ou acrílico **sobre o borne L/N/terra**, parafusada. Cabo de força preso por abraçadeira, para um puxão não arrancar os fios do borne. **Fio terra (verde ou verde-amarelo) ligado.**
- [ ] F1 (10 A) logo no + da fonte e F2 (2 A) no ramo fino, com fusível dentro.
- [ ] Nenhum fio de 12 V encosta no Mega, nos pinos dele ou no LCD.
- [ ] Cada conector de alavanca com a alavanca **fechada** e o fio descascado só o tamanho da janela (~11 mm). Puxar cada fio com a mão: não pode sair.
- [ ] Diodos D1, D2 e D3 com a **faixa no +**.
- [ ] Ventoinhas dos coolers ligadas direto no 12 V (T12), e não pelo relé.
- [ ] Cada Peltier com cooler apertado, pasta térmica nas duas faces e fusível térmico preso na base do cooler.
- [ ] Nada encostado embaixo dos coolers: é por onde entra o ar.
- [ ] Medido com o multímetro em Ω: **B12 não está em curto com o GND** (passo 0.5 dos testes).
- [ ] LM2596 já ajustado em 5,0 V, sem carga (passo 1.2).
- [ ] Alguém olhando o armário nos primeiros 5 minutos. Extintor ou, no mínimo, saber onde está o disjuntor.

## Riscos de cada parte

| Parte | O que pode dar errado | Como o projeto evita | O que vocês fazem |
|---|---|---|---|
| Tomada e fonte | Choque nos 127/220 V do borne da fonte colmeia | Tampa sobre o borne; fonte fechada se a colmeia não chegou | Só mexer com a fonte fora da tomada |
| Fiação de 12 V | Curto esquenta o fio e derrete a capa | F1 10 A protege os fios de 1,5 mm²; F2 2 A protege os de 0,5 mm² | Não trocar fusível por um maior. Nunca "fazer ponte" num fusível |
| Peltier | Sem ventilação passa de 125 °C em minutos, queima e pode chamuscar o MDF | Ventoinha sempre ligada com a fonte; corte por software a 60 °C no cooler; fusível térmico a 85 °C em série | Nunca ligar sem o cooler preso e girando |
| Baia fria | Condensação pinga na eletrônica | Toda a eletrônica fica no vão de trás, fora da baia; bandejinha com papel absorvente embaixo do dissipador frio | Conferir a bandejinha a cada teste longo |
| Trava | Bobina esquenta se ficar ligada; porta presa se a eletrônica falhar | Firmware limita o tempo energizada; liberação mecânica de emergência (Fase 5) | Testar a liberação antes da banca |
| Relés | Pulso ao ligar o Mega abriria a trava | Firmware põe a saída em HIGH antes de configurar o pino (passo 3 dos testes) | Repetir o passo 3 sempre que gravar firmware novo |
| Mega e notebook | 12 V no 5 V do Mega queima o Mega e pode danificar a porta USB do notebook | 12 V e 5 V do Mega nunca no mesmo conector; terra num ponto só | Conferir com o multímetro antes de ligar a USB |
| Armário | Tombar com a porta aberta | Estabilidade conferida na Fase 5 | Na banca, fixar ou escorar |

## Nunca

- Nunca ligar uma Peltier sem o cooler preso e girando, nem "só para ver se funciona". Para descobrir a face fria, 5 V por 2 s, e só.
- Nunca trocar o F1 ou o F2 por um fusível maior, nem substituir por um pedaço de fio.
- Nunca mexer no borne da fonte com ela na tomada.
- Nunca ligar o Vin do Mega no 12 V (o Mega é alimentado pela USB).
- Nunca soldar o fusível térmico (o calor da solda queima ele).
- Nunca deixar o armário ligado sem ninguém por perto antes do teste de 30 minutos (passo 9) dar certo.
- Nunca encostar a mão no dissipador do lado quente com o sistema ligado sem antes medir a temperatura dele.
