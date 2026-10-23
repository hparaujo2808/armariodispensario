// Organização da EEPROM (4 KB no Mega) e as duas estruturas persistentes:
// a fila de eventos (sobrevive a reset e falta de energia, com número de
// sequência) e a tabela de usuários (hash da senha + posição da digital).
#pragma once
#include "tipos.h"

namespace armario {

namespace mem {
const uint16_t CABECALHO = 0;      // 32 bytes
const uint16_t USUARIOS = 32;      // 20 × 16 = 320 bytes
const uint8_t N_USUARIOS = 20;
const uint16_t FILA = 512;         // 200 × 16 = 3200 bytes
const uint16_t N_FILA = 200;
const uint16_t MAGICO = 0xA2D4;
const uint8_t VERSAO = 1;
}  // namespace mem

// Cabeçalho: [0..1] mágico, [2] versão, [3..4] boot, [5..8] próximo seq,
// [9..12] último seq confirmado pelo notebook, [13] estado salvo,
// [14..15] setpoint (décimos °C), [16..17] alarme da porta (s), [18] volume,
// [19..21] qual sensor DS18B20 (índice no barramento) é a baia, o cooler 1 e o cooler 2,
// [22] modo autônomo permitido (0 = não; qualquer outro valor = sim, o padrão)
class Memoria {
 public:
  explicit Memoria(Armazenamento& a) : a_(a) {}
  bool iniciar();                       // devolve true se formatou (primeira vez)
  void formatar();
  uint16_t boot() const { return boot_; }
  uint32_t proximo_seq() const { return seq_; }
  uint32_t confirmado() const { return ack_; }

  uint32_t registrar(Ev tipo, uint8_t usuario, int16_t valor, uint32_t ms);
  bool ler(uint32_t seq, Registro& r) const;     // false se não está mais na fila ou corrompido
  uint32_t primeiro_pendente() const;            // seq do evento mais antigo ainda não confirmado
  uint16_t pendentes() const;
  void confirmar(uint32_t seq);                  // confirma tudo até seq (inclusive)

  uint8_t estado_salvo() const;
  void salvar_estado(uint8_t e);
  bool autonomo() const;
  void salvar_autonomo(bool p);
  int16_t setpoint() const;
  void salvar_setpoint(int16_t sp);
  uint16_t alarme_porta_s() const;
  void salvar_alarme_porta_s(uint16_t s);
  uint8_t volume() const;
  void salvar_volume(uint8_t v);
  uint8_t mapa_sensor(uint8_t i) const;          // i: 0 = baia, 1 = cooler 1, 2 = cooler 2
  void salvar_mapa_sensor(uint8_t i, uint8_t indice);

  Armazenamento& armazenamento() { return a_; }

 private:
  uint32_t ler32(uint16_t e) const;
  void escrever32(uint16_t e, uint32_t v);
  uint16_t ler16(uint16_t e) const;
  void escrever16(uint16_t e, uint16_t v);
  Armazenamento& a_;
  uint16_t boot_ = 0;
  uint32_t seq_ = 1;
  uint32_t ack_ = 0;
};

// Tabela de usuários: [0] ativo, [1] posição da digital no leitor (0xFF = nenhuma),
// [2..3] sal, [4..11] primeiros 8 bytes do SHA-256(sal | id | senha), [12..14] livre, [15] CRC-8
class Usuarios {
 public:
  explicit Usuarios(Memoria& m) : m_(m) {}
  bool ativo(uint8_t id) const;
  bool conferir_senha(uint8_t id, const char* senha) const;
  bool definir_senha(uint8_t id, const char* senha, uint16_t sal);
  bool definir_digital(uint8_t id, uint8_t posicao);
  uint8_t por_digital(uint8_t posicao) const;    // 0 = nenhum usuário
  bool desativar(uint8_t id);
  uint8_t digital_de(uint8_t id) const;

 private:
  uint16_t base(uint8_t id) const { return mem::USUARIOS + (uint16_t)(id - 1) * 16; }
  bool valido(uint8_t id) const;
  void hash(uint8_t id, const char* senha, uint16_t sal, uint8_t out[8]) const;
  void selar(uint8_t id);
  Memoria& m_;
};

}  // namespace armario
