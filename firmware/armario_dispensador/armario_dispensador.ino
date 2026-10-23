// Armário dispensador — firmware do Arduino Mega 2560.
//
// A lógica (máquina de estados, controle térmico, usuários, fila de eventos,
// protocolo) fica em src/logica e é testada no PC (firmware/testes). Este
// arquivo só liga essa lógica ao hardware. Pinos: pinos.h, gerado de
// hardware/pinos.yaml. Protocolo serial: src/logica/protocolo.h.
//
// Laço principal sem delay(): cada parte roda quando chega a vez dela.

#include <Adafruit_Fingerprint.h>
#include <DallasTemperature.h>
#include <EEPROM.h>
#include <Keypad.h>
#include <LiquidCrystal.h>
#include <OneWire.h>
#include <avr/wdt.h>
#include <string.h>

#include "pinos.h"
#include "src/logica/maquina.h"
#include "src/logica/memoria.h"
#include "src/logica/parametros.h"
#include "src/logica/protocolo.h"
#include "src/logica/termico.h"

using namespace armario;

// Usuário e senha criados na primeira vez que a EEPROM é formatada.
// TROQUE pelo notebook ($SENHA) antes de usar com gente de fora.
const uint8_t USUARIO_INICIAL = 1;
const char SENHA_INICIAL[] = "1357";

// ------------------------------------------------------------ EEPROM --
class EepromMega : public Armazenamento {
 public:
  uint8_t ler(uint16_t e) const override { return EEPROM.read(e); }
  void escrever(uint16_t e, uint8_t v) override { EEPROM.update(e, v); }   // só grava se mudou
  uint16_t tamanho() const override { return EEPROM.length(); }
};

EepromMega eeprom;
Memoria memoria(eeprom);
Usuarios usuarios(memoria);

// ------------------------------------------------------------ serial --
void enviar(const char* corpo) {
  char linha[100];
  if (empacotar(corpo, linha, sizeof linha)) Serial.print(linha);
}

class SaidaMega : public Saida {
 public:
  bool online = false;
  void evento(Ev tipo, uint8_t usuario, int16_t valor) override {
    uint32_t seq = memoria.registrar(tipo, usuario, valor, millis());
    if (!online) return;                      // fica na fila e vai quando o notebook voltar
    Registro r;
    char corpo[90];
    if (memoria.ler(seq, r) && corpo_evento(r, corpo, sizeof corpo)) enviar(corpo);
  }
};

SaidaMega saida;
Maquina maquina(saida, usuarios, memoria);
Termico termico(saida);

// ---------------------------------------------------------- periféricos --
LiquidCrystal lcd(PINO_LCD_RS, PINO_LCD_E, PINO_LCD_D4, PINO_LCD_D5, PINO_LCD_D6, PINO_LCD_D7);

const char TECLAS[4][4] = {{'1', '2', '3', 'A'}, {'4', '5', '6', 'B'}, {'7', '8', '9', 'C'}, {'*', '0', '#', 'D'}};
byte linhas_teclado[4] = {PINO_TECLADO_L1, PINO_TECLADO_L2, PINO_TECLADO_L3, PINO_TECLADO_L4};
byte colunas_teclado[4] = {PINO_TECLADO_C1, PINO_TECLADO_C2, PINO_TECLADO_C3, PINO_TECLADO_C4};
Keypad teclado(makeKeymap(TECLAS), linhas_teclado, colunas_teclado, 4, 4);

Adafruit_Fingerprint leitor(&Serial1);
bool leitor_ok = false;

OneWire barramento(PINO_ONEWIRE);
DallasTemperature sensores(&barramento);

// ------------------------------------------------------------ estado --
uint32_t t_leitor = 0, t_temp = 0, t_status = 0, t_reenvio = 0, t_tempmsg = 0, t_energia = 0;
bool pedido_temp = false;
Leituras leituras = {false, false, false, 0, 0, 0};
bool porta_lida = false, porta_estavel = false;
uint32_t porta_mudou = 0;
bool energia_ok = true, energia_lida = true;
uint32_t energia_mudou = 0;
uint16_t mv_12v = 0;
char lcd1[17] = "", lcd2[17] = "";
char rx[100];
uint8_t nrx = 0;
uint8_t volume = par::VOLUME_PADRAO;

// som: bipes de mesma duração separados por pausas iguais, sem bloquear
uint32_t som_troca = 0;       // quando liga ou desliga de novo (0 = parado)
bool som_ligado = false;
uint8_t som_restantes = 0;    // bipes que ainda faltam começar
uint16_t som_ms = 0;
uint8_t som_duty = 0;

// cadastro de digital: passos sem bloquear
uint8_t cad_passo = 0;
uint32_t cad_t = 0;

// ---------------------------------------------------------- saídas --
void saida_digital(uint8_t pino, uint8_t ativo, bool ligar) { digitalWrite(pino, ligar ? ativo : !ativo); }

void iniciar_saidas_seguras() {
  // Antes de pinMode(OUTPUT): grava o nível inativo. Assim o pino passa de
  // entrada direto para "relé desligado", sem pulso (auditoria, item 3).
  for (uint8_t i = 0; i < sizeof(SAIDAS); i++) {
    digitalWrite(SAIDAS[i], SAIDAS_INATIVO[i]);
    pinMode(SAIDAS[i], OUTPUT);
  }
}

uint32_t t_peltier_ligada = 0;          // última passada com alguma Peltier ligada

void aplicar_reles(uint32_t agora) {
  // intertravamento (docs/DECISOES.md 1.4): primeiro as Peltier desligam; a trava só
  // energiza TRAVA_ATRASO_MS depois. Com a trava ligada, as Peltier nunca ligam.
  bool quer_trava = maquina.trava();
  termico.intertravar(quer_trava, agora);
  bool p1 = termico.peltier1() && !quer_trava;
  bool p2 = termico.peltier2() && !quer_trava;
  saida_digital(PINO_RELE_PELTIER_1, ATIVO_RELE_PELTIER_1, p1);
  saida_digital(PINO_RELE_PELTIER_2, ATIVO_RELE_PELTIER_2, p2);
  if (p1 || p2) t_peltier_ligada = agora;
  bool trava = quer_trava && !p1 && !p2 && agora - t_peltier_ligada >= par::TRAVA_ATRASO_MS;
  saida_digital(PINO_RELE_TRAVA, ATIVO_RELE_TRAVA, trava);
  saida_digital(PINO_RELE_LIVRE, ATIVO_RELE_LIVRE, false);
}

void tocar(Som s) {
  if (s == Som::NENHUM) return;
  uint8_t bipes;
  switch (s) {
    case Som::TECLA: bipes = 1; som_ms = 30; break;
    case Som::OK: bipes = 2; som_ms = 80; break;
    case Som::ERRO: bipes = 1; som_ms = 400; break;
    case Som::ALARME: bipes = 1; som_ms = 200; break;
    default: return;
  }
  som_duty = (uint8_t)((uint16_t)volume * 127 / 100);   // 50% de ciclo = volume máximo
  analogWrite(PINO_BUZZER, som_duty);
  som_ligado = true;
  som_restantes = bipes - 1;
  som_troca = millis() + som_ms;
}

void atualizar_som(uint32_t agora) {
  if (som_troca && (int32_t)(agora - som_troca) >= 0) {
    if (som_ligado) {                         // fim de um bipe
      analogWrite(PINO_BUZZER, 0);
      som_ligado = false;
      som_troca = som_restantes ? agora + som_ms : 0;
    } else {                                  // fim da pausa: próximo bipe
      analogWrite(PINO_BUZZER, som_duty);
      som_ligado = true;
      som_restantes--;
      som_troca = agora + som_ms;
    }
  }
  static uint32_t t_alarme = 0;
  if (maquina.alarme() && agora - t_alarme >= 1000) {   // alarme: 200 ms a cada 1 s, volume ajustável (RNF10)
    t_alarme = agora;
    tocar(Som::ALARME);
  }
}

void atualizar_lcd() {
  const char* a = maquina.linha1();
  const char* b = maquina.linha2();
  if (strcmp(a, lcd1)) {
    strncpy(lcd1, a, 16);
    lcd.setCursor(0, 0);
    lcd.print(lcd1);
  }
  if (strcmp(b, lcd2)) {
    strncpy(lcd2, b, 16);
    lcd.setCursor(0, 1);
    lcd.print(lcd2);
  }
}

// --------------------------------------------------------- entradas --
void ler_porta(uint32_t agora) {
  bool aberta = digitalRead(PINO_SENSOR_PORTA) != ATIVO_SENSOR_PORTA;   // LOW = ímã perto = fechada
  if (aberta != porta_lida) {
    porta_lida = aberta;
    porta_mudou = agora;
  }
  if (porta_lida != porta_estavel && agora - porta_mudou >= par::REED_FILTRO_MS) {
    porta_estavel = porta_lida;
    maquina.porta(porta_estavel, agora);
  }
}

void ler_energia(uint32_t agora) {
  if (agora - t_energia < 100) return;
  t_energia = agora;
  // divisor 4,7 kΩ / 2,2 kΩ: V12 = VA0 × 6,9 / 2,2
  mv_12v = (uint16_t)((uint32_t)analogRead(PINO_MEDE_12V) * 5000UL * 69UL / (1023UL * 22UL));
  bool ok = energia_ok ? mv_12v > par::ENERGIA_FALTA_MV : mv_12v > par::ENERGIA_VOLTA_MV;
  if (ok != energia_lida) {
    energia_lida = ok;
    energia_mudou = agora;
  }
  if (energia_lida != energia_ok && agora - energia_mudou >= par::ENERGIA_FILTRO_MS) {
    energia_ok = energia_lida;
    saida.evento(energia_ok ? Ev::ENERGIA_VOLTA : Ev::ENERGIA_FALTA, 0, (int16_t)(mv_12v / 10));
  }
}

void ler_temperaturas(uint32_t agora) {
  // conversão sem esperar: pede, e lê 800 ms depois (DS18B20 leva 750 ms em 12 bits)
  if (!pedido_temp && agora - t_temp >= 1000) {
    sensores.requestTemperatures();
    pedido_temp = true;
    t_temp = agora;
  } else if (pedido_temp && agora - t_temp >= 800) {
    pedido_temp = false;
    float t[3];
    bool ok[3];
    for (uint8_t i = 0; i < 3; i++) {
      t[i] = sensores.getTempCByIndex(memoria.mapa_sensor(i));
      ok[i] = t[i] != DEVICE_DISCONNECTED_C && t[i] != 85.0f;   // 85,0 = valor de quando o sensor reinicia
    }
    leituras = {ok[0], ok[1], ok[2], (int16_t)(t[0] * 10), (int16_t)(t[1] * 10), (int16_t)(t[2] * 10)};
    termico.atualizar(leituras, maquina.trava(), agora);
  }
}

bool esperar_tirar_dedo = false;        // depois de uma leitura: um dedo parado não vira 3 erros
uint32_t t_dedo_saiu = 0;

void ler_leitor(uint32_t agora) {
  if (!leitor_ok || agora - t_leitor < 250) return;
  t_leitor = agora;
  if (maquina.estado() == Estado::OCIOSO) {
    uint8_t img = leitor.getImage();
    if (esperar_tirar_dedo) {
      if (img == FINGERPRINT_NOFINGER) {
        esperar_tirar_dedo = false;
        t_dedo_saiu = agora;
      }
      return;
    }
    if (agora - t_dedo_saiu < par::DIGITAL_INTERVALO_MS) return;   // e mais um intervalo antes da próxima
    if (img != FINGERPRINT_OK) return;   // sem dedo: volta logo
    if (leitor.image2Tz() != FINGERPRINT_OK) return;
    esperar_tirar_dedo = true;
    if (leitor.fingerFastSearch() == FINGERPRINT_OK) maquina.digital(leitor.fingerID, agora);
    else maquina.digital(-1, agora);
    return;
  }
  if (maquina.estado() != Estado::CADASTRANDO) {
    cad_passo = 0;
    return;
  }
  // cadastro: dedo -> tira -> dedo de novo -> grava na posição = número do usuário
  uint8_t u = maquina.usuario();
  switch (cad_passo) {
    case 0:
      if (leitor.getImage() == FINGERPRINT_OK && leitor.image2Tz(1) == FINGERPRINT_OK) {
        cad_passo = 1;
        cad_t = agora;
        lcd.setCursor(0, 1);
        lcd.print("Tire o dedo     ");
      }
      break;
    case 1:
      if (leitor.getImage() == FINGERPRINT_NOFINGER && agora - cad_t > 500) {
        cad_passo = 2;
        lcd.setCursor(0, 1);
        lcd.print("Ponha de novo   ");
      }
      break;
    case 2:
      if (leitor.getImage() == FINGERPRINT_OK && leitor.image2Tz(2) == FINGERPRINT_OK) {
        bool ok = leitor.createModel() == FINGERPRINT_OK && leitor.storeModel(u) == FINGERPRINT_OK;
        maquina.cadastro_terminou(ok, u, agora);
        cad_passo = 0;
        lcd1[0] = 0;   // força redesenhar
      }
      break;
  }
}

// ---------------------------------------------------------- protocolo --
void responder(long id, bool ok, const char* motivo = "") {
  char c[60];
  if (ok) snprintf(c, sizeof c, "OK id=%ld", id);
  else snprintf(c, sizeof c, "ERRO id=%ld m=%s", id, motivo);
  enviar(c);
}

// "201" sim; "000" ou "013" não: cada sensor só pode ter um papel, senão o corte a 60 °C fica cego
bool mapa_valido(const char* t) {
  if (!t || strlen(t) != 3) return false;
  bool usado[3] = {false, false, false};
  for (uint8_t i = 0; i < 3; i++) {
    if (t[i] < '0' || t[i] > '2' || usado[t[i] - '0']) return false;
    usado[t[i] - '0'] = true;
  }
  return true;
}

void tratar(const Mensagem& m, uint32_t agora) {
  maquina.notebook_vivo(agora);
  long id = m.numero("id", 0);
  if (!strcmp(m.tipo, "HELLO")) {
    t_reenvio = 0;                       // reenvia os pendentes já
  } else if (!strcmp(m.tipo, "PING")) {
  } else if (!strcmp(m.tipo, "ACK")) {
    memoria.confirmar((uint32_t)m.numero("seq", 0));
  } else if (!strcmp(m.tipo, "LIB")) {
    responder(id, maquina.cmd_liberar((uint8_t)m.numero("u", 0), agora), "ESTADO");
  } else if (!strcmp(m.tipo, "CANC")) {
    responder(id, maquina.cmd_cancelar(agora), "ESTADO");
  } else if (!strcmp(m.tipo, "CAD")) {
    bool ok = leitor_ok && maquina.cmd_cadastrar((uint8_t)m.numero("u", 0), agora);
    responder(id, ok, leitor_ok ? "ESTADO" : "SEM_LEITOR");
  } else if (!strcmp(m.tipo, "SENHA")) {
    uint8_t u = (uint8_t)m.numero("u", 0);
    const char* pin = m.texto("pin");
    bool ok = pin && usuarios.definir_senha(u, pin, (uint16_t)m.numero("sal", (long)(micros() & 0xFFFF)));
    if (ok) saida.evento(Ev::SENHA_ALTERADA, u, 0);
    responder(id, ok, "SENHA_INVALIDA");
  } else if (!strcmp(m.tipo, "DEL")) {
    uint8_t u = (uint8_t)m.numero("u", 0);
    if (leitor_ok && usuarios.digital_de(u) != 0xFF) leitor.deleteModel(usuarios.digital_de(u));
    responder(id, usuarios.desativar(u), "USUARIO");
  } else if (!strcmp(m.tipo, "SET")) {
    bool ok = false;
    if (m.tem("sp")) { termico.definir_setpoint((int16_t)m.numero("sp")); memoria.salvar_setpoint(termico.setpoint()); ok = true; }
    if (m.tem("vol")) { long v = m.numero("vol"); if (v >= 0 && v <= 100) { volume = (uint8_t)v; memoria.salvar_volume(volume); ok = true; } }
    if (m.tem("alarme")) { long s = m.numero("alarme"); if (s >= 5 && s <= 600) { maquina.definir_alarme_porta_ms((uint32_t)s * 1000); memoria.salvar_alarme_porta_s((uint16_t)s); ok = true; } }
    if (m.tem("mapa") && mapa_valido(m.texto("mapa"))) {   // ex.: mapa=201 -> baia é o sensor 2, cooler 1 o 0, cooler 2 o 1
      for (uint8_t i = 0; i < 3; i++) memoria.salvar_mapa_sensor(i, (uint8_t)(m.texto("mapa")[i] - '0'));
      ok = true;
    }
    if (m.tem("auto")) { bool p = m.numero("auto") != 0; maquina.permitir_autonomo(p); memoria.salvar_autonomo(p); ok = true; }
    responder(id, ok, "PARAMETRO");
  } else {
    responder(id, false, "COMANDO");
  }
}

void ler_serial(uint32_t agora) {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\n') {
      rx[nrx] = 0;
      Mensagem m;
      if (analisar(rx, m)) tratar(m, agora);
      nrx = 0;
    } else if (nrx < sizeof(rx) - 1) {
      rx[nrx++] = ch;
    } else {
      nrx = 0;                           // linha longa demais: descarta
    }
  }
}

void enviar_periodicos(uint32_t agora) {
  saida.online = maquina.notebook_online(agora);
  if (!saida.online) return;
  if (agora - t_reenvio >= 1000) {       // reenvia até 3 eventos não confirmados por segundo
    t_reenvio = agora;
    uint32_t s = memoria.primeiro_pendente();
    for (uint8_t k = 0; k < 3 && s < memoria.proximo_seq(); k++, s++) {
      Registro r;
      char corpo[90];
      if (memoria.ler(s, r) && corpo_evento(r, corpo, sizeof corpo)) enviar(corpo);
    }
  }
  if (agora - t_status >= 1000) {
    t_status = agora;
    char c[80];
    // b e ms: o notebook usa para datar os eventos guardados enquanto ele estava fora do ar
    snprintf(c, sizeof c, "ST e=%s u=%u pend=%u b=%u ms=%lu", nome_estado(maquina.estado()), maquina.usuario(),
             memoria.pendentes(), memoria.boot(), (unsigned long)agora);
    enviar(c);
  }
  if (agora - t_tempmsg >= 2000) {
    t_tempmsg = agora;
    char c[90];
    snprintf(c, sizeof c, "TEMP baia=%d q1=%d q2=%d ok=%u%u%u p1=%u p2=%u al=%u v12=%u", leituras.baia, leituras.q1,
             leituras.q2, leituras.baia_ok, leituras.q1_ok, leituras.q2_ok, termico.peltier1(), termico.peltier2(),
             termico.em_alarme(), mv_12v);
    enviar(c);
  }
}

// ------------------------------------------------------------ setup --
void setup() {
  iniciar_saidas_seguras();              // primeira coisa: relés desligados
  MCUSR = 0;
  wdt_disable();

  // buzzer passivo: Timer 4 (pinos 6, 7 e 8) a ~3,9 kHz. O pino 8 é relé e só usa digitalWrite.
  TCCR4B = (TCCR4B & 0xF8) | 0x02;

  Serial.begin(115200);
  lcd.begin(16, 2);
  lcd.print("Iniciando...");
  pinMode(PINO_SENSOR_PORTA, INPUT_PULLUP);

  bool novo = memoria.iniciar();
  if (novo) usuarios.definir_senha(USUARIO_INICIAL, SENHA_INICIAL, 0x5A17);
  termico.definir_setpoint(memoria.setpoint());
  volume = memoria.volume();
  maquina.definir_alarme_porta_ms((uint32_t)memoria.alarme_porta_s() * 1000);
  maquina.permitir_autonomo(memoria.autonomo());

  sensores.begin();
  sensores.setResolution(12);
  sensores.setWaitForConversion(false);

  leitor.begin(57600);
  leitor_ok = leitor.verifyPassword();
  if (!leitor_ok) saida.evento(Ev::SENSOR_FALHA, 0, 1000);   // 1000 = leitor de digital ausente

  porta_lida = porta_estavel = digitalRead(PINO_SENSOR_PORTA) != ATIVO_SENSOR_PORTA;
  maquina.iniciar(porta_estavel, millis());
  lcd.clear();
  wdt_enable(WDTO_2S);
}

void loop() {
  wdt_reset();
  uint32_t agora = millis();
  ler_serial(agora);
  ler_porta(agora);
  ler_energia(agora);
  char k = teclado.getKey();
  if (k) maquina.tecla(k, agora);
  ler_leitor(agora);
  ler_temperaturas(agora);
  maquina.tick(agora);
  aplicar_reles(agora);
  tocar(maquina.som());
  atualizar_som(agora);
  atualizar_lcd();
  enviar_periodicos(agora);
}
