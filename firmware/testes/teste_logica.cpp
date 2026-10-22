// Testes da lógica do firmware, rodando no PC:
//   c++ -std=c++17 -I../armario_dispensador/src/logica ../armario_dispensador/src/logica/*.cpp teste_logica.cpp -o teste && ./teste
// (ou: pytest tests/test_firmware.py, na raiz do repositório)
#include <cstring>
#include <vector>

#include "maquina.h"
#include "memoria.h"
#include "parametros.h"
#include "protocolo.h"
#include "sha256.h"
#include "termico.h"
#include "teste.h"

using namespace armario;

// ---------------------------------------------------------------- dublês --
struct EepromFalsa : Armazenamento {
  std::vector<uint8_t> m = std::vector<uint8_t>(4096, 0xFF);
  int gravacoes = 0;
  uint8_t ler(uint16_t e) const override { return m.at(e); }
  void escrever(uint16_t e, uint8_t v) override {
    if (m.at(e) != v) { m[e] = v; gravacoes++; }
  }
  uint16_t tamanho() const override { return 4096; }
};

struct SaidaFalsa : Saida {
  std::vector<Ev> evs;
  std::vector<uint8_t> us;
  Memoria* mem = nullptr;
  void evento(Ev t, uint8_t u, int16_t v) override {
    evs.push_back(t);
    us.push_back(u);
    if (mem) mem->registrar(t, u, v, 0);
  }
  bool teve(Ev t) const { for (auto e : evs) if (e == t) return true; return false; }
  int conta(Ev t) const { int n = 0; for (auto e : evs) n += (e == t); return n; }
};

struct Cenario {
  EepromFalsa ee;
  Memoria mem{ee};
  Usuarios usuarios{mem};
  SaidaFalsa saida;
  Maquina maq{saida, usuarios, mem};
  uint32_t t = 1000;
  Cenario(bool porta_aberta = false) {
    mem.iniciar();
    saida.mem = &mem;
    usuarios.definir_senha(3, "2468", 0x1234);
    usuarios.definir_digital(3, 7);
    maq.iniciar(porta_aberta, t);
  }
  void digitar(const char* s) { for (; *s; s++) maq.tecla(*s, t += 100); }
  void passar(uint32_t ms) { for (uint32_t k = 0; k < ms; k += 100) maq.tick(t += 100); }
};

// ------------------------------------------------------------- utilidades --
TESTE(sha256_vetor_padrao) {
  uint8_t h[32];
  sha256((const uint8_t*)"abc", 3, h);
  const uint8_t esperado[4] = {0xba, 0x78, 0x16, 0xbf};
  CHECA(std::memcmp(h, esperado, 4) == 0);
  CHECA_IGUAL(h[31], 0xad);
  uint8_t h2[32];
  std::string longo(200, 'a');                     // mais de um bloco
  sha256((const uint8_t*)longo.data(), longo.size(), h2);
  CHECA_IGUAL(h2[0], 0xc2);
}

TESTE(protocolo_ida_e_volta) {
  char linha[100];
  CHECA(empacotar("LIB id=5 u=3", linha, sizeof linha) > 0);
  linha[std::strlen(linha) - 1] = 0;               // tira o \n
  Mensagem m;
  CHECA(analisar(linha, m));
  CHECA(std::strcmp(m.tipo, "LIB") == 0);
  CHECA_IGUAL(m.numero("id"), 5);
  CHECA_IGUAL(m.numero("u"), 3);
  CHECA_IGUAL(m.numero("x", -7), -7);
  linha[2] = 'X';                                  // corrompe: CRC não bate
  CHECA(!analisar(linha, m));
  CHECA(!analisar("LIB id=5*00", m));              // sem $
  CHECA(!analisar("$LIB id=5", m));                // sem *
}

TESTE(protocolo_evento) {
  Registro r{12, 34567, 3, (uint8_t)Ev::AUTH_OK, 3, 1, 0};
  char corpo[90], linha[100];
  CHECA(corpo_evento(r, corpo, sizeof corpo) > 0);
  CHECA(std::strcmp(corpo, "EV seq=12 t=AUTH_OK u=3 v=1 ms=34567 b=3") == 0);
  CHECA(empacotar(corpo, linha, sizeof linha) > 0);
}

// ---------------------------------------------------------------- memória --
TESTE(memoria_fila_sobrevive_a_reset) {
  EepromFalsa ee;
  {
    Memoria m(ee);
    CHECA(m.iniciar());                            // formatou
    CHECA_IGUAL(m.boot(), 1);
    for (int i = 0; i < 5; i++) m.registrar(Ev::PORTA_ABERTA, 2, (int16_t)i, 1000u + i);
    m.confirmar(2);
  }
  Memoria m2(ee);                                  // "reset"
  CHECA(!m2.iniciar());
  CHECA_IGUAL(m2.boot(), 2);
  CHECA_IGUAL(m2.proximo_seq(), 6u);
  CHECA_IGUAL(m2.primeiro_pendente(), 3u);
  CHECA_IGUAL(m2.pendentes(), 3);
  Registro r;
  CHECA(m2.ler(4, r));
  CHECA_IGUAL(r.valor, 3);
  CHECA_IGUAL(r.tipo, (uint8_t)Ev::PORTA_ABERTA);
  ee.m[512 + (4 % 200) * 16 + 5] ^= 0xFF;          // corrompe o registro 4
  CHECA(!m2.ler(4, r));
}

TESTE(memoria_fila_circular) {
  EepromFalsa ee;
  Memoria m(ee);
  m.iniciar();
  for (int i = 0; i < 250; i++) m.registrar(Ev::BOOT, 0, (int16_t)i, 0);
  CHECA_IGUAL(m.pendentes(), 200);                 // os 50 mais antigos foram sobrescritos
  CHECA_IGUAL(m.primeiro_pendente(), 51u);
  Registro r;
  CHECA(!m.ler(10, r));
  CHECA(m.ler(250, r));
  m.confirmar(249);
  CHECA_IGUAL(m.pendentes(), 1);
}

TESTE(usuarios_senha_com_hash) {
  EepromFalsa ee;
  Memoria m(ee);
  m.iniciar();
  Usuarios u(m);
  CHECA(u.definir_senha(4, "13579", 99));
  CHECA(u.conferir_senha(4, "13579"));
  CHECA(!u.conferir_senha(4, "13578"));
  CHECA(!u.conferir_senha(5, "13579"));
  CHECA(!u.definir_senha(4, "12a4", 1));           // só dígitos
  CHECA(!u.definir_senha(4, "123", 1));            // curta demais
  // a senha não fica gravada em texto
  std::string mem(ee.m.begin(), ee.m.end());
  CHECA(mem.find("13579") == std::string::npos);
  CHECA(u.definir_digital(4, 12));
  CHECA_IGUAL(u.por_digital(12), 4);
  CHECA(u.desativar(4));
  CHECA_IGUAL(u.por_digital(12), 0);
  CHECA(!u.conferir_senha(4, "13579"));
}

// ------------------------------------------------------- máquina de estados --
TESTE(senha_sem_notebook_libera_direto) {
  Cenario c;
  c.digitar("3#2468#");
  CHECA(c.maq.estado() == Estado::LIBERADO);
  CHECA(c.maq.trava());
  CHECA(c.saida.teve(Ev::AUTH_OK) && c.saida.teve(Ev::MODO_AUTONOMO) && c.saida.teve(Ev::LIBERADO));
  c.maq.porta(true, c.t += 500);
  CHECA(c.maq.estado() == Estado::PORTA_ABERTA);
  CHECA(!c.maq.trava());                           // trava desliga assim que a porta abre
  c.maq.porta(false, c.t += 8000);
  CHECA(c.maq.estado() == Estado::OCIOSO);
  CHECA(c.saida.teve(Ev::PORTA_FECHADA));
  CHECA_IGUAL(c.saida.us.back(), 3);               // a abertura fica registrada com o usuário
}

TESTE(com_notebook_espera_o_cpf) {
  Cenario c;
  c.maq.notebook_vivo(c.t);
  c.digitar("3#2468#");
  CHECA(c.maq.estado() == Estado::AGUARDANDO_NOTEBOOK);
  CHECA(!c.maq.trava());
  CHECA(!c.maq.cmd_liberar(4, c.t));               // usuário errado
  c.maq.notebook_vivo(c.t);
  CHECA(c.maq.cmd_liberar(3, c.t += 100));
  CHECA(c.maq.trava());
  CHECA(!c.saida.teve(Ev::MODO_AUTONOMO));
}

TESTE(notebook_cai_durante_a_espera) {
  Cenario c;
  c.maq.notebook_vivo(c.t);
  c.digitar("3#2468#");
  CHECA(c.maq.estado() == Estado::AGUARDANDO_NOTEBOOK);
  c.passar(par::NOTEBOOK_SILENCIO_MS + 200);
  CHECA(c.saida.teve(Ev::MODO_AUTONOMO));
  CHECA(!c.maq.trava() || c.maq.estado() == Estado::LIBERADO);
}

TESTE(bloqueio_depois_de_tres_erros) {
  Cenario c;
  c.digitar("3#1111#");
  c.digitar("3#2222#");
  CHECA(c.maq.estado() == Estado::OCIOSO);
  c.digitar("3#3333#");
  CHECA(c.maq.estado() == Estado::BLOQUEADO);
  CHECA(c.saida.teve(Ev::BLOQUEIO));
  c.digitar("3#2468#");                            // nem a senha certa entra
  CHECA(c.maq.estado() == Estado::BLOQUEADO);
  c.maq.digital(7, c.t += 100);
  CHECA(c.maq.estado() == Estado::BLOQUEADO);
  c.passar(par::BLOQUEIO_MS);
  CHECA(c.maq.estado() == Estado::OCIOSO);
  c.digitar("3#2468#");
  CHECA(c.maq.estado() == Estado::LIBERADO);
}

TESTE(acerto_zera_os_erros) {
  Cenario c;
  c.digitar("3#1111#");
  c.digitar("3#2222#");
  c.digitar("3#2468#");
  c.maq.porta(true, c.t += 100);
  c.maq.porta(false, c.t += 100);
  c.digitar("3#1111#");
  c.digitar("3#2222#");
  CHECA(c.maq.estado() == Estado::OCIOSO);         // ainda não bloqueou: contou do zero
}

TESTE(digital) {
  Cenario c;
  c.maq.digital(-1, c.t += 100);
  CHECA(c.saida.teve(Ev::AUTH_FALHA));
  c.maq.digital(9, c.t += 100);                    // posição sem usuário
  CHECA_IGUAL(c.saida.conta(Ev::AUTH_FALHA), 2);
  c.maq.digital(7, c.t += 100);
  CHECA(c.maq.estado() == Estado::LIBERADO);
  CHECA_IGUAL(c.maq.usuario(), 3);
}

TESTE(trava_nunca_passa_do_tempo_maximo) {
  Cenario c;
  c.digitar("3#2468#");
  CHECA(c.maq.trava());
  c.passar(par::TRAVA_MAX_MS - 200);
  CHECA(c.maq.trava());
  c.passar(300);
  CHECA(!c.maq.trava());
  CHECA(c.saida.teve(Ev::LIBERACAO_EXPIROU));
  CHECA(c.maq.estado() == Estado::OCIOSO);
}

TESTE(alarme_de_porta_aberta) {
  Cenario c;
  c.digitar("3#2468#");
  c.maq.porta(true, c.t += 100);
  c.passar(29000);
  CHECA(!c.maq.alarme());
  c.passar(1200);
  CHECA(c.maq.alarme());
  CHECA_IGUAL(c.saida.conta(Ev::PORTA_ABERTA_TEMPO), 1);
  c.passar(5000);
  CHECA_IGUAL(c.saida.conta(Ev::PORTA_ABERTA_TEMPO), 1);   // avisa uma vez só
  c.maq.porta(false, c.t += 100);
  CHECA(!c.maq.alarme());
}

TESTE(abertura_sem_autorizacao) {
  Cenario c;
  c.maq.porta(true, c.t += 100);
  CHECA(c.saida.teve(Ev::ABERTURA_NAO_AUTORIZADA));
  CHECA(c.maq.alarme());
  CHECA(!c.maq.trava());
  c.maq.porta(false, c.t += 100);
  CHECA(!c.maq.alarme());
  CHECA(c.maq.estado() == Estado::OCIOSO);
}

TESTE(reset_com_porta_aberta) {
  Cenario c(true);
  CHECA(c.saida.teve(Ev::BOOT) && c.saida.teve(Ev::RECUPERADO));
  CHECA(c.maq.estado() == Estado::PORTA_ABERTA);
  CHECA(!c.maq.trava());
}

TESTE(digitacao_abandonada_volta_ao_inicio) {
  Cenario c;
  c.digitar("3#24");
  CHECA(c.maq.estado() == Estado::DIGITANDO_SENHA);
  CHECA(std::strstr(c.maq.linha1(), "**") != nullptr);   // senha aparece como asteriscos
  CHECA(std::strstr(c.maq.linha1(), "24") == nullptr);
  c.passar(par::DIGITACAO_MS + 200);
  CHECA(c.maq.estado() == Estado::OCIOSO);
}

TESTE(cadastro_de_digital) {
  Cenario c;
  CHECA(c.maq.cmd_cadastrar(3, c.t));
  CHECA(c.maq.estado() == Estado::CADASTRANDO);
  c.maq.cadastro_terminou(true, 15, c.t += 100);
  CHECA(c.saida.teve(Ev::DIGITAL_CADASTRADA));
  CHECA_IGUAL(c.usuarios.por_digital(15), 3);
  CHECA(!c.maq.cmd_cadastrar(9, c.t));            // usuário inexistente
}

TESTE(lcd_sempre_16_colunas) {
  Cenario c;
  c.digitar("3#1111#");
  CHECA_IGUAL(std::strlen(c.maq.linha1()), 16u);
  CHECA_IGUAL(std::strlen(c.maq.linha2()), 16u);
  c.passar(3500);
  CHECA(std::strncmp(c.maq.linha1(), "Digital ou ID+#", 15) == 0);
}

// ---------------------------------------------------------------- térmico --
struct T { SaidaFalsa s; Termico t{s}; uint32_t agora = 0; };

static Leituras lei(int16_t baia, int16_t q = 300) { return Leituras{true, true, true, baia, q, q}; }

TESTE(termico_histerese_e_tempos_minimos) {
  T x;
  x.t.atualizar(lei(70), false, x.agora);
  CHECA(!x.t.peltier1());                          // ao ligar, espera o tempo mínimo desligado
  x.agora += par::MIN_DESLIGADO_MS;
  x.t.atualizar(lei(70), false, x.agora);
  CHECA(x.t.peltier1());
  CHECA(!x.t.peltier2());                          // escalonada
  x.agora += par::ESCALONA_MS;
  x.t.atualizar(lei(55), false, x.agora);
  CHECA(x.t.peltier2());
  x.agora += 1000;
  x.t.atualizar(lei(39), false, x.agora);          // abaixo de sp − 1,0, mas ligado há pouco
  CHECA(x.t.peltier1());
  x.agora += par::MIN_LIGADO_MS;
  x.t.atualizar(lei(39), false, x.agora);
  CHECA(!x.t.peltier1() && !x.t.peltier2());
  x.agora += 1000;
  x.t.atualizar(lei(61), false, x.agora);          // voltou a esquentar, mas desligado há pouco
  CHECA(!x.t.peltier1());
}

TESTE(termico_corte_contra_congelar) {
  T x;
  x.t.atualizar(lei(70), false, 0);                // primeira leitura: começa a contar o mínimo desligado
  x.agora = par::MIN_DESLIGADO_MS;
  x.t.atualizar(lei(70), false, x.agora);
  CHECA(x.t.peltier1());
  x.agora += 1000;
  x.t.atualizar(lei(19), false, x.agora);          // ≤ 2,0 °C: desliga na hora, sem esperar o mínimo
  CHECA(!x.t.peltier1());
  x.agora += par::MIN_DESLIGADO_MS;
  x.t.atualizar(lei(35), false, x.agora);
  CHECA(!x.t.peltier1());                          // ainda abaixo de 4,0
  x.t.atualizar(lei(61), false, x.agora += 1000);
  CHECA(x.t.peltier1());
}

TESTE(termico_falha_de_sensor) {
  T x;
  x.t.atualizar(lei(70), false, 0);                // primeira leitura: começa a contar o mínimo desligado
  x.agora = par::MIN_DESLIGADO_MS;
  x.t.atualizar(lei(70), false, x.agora);
  CHECA(x.t.peltier1());
  Leituras l = lei(70);
  l.baia_ok = false;
  x.t.atualizar(l, false, x.agora += 1000);
  CHECA(!x.t.peltier1());
  CHECA(x.t.falha_sensor());
  x.t.atualizar(l, false, x.agora += 1000);
  CHECA_IGUAL(x.s.conta(Ev::SENSOR_FALHA), 1);
  x.t.atualizar(lei(850), false, x.agora += 1000); // 85 °C na baia: leitura absurda
  CHECA(!x.t.peltier1());
}

TESTE(termico_corte_do_lado_quente) {
  T x;
  x.t.atualizar(lei(70), false, 0);                // primeira leitura: começa a contar o mínimo desligado
  x.agora = par::MIN_DESLIGADO_MS;
  x.t.atualizar(lei(70), false, x.agora);
  x.t.atualizar(lei(70, 605), false, x.agora += 1000);
  CHECA(!x.t.peltier1());
  CHECA(x.s.teve(Ev::CORTE_QUENTE));
  x.t.atualizar(lei(70, 500), false, x.agora += par::MIN_DESLIGADO_MS);
  CHECA(!x.t.peltier1());                          // só religa abaixo de 45 °C
  x.t.atualizar(lei(70, 440), false, x.agora += 1000);
  CHECA(x.t.peltier1());
}

TESTE(termico_intertravamento_com_a_trava) {
  T x;
  x.t.atualizar(lei(70), false, 0);                // primeira leitura: começa a contar o mínimo desligado
  x.agora = par::MIN_DESLIGADO_MS;
  x.t.atualizar(lei(70), false, x.agora);
  x.t.atualizar(lei(70), false, x.agora += 5000);
  CHECA(x.t.peltier1() && x.t.peltier2());
  x.t.atualizar(lei(70), true, x.agora += 100);    // trava energizada
  CHECA(!x.t.peltier1() && !x.t.peltier2());
  x.t.atualizar(lei(70), false, x.agora += 2900);  // fim do pulso: volta sem esperar 120 s
  CHECA(x.t.peltier1());
  CHECA(!x.t.peltier2());                          // escalonada de novo
  x.t.atualizar(lei(70), false, x.agora += par::ESCALONA_MS);
  CHECA(x.t.peltier2());
}

TESTE(termico_alarme_fora_da_faixa) {
  T x;
  x.t.atualizar(lei(95), false, x.agora);
  x.t.atualizar(lei(95), false, x.agora += par::ALARME_FAIXA_MS - 1000);
  CHECA(!x.s.teve(Ev::TEMP_ALARME));
  x.t.atualizar(lei(95), false, x.agora += 2000);
  CHECA(x.s.teve(Ev::TEMP_ALARME));
  x.t.atualizar(lei(60), false, x.agora += 1000);
  CHECA(x.s.teve(Ev::TEMP_NORMAL));
}

int main() {
  for (auto& c : casos()) {
    int antes = falhas();
    c.f();
    std::printf("%s %s\n", falhas() == antes ? "ok    " : "FALHOU", c.nome);
  }
  std::printf("\n%zu testes, %d falha(s)\n", casos().size(), falhas());
  return falhas() ? 1 : 0;
}
