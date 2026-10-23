// GERADO por hardware/gerar.py a partir de hardware/pinos.yaml. Não editar à mão.
#pragma once
#include <Arduino.h>

// IN1 do módulo de relés
const uint8_t PINO_RELE_TRAVA = 8;
const uint8_t ATIVO_RELE_TRAVA = LOW;
// IN2 do módulo de relés
const uint8_t PINO_RELE_PELTIER_1 = 9;
const uint8_t ATIVO_RELE_PELTIER_1 = LOW;
// IN3 do módulo de relés
const uint8_t PINO_RELE_PELTIER_2 = 10;
const uint8_t ATIVO_RELE_PELTIER_2 = LOW;
// IN4 do módulo de relés
const uint8_t PINO_RELE_LIVRE = 11;
const uint8_t ATIVO_RELE_LIVRE = LOW;
// Buzzer passivo (+) por resistor de 1 kΩ
const uint8_t PINO_BUZZER = 7;
const uint8_t ATIVO_BUZZER = HIGH;
// Reed MC-38 (o outro fio no GND)
const uint8_t PINO_SENSOR_PORTA = 3;
const uint8_t ATIVO_SENSOR_PORTA = LOW;
// RX do AS608 por divisor 1 kΩ / 2,2 kΩ
const uint8_t PINO_DIGITAL_TX = 18;
// TX do AS608
const uint8_t PINO_DIGITAL_RX = 19;
// RS do LCD 16x2
const uint8_t PINO_LCD_RS = 38;
const uint8_t ATIVO_LCD_RS = HIGH;
// E do LCD
const uint8_t PINO_LCD_E = 40;
const uint8_t ATIVO_LCD_E = HIGH;
// D4 do LCD
const uint8_t PINO_LCD_D4 = 42;
const uint8_t ATIVO_LCD_D4 = HIGH;
// D5 do LCD
const uint8_t PINO_LCD_D5 = 44;
const uint8_t ATIVO_LCD_D5 = HIGH;
// D6 do LCD
const uint8_t PINO_LCD_D6 = 46;
const uint8_t ATIVO_LCD_D6 = HIGH;
// D7 do LCD
const uint8_t PINO_LCD_D7 = 48;
const uint8_t ATIVO_LCD_D7 = HIGH;
// Linha 1 do teclado (pino 1 do flat)
const uint8_t PINO_TECLADO_L1 = 22;
const uint8_t ATIVO_TECLADO_L1 = LOW;
// Linha 2 (pino 2)
const uint8_t PINO_TECLADO_L2 = 24;
const uint8_t ATIVO_TECLADO_L2 = LOW;
// Linha 3 (pino 3)
const uint8_t PINO_TECLADO_L3 = 26;
const uint8_t ATIVO_TECLADO_L3 = LOW;
// Linha 4 (pino 4)
const uint8_t PINO_TECLADO_L4 = 28;
const uint8_t ATIVO_TECLADO_L4 = LOW;
// Coluna 1 (pino 5)
const uint8_t PINO_TECLADO_C1 = 30;
const uint8_t ATIVO_TECLADO_C1 = LOW;
// Coluna 2 (pino 6)
const uint8_t PINO_TECLADO_C2 = 32;
const uint8_t ATIVO_TECLADO_C2 = LOW;
// Coluna 3 (pino 7)
const uint8_t PINO_TECLADO_C3 = 34;
const uint8_t ATIVO_TECLADO_C3 = LOW;
// Coluna 4 (pino 8)
const uint8_t PINO_TECLADO_C4 = 36;
const uint8_t ATIVO_TECLADO_C4 = LOW;
// DQ dos 3 DS18B20 (amarelo), pull-up de 4,7 kΩ para 5 V
const uint8_t PINO_ONEWIRE = 4;
// Meio do divisor 4,7 kΩ (do +12 V) / 2,2 kΩ (do GND), por mais 4,7 kΩ em série
const uint8_t PINO_MEDE_12V = A0;

// Saídas em ordem de inicialização segura: nível inativo antes de pinMode(OUTPUT)
const uint8_t SAIDAS[15] = {PINO_RELE_TRAVA, PINO_RELE_PELTIER_1, PINO_RELE_PELTIER_2, PINO_RELE_LIVRE, PINO_BUZZER, PINO_LCD_RS, PINO_LCD_E, PINO_LCD_D4, PINO_LCD_D5, PINO_LCD_D6, PINO_LCD_D7, PINO_TECLADO_C1, PINO_TECLADO_C2, PINO_TECLADO_C3, PINO_TECLADO_C4};
const uint8_t SAIDAS_INATIVO[15] = {HIGH, HIGH, HIGH, HIGH, LOW, LOW, LOW, LOW, LOW, LOW, LOW, HIGH, HIGH, HIGH, HIGH};
