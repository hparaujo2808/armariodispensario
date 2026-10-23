// Tipos comuns da lógica do armário. Sem Arduino.h: compila no PC para os testes.
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace armario {

enum class Estado : uint8_t {
  OCIOSO = 0,
  DIGITANDO_ID,
  DIGITANDO_SENHA,
  AGUARDANDO_NOTEBOOK,   // autenticado; o notebook pede o CPF e manda LIBERAR
  LIBERADO,              // trava energizada (no máximo TRAVA_MAX_MS)
  PORTA_ABERTA,
  BLOQUEADO,
  CADASTRANDO,           // cadastro de digital pedido pelo notebook
};

// Tipos de evento. O número vai na EEPROM e no protocolo: não renumerar.
enum class Ev : uint8_t {
  NENHUM = 0,
  BOOT = 1,
  AUTH_OK = 2,
  AUTH_FALHA = 3,
  BLOQUEIO = 4,
  LIBERADO = 5,
  PORTA_ABERTA = 6,
  PORTA_FECHADA = 7,
  PORTA_ABERTA_TEMPO = 8,
  ABERTURA_NAO_AUTORIZADA = 9,
  LIBERACAO_EXPIROU = 10,
  CANCELADO = 11,
  TEMP_ALARME = 12,
  TEMP_NORMAL = 13,
  SENSOR_FALHA = 14,
  CORTE_QUENTE = 15,
  ENERGIA_FALTA = 16,
  ENERGIA_VOLTA = 17,
  DIGITAL_CADASTRADA = 18,
  SENHA_ALTERADA = 19,
  RECUPERADO = 20,       // reiniciou com a porta aberta
  MODO_AUTONOMO = 21,    // liberou sem o notebook (notebook fora do ar)
  FRIO_SEM_EFEITO = 22,  // Peltier ligadas há 20 min sem a baia esfriar: desliga e alarma
};

const char* nome_evento(Ev e);
const char* nome_estado(Estado e);

// Registro de evento guardado na EEPROM: 16 bytes.
struct Registro {
  uint32_t seq;      // número de sequência, nunca repete (sobrevive a reset)
  uint32_t ms;       // millis() no momento do evento
  uint16_t boot;     // contador de inicializações
  uint8_t tipo;      // Ev
  uint8_t usuario;   // 0 = nenhum
  int16_t valor;     // depende do tipo (temperatura em décimos de °C, método de autenticação, etc.)
  uint16_t crc;      // CRC-16 dos 14 bytes anteriores
};
static_assert(sizeof(Registro) == 16, "Registro precisa ter 16 bytes");

enum class Metodo : uint8_t { NENHUM = 0, DIGITAL = 1, SENHA = 2, NOTEBOOK = 3 };

enum class Som : uint8_t { NENHUM = 0, TECLA, OK, ERRO, ALARME };

// Memória persistente (EEPROM no Mega, vetor nos testes)
class Armazenamento {
 public:
  virtual ~Armazenamento() {}
  virtual uint8_t ler(uint16_t endereco) const = 0;
  virtual void escrever(uint16_t endereco, uint8_t valor) = 0;   // só grava se mudou
  virtual uint16_t tamanho() const = 0;
};

// Quem recebe os eventos (fila persistente + envio ao notebook)
class Saida {
 public:
  virtual ~Saida() {}
  virtual void evento(Ev tipo, uint8_t usuario, int16_t valor) = 0;
};

uint16_t crc16(const uint8_t* dados, size_t n);
uint8_t crc8(const char* texto, size_t n);

}  // namespace armario
