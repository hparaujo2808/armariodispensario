#include "maquina.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "parametros.h"

namespace armario {

namespace {
void copiar16(char* dst, const char* src) {
  size_t n = strlen(src);
  if (n > 16) n = 16;
  memcpy(dst, src, n);
  for (size_t i = n; i < 16; i++) dst[i] = ' ';   // completa com espaços: o LCD não guarda lixo da tela anterior
  dst[16] = 0;
}
}  // namespace

void Maquina::tela(const char* a, const char* b) {
  copiar16(l1_, a);
  copiar16(l2_, b);
}

void Maquina::tela_padrao() { tela("Digital ou ID+#", "Dispensario"); }

void Maquina::ir(Estado e, uint32_t agora) {
  estado_ = e;
  desde_ = agora;
  nbuf_ = 0;
  buf_[0] = 0;
  // só os estados que importam depois de um reset vão para a EEPROM (poupa gravações)
  // BLOQUEADO também: um reset (tirar a USB) não zera o bloqueio
  if (e == Estado::OCIOSO || e == Estado::LIBERADO || e == Estado::PORTA_ABERTA || e == Estado::BLOQUEADO)
    mem_.salvar_estado((uint8_t)e);
  msg_temporaria_ = false;
  if (e == Estado::OCIOSO) {
    usuario_ = 0;
    tela_padrao();
  }
}

void Maquina::iniciar(bool porta_aberta, uint32_t agora) {
  porta_aberta_ = porta_aberta;
  Estado salvo = (Estado)mem_.estado_salvo();
  saida_.evento(Ev::BOOT, 0, (int16_t)salvo);
  if (porta_aberta) {
    // reiniciou com a porta aberta: segue como porta aberta, sem usuário conhecido
    saida_.evento(Ev::RECUPERADO, 0, (int16_t)salvo);
    ir(Estado::PORTA_ABERTA, agora);
    usuario_ = 0;
    tela("Porta aberta", "Feche a porta");
  } else if (salvo == Estado::BLOQUEADO) {
    erros_ = par::MAX_ERROS;
    ir(Estado::BLOQUEADO, agora);      // recomeça os 30 s inteiros
    tela("Bloqueado", "");
  } else {
    ir(Estado::OCIOSO, agora);
  }
}

void Maquina::autenticado(uint8_t u, Metodo m, uint32_t agora) {
  erros_ = 0;
  erros_digital_ = 0;
  usuario_ = u;
  som_ = Som::OK;
  saida_.evento(Ev::AUTH_OK, u, (int16_t)m);
  if (notebook_online(agora)) {
    ir(Estado::AGUARDANDO_NOTEBOOK, agora);
    usuario_ = u;
    char b[17];
    snprintf(b, sizeof b, "Ola, usuario %u", u);
    tela(b, "Digite o CPF");
  } else {
    sem_notebook(agora);
  }
}

void Maquina::sem_notebook(uint32_t agora) {
  if (autonomo_ok_) {
    liberar(agora, true);
    return;
  }
  saida_.evento(Ev::CANCELADO, usuario_, 2);   // 2 = notebook fora do ar e modo autônomo desligado
  ir(Estado::OCIOSO, agora);
  tela("Sistema fora", "do ar");
  msg_temporaria_ = true;
}

void Maquina::falhou(Metodo m, uint32_t agora) {
  uint8_t& erros = m == Metodo::DIGITAL ? erros_digital_ : erros_;
  erros++;
  som_ = Som::ERRO;
  saida_.evento(Ev::AUTH_FALHA, 0, (int16_t)m);
  if (erros >= par::MAX_ERROS) {
    saida_.evento(Ev::BLOQUEIO, 0, (int16_t)(par::BLOQUEIO_MS / 1000));
    ir(Estado::BLOQUEADO, agora);
    tela("Bloqueado", "");
  } else {
    ir(Estado::OCIOSO, agora);
    tela(m == Metodo::DIGITAL ? "Digital invalida" : "Senha errada", "Tente de novo");
    msg_temporaria_ = true;
  }
}

void Maquina::liberar(uint32_t agora, bool autonomo) {
  uint8_t u = usuario_;
  if (autonomo) saida_.evento(Ev::MODO_AUTONOMO, u, 0);
  saida_.evento(Ev::LIBERADO, u, 0);
  ir(Estado::LIBERADO, agora);
  usuario_ = u;
  tela("Pode abrir", "a porta");
}

void Maquina::tecla(char k, uint32_t agora) {
  ultima_tecla_ = agora;
  if (estado_ == Estado::BLOQUEADO || estado_ == Estado::LIBERADO || estado_ == Estado::CADASTRANDO) return;
  som_ = Som::TECLA;
  if (estado_ == Estado::AGUARDANDO_NOTEBOOK || estado_ == Estado::PORTA_ABERTA) {
    if (k == 'D' && estado_ == Estado::AGUARDANDO_NOTEBOOK) cmd_cancelar(agora);
    return;
  }
  if (k == '*') {                       // apaga e volta ao início
    ir(Estado::OCIOSO, agora);
    return;
  }
  bool digito = k >= '0' && k <= '9';
  if (estado_ == Estado::OCIOSO) {
    if (!digito) return;
    ir(Estado::DIGITANDO_ID, agora);
  }
  if (digito) {
    if (nbuf_ < (estado_ == Estado::DIGITANDO_ID ? 2 : par::TAM_SENHA_MAX)) {
      buf_[nbuf_++] = k;
      buf_[nbuf_] = 0;
    }
  } else if (k == '#') {
    if (estado_ == Estado::DIGITANDO_ID) {
      int id = nbuf_ ? atoi(buf_) : 0;
      if (id < 1 || id > mem::N_USUARIOS) {
        falhou(Metodo::SENHA, agora);
        return;
      }
      id_digitado_ = (uint8_t)id;
      ir(Estado::DIGITANDO_SENHA, agora);
    } else if (estado_ == Estado::DIGITANDO_SENHA) {
      if (nbuf_ >= par::TAM_SENHA_MIN && usuarios_.conferir_senha(id_digitado_, buf_)) {
        memset(buf_, 0, sizeof buf_);
        autenticado(id_digitado_, Metodo::SENHA, agora);
      } else {
        memset(buf_, 0, sizeof buf_);
        falhou(Metodo::SENHA, agora);
      }
      return;
    }
  }
  // tela da digitação: o ID aparece, a senha vira asteriscos
  char b[17];
  if (estado_ == Estado::DIGITANDO_ID) {
    snprintf(b, sizeof b, "ID: %s", buf_);
    tela(b, "#=ok  *=apaga");
  } else {
    char a[9] = {0};
    for (uint8_t i = 0; i < nbuf_; i++) a[i] = '*';
    snprintf(b, sizeof b, "Senha: %s", a);
    tela(b, "#=ok  *=apaga");
  }
}

void Maquina::digital(int16_t posicao, uint32_t agora) {
  if (estado_ != Estado::OCIOSO) return;
  if (posicao < 0) {
    falhou(Metodo::DIGITAL, agora);
    return;
  }
  uint8_t u = usuarios_.por_digital((uint8_t)posicao);
  if (!u) {
    falhou(Metodo::DIGITAL, agora);
    return;
  }
  autenticado(u, Metodo::DIGITAL, agora);
}

void Maquina::porta(bool aberta, uint32_t agora) {
  if (aberta == porta_aberta_) return;
  porta_aberta_ = aberta;
  if (aberta) {
    if (estado_ == Estado::LIBERADO) {
      saida_.evento(Ev::PORTA_ABERTA, usuario_, 0);
      uint8_t u = usuario_;
      ir(Estado::PORTA_ABERTA, agora);   // a trava desliga ao sair de LIBERADO
      usuario_ = u;
      tela("Porta aberta", "Feche ao sair");
    } else if (expirou_u_ && agora - expirou_em_ < par::JANELA_ABERTURA_MS && estado_ != Estado::PORTA_ABERTA) {
      // a lingueta soltou no pulso, mas o reed só abriu depois de a liberação expirar:
      // a abertura ainda é do último usuário (valor 1 = abertura tardia)
      uint8_t u = expirou_u_;
      saida_.evento(Ev::PORTA_ABERTA, u, 1);
      ir(Estado::PORTA_ABERTA, agora);
      usuario_ = u;
      tela("Porta aberta", "Feche ao sair");
    } else if (estado_ != Estado::PORTA_ABERTA) {
      // abriu sem autenticação (chave, força ou liberação de emergência): RNF03
      saida_.evento(Ev::ABERTURA_NAO_AUTORIZADA, 0, (int16_t)estado_);
      ir(Estado::PORTA_ABERTA, agora);
      usuario_ = 0;
      alarme_ = true;
      tela("ABERTURA SEM", "AUTORIZACAO");
    }
    aviso_tempo_dado_ = false;
    expirou_u_ = 0;
  } else if (estado_ == Estado::PORTA_ABERTA) {
    uint32_t s = (agora - desde_) / 1000;
    saida_.evento(Ev::PORTA_FECHADA, usuario_, (int16_t)(s > 32767 ? 32767 : s));
    alarme_ = false;
    ir(Estado::OCIOSO, agora);
  }
}

void Maquina::tick(uint32_t agora) {
  switch (estado_) {
    case Estado::DIGITANDO_ID:
    case Estado::DIGITANDO_SENHA:
      if (agora - ultima_tecla_ >= par::DIGITACAO_MS) ir(Estado::OCIOSO, agora);
      break;
    case Estado::AGUARDANDO_NOTEBOOK:
      if (agora - desde_ >= par::AGUARDA_NOTEBOOK_MS) {
        saida_.evento(Ev::CANCELADO, usuario_, 1);
        ir(Estado::OCIOSO, agora);
      } else if (!notebook_online(agora)) {
        sem_notebook(agora);           // notebook caiu: o Mega segue sozinho (se a farmácia permitir)
      }
      break;
    case Estado::LIBERADO:
      if (agora - desde_ >= par::TRAVA_MAX_MS) {   // trava nunca fica ligada mais que isso
        saida_.evento(Ev::LIBERACAO_EXPIROU, usuario_, 0);
        expirou_u_ = usuario_;
        expirou_em_ = agora;
        ir(Estado::OCIOSO, agora);
      }
      break;
    case Estado::PORTA_ABERTA:
      if (!aviso_tempo_dado_ && agora - desde_ >= alarme_porta_ms_) {
        aviso_tempo_dado_ = true;
        alarme_ = true;
        saida_.evento(Ev::PORTA_ABERTA_TEMPO, usuario_, (int16_t)(alarme_porta_ms_ / 1000));
        tela("Feche a porta", "");
      }
      break;
    case Estado::BLOQUEADO: {
      uint32_t passou = agora - desde_;
      if (passou >= par::BLOQUEIO_MS) {
        erros_ = 0;
        erros_digital_ = 0;
        ir(Estado::OCIOSO, agora);
      } else {
        char b[17];
        snprintf(b, sizeof b, "Aguarde %lus", (unsigned long)((par::BLOQUEIO_MS - passou + 999) / 1000));
        tela("Bloqueado", b);
      }
      break;
    }
    case Estado::CADASTRANDO:
      if (agora - desde_ >= 60000) ir(Estado::OCIOSO, agora);
      break;
    case Estado::OCIOSO:
      if (msg_temporaria_ && agora - desde_ >= 3000) {
        msg_temporaria_ = false;
        tela_padrao();
      }
      break;
  }
}

bool Maquina::notebook_online(uint32_t agora) const {
  return teve_notebook_ && agora - ultimo_notebook_ < par::NOTEBOOK_SILENCIO_MS;
}

bool Maquina::cmd_liberar(uint8_t u, uint32_t agora) {
  if (estado_ != Estado::AGUARDANDO_NOTEBOOK || u != usuario_) return false;
  liberar(agora, false);
  return true;
}

bool Maquina::cmd_cancelar(uint32_t agora) {
  if (estado_ != Estado::AGUARDANDO_NOTEBOOK && estado_ != Estado::CADASTRANDO) return false;
  saida_.evento(Ev::CANCELADO, usuario_, 0);
  ir(Estado::OCIOSO, agora);
  return true;
}

bool Maquina::cmd_cadastrar(uint8_t u, uint32_t agora) {
  if (estado_ != Estado::OCIOSO || !usuarios_.ativo(u)) return false;
  ir(Estado::CADASTRANDO, agora);
  usuario_ = u;
  tela("Cadastro digital", "Ponha o dedo");
  return true;
}

void Maquina::cadastro_terminou(bool ok, uint8_t posicao, uint32_t agora) {
  if (estado_ != Estado::CADASTRANDO) return;
  if (ok && usuarios_.definir_digital(usuario_, posicao)) {
    saida_.evento(Ev::DIGITAL_CADASTRADA, usuario_, posicao);
    som_ = Som::OK;
  } else {
    som_ = Som::ERRO;
  }
  ir(Estado::OCIOSO, agora);
}

}  // namespace armario
