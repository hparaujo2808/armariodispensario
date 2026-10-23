#include "tipos.h"

namespace armario {

const char* nome_evento(Ev e) {
  switch (e) {
    case Ev::BOOT: return "BOOT";
    case Ev::AUTH_OK: return "AUTH_OK";
    case Ev::AUTH_FALHA: return "AUTH_FALHA";
    case Ev::BLOQUEIO: return "BLOQUEIO";
    case Ev::LIBERADO: return "LIBERADO";
    case Ev::PORTA_ABERTA: return "PORTA_ABERTA";
    case Ev::PORTA_FECHADA: return "PORTA_FECHADA";
    case Ev::PORTA_ABERTA_TEMPO: return "PORTA_ABERTA_TEMPO";
    case Ev::ABERTURA_NAO_AUTORIZADA: return "ABERTURA_NAO_AUTORIZADA";
    case Ev::LIBERACAO_EXPIROU: return "LIBERACAO_EXPIROU";
    case Ev::CANCELADO: return "CANCELADO";
    case Ev::TEMP_ALARME: return "TEMP_ALARME";
    case Ev::TEMP_NORMAL: return "TEMP_NORMAL";
    case Ev::SENSOR_FALHA: return "SENSOR_FALHA";
    case Ev::CORTE_QUENTE: return "CORTE_QUENTE";
    case Ev::ENERGIA_FALTA: return "ENERGIA_FALTA";
    case Ev::ENERGIA_VOLTA: return "ENERGIA_VOLTA";
    case Ev::DIGITAL_CADASTRADA: return "DIGITAL_CADASTRADA";
    case Ev::SENHA_ALTERADA: return "SENHA_ALTERADA";
    case Ev::RECUPERADO: return "RECUPERADO";
    case Ev::MODO_AUTONOMO: return "MODO_AUTONOMO";
    case Ev::FRIO_SEM_EFEITO: return "FRIO_SEM_EFEITO";
    default: return "?";
  }
}

const char* nome_estado(Estado e) {
  switch (e) {
    case Estado::OCIOSO: return "OCIOSO";
    case Estado::DIGITANDO_ID: return "DIGITANDO_ID";
    case Estado::DIGITANDO_SENHA: return "DIGITANDO_SENHA";
    case Estado::AGUARDANDO_NOTEBOOK: return "AGUARDANDO_NOTEBOOK";
    case Estado::LIBERADO: return "LIBERADO";
    case Estado::PORTA_ABERTA: return "PORTA_ABERTA";
    case Estado::BLOQUEADO: return "BLOQUEADO";
    case Estado::CADASTRANDO: return "CADASTRANDO";
  }
  return "?";
}

// CRC-16/CCITT-FALSE
uint16_t crc16(const uint8_t* d, size_t n) {
  uint16_t c = 0xFFFF;
  for (size_t i = 0; i < n; i++) {
    c ^= (uint16_t)d[i] << 8;
    for (uint8_t b = 0; b < 8; b++) c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1);
  }
  return c;
}

// CRC-8 (polinômio 0x07), usado no protocolo serial
uint8_t crc8(const char* t, size_t n) {
  uint8_t c = 0;
  for (size_t i = 0; i < n; i++) {
    c ^= (uint8_t)t[i];
    for (uint8_t b = 0; b < 8; b++) c = (c & 0x80) ? (uint8_t)((c << 1) ^ 0x07) : (uint8_t)(c << 1);
  }
  return c;
}

}  // namespace armario
