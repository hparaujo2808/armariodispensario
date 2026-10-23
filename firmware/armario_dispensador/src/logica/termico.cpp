#include "termico.h"

#include "parametros.h"

namespace armario {

void Termico::definir_setpoint(int16_t sp) {
  if (sp < par::SETPOINT_MIN) sp = par::SETPOINT_MIN;
  if (sp > par::SETPOINT_MAX) sp = par::SETPOINT_MAX;
  sp_ = sp;
}

bool Termico::absurdo(int16_t t, int16_t max) { return t < par::SENSOR_MIN || t > max; }

void Termico::desligar(uint32_t agora) {
  if (ligado_) mudou_ = agora;
  ligado_ = false;
  p1_ = p2_ = false;
}

void Termico::atualizar(const Leituras& l, bool pausa, uint32_t agora) {
  if (!iniciado_) {               // ao ligar, conta como "acabou de desligar": respeita o tempo mínimo
    iniciado_ = true;
    mudou_ = agora;
  }

  // 1. sensores
  bool falha = !l.baia_ok || !l.q1_ok || !l.q2_ok || absurdo(l.baia, par::SENSOR_MAX) ||
               absurdo(l.q1, par::SENSOR_QUENTE_MAX) || absurdo(l.q2, par::SENSOR_QUENTE_MAX);
  if (falha && !falha_sensor_) saida_.evento(Ev::SENSOR_FALHA, 0, l.baia_ok ? l.baia : -999);
  falha_sensor_ = falha;

  // 2. lado quente (independente do fusível térmico de 85 °C, que corta por hardware)
  int16_t quente = l.q1 > l.q2 ? l.q1 : l.q2;
  if (!falha && !corte_quente_ && quente >= par::QUENTE_CORTE) {
    corte_quente_ = true;
    saida_.evento(Ev::CORTE_QUENTE, 0, quente);
  } else if (corte_quente_ && !falha && quente < par::QUENTE_RELIGA) {
    corte_quente_ = false;
  }

  // 3. congelamento e histerese
  if (!falha) {
    if (l.baia <= par::CORTE_CONGELAR) corte_congelar_ = true;
    if (corte_congelar_ && l.baia > par::RELIGA_APOS_CORTE) corte_congelar_ = false;
    if (l.baia >= sp_ + par::HISTERESE) querer_ = true;
    if (l.baia <= sp_ - par::HISTERESE) querer_ = false;

    // alarme de faixa (2–8 °C) depois de 10 min seguidos fora
    bool fora = l.baia < par::FAIXA_MIN || l.baia > par::FAIXA_MAX;
    if (fora && !fora_faixa_) fora_desde_ = agora;
    fora_faixa_ = fora;
    if (fora && !alarme_faixa_ && agora - fora_desde_ >= par::ALARME_FAIXA_MS) {
      alarme_faixa_ = true;
      saida_.evento(Ev::TEMP_ALARME, 0, l.baia);
    } else if (!fora && alarme_faixa_) {
      alarme_faixa_ = false;
      saida_.evento(Ev::TEMP_NORMAL, 0, l.baia);
    }
  }

  // 4. ligada sem efeito: o DS18B20 do cooler não vê pastilha solta (a face quente esquenta,
  // a base do cooler não). Se a baia não cai 1 °C em 20 min, desliga e alarma.
  if (sem_efeito_ && agora - sem_efeito_desde_ >= par::SEM_EFEITO_ESPERA_MS) sem_efeito_ = false;
  if (!falha && ligado_ && !sem_efeito_) {
    if (l.baia <= ref_baia_ - par::SEM_EFEITO_QUEDA || l.baia < sp_ + par::HISTERESE) {
      ref_baia_ = l.baia;
      ref_t_ = agora;
    } else if (agora - ref_t_ >= par::SEM_EFEITO_MS) {
      sem_efeito_ = true;
      sem_efeito_desde_ = agora;
      saida_.evento(Ev::FRIO_SEM_EFEITO, 0, l.baia);
    }
  }

  // 5. decisão final: cortes desligam na hora; ligar e desligar pela histerese respeitam os tempos mínimos
  if (falha || corte_quente_ || corte_congelar_ || sem_efeito_) {
    desligar(agora);
    return;
  }
  if (querer_ && !ligado_ && agora - mudou_ >= par::MIN_DESLIGADO_MS) {
    ligado_ = true;
    mudou_ = agora;
    escalona_desde_ = agora;
    ref_baia_ = l.baia;
    ref_t_ = agora;
  } else if (!querer_ && ligado_ && agora - mudou_ >= par::MIN_LIGADO_MS) {
    desligar(agora);
  }
  intertravar(pausa, agora);
}

void Termico::intertravar(bool pausa, uint32_t agora) {
  // intertravamento: durante o pulso da trava as saídas desligam, mas a histerese e os
  // tempos mínimos continuam valendo; quando a pausa acaba, volta escalonado
  if (pausa) {
    em_pausa_ = true;
    p1_ = p2_ = false;
    return;
  }
  if (em_pausa_) {
    em_pausa_ = false;
    escalona_desde_ = agora;
  }
  p1_ = ligado_;
  p2_ = ligado_ && agora - escalona_desde_ >= par::ESCALONA_MS;   // segunda Peltier entra 2 s depois
}

}  // namespace armario
