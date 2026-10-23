// Controle liga/desliga da baia fria com histerese (docs/DECISOES.md, 1.1 e 1.4).
#pragma once
#include "tipos.h"

namespace armario {

struct Leituras {
  bool baia_ok, q1_ok, q2_ok;   // false = sensor ausente ou CRC errado
  int16_t baia, q1, q2;         // décimos de °C
};

class Termico {
 public:
  explicit Termico(Saida& s) : saida_(s) {}
  void definir_setpoint(int16_t sp);     // décimos de °C, limitado a 3,0–7,0
  int16_t setpoint() const { return sp_; }

  // Chamar a cada leitura (≈ 1 s). `pausa` = intertravamento com a trava.
  void atualizar(const Leituras& l, bool pausa, uint32_t agora);
  // Chamar a cada passada do loop: aplica a pausa da trava na hora, sem esperar a próxima leitura.
  void intertravar(bool pausa, uint32_t agora);

  bool peltier1() const { return p1_; }
  bool peltier2() const { return p2_; }
  bool em_alarme() const { return alarme_faixa_ || falha_sensor_ || corte_quente_ || sem_efeito_; }
  bool sem_efeito() const { return sem_efeito_; }
  bool corte_quente() const { return corte_quente_; }
  bool falha_sensor() const { return falha_sensor_; }

 private:
  static bool absurdo(int16_t t, int16_t max);
  void desligar(uint32_t agora);
  Saida& saida_;
  int16_t sp_ = 50;
  bool querer_ = false;          // decisão da histerese (antes de cortes e pausa)
  bool ligado_ = false;          // grupo das Peltier ligado de fato
  bool p1_ = false, p2_ = false;
  bool corte_congelar_ = false;
  bool corte_quente_ = false;
  bool falha_sensor_ = false;
  bool alarme_faixa_ = false;
  bool fora_faixa_ = false;
  bool iniciado_ = false;
  bool em_pausa_ = false;
  bool sem_efeito_ = false;
  int16_t ref_baia_ = 0;         // última temperatura em que a baia mostrou que está esfriando
  uint32_t ref_t_ = 0;
  uint32_t sem_efeito_desde_ = 0;
  uint32_t mudou_ = 0;           // última vez que ligou ou desligou (tempos mínimos)
  uint32_t escalona_desde_ = 0;  // quando a primeira Peltier entrou (ou a pausa acabou)
  uint32_t fora_desde_ = 0;
};

}  // namespace armario
