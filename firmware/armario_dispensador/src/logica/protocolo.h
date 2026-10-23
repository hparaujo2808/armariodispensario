// Protocolo serial Mega <-> notebook (115200 baud, texto, uma mensagem por linha).
//
//   $<CORPO>*<CRC8 em 2 hex>\n       CRC-8 (polinômio 0x07) só do CORPO
//
// Mega -> notebook
//   $EV seq=12 t=AUTH_OK u=3 v=1 ms=123456 b=7*5A   evento da fila (repete até receber ACK)
//   $ST e=OCIOSO u=0 pend=2 b=7 ms=123999*..         estado e relógio do Mega (a cada 1 s)
//   $TEMP baia=54 q1=401 q2=398 ok=111 p1=1 p2=1 al=0 v12=12040*..   (décimos de °C, mV; a cada 2 s)
//   $OK id=5*..  /  $ERRO id=5 m=ESTADO*..           resposta a um comando
// notebook -> Mega
//   $HELLO*..  $PING*..             o notebook está vivo (mandar a cada 1 s)
//   $ACK seq=12*..                  confirma todos os eventos até 12
//   $LIB id=5 u=3*..                libera o usuário 3 (depois do CPF e da confirmação)
//   $CANC id=6*..                   cancela a retirada em andamento
//   $CAD id=7 u=3*..                cadastra a digital do usuário 3
//   $SENHA id=8 u=3 pin=2468 sal=513*..   define a senha (o Mega guarda só o hash)
//   $DEL id=9 u=3*..                desativa o usuário 3
//   $SET id=10 sp=50*..  /  vol=30  /  alarme=30  /  mapa=201  /  auto=0
//                                   setpoint (décimos °C), volume (0–100), alarme da porta (s),
//                                   papel de cada DS18B20 (permutação de 0, 1, 2), modo autônomo
#pragma once
#include "tipos.h"

namespace armario {

const uint8_t MAX_CAMPOS = 6;

struct Mensagem {
  char tipo[8];
  uint8_t n;
  char chave[MAX_CAMPOS][8];
  char valor[MAX_CAMPOS][12];
  bool tem(const char* k) const;
  long numero(const char* k, long padrao = -1) const;
  const char* texto(const char* k) const;
};

// Analisa uma linha recebida (sem o \n). Devolve false se faltar $ ou *, ou se o CRC não bater.
bool analisar(const char* linha, Mensagem& m);

// Monta "$<corpo>*HH\n" em `saida`. Devolve o tamanho, ou 0 se não couber.
size_t empacotar(const char* corpo, char* saida, size_t tam);

// Corpo de um evento da fila.
size_t corpo_evento(const Registro& r, char* saida, size_t tam);

}  // namespace armario
