// Parâmetros do firmware. Os de temperatura vêm de docs/DECISOES.md (1.1 e 1.4).
#pragma once
#include <stdint.h>

namespace armario {
namespace par {

// --- acesso ---
const uint8_t MAX_ERROS = 3;               // erros seguidos até bloquear
const uint32_t BLOQUEIO_MS = 30000;        // tempo de bloqueio
const uint32_t DIGITACAO_MS = 15000;       // sem tecla por esse tempo: volta ao início
const uint8_t TAM_SENHA_MIN = 4;
const uint8_t TAM_SENHA_MAX = 8;
const uint32_t AGUARDA_NOTEBOOK_MS = 120000;  // tempo para o notebook mandar LIBERAR
const uint32_t NOTEBOOK_SILENCIO_MS = 5000;   // sem linha do notebook por isso = fora do ar
const uint32_t DIGITAL_INTERVALO_MS = 2000;   // depois de uma leitura, espera o dedo sair e mais isso

// --- trava e porta ---
const uint32_t TRAVA_MAX_MS = 3000;        // trava nunca energizada mais que isso
const uint32_t ALARME_PORTA_MS_PADRAO = 30000;   // RF09: porta aberta além disso -> alarme
const uint32_t REED_FILTRO_MS = 50;        // reed precisa ficar estável esse tempo
const uint32_t JANELA_ABERTURA_MS = 5000;  // porta aberta até 5 s depois de a liberação expirar ainda é
                                           // do último usuário (o reed só abre com ~15–25 mm de folga)
const uint32_t TRAVA_ATRASO_MS = 20;       // trava só energiza 20 ms depois de as Peltier desligarem

// --- frio ---
const int16_t SETPOINT_PADRAO = 50;        // décimos de °C
const int16_t SETPOINT_MIN = 30;
const int16_t SETPOINT_MAX = 70;
const int16_t HISTERESE = 10;              // liga em sp+1,0; desliga em sp−1,0
const int16_t CORTE_CONGELAR = 20;         // ≤ 2,0 °C desliga
const int16_t RELIGA_APOS_CORTE = 40;      // só religa acima de 4,0 °C
const int16_t FAIXA_MIN = 20, FAIXA_MAX = 80;
const uint32_t ALARME_FAIXA_MS = 600000;   // fora de 2–8 °C por 10 min
const uint32_t MIN_LIGADO_MS = 60000;
const uint32_t MIN_DESLIGADO_MS = 120000;
const uint32_t ESCALONA_MS = 2000;         // segunda Peltier liga 2 s depois da primeira
const int16_t SENSOR_MIN = -200;           // abaixo disso: leitura absurda (qualquer sensor)
const int16_t SENSOR_MAX = 600;            // acima disso: absurda no ar da baia
const int16_t SENSOR_QUENTE_MAX = 1250;    // acima disso: absurda no cooler (limite do DS18B20)
const int16_t QUENTE_CORTE = 600;          // cooler acima de 60,0 °C: desliga
const int16_t QUENTE_RELIGA = 450;         // e só religa abaixo de 45,0 °C
const uint32_t SEM_EFEITO_MS = 1200000;    // ligada 20 min acima de sp+1 sem cair 1,0 °C: pastilha solta
const int16_t SEM_EFEITO_QUEDA = 10;       //   ou prensa frouxa -> desliga e alarma
const uint32_t SEM_EFEITO_ESPERA_MS = 1800000;   // tenta de novo depois de 30 min

// --- energia (12 V medido no A0) ---
const uint16_t ENERGIA_FALTA_MV = 9000;
const uint16_t ENERGIA_VOLTA_MV = 10500;
const uint32_t ENERGIA_FILTRO_MS = 300;

// --- som ---
const uint8_t VOLUME_PADRAO = 40;          // 0–100 (ciclo de trabalho do PWM do buzzer passivo)

}  // namespace par
}  // namespace armario
