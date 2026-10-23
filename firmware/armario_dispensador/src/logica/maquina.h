// Máquina de estados do acesso. Não bloqueia: cada chamada só muda o estado
// e as saídas; quem chama passa o tempo (millis) e lê as saídas depois.
#pragma once
#include "memoria.h"
#include "tipos.h"

namespace armario {

class Maquina {
 public:
  Maquina(Saida& s, Usuarios& u, Memoria& m) : saida_(s), usuarios_(u), mem_(m) {}

  // Recupera depois de um reset: a trava sempre começa desligada.
  void iniciar(bool porta_aberta, uint32_t agora);

  // Entradas
  void tecla(char k, uint32_t agora);
  void digital(int16_t posicao, uint32_t agora);    // posição no leitor; −1 = dedo não reconhecido
  void porta(bool aberta, uint32_t agora);          // já filtrado
  void notebook_vivo(uint32_t agora) { ultimo_notebook_ = agora; teve_notebook_ = true; }
  void tick(uint32_t agora);

  // Comandos do notebook (devolvem false se recusados)
  bool cmd_liberar(uint8_t usuario, uint32_t agora);
  bool cmd_cancelar(uint32_t agora);
  bool cmd_cadastrar(uint8_t usuario, uint32_t agora);
  void cadastro_terminou(bool ok, uint8_t posicao, uint32_t agora);
  void definir_alarme_porta_ms(uint32_t ms) { alarme_porta_ms_ = ms; }
  // Modo autônomo (notebook fora do ar): libera só com a autenticação, sem CPF nem vídeo.
  // A farmácia decide (SET auto=0|1); com 0, o Mega recusa e mostra "Sistema fora do ar".
  void permitir_autonomo(bool p) { autonomo_ok_ = p; }

  // Saídas
  Estado estado() const { return estado_; }
  bool trava() const { return estado_ == Estado::LIBERADO; }
  bool alarme() const { return alarme_; }
  Som som() { Som s = som_; som_ = Som::NENHUM; return s; }   // som de um toque (consome)
  const char* linha1() const { return l1_; }
  const char* linha2() const { return l2_; }
  uint8_t usuario() const { return usuario_; }
  bool notebook_online(uint32_t agora) const;

 private:
  void ir(Estado e, uint32_t agora);
  void autenticado(uint8_t u, Metodo m, uint32_t agora);
  void falhou(Metodo m, uint32_t agora);
  void liberar(uint32_t agora, bool autonomo);
  void sem_notebook(uint32_t agora);
  void tela(const char* a, const char* b);
  void tela_padrao();

  Saida& saida_;
  Usuarios& usuarios_;
  Memoria& mem_;
  Estado estado_ = Estado::OCIOSO;
  uint32_t desde_ = 0;            // quando entrou no estado atual
  uint32_t ultima_tecla_ = 0;
  uint32_t ultimo_notebook_ = 0;
  bool teve_notebook_ = false;
  uint32_t alarme_porta_ms_ = 30000;
  uint8_t usuario_ = 0;
  uint8_t erros_ = 0;             // erros de senha seguidos
  uint8_t erros_digital_ = 0;     // erros de digital seguidos (contados à parte: RF01 e RF02)
  uint8_t expirou_u_ = 0;         // último usuário cuja liberação expirou (JANELA_ABERTURA_MS)
  uint32_t expirou_em_ = 0;
  bool autonomo_ok_ = true;
  uint8_t id_digitado_ = 0;
  bool alarme_ = false;
  bool aviso_tempo_dado_ = false;
  bool porta_aberta_ = false;
  bool msg_temporaria_ = false;   // mensagem de erro some depois de 3 s
  Som som_ = Som::NENHUM;
  char buf_[9] = {0};
  uint8_t nbuf_ = 0;
  char l1_[17] = {0};
  char l2_[17] = {0};
};

}  // namespace armario
