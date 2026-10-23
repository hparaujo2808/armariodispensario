#include "memoria.h"

#include <string.h>

#include "parametros.h"
#include "sha256.h"

namespace armario {

// ------------------------------------------------------------ Memoria --
uint32_t Memoria::ler32(uint16_t e) const {
  return (uint32_t)a_.ler(e) | (uint32_t)a_.ler(e + 1) << 8 | (uint32_t)a_.ler(e + 2) << 16 | (uint32_t)a_.ler(e + 3) << 24;
}
void Memoria::escrever32(uint16_t e, uint32_t v) {
  for (uint8_t i = 0; i < 4; i++) a_.escrever(e + i, (uint8_t)(v >> (8 * i)));
}
uint16_t Memoria::ler16(uint16_t e) const { return (uint16_t)(a_.ler(e) | a_.ler(e + 1) << 8); }
void Memoria::escrever16(uint16_t e, uint16_t v) {
  a_.escrever(e, (uint8_t)v);
  a_.escrever(e + 1, (uint8_t)(v >> 8));
}

void Memoria::formatar() {
  for (uint16_t i = 0; i < mem::FILA; i++) a_.escrever(i, 0xFF);
  escrever16(0, mem::MAGICO);
  a_.escrever(2, mem::VERSAO);
  escrever16(3, 0);
  escrever32(5, 1);
  escrever32(9, 0);
  a_.escrever(13, (uint8_t)Estado::OCIOSO);
  escrever16(14, (uint16_t)par::SETPOINT_PADRAO);
  escrever16(16, (uint16_t)(par::ALARME_PORTA_MS_PADRAO / 1000));
  a_.escrever(18, par::VOLUME_PADRAO);
  for (uint8_t i = 0; i < 3; i++) a_.escrever(19 + i, i);
  a_.escrever(22, 1);
}

bool Memoria::iniciar() {
  bool novo = ler16(0) != mem::MAGICO || a_.ler(2) != mem::VERSAO;
  if (novo) formatar();
  boot_ = (uint16_t)(ler16(3) + 1);
  escrever16(3, boot_);
  seq_ = ler32(5);
  ack_ = ler32(9);
  if (ack_ >= seq_) ack_ = seq_ - 1;
  return novo;
}

uint32_t Memoria::registrar(Ev tipo, uint8_t usuario, int16_t valor, uint32_t ms) {
  Registro r;
  r.seq = seq_;
  r.ms = ms;
  r.boot = boot_;
  r.tipo = (uint8_t)tipo;
  r.usuario = usuario;
  r.valor = valor;
  r.crc = crc16((const uint8_t*)&r, 14);
  uint16_t e = mem::FILA + (uint16_t)(r.seq % mem::N_FILA) * 16;
  const uint8_t* b = (const uint8_t*)&r;
  for (uint8_t i = 0; i < 16; i++) a_.escrever(e + i, b[i]);
  seq_++;
  escrever32(5, seq_);           // grava o próximo seq depois do registro: um reset no meio perde no máximo este evento
  return r.seq;
}

bool Memoria::ler(uint32_t seq, Registro& r) const {
  if (seq == 0 || seq >= seq_ || seq + mem::N_FILA < seq_) return false;
  uint16_t e = mem::FILA + (uint16_t)(seq % mem::N_FILA) * 16;
  uint8_t* b = (uint8_t*)&r;
  for (uint8_t i = 0; i < 16; i++) b[i] = a_.ler(e + i);
  return r.seq == seq && r.crc == crc16(b, 14);
}

uint32_t Memoria::primeiro_pendente() const {
  uint32_t menor = seq_ > mem::N_FILA ? seq_ - mem::N_FILA : 1;
  return ack_ + 1 > menor ? ack_ + 1 : menor;
}

uint16_t Memoria::pendentes() const { return (uint16_t)(seq_ - primeiro_pendente()); }

void Memoria::confirmar(uint32_t seq) {
  if (seq > ack_ && seq < seq_) {
    ack_ = seq;
    escrever32(9, ack_);
  }
}

uint8_t Memoria::estado_salvo() const { return a_.ler(13); }
void Memoria::salvar_estado(uint8_t e) { a_.escrever(13, e); }
int16_t Memoria::setpoint() const {
  int16_t sp = (int16_t)ler16(14);
  return (sp < par::SETPOINT_MIN || sp > par::SETPOINT_MAX) ? par::SETPOINT_PADRAO : sp;
}
void Memoria::salvar_setpoint(int16_t sp) { escrever16(14, (uint16_t)sp); }
uint16_t Memoria::alarme_porta_s() const {
  uint16_t s = ler16(16);
  return (s < 5 || s > 600) ? (uint16_t)(par::ALARME_PORTA_MS_PADRAO / 1000) : s;
}
void Memoria::salvar_alarme_porta_s(uint16_t s) { escrever16(16, s); }
uint8_t Memoria::volume() const {
  uint8_t v = a_.ler(18);
  return v > 100 ? par::VOLUME_PADRAO : v;
}
void Memoria::salvar_volume(uint8_t v) { a_.escrever(18, v); }
uint8_t Memoria::mapa_sensor(uint8_t i) const {
  uint8_t v = a_.ler(19 + i);
  return v > 2 ? i : v;
}
void Memoria::salvar_mapa_sensor(uint8_t i, uint8_t indice) { a_.escrever(19 + i, indice); }
bool Memoria::autonomo() const { return a_.ler(22) != 0; }
void Memoria::salvar_autonomo(bool p) { a_.escrever(22, p ? 1 : 0); }

// ----------------------------------------------------------- Usuarios --
bool Usuarios::valido(uint8_t id) const {
  if (id < 1 || id > mem::N_USUARIOS) return false;
  char b[15];
  for (uint8_t i = 0; i < 15; i++) b[i] = (char)m_.armazenamento().ler(base(id) + i);
  return crc8(b, 15) == m_.armazenamento().ler(base(id) + 15);
}

void Usuarios::selar(uint8_t id) {
  char b[15];
  for (uint8_t i = 0; i < 15; i++) b[i] = (char)m_.armazenamento().ler(base(id) + i);
  m_.armazenamento().escrever(base(id) + 15, crc8(b, 15));
}

bool Usuarios::ativo(uint8_t id) const { return valido(id) && m_.armazenamento().ler(base(id)) == 1; }

void Usuarios::hash(uint8_t id, const char* senha, uint16_t sal, uint8_t out[8]) const {
  uint8_t buf[3 + par::TAM_SENHA_MAX];
  size_t n = strlen(senha);
  if (n > par::TAM_SENHA_MAX) n = par::TAM_SENHA_MAX;
  buf[0] = (uint8_t)sal;
  buf[1] = (uint8_t)(sal >> 8);
  buf[2] = id;
  memcpy(buf + 3, senha, n);
  uint8_t h[32];
  sha256(buf, 3 + n, h);
  memcpy(out, h, 8);
}

bool Usuarios::conferir_senha(uint8_t id, const char* senha) const {
  if (!ativo(id)) return false;
  Armazenamento& a = m_.armazenamento();
  uint16_t sal = (uint16_t)(a.ler(base(id) + 2) | a.ler(base(id) + 3) << 8);
  uint8_t h[8];
  hash(id, senha, sal, h);
  uint8_t dif = 0;                       // compara tudo, sem sair no primeiro byte diferente
  for (uint8_t i = 0; i < 8; i++) dif |= (uint8_t)(h[i] ^ a.ler(base(id) + 4 + i));
  return dif == 0;
}

bool Usuarios::definir_senha(uint8_t id, const char* senha, uint16_t sal) {
  size_t n = strlen(senha);
  if (id < 1 || id > mem::N_USUARIOS || n < par::TAM_SENHA_MIN || n > par::TAM_SENHA_MAX) return false;
  for (size_t i = 0; i < n; i++)
    if (senha[i] < '0' || senha[i] > '9') return false;
  Armazenamento& a = m_.armazenamento();
  uint8_t digital = valido(id) ? a.ler(base(id) + 1) : 0xFF;
  uint8_t h[8];
  hash(id, senha, sal, h);
  a.escrever(base(id), 1);
  a.escrever(base(id) + 1, digital);
  a.escrever(base(id) + 2, (uint8_t)sal);
  a.escrever(base(id) + 3, (uint8_t)(sal >> 8));
  for (uint8_t i = 0; i < 8; i++) a.escrever(base(id) + 4 + i, h[i]);
  for (uint8_t i = 12; i < 15; i++) a.escrever(base(id) + i, 0);
  selar(id);
  return true;
}

bool Usuarios::definir_digital(uint8_t id, uint8_t posicao) {
  if (!ativo(id)) return false;
  m_.armazenamento().escrever(base(id) + 1, posicao);
  selar(id);
  return true;
}

uint8_t Usuarios::digital_de(uint8_t id) const { return ativo(id) ? m_.armazenamento().ler(base(id) + 1) : 0xFF; }

uint8_t Usuarios::por_digital(uint8_t posicao) const {
  for (uint8_t id = 1; id <= mem::N_USUARIOS; id++)
    if (ativo(id) && m_.armazenamento().ler(base(id) + 1) == posicao) return id;
  return 0;
}

bool Usuarios::desativar(uint8_t id) {
  if (!valido(id)) return false;
  m_.armazenamento().escrever(base(id), 0);
  selar(id);
  return true;
}

}  // namespace armario
