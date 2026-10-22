#include "sha256.h"

#include <string.h>
#ifdef __AVR__
#include <avr/pgmspace.h>
#endif

namespace armario {
namespace {

#ifdef __AVR__
#define K_LER(i) pgm_read_dword(&K[i])
const uint32_t K[64] PROGMEM = {
#else
#define K_LER(i) K[i]
const uint32_t K[64] = {
#endif
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

inline uint32_t rotr(uint32_t x, uint8_t n) { return (x >> n) | (x << (32 - n)); }

void bloco(uint32_t h[8], const uint8_t* b) {
  uint32_t w[16];
  for (uint8_t i = 0; i < 16; i++)
    w[i] = (uint32_t)b[4 * i] << 24 | (uint32_t)b[4 * i + 1] << 16 | (uint32_t)b[4 * i + 2] << 8 | b[4 * i + 3];
  uint32_t a = h[0], bb = h[1], c = h[2], d = h[3], e = h[4], f = h[5], g = h[6], hh = h[7];
  for (uint8_t i = 0; i < 64; i++) {
    uint32_t wi;
    if (i < 16) {
      wi = w[i];
    } else {
      uint32_t w15 = w[(i + 1) & 15], w2 = w[(i + 14) & 15];
      uint32_t s0 = rotr(w15, 7) ^ rotr(w15, 18) ^ (w15 >> 3);
      uint32_t s1 = rotr(w2, 17) ^ rotr(w2, 19) ^ (w2 >> 10);
      wi = w[i & 15] = w[i & 15] + s0 + w[(i + 9) & 15] + s1;
    }
    uint32_t t1 = hh + (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) + ((e & f) ^ (~e & g)) + K_LER(i) + wi;
    uint32_t t2 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) + ((a & bb) ^ (a & c) ^ (bb & c));
    hh = g; g = f; f = e; e = d + t1; d = c; c = bb; bb = a; a = t1 + t2;
  }
  h[0] += a; h[1] += bb; h[2] += c; h[3] += d; h[4] += e; h[5] += f; h[6] += g; h[7] += hh;
}

}  // namespace

void sha256(const uint8_t* dados, size_t n, uint8_t saida[32]) {
  uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
  uint8_t b[64];
  size_t i = 0;
  for (; i + 64 <= n; i += 64) bloco(h, dados + i);
  size_t r = n - i;
  memset(b, 0, 64);
  memcpy(b, dados + i, r);
  b[r] = 0x80;
  if (r >= 56) {
    bloco(h, b);
    memset(b, 0, 64);
  }
  uint64_t bits = (uint64_t)n * 8;
  for (uint8_t k = 0; k < 8; k++) b[63 - k] = (uint8_t)(bits >> (8 * k));
  bloco(h, b);
  for (uint8_t k = 0; k < 8; k++) {
    saida[4 * k] = h[k] >> 24; saida[4 * k + 1] = h[k] >> 16; saida[4 * k + 2] = h[k] >> 8; saida[4 * k + 3] = h[k];
  }
}

}  // namespace armario
