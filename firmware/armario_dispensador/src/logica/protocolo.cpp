#include "protocolo.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace armario {

bool Mensagem::tem(const char* k) const {
  for (uint8_t i = 0; i < n; i++)
    if (!strcmp(chave[i], k)) return true;
  return false;
}

const char* Mensagem::texto(const char* k) const {
  for (uint8_t i = 0; i < n; i++)
    if (!strcmp(chave[i], k)) return valor[i];
  return nullptr;
}

long Mensagem::numero(const char* k, long padrao) const {
  const char* v = texto(k);
  if (!v || !*v) return padrao;
  char* fim;
  long x = strtol(v, &fim, 10);
  return *fim ? padrao : x;
}

namespace {
int hex(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}
}  // namespace

bool analisar(const char* linha, Mensagem& m) {
  memset(&m, 0, sizeof m);
  while (*linha == ' ' || *linha == '\r') linha++;
  if (*linha != '$') return false;
  const char* ini = linha + 1;
  const char* ast = strchr(ini, '*');
  if (!ast || ast - ini > 90) return false;
  int a = hex(ast[1]), b = hex(ast[2]);
  if (a < 0 || b < 0) return false;
  if (crc8(ini, (size_t)(ast - ini)) != (uint8_t)(a * 16 + b)) return false;

  char corpo[92];
  size_t n = (size_t)(ast - ini);
  memcpy(corpo, ini, n);
  corpo[n] = 0;
  char* tok = strtok(corpo, " ");
  if (!tok || strlen(tok) >= sizeof m.tipo) return false;
  strcpy(m.tipo, tok);
  while ((tok = strtok(nullptr, " ")) && m.n < MAX_CAMPOS) {
    char* igual = strchr(tok, '=');
    if (!igual) return false;
    *igual = 0;
    if (strlen(tok) >= sizeof m.chave[0] || strlen(igual + 1) >= sizeof m.valor[0]) return false;
    strcpy(m.chave[m.n], tok);
    strcpy(m.valor[m.n], igual + 1);
    m.n++;
  }
  return true;
}

size_t empacotar(const char* corpo, char* saida, size_t tam) {
  size_t n = strlen(corpo);
  if (n + 6 > tam) return 0;
  uint8_t c = crc8(corpo, n);
  int r = snprintf(saida, tam, "$%s*%02X\n", corpo, c);
  return r > 0 && (size_t)r < tam ? (size_t)r : 0;
}

size_t corpo_evento(const Registro& r, char* saida, size_t tam) {
  int n = snprintf(saida, tam, "EV seq=%lu t=%s u=%u v=%d ms=%lu b=%u", (unsigned long)r.seq,
                   nome_evento((Ev)r.tipo), r.usuario, r.valor, (unsigned long)r.ms, r.boot);
  return n > 0 && (size_t)n < tam ? (size_t)n : 0;
}

}  // namespace armario
