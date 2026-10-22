// SHA-256 compacto (FIPS 180-4) para guardar o hash das senhas, nunca a senha.
#pragma once
#include <stdint.h>
#include <stddef.h>

namespace armario {

void sha256(const uint8_t* dados, size_t n, uint8_t saida[32]);

}  // namespace armario
