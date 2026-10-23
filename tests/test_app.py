"""App do notebook (Fase 4): fluxo da banca com o Mega simulado, auditoria,
LGPD, recuperação e API. Os testes do legado foram trazidos para cá e
adaptados à arquitetura Mega + notebook."""
import json
import os
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import protocolo as P
from app.api import criar_app
from app.auth import gerar_hash
from app.config import Config
from app.core import CONFIRMACAO, LIBERADO, OCIOSO, PORTA_ABERTA, PRESCRICAO, AUTENTICADO, Dispensario, ErroOperacao
from app.hal.mega_simulado import MegaSimulado
from app.mock_mv import PRESCRICOES
from app.mv_client import ErroMV, ItemPrescrito, Prescricao
from app.semente import semear
from app.storage import Banco, ErroRegra

SEGREDO = b"k" * 32
CPF = "11122233344"   # fictício (app/mock_mv.py)


class Relogio:
    def __init__(self, t=1_790_000_000.0):
        self.t = t

    def __call__(self):
        return self.t

    def avancar(self, s):
        self.t += s


class MVFalso:
    def __init__(self):
        self.fora_do_ar = False
        self.recebidas = []

    def consultar_prescricao(self, ident):
        if self.fora_do_ar:
            raise ErroMV("timeout")
        d = PRESCRICOES.get("".join(c for c in ident.upper() if c.isalnum()))
        if not d:
            return None
        return Prescricao(d["prescricao_id"], d["paciente"]["nome"], d["paciente"]["leito"],
                          [ItemPrescrito(i["codigo"], i["descricao"], i["quantidade"], i["posologia"]) for i in d["itens"]])

    def informar_dispensacao(self, p):
        if self.fora_do_ar:
            return False
        self.recebidas.append(p)
        return True


@pytest.fixture
def a(tmp_path):
    cfg = Config(porta_serial="sim", dados_dir=str(tmp_path),
                 cameras=[{"nome": "externa", "fonte": "sim"}, {"nome": "interna", "fonte": "sim"}])
    db = Banco(str(tmp_path / "d.db"), SEGREDO)
    rel = Relogio()
    mega = MegaSimulado(rel)
    semear(db, "admin123", mega)

    class A:
        pass
    x = A()
    x.cfg, x.db, x.rel, x.mega, x.mv, x.tmp = cfg, db, rel, mega, MVFalso(), tmp_path
    x.novo = lambda: Dispensario(cfg, mega, db, x.mv, relogio=rel)
    x.d = x.novo()
    x.d.tick()
    return x


def rodar(a, s=1.0, passo=0.1):
    for _ in range(int(s / passo)):
        a.rel.avancar(passo)
        a.d.tick()


def saldo(a, comp, item):
    return [e for e in a.db.estoque() if e["compartimento"] == comp and e["item"] == item][0]["quantidade"]


def tipos(a):
    return [r["tipo"] for r in a.db.auditoria(limite=5000)]


def retirada_ate_porta_aberta(a):
    a.mega.autenticar(1)
    rodar(a, 0.2)
    assert a.d.estado == AUTENTICADO
    a.d.consultar(CPF)
    assert a.d.estado == PRESCRICAO
    a.d.liberar()
    assert a.d.estado == LIBERADO and "LIB 1" in a.mega.comandos
    a.mega.abrir_porta()
    rodar(a, 0.2)
    assert a.d.estado == PORTA_ABERTA


# ------------------------------------------------------------------ protocolo
def test_crc_igual_ao_do_firmware():
    # os mesmos vetores estão em firmware/testes/teste_logica.cpp
    assert P.empacotar("LIB id=5 u=3") == b"$LIB id=5 u=3*8D\n"
    assert P.empacotar("EV seq=12 t=AUTH_OK u=3 v=1 ms=34567 b=3") == b"$EV seq=12 t=AUTH_OK u=3 v=1 ms=34567 b=3*35\n"
    tipo, c = P.analisar("$EV seq=12 t=AUTH_OK u=3 v=1 ms=34567 b=3*35")
    assert tipo == "EV" and P.evento(c)["u"] == 3
    assert P.analisar("$EV seq=12 t=AUTH_OK u=3 v=1 ms=34567 b=3*36") is None


# ------------------------------------------------------------------ fluxo da banca
def test_fluxo_completo_da_banca(a):
    antes_ins, antes_ser = saldo(a, "BAIA_FRIA", "INS-NPH"), saldo(a, "A1", "SER-1ML")
    retirada_ate_porta_aberta(a)
    assert a.d.cameras.gravando
    rodar(a, 5)
    a.mega.fechar_porta()
    rodar(a, 0.2)
    assert a.d.estado == CONFIRMACAO and not a.d.cameras.gravando
    a.d.confirmar()
    assert a.d.estado == OCIOSO
    assert saldo(a, "BAIA_FRIA", "INS-NPH") == antes_ins - 1
    assert saldo(a, "A1", "SER-1ML") == antes_ser - 2
    t = tipos(a)
    for e in ("MEGA_AUTH_OK", "PRESCRICAO_CONSULTADA", "PORTA_LIBERADA", "MEGA_LIBERADO", "ABERTURA",
              "MEGA_PORTA_ABERTA", "FECHAMENTO", "MEGA_PORTA_FECHADA", "RETIRADA_REGISTRADA"):
        assert e in t, e
    # RF05: abertura com usuário e horário; RF07: mídia de cada câmera com SHA-256
    ab = a.db.auditoria(tipo="ABERTURA")[0]
    assert ab["usuario_id"] == a.db.usuario(mega_id=1)["id"] and ab["ts"] > 0
    fe = a.db.auditoria(tipo="FECHAMENTO")[0]
    assert {m["camera"] for m in fe["midia"]} == {"externa", "interna"}
    for m in fe["midia"]:
        assert len(m["sha256"]) == 64 and os.path.exists(os.path.join(a.cfg.dados_dir, m["arquivo"]))
    assert a.db.verificar_cadeia()["integra"]
    assert a.mega.eventos() == []                    # tudo confirmado ao Mega
    assert a.db.pendentes_mv()[0]["payload"]["prescricao_id"] == PRESCRICOES[CPF]["prescricao_id"]
    assert a.d.enviar_pendentes_mv() == 1 and a.mv.recebidas


def test_eventos_repetidos_nao_duplicam(a):
    a.mega.autenticar(1)
    pend = a.mega.eventos()
    a.d.tick()
    for ev in pend:                                  # o Mega reenviou antes de receber o ACK
        a.d._evento_mega(ev)
    assert tipos(a).count("MEGA_AUTH_OK") == 1


def test_divergencia_e_estoque_baixo(a):
    a.db.movimentar("ajuste", "INS-NPH", "BAIA_FRIA", 3, None)
    retirada_ate_porta_aberta(a)
    a.mega.fechar_porta()
    rodar(a, 0.2)
    a.d.confirmar({"INS-NPH": 1, "SER-1ML": 1})      # retirou 1 seringa a menos que o prescrito
    t = tipos(a)
    assert "DIVERGENCIA_PRESCRICAO" in t
    assert any(n["tipo"] == "ESTOQUE_BAIXO" and n["item"] == "INS-NPH" for n in a.db.notificacoes())


def test_reposicao_pela_logistica(a):
    a.mega.autenticar(2, "senha", "2468")
    rodar(a, 0.2)
    a.d.iniciar_reposicao()
    a.mega.abrir_porta()
    rodar(a, 0.2)
    a.mega.fechar_porta()
    rodar(a, 0.2)
    antes = saldo(a, "C2", "CAT-22")
    a.d.confirmar({"C2|CAT-22": 10})
    assert saldo(a, "C2", "CAT-22") == antes + 10


def test_enfermagem_nao_faz_reposicao_e_logistica_nao_retira(a):
    a.mega.autenticar(1)
    rodar(a, 0.2)
    with pytest.raises(ErroOperacao):
        a.d.iniciar_reposicao()
    a.d.cancelar()
    a.mega.autenticar(2, "senha", "2468")
    rodar(a, 0.2)
    with pytest.raises(ErroOperacao):
        a.d.consultar(CPF)


def test_liberacao_expira_se_a_porta_nao_abrir(a):
    a.mega.autenticar(1)
    rodar(a, 0.2)
    a.d.consultar(CPF)
    a.d.liberar()
    rodar(a, 3.5)
    assert a.d.estado == LIBERADO                    # ainda na janela de abertura tardia
    rodar(a, 5.5)
    assert a.d.estado == OCIOSO
    assert "MEGA_LIBERACAO_EXPIROU" in tipos(a)


def test_abertura_nao_autorizada_grava_e_alarma(a):
    a.mega.abrir_porta()
    rodar(a, 0.2)
    assert "ABERTURA_NAO_AUTORIZADA" in a.d.estado_publico()["alarmes"]
    assert a.d.cameras.gravando
    a.mega.fechar_porta()
    rodar(a, 0.2)
    reg = a.db.auditoria(tipo="FECHAMENTO_SEM_SESSAO")[0]
    assert len(reg["midia"]) == 2
    assert "ABERTURA_NAO_AUTORIZADA" not in a.d.estado_publico()["alarmes"]


def test_alarme_porta_aberta_tempo(a):
    retirada_ate_porta_aberta(a)
    rodar(a, 31)
    assert "PORTA_ABERTA_TEMPO" in a.d.estado_publico()["alarmes"]


def test_usuario_do_mega_sem_cadastro_no_notebook(a):
    a.mega.senhas[9] = "9999"
    a.mega.autenticar(9, "senha", "9999")
    rodar(a, 0.2)
    assert a.d.estado == OCIOSO
    assert "USUARIO_MEGA_DESCONHECIDO" in tipos(a) and "CANC" in a.mega.comandos


def test_mv_fora_do_ar(a):
    a.mv.fora_do_ar = True
    a.mega.autenticar(1)
    rodar(a, 0.2)
    with pytest.raises(ErroOperacao, match="MV indisponível"):
        a.d.consultar(CPF)


def test_inatividade_encerra_e_cancela_no_mega(a):
    a.mega.autenticar(1)
    rodar(a, 0.2)
    rodar(a, a.cfg.sessao_inatividade_s + 1, passo=1.0)
    assert a.d.estado == OCIOSO and "CANC" in a.mega.comandos


# ------------------------------------------------------------------ RNF07.1 e RNF04/05
def test_notebook_reinicia_com_a_porta_aberta(a):
    retirada_ate_porta_aberta(a)
    a.d = a.novo()                                    # notebook reiniciou (o journal está no banco)
    assert a.d.estado == CONFIRMACAO and a.d.estado_publico()["recuperada"]
    a.d.confirmar()
    assert "SESSAO_RECUPERADA" in tipos(a)


def test_auditoria_somente_insercao_e_cadeia(a):
    retirada_ate_porta_aberta(a)
    with pytest.raises(sqlite3.DatabaseError):
        a.db.con.execute("UPDATE auditoria SET tipo='X' WHERE id=1")
    with pytest.raises(sqlite3.DatabaseError):
        a.db.con.execute("DELETE FROM mega_eventos")
    assert a.db.verificar_cadeia()["integra"]
    # alguém mexe no arquivo por fora (sem os gatilhos): a cadeia acusa
    con = sqlite3.connect(a.db.caminho)
    con.execute("DROP TRIGGER aud_sem_update")
    con.execute("UPDATE auditoria SET dados='{}' WHERE id=3")
    con.commit()
    assert not a.db.verificar_cadeia()["integra"]


def test_cpf_nao_fica_gravado(a):
    retirada_ate_porta_aberta(a)
    a.mega.fechar_porta()
    rodar(a, 0.2)
    a.d.confirmar()
    a.db.con.execute("PRAGMA wal_checkpoint(FULL)")
    bruto = open(a.db.caminho, "rb").read()
    assert CPF.encode() not in bruto
    assert a.d.db.mascarar(CPF) == "***.222.333-**"


def test_rf12_refrigerado_so_em_compartimento_climatizado(a):
    with pytest.raises(ErroRegra):
        a.db.alocar("A1", "INS-NPH")


# ------------------------------------------------------------------ API
def test_api_quiosque_e_painel(a):
    cli = TestClient(criar_app(a.d, laços=False))
    assert cli.get("/api/kiosk/estado").json()["estado"] == OCIOSO
    r = cli.post("/api/kiosk/sim/autenticar", json={"mega_id": 1})
    assert r.json()["estado"] == AUTENTICADO
    assert cli.post("/api/kiosk/consultar", json={"identificador": CPF}).status_code == 200
    assert cli.post("/api/kiosk/liberar", json={}).json()["estado"] == LIBERADO
    assert cli.post("/api/kiosk/sim/porta", json={"aberta": True}).json()["estado"] == PORTA_ABERTA
    assert cli.post("/api/kiosk/sim/porta", json={"aberta": False}).json()["estado"] == CONFIRMACAO
    assert cli.post("/api/kiosk/confirmar", json={"quantidades": None}).json()["estado"] == OCIOSO
    # painel: logística vê estoque, mas não a auditoria
    tok = cli.post("/api/auth/token", json={"matricula": "2001", "senha": "logistica2026"}).json()["token"]
    h = {"Authorization": "Bearer " + tok}
    assert cli.get("/api/estoque", headers=h).status_code == 200
    assert cli.get("/api/auditoria", headers=h).status_code == 403
    tok = cli.post("/api/auth/token", json={"matricula": "admin", "senha": "admin123"}).json()["token"]
    h = {"Authorization": "Bearer " + tok}
    assert cli.get("/api/auditoria/verificar", headers=h).json()["integra"]
    assert cli.get("/api/midia/../d.db", headers=h).status_code == 404   # sem sair da pasta de mídia
    ev = cli.get("/api/mega/eventos", headers=h).json()
    assert ev["eventos"] and ev["online"]


def test_painel_define_senha_da_porta(a):
    cli = TestClient(criar_app(a.d, laços=False))
    tok = cli.post("/api/auth/token", json={"matricula": "admin", "senha": "admin123"}).json()["token"]
    h = {"Authorization": "Bearer " + tok}
    uid = cli.post("/api/usuarios", json={"matricula": "1002", "nome": "Bia Técnica", "perfil": "enfermagem"},
                   headers=h).json()["id"]
    r = cli.post(f"/api/usuarios/{uid}/senha_porta", json={"senha": "8642"}, headers=h).json()
    assert r["mega_id"] == 4 and a.mega.senhas[4] == "8642"
    assert cli.post(f"/api/usuarios/{uid}/senha_porta", json={"senha": "12"}, headers=h).status_code == 400


# ------------------------------------------------------------------ revisão independente (23/10)
def _ev(seq, t="AUTH_FALHA", u=0, v=2, ms=1000, b=1):
    return {"seq": seq, "t": t, "u": u, "v": v, "ms": ms, "b": b}


def test_eeprom_formatada_nao_descarta_eventos_novos(a):
    """Item 3: o seq do Mega recomeça em 1 depois de formatar a EEPROM."""
    n = len(a.db.mega_eventos(5000))
    a.d._evento_mega(_ev(1, "BOOT", ms=50, b=1))      # mesmo seq do BOOT do simulador, conteúdo diferente
    assert "MEGA_SEQUENCIA_REINICIADA" in tipos(a)
    assert len(a.db.mega_eventos(5000)) == n + 1
    a.d._evento_mega(_ev(1, "BOOT", ms=50, b=1))      # agora sim, repetido
    assert len(a.db.mega_eventos(5000)) == n + 1


def test_ack_so_ate_o_ultimo_sem_buraco(a):
    """Item 7: o ACK do Mega é cumulativo; um evento que faltou não pode ser apagado da fila."""
    acks = []
    a.mega.confirmar = lambda seq: acks.append(seq)
    base = a.db.mega_contiguo()[0]
    a.d._evento_mega(_ev(base + 2))                     # o base+1 se perdeu (CRC ruim)
    a.d._confirmar_mega()
    assert acks[-1] == base
    a.d._evento_mega(_ev(base + 1))                     # reenviado pelo Mega
    a.d._confirmar_mega()
    assert acks[-1] == base + 2
    a.d._evento_mega(_ev(base + 5))                     # base+3 e base+4 nunca chegam
    a.d._confirmar_mega()
    a.rel.avancar(61)
    a.d._confirmar_mega()
    assert acks[-1] == base + 5 and "MEGA_EVENTOS_PERDIDOS" in tipos(a)


def test_evento_guardado_recebe_a_hora_do_mega(a):
    """Item 8: evento guardado com o notebook fora do ar entra com a hora em que aconteceu."""
    ms_agora = int(a.rel() * 1000) % 2**32
    a.d._evento_mega(_ev(a.db.mega_contiguo()[1] + 1, ms=ms_agora - 600_000, b=1))
    r = a.db.auditoria(tipo="MEGA_AUTH_FALHA")[0]
    assert r["dados"]["hora_estimada"] and abs(r["ts"] - (a.rel() - 600)) < 1


def test_desativar_usuario_apaga_no_mega(a):
    """Item 4: senão o usuário revogado abriria a porta no modo autônomo."""
    u = a.db.usuario(mega_id=2)
    assert 2 in a.mega.senhas
    a.d.definir_ativo(u["id"], False, None)
    assert 2 not in a.mega.senhas and not a.db.usuario(mega_id=2)["ativo"]


def test_rf12_compartimento_com_refrigerado_nao_perde_o_frio(a):
    """Item 10."""
    with pytest.raises(ErroRegra):
        a.db.salvar_compartimento("BAIA_FRIA", "Baia fria", False)


def test_confirmacao_e_tudo_ou_nada(a):
    """Item 14: se um item falha, nenhum é baixado."""
    antes = saldo(a, "BAIA_FRIA", "INS-NPH")
    retirada_ate_porta_aberta(a)
    a.mega.fechar_porta()
    rodar(a, 0.2)
    a.db.movimentar("ajuste", "SER-1ML", "A1", 0, None)    # saldo da seringa zerou no meio
    with pytest.raises(Exception):
        a.d.confirmar()
    assert saldo(a, "BAIA_FRIA", "INS-NPH") == antes
    assert a.d.estado == CONFIRMACAO


def test_abertura_tardia_ainda_e_da_sessao(a):
    """Item 16: a lingueta soltou no pulso, mas o reed só abriu depois de a liberação expirar."""
    a.mega.autenticar(1)
    rodar(a, 0.2)
    a.d.consultar(CPF)
    a.d.liberar()
    rodar(a, 4)
    a.mega.abrir_porta()
    rodar(a, 0.2)
    assert a.d.estado == PORTA_ABERTA and "ABERTURA" in tipos(a)
    assert "ABERTURA_SEM_SESSAO" not in tipos(a)
