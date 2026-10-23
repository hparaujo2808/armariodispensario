# Firmware do Arduino Mega

Sketch: `armario_dispensador/`. A lógica fica em `armario_dispensador/src/logica/`, em C++ sem `Arduino.h`; por isso é testada no PC. O `.ino` só liga essa lógica ao hardware.

| Arquivo | O que faz |
|---|---|
| `pinos.h` | **Gerado** de `hardware/pinos.yaml` por `hardware/gerar.py`. Não editar à mão |
| `src/logica/maquina.*` | Máquina de estados do acesso, sem `delay` (OCIOSO → ID/senha ou digital → espera o notebook ou libera sozinha → porta aberta → fechada; bloqueio depois de 3 erros) |
| `src/logica/termico.*` | Controle da baia fria: histerese, tempos mínimos, cortes (congelar, sensor, lado quente), partida escalonada e pausa durante a trava |
| `src/logica/memoria.*` | EEPROM: fila de 200 eventos com número de sequência, tabela de 20 usuários com hash da senha, parâmetros |
| `src/logica/protocolo.*` | Protocolo serial com o notebook (texto + CRC-8) |
| `src/logica/sha256.*` | Hash das senhas (a senha nunca fica gravada) |
| `src/logica/parametros.h` | Tempos e limites (vêm de `docs/DECISOES.md`) |

## Compilar e gravar

Instale o `arduino-cli` (no Mac: `brew install arduino-cli`), o núcleo do Mega e as bibliotecas, uma vez:

```bash
arduino-cli core install arduino:avr
```

```bash
arduino-cli lib install Keypad "Adafruit Fingerprint Sensor Library" OneWire DallasTemperature
```

Compilar:

```bash
arduino-cli compile --fqbn arduino:avr:mega --output-dir firmware/armario_dispensador/build firmware/armario_dispensador
```

Resultado em 22/10/2026: **30.856 bytes de flash (12%)** e **2.074 bytes de RAM (25%)**.

Gravar (troque a porta pela do Mega; veja com `arduino-cli board list`):

```bash
arduino-cli upload --fqbn arduino:avr:mega -p /dev/cu.usbmodem1101 firmware/armario_dispensador
```

Também abre e grava pela Arduino IDE, com as mesmas bibliotecas instaladas.

## Primeira vez

- Na primeira inicialização, a EEPROM é formatada e é criado o **usuário 1 com a senha 1357**. **Troquem pelo notebook** (`$SENHA`) antes de mostrar a alguém de fora.
- **Sensores DS18B20:** o firmware não sabe qual dos três é qual. Pelo notebook, veja a linha `TEMP` e aqueça um sensor com a mão para descobrir qual índice mudou. Depois mande `SET mapa=XYZ`, onde X é o índice da baia, Y o do cooler 1 e Z o do cooler 2. O padrão é `012`.
- **Leitor de digital:** se não estiver ligado, o firmware segue só com senha e registra `SENSOR_FALHA v=1000`. As digitais são cadastradas pelo notebook (`CAD u=3`) e ficam guardadas no próprio leitor, na posição igual ao número do usuário.

## Teclado

| Tecla | O que faz |
|---|---|
| Dígitos e `#` | ID do usuário (1 a 20) e `#`, depois a senha e `#` |
| `*` | Apaga e volta ao começo |
| `D` | Cancela uma retirada que está esperando o CPF no notebook |

## Segurança no código

- **Relés no reset:** cada saída recebe o nível desligado **antes** de `pinMode(OUTPUT)` (lista `SAIDAS` do `pinos.h`). Conferir na bancada (`docs/TESTES_DE_BANCADA.md`, passo 3).
- **Trava:** fica energizada no máximo 3 s e desliga assim que a porta abre.
- **Intertravamento:** a cada passada do laço, as Peltier desligam primeiro e a trava só energiza 20 ms depois; com a trava energizada, os relés das Peltier ficam desligados.
- **Relés com o Mega desligado:** o VCC dos LEDs do módulo vem do 5 V do Mega (sem o jumper JD-VCC). Sem USB, nenhum relé arma (`docs/DECISOES.md` 1.3, teste 3.6).
- **Baia que não esfria:** Peltier ligadas há 20 min com a baia acima de 6 °C e sem cair 1 °C → desliga, `FRIO_SEM_EFEITO`, nova tentativa em 30 min (pastilha solta ou prensa frouxa, que o sensor do cooler não percebe).
- **Leitor de digital:** depois de cada leitura, espera o dedo sair e mais 2 s. Os erros de digital e de senha são contados separados (3 de cada bloqueiam por 30 s). O bloqueio fica na EEPROM: tirar a USB não zera.
- **Porta aberta logo depois da liberação expirar** (até 5 s): conta como abertura do último usuário liberado (`PORTA_ABERTA` com `v=1`), porque o reed só abre com a porta já afastada.
- **Mapa dos sensores:** `SET mapa=` só aceita uma permutação de 0, 1 e 2 (cada sensor com um papel só).
- **Watchdog de 2 s:** se o laço travar, o Mega reinicia com tudo desligado. Ao voltar:
  - se a porta estiver aberta, registra `RECUPERADO`;
  - os eventos que ainda não foram confirmados continuam na EEPROM e são reenviados.
- **Abrir a serial reinicia o Mega** (DTR). Isso é seguro: ele volta com a trava desligada e nunca libera sem uma autenticação nova.
- **Notebook fora do ar há mais de 5 s:** o Mega libera sozinho depois da autenticação (`MODO_AUTONOMO`) e guarda os eventos para mandar depois. Nesse caso não há CPF nem vídeo: é uma exceção aos RF03 e RF07, que a farmácia aceita ou não. Com `SET auto=0` (no app: `modo_autonomo: false`), o Mega recusa e mostra "Sistema fora do ar".
- **Horário:** o Mega não tem relógio. A linha `ST` leva o `b` (número da inicialização) e o `ms` atual. Com isso, o notebook calcula a hora de cada evento guardado da mesma inicialização e marca `hora_estimada` na auditoria. Eventos de uma inicialização anterior ficam com a hora de chegada.
- **ACK cumulativo:** o notebook só confirma até o último evento sem buraco. Se um evento sumir da fila, o notebook espera 60 s e registra `MEGA_EVENTOS_PERDIDOS`. Se a EEPROM for formatada (o `seq` volta a 1), o notebook abre uma nova época e registra `MEGA_SEQUENCIA_REINICIADA`.

## Protocolo serial

115200 baud, uma mensagem por linha, `$<corpo>*<CRC-8 em hex>`. A descrição completa está em `src/logica/protocolo.h`.

| Sentido | Mensagem | Para quê |
|---|---|---|
| Mega → notebook | `EV seq=12 t=AUTH_OK u=3 v=1 ms=123456 b=7` | Evento. Repete até receber `ACK` |
| Mega → notebook | `ST e=OCIOSO u=0 pend=2 b=7 ms=123999` | Estado, a cada 1 s (com o relógio do Mega) |
| Mega → notebook | `TEMP baia=54 q1=401 q2=398 ok=111 p1=1 p2=1 al=0 v12=12040` | Temperaturas (décimos de °C) e 12 V (mV), a cada 2 s |
| Mega → notebook | `OK id=5` / `ERRO id=5 m=ESTADO` | Resposta a um comando |
| notebook → Mega | `HELLO`, `PING` | Mandar a cada 1 s (é como o Mega sabe que o notebook está vivo) |
| notebook → Mega | `ACK seq=12` | Confirma os eventos até o 12 |
| notebook → Mega | `LIB id=5 u=3` | Libera o usuário 3 depois do CPF e da confirmação |
| notebook → Mega | `CANC id=6`, `CAD id=7 u=3`, `SENHA id=8 u=3 pin=2468`, `DEL id=9 u=3` | Cancelar, cadastrar digital, trocar senha, desativar |
| notebook → Mega | `SET id=10 sp=50` / `vol=30` / `alarme=30` / `mapa=012` / `auto=1` | Setpoint, volume, alarme da porta, mapa dos sensores, modo autônomo |

Números dos eventos: `src/logica/tipos.h` (`enum class Ev`). Não renumerar: eles ficam gravados na EEPROM.

## Testes

Na raiz do repositório:

```bash
pytest tests/test_firmware.py -v
```

O comando compila e roda os 32 testes da lógica no PC (máquina de estados, bloqueio, trava, alarme de porta, abertura sem autorização e tardia, reset com a porta aberta e bloqueado, fila na EEPROM, hash das senhas, controle térmico, intertravamento, baia que não esfria) e compila para o Mega se houver `arduino-cli`.

## Simulação (Wokwi)

`simulacao/diagram.json` é **gerado** de `hardware/pinos.yaml`. Na simulação:
- os relés viram LEDs, acesos quando o pino vai a LOW;
- a chave deslizante faz o papel do reed (para a esquerda = porta fechada);
- um potenciômetro faz o papel do 12 V;
- há 3 DS18B20.

O Wokwi não tem o leitor AS608, então a simulação testa só a senha. Para rodar:
1. Instale a extensão Wokwi no VS Code.
2. Compile com o comando de "Compilar", que gera o `.hex` em `build/`.
3. Abra `simulacao/diagram.json` e dê play.

A extensão pede uma conta gratuita do Wokwi.
