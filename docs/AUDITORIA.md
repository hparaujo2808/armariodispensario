# Auditoria do projeto — Dispensário Eletrônico

Revisão de 22/10/2026, branch `revisao-geral`. Fases 0 e 1 do plano: inventário (só leitura) e auditoria. Nada foi consertado ainda. As correções dependem da **DECISÃO 1** (arquitetura), no fim deste documento.

> **Atualização de 23/10/2026:** as seções 1 a 8 mostram o projeto como estava em 22/10, antes das correções, e servem de registro. O que foi feito com cada item está na **seção 9**, e o resultado da revisão independente, na **seção 10**.

## Como ler

Cada valor técnico tem uma marca de origem:

- **[ds]** datasheet ou página do fabricante/loja, com link na seção 8;
- **[calc]** conta mostrada aqui ou num script de `calculos/`;
- **[medir]** precisa de medição na bancada (o procedimento está na seção 7);
- **[est]** estimativa sem fonte boa. Precisa virar [ds] ou [medir] antes de valer.

Gravidade: **crítica** (risco de queimar, ferir ou o protótipo não funcionar na banca), **alta** (requisito Must não atendido ou erro que faz montar errado), **média** (funciona, mas mal ou fora do pedido), **baixa** (texto, cosmético).

Scripts usados como evidência (rodam com Python 3.12):

```bash
python calculos/termico_atual.py
```

```bash
python calculos/conferir_geometria.py
```

---

## 1. Inventário: onde está cada coisa

O repositório que vale é `~/Desktop/armariodispensario` (GitHub `hparaujo2808/armariodispensario`). O material de referência foi copiado para `referencias_externas/`, que está no `.gitignore` (tem 138 MB e ambientes virtuais). Os três zips enviados batem arquivo por arquivo com as pastas do Desktop (conferido com `diff -r`).

### 1.1 As versões que existem e o que cada uma tem de aproveitável

| # | Versão | Onde | Arquitetura | Situação | O que aproveitar |
|---|---|---|---|---|---|
| 1 | Pi + reconhecimento facial | `Captura de Tela 2026-09-01 ….png` | Raspberry Pi, câmera, reconhecimento facial | Descartada | Nada. Facial não está no escopo (RF01 pede digital) |
| 2 | Pi + placa própria DISP-IF | `dispensario_interno/legado/hardware/` | Pi 4 + placa KiCad com SMD e supercapacitores | Abandonada em 07/10 (custo, exige solda SMD) | Só ideias: proteções, cálculo de energia. A placa não |
| 3 | Pi + módulos | `dispensario_interno/docs/01_ARQUITETURA.md`, `calculos/`, `legado/firmware/` | Pi 4 2 GB, tela 7" touch, AS608, 2 webcams, 1 Peltier 12706 em baia isolada, MOSFETs, KSD301 | Abandonada por custo (lista de R$ 2.812, sendo R$ 950 do Pi) | **Muito**: software Python completo (seção 1.3), cálculo térmico, orçamento de energia, escolha de proteções, lista de preços de 07–15/10 |
| 4 | Mega + relés (atual) | raiz do repo: `README.md`, `LISTA-DE-COMPRAS.md`, `docs/` | Arduino Mega, senha fixa, LCD, teclado, 2 Peltier 12703 sem cooler, trava por relé, webcam ao vivo no notebook | Em montagem; itens da lista já comprados | Mega, LCD, teclado, buzzer, relés, LM2596, fonte, trava, webcam, notebook. Mapa de pinos e simulação 3D (com correções) |
| — | Armário V2 | `Projeto de Sistemas Embarcados/ARMARIO_V2/` | Chapas 01–21 | 01–15 cortadas; 16–21 são sobra de versão antiga | Peças físicas. Manual PDF e desenho frontal **desatualizados** (o próprio LEIA_PRIMEIRO da V2.3 diz isso) |
| — | Armário V2.3 | `referencias_externas/ARMARIO_V2.3/` | Gerador paramétrico + laterais novas (CHAPA_22 e 23) | Reflete o armário real | `config.py` é a fonte das medidas. Base para a porta (Fase 5) |

O próprio legado se contradiz: a lista de compras e o `01_ARQUITETURA.md` pedem o leitor **AS608**, mas o código (`hal/r503.py`, `pinmap.py`, `auth.py`) foi escrito para o **R503**. Os dois falam o mesmo protocolo de comandos (família ZFM/Synochip) [est], então a troca é pequena, mas precisa ser decidida.

A memória do projeto registra duas decisões em conflito, com um dia de diferença: em 15/10 "1 TEC1-12706 com baia C1 isolada e Raspberry Pi 4" (legado) e em 16/10 "2 TEC1-12703 sem cooler e Arduino Mega" (repo). A DECISÃO 1 resolve isso de vez.

### 1.2 Gerador da V2.3: não roda como foi entregue

- `python gerador/main.py` **quebra** com `TypeError: 'NoneType' object is not iterable`. O `config.py` diz `PECAS_JA_CORTADAS = None   # v2.3: definido abaixo`, mas a variável nunca é definida. [calc: rodado num ambiente novo, Python 3.12, ezdxf 1.4.5]
- Preenchendo a variável com "todas as peças menos `CORTAR_NA_MAQUINA`" (o que o comentário descreve), o gerador roda e os 6 DXFs saem **idênticos** aos do zip, entidade por entidade e byte a byte nas chapas 22 e 23, com `INSUNITS = 4` (mm). Então a geometria está reproduzível.
- Mas o gerador **sobrescreve o `LEIA_PRIMEIRO.md` da V2.3 com o texto da v2.1** e grava `"versao": "v2.1"` no `VALIDACAO.json`. O LEIA_PRIMEIRO da V2.3 foi escrito à mão depois. Ele fala em 68 peças; o gerador conta 71.
- O teste 3D citado no LEIA_PRIMEIRO ("as 68 peças foram montadas em 3D com o formato real das peças da v2") **não está no zip**. Não dá para repetir essa verificação.

### 1.3 Software do legado: testes

Rodados numa cópia, com ambiente novo (Python 3.12, FastAPI 0.160, pytest 9.1): **36 passam, 2 falham**.

| Teste | Por que falha | Conserto |
|---|---|---|
| `test_hardware.py::test_pinmap_bate_com_o_conector_da_placa` | Lê `hardware/gerador/projeto.py`, da placa DISP-IF abandonada | Apagar junto com a placa |
| `test_fluxo.py::test_senha_como_fallback_e_bloqueio` | **Bug real**: `auth.py` usa `time.time()` (relógio do sistema) no bloqueio, mas o resto do `core.py` usa o relógio injetável. O teste avança o relógio falso 301 s e o usuário continua bloqueado | Passar o relógio do `core` para o `Autenticador` |

O cache antigo (`.pytest_cache/lastfailed`) mostra quase todos os testes falhando. Isso era do ambiente Python 3.9 sem as dependências, não do código.

O que dá para reaproveitar quase sem mexer: `storage.py` (SQLite com log só de acréscimo e hash encadeado), `auth.py` (hash de senha com sal, bloqueio), `mock_mv.py` e `mv_client.py` (MV simulado), `api.py` (FastAPI), `web/kiosk.html` e `web/painel.html`, `termico.py` (controle com histerese), `core.py` (máquina de estados, recuperação após queda). O que é específico do Pi e sai: `hal/rpi.py`, `pinmap.py`, a parte de supercapacitores (`vcap`) do `core.py`.

---

## 2. Medidas do armário (calculadas do `config.py` da V2.3)

Olhando de frente, a partir do canto externo de baixo à esquerda. Saída de `calculos/conferir_geometria.py`. [calc]

| O quê | Valor |
|---|---|
| Externo | 880 × 880 × 700 mm (L × A × P), MDF 3 mm |
| Vão entre laterais | 874 mm |
| Profundidade útil (gavetas e prateleiras) | 0 a 494 mm |
| Fundo falso | Y 494 a 497 |
| Vão de trás (eletrônica) | Y 497 a 697 (200 mm) |
| Gaveteiro | Z 3 a 399 · teto do gaveteiro 399 a 402 |
| Prateleira 2 · Prateleira 1 · piso da câmera | Z 530,7 · 662,3 · 794,0 (face de baixo) |
| Compartimento de cima (câmera) | Z 797 a 877 |
| Nervuras (3 sob cada prateleira, de lateral a lateral, Y = 82, 247, 412) | sob PRAT_2: Z 492,7–530,7 · sob PRAT_1: 624,3–662,3 · sob P_CAM: 756,0–794,0 |
| Coluna A · B · C · baia do dispensador | X 3–346 · 349–511 · 514–676 · 679–877 |
| Gaveta **C1** (pela tabela de corrediças) | Z 5 a 200 — **a de baixo** |
| Gaveta **C2** | Z 202 a 397 — **a de cima** |

Convenção de numeração das gavetas, a partir da V2.3: **1 é a de baixo** (A1 tem a corrediça mais baixa, 53,4 mm; C1 tem a gaveta de 5 a 200 mm). A simulação e o LIGACOES.md numeram de cima para baixo. Ver item 15.

---

## 3. Tabela de inconsistências

### 3.1 Os 18 pontos levantados antes

| ID | Onde | O que diz | O que é correto | Evidência | Gravidade | Correção proposta |
|---|---|---|---|---|---|---|
| 1 | README, LISTA, LIGACOES, simulação | 2 × TEC1-12703 com dissipador 65 × 46 × 24 mm sem cooler; "o dissipador sem ventoinha dá conta por mais tempo" | **Confirmado, e pior que o previsto.** Cada pastilha puxa 3,05 A / 36,7 W na partida. O dissipador passivo tem 7 a 11 K/W. Com 7 K/W o lado quente iria a ~180 °C (o módulo aguenta 125 °C e a solda funde a 138 °C) e o lado frio a ~80 °C: a gaveta **esquenta**. Mesmo com 3 K/W (otimista), o lado quente fica em 108 °C e o frio a 24 °C, sem tirar calor nenhum. O vão de trás fechado sobe ~9 K | [ds] Huimao TES1-12703; [calc] `termico_atual.py` (seção 6.1); [medir] 7.3 | **crítica** | Não ligar a Peltier como está. Dissipador de CPU com ventoinha 12 V no lado quente, dissipador + ventoinha no lado frio, isolamento, KSD301. Detalhe na DECISÃO 1 |
| 2 | Todo o repo atual | Peltier ligada à mão pelas teclas A/B; sem sensor; sem proteção térmica | **Confirmado.** Não há KSD301, fusível térmico nem sensor de temperatura. Não atende "regulagem de temperatura" (reunião) nem o RNF08 | Leitura do README, LIGACOES e diagrama | **crítica** | KSD301 NF em série com a Peltier, colado no dissipador quente; DS18B20 na gaveta e no dissipador; controle on/off com histerese no Mega |
| 3 | Firmware ainda não existe | — | **Risco real.** O AVR liga com os pinos em entrada (alta impedância) [ds ATmega2560]. Nesse estado o relé ativo em LOW fica desligado. Mas `pinMode(OUTPUT)` antes de `digitalWrite(HIGH)` põe o pino em LOW (o registrador PORT começa em 0) e o relé pulsa a cada reset. O bootloader do Mega só mexe no pino 13 [est: conferir no fonte do stk500v2] | [ds] ATmega2560, seção I/O Ports; [medir] 7.6 | alta | No `setup()`, `digitalWrite(pino, HIGH)` **antes** de `pinMode(pino, OUTPUT)`. Não usar o pino 13 para relé. Teste de bancada: LED no IN, apertar reset 10 vezes |
| 4 | Arquitetura com notebook | — | **Confirmado.** No Mega 2560 o DTR do 16U2 está ligado no RESET por um capacitor de 100 nF: abrir a porta serial reinicia a placa [ds Arduino]. Se a trava estiver energizada nesse instante, ela solta | [ds] docs.arduino.cc Mega 2560 | alta | Firmware que inicia em estado seguro (trava e Peltier desligadas), lê o estado da EEPROM e só libera a trava com comando novo. O app abre a serial **uma vez** e mantém aberta |
| 5 | Todo o repo | Nada sobre abertura de emergência | **Confirmado.** A trava é de lingueta e tranca sem energia; não há liberação mecânica em nenhum documento (busca por "emerg" sem resultado) | Busca de texto | **crítica** (para a banca) | Cordão ou haste presa na lingueta, saindo por um furo discreto (Fase 5). Documentar e testar antes da banca |
| 6 | LISTA (FE-91 "12 V 0,5 A") × legado (XG07E "bobina 6 Ω") | 0,5 A | **São duas travas diferentes.** A FE-91 da Eletrogate anuncia 12 V / 500 mA → bobina de ~24 Ω [calc]. A XG07E do legado tinha 6 Ω → 2 A. A página da FE-91 não informa resistência, tempo máximo energizada nem medidas | [ds] Eletrogate FE-91; [calc] 12/0,5 = 24 Ω; [medir] 7.2 | média | Medir a bobina da trava que chegou. Dimensionar pela medição. Firmware: no máximo N s energizada |
| 7 | LIGACOES ("12 V de COM em COM") | Fonte → fusível → COM1 → COM2 → COM3 | **Confirmado.** O borne do COM1 leva toda a corrente: 2 × 3,05 + 0,5 + 0,12 + 0,15 ≈ **6,9 A** na partida [calc], com dois fios de 1,5 mm² num parafuso. O contato do relé é de 10 A [ds distribuidor], mas o borne e a trilha da placa não têm especificação | [ds] SRD-05VDC-SL-C (LCSC); [calc] seção 5 | alta | Barramento 12 V e GND com conectores de alavanca (32 A [ds]). Cada COM recebe o seu próprio fio do barramento |
| 8 | LISTA, Carrinho 2 | Fonte colmeia 12 V 10 A, ligada pelo grupo no borne L/N/terra | **Confirmado.** Terminais de 127/220 V expostos, e o cabo de força tem a ponta cortada e parafusada pelo grupo | Própria LISTA ("Cuidados") | **crítica** | Se já chegou: tampa de acrílico/MDF sobre o borne, prensa-cabo, terra ligado, primeira ligação com o professor. Se ainda não foi comprada: fonte fechada com cabo (R$ 94,40 em 15/10, KaBuM) |
| 9 | README | "A senha é uma constante no código" | **Confirmado.** Senha única não identifica quem abriu (RF05), não há biometria (RF01, Must) | README | alta | Usuários com ID, senha por usuário com hash, leitor biométrico |
| 10 | Todo o repo | Nada grava quem abriu | **Confirmado.** RF05 (Must) e pedido explícito da reunião | README, LIGACOES | alta | Registro de auditoria só de acréscimo (legado `storage.py`) + fila de eventos no Mega |
| 11 | README, LIGACOES | Webcam só mostra ao vivo, "independente do Arduino" | **Confirmado.** Sem gravação nem vínculo com o evento (RF07, Must). A reunião pediu câmera interna **e** externa | README | alta | Gravar clipe a cada abertura e ligar ao registro. Segunda câmera dentro |
| 12 | Todo o repo | Sem tela, CPF ou MV | **Confirmado** (RF03, RF04, RF10 Must). O legado tem quiosque, MV simulado e API prontos e testados | Legado, testes | alta | Reaproveitar o software do legado no notebook |
| 13 | Commit `888a5e6` (15/10) | "Tira o sensor de porta, tranca só pelo teclado" | **Confirmado.** Sem reed não há alarme de porta aberta (RF09), nem como saber se a porta abriu de fato (RF05 fala em "cada abertura"), nem como detectar porta forçada (RNF03). MC-38 custa R$ 10,88 (Usinainfo, 07/10) | Commit, lista do legado | alta | Voltar com o reed. Fio rompido = "aberta" |
| 14 | Todo o repo | Nada sobre queda de energia | **Confirmado.** RNF07.1 pede manter o estado por ~15 s sem bateria dedicada e sem perder auditoria. O Mega alimentado pela fonte reinicia na queda | Escopo, LIGACOES | média | Mega alimentado pelo USB do notebook (que tem bateria); estado na EEPROM; auditoria no notebook. A trava fail-secure fica fechada |
| 15 | LIGACOES, simulação, diagrama | Peltier da C1 a 298 mm, da C2 a 101 mm; C1 é a de cima | **Confirmado: trocadas.** Pela tabela de corrediças da V2.3, C1 é a de baixo (Z 5–200) e C2 a de cima (Z 202–397). O mesmo vale para A e B: a simulação põe A1 e B1 em cima | [calc] `conferir_geometria.py` | média | Convenção única: **1 = de baixo**, como na V2.3. Corrigir LIGACOES, simulação e diagrama |
| 16 | README × V2.3 | "Fora do escopo: o dispensador por gravidade" | **Confirmado.** A V2.3 constrói a pista, os perfis, o retentor e as tiras de apoio | LEIA_PRIMEIRO da V2.3 | baixa | Documentar: a baia existe como estrutura passiva (rolos descem por gravidade), sem sensor nem motor |
| 17 | Simulação | Puxador saltado 1 mm; a própria tabela avisa que a porta "bateria em qualquer puxador" | **Confirmado.** Na simulação a face da gaveta está no mesmo plano da face interna da porta: folga zero. Na V2.3 a corrediça começa a 3 mm da frente e a lateral da gaveta (463 mm) é 6 mm maior que a corrediça (457 mm), então a frente da gaveta fica praticamente rente à borda da caixa [calc aproximado] | Simulação linhas 1003 e 1010; V2.3 | média | Puxador embutido (furo ou rasgo na frente) ou calço de afastamento na porta. Medir no armário real (7.8). Fase 5 |
| 18 | LIGACOES, simulação | Externo 880 × 880 × 700, vão 874, profundidade 494 | **Confirmado** pelo `config.py`. As posições X da coluna C (595) e da câmera (835) batem. Erros: rota dos cabos da porta (N03) e C1/C2 (item 15). A simulação desenha as laterais com 874 de altura (são 880) e a porta com 6 mm (o MDF é 3 mm) | [calc] `conferir_geometria.py`; simulação linhas 975–976 e 1057 | baixa | Simulação gerada a partir do `config.py` na Fase 2 |

### 3.2 Outros problemas encontrados

| ID | Onde | O que diz | O que é correto | Evidência | Gravidade | Correção proposta |
|---|---|---|---|---|---|---|
| N01 | LIGACOES ("Peltier") | A pastilha fica no furo de 38 mm, sem nada do lado frio | Só os 11 cm² de cerâmica atrás do furo trocam calor com o ar da gaveta: ~88 K/W. Mesmo com o lado quente perfeito, a pastilha tiraria menos de 1 W da gaveta | [calc] `termico_atual.py` | **crítica** | Dissipador + ventoinha do lado frio, dentro de uma baia isolada |
| N02 | LIGACOES | Abraçadeira de nylon segura o dissipador; cola quente veda a borda da pastilha | O lado quente passaria de 100 °C (item 1). Cola quente amolece por volta de 60–80 °C e nylon comum é para uso contínuo até ~85 °C [est] | [calc] item 1 | alta | Fixar com parafuso passante M3/M4 e placa de apoio; vedar com espuma/fita de alumínio fora da área quente |
| N03 | LIGACOES ("Cabos e caminhos", "Furos") | Cabos da porta pela lateral esquerda a 660 mm; furo de 10 mm a 660 mm na lateral e no fundo falso | A 660 mm a rota **cruza as 3 nervuras** sob a Prateleira 1 (Z 624,3–662,3, de lateral a lateral). O furo de Ø10 (655–665) encosta na prateleira (662,3) e, no fundo falso, cai em cima do rasgo dela (borda de baixo a 662) | [calc] `conferir_geometria.py` | alta | Descer a rota para o vão entre a Prateleira 2 e as nervuras (Z ~ 540 a 615) ou passar por cima de uma prateleira. Recalcular na Fase 2 |
| N04 | LIGACOES ("Vin") | Mega alimentado por 12 V no Vin | O regulador linear do Mega dissipa (12 − 5) × I. Com Mega + LCD + buzzer (~150 mA [est]) são ~1 W num regulador SOT-223, que esquenta muito. Com leitor biométrico fica pior. A Arduino recomenda 7–12 V | [ds] Arduino Mega; [calc] | média | Na arquitetura híbrida, alimentar o Mega pelo USB do notebook. Senão, 5 V do LM2596 no pino 5V, ou Vin em ~9 V |
| N05 | LIGACOES ("Buzzer") | Buzzer ativo direto no pino 7 | O pino do Mega aguenta 20 mA recomendado (40 mA máximo absoluto) [ds]. A corrente do buzzer não está documentada. O buzzer ativo tem volume fixo: não atende "volume configurável" (RNF10) | [ds] Arduino Mega; [medir] 7.5 | média | Medir. Transistor se passar de 20 mA. Para volume ajustável, buzzer passivo ou piezo com PWM |
| N06 | LIGACOES ("LCD") | LCD paralelo por 2,5 m de cabo de rede | Funciona em muitos casos, mas o sinal E com cabo longo pode dar caracteres trocados [est] | — | média | Testar na bancada com o cabo real antes de fechar a porta (7.7). Se falhar: par trançado sinal+GND, ou adaptador I²C |
| N07 | LIGACOES ("Câmera") | Webcam atrás de um furo de 15 mm na porta, a 1–2 cm | Com a porta-caixão (Fase 5, 15 a 25 mm de espessura), o furo vira um túnel e corta o campo de visão. Com a porta aberta a câmera não vê mais a porta | [calc] geometria | média | Câmera externa presa na face de fora (ou no topo), olhando para quem está no teclado. Câmera interna olhando para as gavetas |
| N08 | LIGACOES ("12 V") | Só um fusível de 10 A na saída da fonte | Os ramos de 0,5 mm² (trava, LM2596, Vin) ficam protegidos só pelo fusível de 10 A | [calc] | média | Fusível de 2 A no ramo de baixa corrente, ou fio de 1,0 mm² em tudo |
| N09 | Gerador V2.3 | `main.py` quebra; sobrescreve o LEIA_PRIMEIRO com texto da v2.1 | Seção 1.2 | Execução | alta (bloqueia a Fase 5) | Definir `PECAS_JA_CORTADAS` a partir de `CORTAR_NA_MAQUINA` e não regerar o LEIA_PRIMEIRO à mão. Trazer o gerador para dentro do repo |
| N10 | Legado `auth.py` | Bloqueio por `time.time()` | Relógio diferente do resto do `core` (seção 1.3) | Teste falhando | média | Corrigir ao reaproveitar |
| N11 | Simulação | Lateral com 874 de altura, porta com 6 mm, prateleiras ~2–3 mm abaixo | Laterais 880, MDF 3 mm, prateleiras pelo `config.py` | [calc] | baixa | Gerar as medidas a partir do `config.py` |
| N12 | README, LISTA, LIGACOES, simulação | Prefixo `rogi:` em 19 parágrafos (2 + 6 + 6 + 5) | Texto sem prefixo | Busca de texto | baixa | Remover |
| N13 | Reunião × escopo | "Dupla confirmação da retirada/entrega" | Não está no docx de escopo nem em nenhuma versão | Transcrição da reunião | média | Na Fase 4: confirmar no quiosque o que foi tirado, contra a prescrição (o legado já tem "divergência") |
| N14 | README | "A trava fica liberada por 5 s, com ou sem a porta aberta" (commit `888a5e6`) | Sem reed, o sistema não sabe se alguém abriu. O registro seria de "autorização", não de "abertura" | Commit | alta | Com reed: registrar autorização e abertura como eventos separados |

---

## 4. Matriz de rastreabilidade (RF e RNF do escopo)

"Hoje" é o que está na raiz do repo (Mega + senha fixa). "Proposta" é a arquitetura híbrida da DECISÃO 1, ainda **não aprovada**.

| ID | Requisito | Prior. | Hoje | Como a proposta atende | Status com a proposta | Como demonstrar na banca |
|---|---|---|---|---|---|---|
| RF01 | Biometria | Must | não atende | Leitor de digital na porta, ligado no Mega (Serial1), digitais guardadas no próprio leitor | atende | Cadastrar o dedo de um professor e abrir |
| RF02 | Senha como alternativa | Must | parcial (senha única) | Senha por usuário no teclado, com hash; oferecida após falha da digital | atende | Errar a digital 3 vezes e entrar com senha |
| RF03 | Consulta por CPF | Must | não atende | Quiosque no notebook (legado `kiosk.html`) | atende | Digitar o CPF de um paciente fictício |
| RF04 | Integração MV por API | Must | não atende | API REST com MV simulado (`mock_mv.py`); contrato pronto para o MV real | parcial justificado (não há acesso ao MV real; o escopo prevê contingência) | Mostrar a chamada à API e o JSON |
| RF05 | Usuário e horário de cada abertura | Must | não atende | Evento do Mega (auth + reed) gravado no SQLite com hash encadeado | atende | Abrir e mostrar o registro no painel |
| RF06 | Dados para farmácia/TI | Should | não atende | Painel e API com filtro (legado `painel.html`) | atende | Filtrar por usuário |
| RF07 | Imagem/vídeo de cada abertura | Must | não atende | Notebook grava clipe das 2 webcams quando o reed abre | atende | Abrir o clipe a partir do registro |
| RF08 | Estoque pela logística | Should | não atende | Painel de estoque (legado) | atende | Mostrar baixa após a retirada |
| RF09 | Alerta de porta aberta | Should | não atende (sem reed) | Reed + tempo configurável no Mega | atende | Deixar a porta aberta 30 s |
| RF10 | Configurar itens por compartimento | Must | não atende | Cadastro no painel (legado) | atende | Mudar o item da gaveta B1 |
| RF11 | Registro de reabastecimento | Should | não atende | Tela de reposição (legado) | atende | Repor um item |
| RF12 | Segmentar climatizados | Must | parcial (gavetas existem, sistema não) | Gaveta fria marcada no cadastro; o sistema recusa item refrigerado fora dela (legado tem teste) | atende | Tentar pôr insulina numa gaveta comum |
| RF13 | Notificação de estoque baixo | Could | não atende | Alerta no painel | atende | Retirar até o mínimo |
| RNF01 | Custo bem abaixo de R$ 4 mi | — | atende | Reaproveita o que o grupo tem | atende | Tabela de custo |
| RNF02 | Construível com apoio simples | — | atende | Sem solda SMD, conectores de alavanca | atende | Montagem pelo grupo |
| RNF03 | Nenhuma abertura sem autenticação | — | parcial | Trava só com autenticação + reed detecta abertura forçada | atende | Abrir pela liberação de emergência e mostrar o alarme |
| RNF04 | Registros inalteráveis | — | não atende | Tabela só de acréscimo + hash encadeado + verificação | atende | Alterar uma linha no SQLite e mostrar a verificação falhando |
| RNF05 | LGPD (CPF, biometria) | — | não se aplica hoje | Digital fica no leitor; CPF guardado com hash/mascarado | atende | Mostrar o banco sem CPF em claro |
| RNF06 | Resposta em poucos segundos | — | atende | Tudo local | atende | Cronometrar |
| RNF07 | Equipamento de tomada | — | atende | — | atende | — |
| RNF07.1 | Aguentar ~15 s sem energia | — | não atende | Notebook com bateria alimenta o Mega por USB; estado na EEPROM; auditoria em SQLite com `synchronous=FULL` | atende (Peltier e trava param 15 s, sem efeito) | Tirar a fonte da tomada no meio de uma retirada |
| RNF08 | Conservação térmica | — | não atende (seção 6.1) | 1 gaveta fria isolada, Peltier com coolers, DS18B20, histerese | parcial: alcança 2–8 °C até ~28–32 °C de ambiente [calc], a confirmar na bancada | Gráfico de 30 min de temperatura |
| RNF09 | Simples para a enfermagem | — | parcial | Fluxo digital → CPF → abrir | atende | Retirada completa em menos de 1 min |
| RNF10 | Alarme baixo | — | não atende | Volume configurável (buzzer passivo/PWM) e modo noturno | atende | Mostrar os dois volumes |
| RNF11 | MV sem alteração | — | não atende | Só consulta por API | atende | — |
| RNF12 | Replicável | — | parcial | Mesmo software, configuração por arquivo | atende | — |
| RNF13 | Prazo | — | em risco | Reaproveitar o legado reduz o trabalho | em risco (18/11) | — |
| RNF14 | Fixação na parede | — | não atende | Furos e reforço para parede; na banca, apoio que não tomba com a porta a 90° | parcial justificado | Abrir a porta a 90° sem o armário tombar |

Pedidos da reunião que não estão no docx: **câmera interna e externa** (proposta: 2 webcams), **monitor touch** (proposta: tela do notebook na demonstração; touch real fica como evolução), **regulagem de temperatura** (proposta: setpoint ajustável), **dupla confirmação** (N13).

---

## 5. Orçamento de energia

### 5.1 Como está hoje (2 × 12703 sem cooler, trava por relé, Mega no Vin)

Trilho 12 V, fonte de 10 A:

| Carga | Corrente | Origem |
|---|---:|---|
| Peltier C1, partida (ΔT = 0) | 3,05 A | [calc] 12 V ÷ 3,93 Ω, R do datasheet Huimao |
| Peltier C2, partida | 3,05 A | idem |
| Trava FE-91 | 0,50 A (2,0 A se for bobina de 6 Ω) | [ds] Eletrogate / [medir] |
| LM2596 → 3 relés (bobina 70 Ω → 71 mA cada) | 0,21 A em 5 V → ~0,10 A em 12 V (85% de eficiência [est]) | [ds] SRD-05VDC; [calc] |
| Mega + LCD + buzzer pelo Vin | ~0,15 A | [est] → [medir] 7.4 |
| **Pior caso** | **6,9 A** (8,4 A com trava de 2 A) | [calc] |
| Margem na fonte de 10 A | 31% (16%) | [calc] |
| Regime (pastilhas a ~2 A com ΔT grande) | ~4,7 A | [calc] |

A conta fecha na fonte, mas o problema não é a fonte: é o calor (item 1). O fusível de 10 A fica acima do pior caso.

Trilho 5 V (LM2596, 3 A [ds TI]): 3 relés × 71 mA + LEDs do módulo ≈ **0,23 A** (8%). Folga grande.

### 5.2 Como ficaria com a proposta (prévia, para a decisão)

| Carga | Corrente | Origem |
|---|---:|---|
| 1 × TEC1-12703, partida | 3,05 A | [calc] |
| Ventoinha do cooler do lado quente | ~0,2 A | [est] → etiqueta |
| Ventoinha 60 mm do lado frio | ~0,1 A | [est] → etiqueta |
| Trava | 0,5 A (2,0 A) | [ds] / [medir] |
| LM2596 → relés | ~0,10 A | [calc] |
| **Pior caso (Peltier + trava juntas)** | **4,0 A** (5,5 A) | [calc] |
| Margem na fonte de 10 A | 60% (45%) | [calc] |

Mega no USB do notebook (porta USB 2.0 de 500 mA, fusível do Mega de 500 mA [ds Arduino]): Mega ~70–100 mA [est] + LCD com luz ~20–30 mA [est] + leitor biométrico até ~120 mA [est, conferir no datasheet do modelo escolhido] + DS18B20 ~1 mA + buzzer ~30 mA [medir] ≈ **0,3 A**. Cabe, mas precisa ser medido (7.4). Os relés continuam no LM2596.

---

## 6. Contas

### 6.1 Peltier como está hoje (`calculos/termico_atual.py`)

Módulo [ds Huimao TES1-12703, Th = 25 °C]: Imax 3 A, Umax 15,2 V, Qmax 28,3 W, ΔTmax 67 K, ACR 3,88 Ω, máximo 125 °C. A Mixtou (vendedora da pastilha comprada) só publica "40 × 40, 15,5 V, 27 W", sem datasheet.

Parâmetros efetivos [calc]: S = Umax/Th = 51,0 mV/K · R = Umax(Th − ΔTmax)/(Imax·Th) = 3,93 Ω · K = Imax·Umax(Th − ΔTmax)/(2·Th·ΔTmax) = 0,264 W/K.

Dissipador 65 × 46 × 24 mm em convecção natural [calc]: volume 71,8 cm³ × resistência volumétrica de 500 a 800 cm³·K/W (Simons, Electronics Cooling, 2003) = **7 a 11 K/W**. Rodamos também 3 K/W como caso otimista.

Ambiente 25 °C, duas pastilhas no vão de trás fechado:

| Dissipador | I (A) | Th (°C) | Tc (°C) | Calor tirado da gaveta | Vão de trás | Gaveta |
|---:|---:|---:|---:|---:|---:|---:|
| 3 K/W | 1,97 | 108 | 24 | ~0 W | 34 °C | 25,0 °C |
| 7 K/W | 1,76 | **179** | 80 | −0,6 W (aquece) | 33 °C | 25,3 °C |
| 11 K/W | 1,63 | **236** | 126 | −1,1 W (aquece) | 32 °C | 25,5 °C |

Acima de ΔTmax o modelo é extrapolação. A conclusão não depende do número exato: qualquer dissipador acima de ~2 K/W leva o lado quente a mais de 100 °C, e aí o lado frio não fica abaixo do ambiente. Na prática a pastilha queima antes de chegar a esses números.

Tempo: com ~60 g de alumínio [est] (capacidade ~54 J/K) e 37 W, o dissipador sobe ~0,7 K/s no começo [calc]. Em 1 a 2 minutos já não dá para encostar a mão, o mesmo critério que a LISTA usa para desligar. Ou seja, a demonstração "ligar só pelo tempo da apresentação" duraria menos que a apresentação, e sem frio nenhum na gaveta.

### 6.2 Prévia da alternativa (modelo térmico do legado, trocando o módulo pela 12703)

Mesmo modelo do `calculos/termico.py` do legado (baia de uma gaveta C isolada, 6 aberturas por hora, ventoinha interna). Lado quente com cooler de CPU com ventoinha. As resistências de 0,5 e 1,0 K/W são [est] e precisam de medição.

| 1 × 12703 | Ambiente 25 °C | 28 °C | 32 °C |
|---|---:|---:|---:|
| XPS 50 mm, cooler 0,5 K/W | 0,7 °C | 3,2 °C | 6,5 °C |
| XPS 50 mm, cooler 1,0 K/W | 7,3 °C | 9,8 °C | 13,2 °C |
| XPS 25 mm, cooler 0,5 K/W | 10,5 °C | 13,2 °C | 16,8 °C |

Leitura: **uma** 12703 (que o grupo já tem) segura a faixa de 2–8 °C numa baia com 50 mm de XPS **se** o lado quente tiver um cooler bom (≤ 0,5 K/W). Com isolamento fino ou cooler fraco, não chega. Duas gavetas frias exigiriam o dobro de tudo e não cabem no orçamento de tempo.

---

## 7. Procedimentos de medição [medir]

7.1 **Fonte 12 V em vazio.** Multímetro em DC 20 V nos bornes V+ e V−, nada ligado. Esperado 12,0 V ± 5%. Ajustar no trimpot da fonte se tiver.

7.2 **Bobina da trava.** Trava desligada de tudo. Multímetro em Ω (escala 200) nos dois fios. Esperado ~24 Ω (FE-91 de 0,5 A). Se der ~6 Ω, a trava puxa 2 A: avisar antes de ligar.

7.3 **Resistência térmica do dissipador (só se quiserem aproveitar o passivo em outro lugar).** Resistor de potência ou a própria Peltier com potência conhecida, termômetro no dissipador e no ar. R = (T_dissipador − T_ar) / P depois de estabilizar. **Não fazer com a Peltier sem cooler**: desligar se passar de 60 °C.

7.4 **Corrente do Mega.** Multímetro em série (escala 200 mA) no cabo USB (adaptador USB com bornes) ou no fio do Vin. Medir com LCD aceso, buzzer tocando e leitor biométrico lendo.

7.5 **Corrente do buzzer.** Multímetro em série entre o pino 7 e o + do buzzer, com o pino em HIGH. Se passar de 20 mA, usar transistor.

7.6 **Relés no reset.** LED + resistor de 1 kΩ entre 5 V e o IN de cada relé (ou multímetro no IN). Apertar o reset do Mega 10 vezes e abrir o Monitor Serial 10 vezes. Nenhum relé pode estalar.

7.7 **LCD com cabo longo.** Ligar o LCD no Mega pelos 2,5 m de cabo de rede, antes de passar o cabo no armário. Escrever texto que muda a cada 100 ms por 5 min. Não pode aparecer caractere errado.

7.8 **Folga porta × gavetas.** Régua na frente do armário montado, encostada nas duas laterais. Medir a distância da régua até a frente de cada gaveta e de cada prateleira. Esse valor é a folga máxima para puxador.

---

## 8. Fontes consultadas (22/10/2026)

- Escopo: `referencias_externas/Projeto de Sistemas Embarcados/Dispensários Eletrônicos.docx` (texto extraído do XML).
- Reunião: `referencias_externas/Alinhamento_do_projeto.pdf` é manuscrito escaneado, sem texto extraível. Usada a transcrição do grupo.
- Peltier: [Beijing Huimao TES1-12703 (PDF)](https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/38/PELTIER-HUIMAO-TES1_2D00_12703T125.pdf) · [Mixtou TEC1-12703 40×40](https://www.mixtou.com.br/pastilha-termoeletrica-peltier-tec1-12703-40x40mm-15-5v-27w-1/p) (R$ 26,90 hoje)
- Trava: [Eletrogate FE-91](https://www.eletrogate.com/mini-trava-eletrica-solenoide) (12 V, 500 mA, R$ 48,90 hoje)
- Relé: [LCSC SRD-05VDC-SL-C](https://lcsc.com/product-detail/Power-Relays_Ningbo-Songle-Relay-SRD-05VDC-SL-C_C35449.html) (bobina 70 Ω, 360 mW) · [Electrokit](https://www.electrokit.com/en/rela-srd-1-pol-vaxlande-5v) (10 A)
- Conector de alavanca: [Element14 WAGO 221-413](https://sg.element14.com/wago/221-413/terminal-block-pluggable-3pos/dp/2534733) (32 A, 450 V, 0,2–4 mm²)
- Arduino Mega 2560: [docs.arduino.cc/hardware/mega-2560](https://docs.arduino.cc/hardware/mega-2560/) (Vin 7–12 V, 20 mA por pino, reset automático pelo DTR)
- ATmega2560: [datasheet Microchip](https://ww1.microchip.com/downloads/en/devicedoc/atmel-2549-8-bit-avr-microcontroller-atmega640-1280-1281-2560-2561_datasheet.pdf), seção I/O Ports
- LM2596: [TI](https://www.ti.com/lit/ds/symlink/lm2596.pdf) (3 A)
- Dissipadores em convecção natural: R. E. Simons, "Estimating Parallel Plate-Fin Heat Sink Thermal Resistance", *Electronics Cooling*, fev/2003
- A página do dissipador 65 × 46 × 24 da Usinainfo (link da LISTA) responde **404** hoje.
- Preços do legado: `referencias_externas/.../dispensario_interno/docs/lista_de_compras.csv` (consultados de 07 a 15/10; reconferir na Fase 2).

---

## 9. Situação de cada item em 23/10/2026

Legenda: **resolvido** (no projeto e com teste ou conta), **no papel** (projetado, mas depende de montagem ou medição), **pendente**.

| ID | O que foi feito | Onde | Situação |
|---|---|---|---|
| 1 | Peltier com cooler de CPU e ventoinha (Hyper 212), dissipador e ventoinha também do lado frio, baia isolada com EPS de 50 mm. Os coolers ficam do lado de fora da lateral esquerda, porque o vão de trás não tem acesso com o armário colado | DECISOES 1.0–1.2, `calculos/gaveta_fria.py`, `calculos/coolers_externos.py` | no papel: falta medir na bancada (teste 7 e 9) |
| 2 | Fusível térmico de 85 °C em série com cada Peltier, 3 DS18B20 e controle automático com histerese no firmware | `hardware/potencia.yaml`, `src/logica/termico.cpp` + 6 testes | resolvido (falta montar) |
| 3 | Nível inativo gravado antes de `pinMode(OUTPUT)` (lista `SAIDAS` gerada) | `armario_dispensador.ino`, `pinos.h` | resolvido no código; conferir na bancada (teste 3) |
| 4 | O Mega inicia com tudo desligado; a trava só abre com autenticação nova; o app abre a serial uma vez só | firmware, `app/hal/serial_mega.py` | resolvido |
| 5 | Liberação de emergência: 2 parafusos do batente dentro da cava do puxador | `armario/MANUAL_PORTA.md` 4 | no papel: testar no cupom |
| 6 | Bobina medida antes de ligar; F2 trocado por um de 4 A se der ~6 Ω; intertravamento cobre os 2 A | TESTES 0.1, DECISOES 1.4 | no papel: medir |
| 7 | Barramento de 12 V e de GND com conectores de alavanca, cada COM com o seu fio | LIGACOES 4 | resolvido no projeto |
| 8 | Fonte dentro da caixa da eletrônica, que cobre o borne; fonte fechada como alternativa na lista | DECISOES 1.5, LISTA | no papel |
| 9 | 20 usuários com ID e senha própria (SHA-256 com sal no Mega) + digital | `src/logica/memoria.*` + testes | resolvido |
| 10 | Auditoria só de acréscimo com HMAC encadeado no notebook + fila de eventos com número de sequência na EEPROM | `app/storage.py`, `src/logica/memoria.*` + testes | resolvido |
| 11 | 2 webcams (externa no tampo, interna na lateral direita), clipe por abertura com SHA-256 na auditoria | `app/cameras.py`, `app/core.py` + testes | resolvido com câmera simulada; testar com as webcams |
| 12 | Quiosque com CPF, MV simulado e API do legado reaproveitados | `app/` | resolvido (MV real fora do alcance) |
| 13 | Reed de volta, com pull-up (fio rompido = aberta) | `pinos.yaml`, firmware | resolvido (falta montar) |
| 14 | Mega na USB do notebook (bateria), estado e eventos na EEPROM, sessão no journal do SQLite | DECISOES 1.3, testes de reset | resolvido; testar na bancada (teste 10) |
| 15 | Convenção única: gaveta 1 = a de baixo | DECISOES, simulação, `app/semente.py` | resolvido |
| 16 | Dispensador documentado como estrutura passiva | README | resolvido |
| 17 | Porta afastada 9 mm das gavetas; puxadores das gavetas só embutidos; o gerador recusa folga abaixo de 5 mm | `armario/gerador/porta_colisao.py` | resolvido; medir as frentes reais |
| 18 | Todas as posições saem do `config.py` e do `layout.py`; furos e simulação gerados | `hardware/`, `docs/gerar_simulacao.py` | resolvido |
| N01, N02 | Dissipador frio com ventoinha; prensa com barra roscada e berço (sem cola quente nem nylon no lado quente) | LIGACOES 7 | no papel |
| N03 | Rotas novas por fora do armário; furos só nas laterais, conferidos contra prateleiras, nervuras e corrediças | `hardware/furos.py` | resolvido |
| N04 | Vin desligado (Mega na USB) | DECISOES 1.3 | resolvido |
| N05 | Buzzer passivo com volume por PWM e resistor de 1 kΩ; volume mais baixo à noite | firmware, `app/core.py` | resolvido; medir o volume (teste 4.6) |
| N06 | Teste do LCD com o cabo longo; adaptador I²C como plano B na lista | TESTES 4.1 | no papel |
| N07 | Câmera externa no tampo, sem furo na porta | DECISOES, simulação | resolvido |
| N08 | F2 de 2 A no ramo fino; o teste de potência confere bitola × fusível | `hardware/potencia.yaml`, `tests/test_pinos.py` | resolvido |
| N09 | Gerador da V2.3 corrigido, sem sobrescrever o LEIA_PRIMEIRO | `armario/gerador`, `tests/test_armario.py` | resolvido |
| N10 | Bloqueio do painel com o relógio do núcleo | `app/auth.py` | resolvido |
| N11 | Simulação refeita a partir do `config.py` | `docs/simulacao.html` | resolvido |
| N12 | Prefixos `rogi:` removidos | README, LIGACOES, LISTA (os antigos estão em `legado/`) | resolvido |
| N13 | Dupla confirmação: itens conferidos antes de liberar e quantidades confirmadas depois de fechar, com registro de divergência | `app/core.py` | resolvido |
| N14 | Autorização (`LIBERADO`) e abertura (`PORTA_ABERTA`) são eventos separados | firmware, app | resolvido |

### 9.1 Matriz RF/RNF com o que existe hoje

Todos os requisitos **Must** estão atendidos no software e testados com o Mega simulado, menos o RF04 (parcial, justificado: o MV real não foi liberado). Falta confirmar na montagem:

- **RF01 e RF07:** o leitor AS608 e as webcams reais.
- **RF12 e RNF08:** a baia fria, que precisa do teste de 30 minutos.
- **RNF14:** parcial justificado; na banca, grampos na mesa.
- **RNF13 (prazo):** a montagem e os testes de bancada são o caminho crítico até 18/11.

