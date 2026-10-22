// Mini-arcabouço de teste para rodar a lógica do firmware no PC.
#pragma once
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <string>
#include <vector>

struct Caso { const char* nome; std::function<void()> f; };
inline std::vector<Caso>& casos() { static std::vector<Caso> v; return v; }
inline int& falhas() { static int n = 0; return n; }
struct Registra { Registra(const char* n, std::function<void()> f) { casos().push_back({n, f}); } };

#define TESTE(nome) static void nome(); static Registra reg_##nome(#nome, nome); static void nome()
#define CHECA(cond) do { if (!(cond)) { std::printf("  FALHOU %s:%d: %s\n", __FILE__, __LINE__, #cond); falhas()++; } } while (0)
#define CHECA_IGUAL(a, b) do { auto _a = (a); auto _b = (b); if (!(_a == _b)) { \
  std::printf("  FALHOU %s:%d: %s == %s (%lld != %lld)\n", __FILE__, __LINE__, #a, #b, (long long)_a, (long long)_b); falhas()++; } } while (0)
