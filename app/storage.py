"""Banco de dados local (SQLite) do dispensário, no notebook.

Veio do software do legado (Raspberry Pi) quase sem mudança. Novidades:
`usuarios.mega_id` (número do usuário no Arduino Mega, 1 a 20) e a tabela
`mega_eventos`, que guarda cada evento recebido do Mega uma vez só (pela época e
pelo número de sequência), também somente-inserção.

Garantias de projeto:
- RNF04 (auditabilidade): `auditoria` e `movimentos` são somente-inserção
  (gatilhos bloqueiam UPDATE/DELETE) e cada registro de auditoria carrega um
  HMAC-SHA256 encadeado com o anterior -> qualquer alteração direta no arquivo
  quebra a cadeia e é detectada por `verificar_cadeia()`.
- RNF07.1 (queda de energia): modo WAL + synchronous=FULL; cada commit está em
  disco antes de a função retornar. A sessão em andamento fica gravada em
  `sessao_ativa` (journal) e é recuperada no boot.
- RNF05 (LGPD): CPF/código do paciente nunca é gravado em claro: guarda-se um
  pseudônimo HMAC e uma versão mascarada para exibição.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY,
    matricula TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK (perfil IN ('enfermagem','farmacia','logistica','admin')),
    digital_slot INTEGER UNIQUE,
    mega_id INTEGER UNIQUE CHECK (mega_id IS NULL OR mega_id BETWEEN 1 AND 20),
    senha_hash TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    tentativas INTEGER NOT NULL DEFAULT 0,
    bloqueado_ate REAL NOT NULL DEFAULT 0,
    criado_em REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS itens (
    codigo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    unidade TEXT NOT NULL DEFAULT 'un',
    requer_refrigeracao INTEGER NOT NULL DEFAULT 0,
    estoque_minimo INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS compartimentos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    climatizado INTEGER NOT NULL DEFAULT 0,
    ordem INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS estoque (
    compartimento TEXT NOT NULL REFERENCES compartimentos(id),
    item TEXT NOT NULL REFERENCES itens(codigo),
    quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    PRIMARY KEY (compartimento, item)
);
CREATE TABLE IF NOT EXISTS movimentos (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('retirada','reposicao','ajuste','devolucao')),
    usuario_id INTEGER,
    item TEXT NOT NULL,
    compartimento TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    saldo_apos INTEGER NOT NULL,
    paciente_ref TEXT,
    prescricao_id TEXT,
    sessao_id TEXT
);
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    tipo TEXT NOT NULL,
    usuario_id INTEGER,
    sessao_id TEXT,
    dados TEXT NOT NULL,
    midia TEXT NOT NULL DEFAULT '[]',
    hash_ant TEXT NOT NULL,
    hash TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_aud_ts ON auditoria(ts);
CREATE INDEX IF NOT EXISTS idx_mov_ts ON movimentos(ts);
CREATE TABLE IF NOT EXISTS temperaturas (
    ts REAL NOT NULL, frio REAL, quente REAL, ambiente REAL, duty REAL
);
CREATE TABLE IF NOT EXISTS sessao_ativa (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    dados TEXT NOT NULL,
    atualizado REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox_mv (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    payload TEXT NOT NULL,
    tentativas INTEGER NOT NULL DEFAULT 0,
    enviado REAL
);
CREATE TABLE IF NOT EXISTS notificacoes (
    id INTEGER PRIMARY KEY,
    ts REAL NOT NULL,
    tipo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    item TEXT,
    lida INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS mega_eventos (
    epoca INTEGER NOT NULL,          -- sobe quando a EEPROM do Mega é formatada ou a placa é trocada
    seq INTEGER NOT NULL,
    boot INTEGER NOT NULL,
    ms INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    usuario INTEGER NOT NULL,
    valor INTEGER NOT NULL,
    recebido REAL NOT NULL,
    PRIMARY KEY (epoca, seq)
);
CREATE TRIGGER IF NOT EXISTS mega_sem_update BEFORE UPDATE ON mega_eventos
BEGIN SELECT RAISE(ABORT, 'eventos do Mega sao somente-insercao (RNF04)'); END;
CREATE TRIGGER IF NOT EXISTS mega_sem_delete BEFORE DELETE ON mega_eventos
BEGIN SELECT RAISE(ABORT, 'eventos do Mega sao somente-insercao (RNF04)'); END;
CREATE TRIGGER IF NOT EXISTS aud_sem_update BEFORE UPDATE ON auditoria
BEGIN SELECT RAISE(ABORT, 'auditoria e somente-insercao (RNF04)'); END;
CREATE TRIGGER IF NOT EXISTS aud_sem_delete BEFORE DELETE ON auditoria
BEGIN SELECT RAISE(ABORT, 'auditoria e somente-insercao (RNF04)'); END;
CREATE TRIGGER IF NOT EXISTS mov_sem_update BEFORE UPDATE ON movimentos
BEGIN SELECT RAISE(ABORT, 'movimentos sao somente-insercao (RNF04)'); END;
CREATE TRIGGER IF NOT EXISTS mov_sem_delete BEFORE DELETE ON movimentos
BEGIN SELECT RAISE(ABORT, 'movimentos sao somente-insercao (RNF04)'); END;
"""

GENESIS = "0" * 64
FILA_MEGA = 200          # eventos que cabem na fila da EEPROM do Mega (firmware: mem::N_FILA)


class ErroRegra(Exception):
    """Violação de regra de negócio (ex.: RF12 refrigeração)."""


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def carregar_segredo(caminho: str) -> bytes:
    """Lê (ou cria, com permissão 600) a chave secreta do equipamento."""
    if os.path.exists(caminho):
        with open(caminho, "rb") as f:
            return f.read()
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    chave = os.urandom(32)
    fd = os.open(caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(chave)
    return chave


class Banco:
    def __init__(self, caminho: str, segredo: bytes):
        self.caminho = caminho
        self._segredo = segredo
        self._lock = threading.RLock()
        if caminho != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(caminho)), exist_ok=True)
        self.con = sqlite3.connect(caminho, check_same_thread=False, isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA journal_mode=WAL")
        self.con.execute("PRAGMA synchronous=FULL")
        self.con.execute("PRAGMA foreign_keys=ON")
        self._migrar_mega_eventos()
        self.con.executescript(ESQUEMA)

    def _migrar_mega_eventos(self) -> None:
        """Bancos de antes de 23/10 tinham `seq` como chave sozinho: a tabela velha é guardada com outro nome."""
        cols = [r[1] for r in self.con.execute("PRAGMA table_info(mega_eventos)")]
        if cols and "epoca" not in cols:
            self.con.executescript("DROP TRIGGER IF EXISTS mega_sem_update; DROP TRIGGER IF EXISTS mega_sem_delete; "
                                   "ALTER TABLE mega_eventos RENAME TO mega_eventos_ate_2026_10_23;")

    # ------------------------------------------------------------ utilitários
    def _q(self, sql: str, args: Iterable = ()) -> List[sqlite3.Row]:
        with self._lock:
            return self.con.execute(sql, tuple(args)).fetchall()

    def _x(self, sql: str, args: Iterable = ()) -> sqlite3.Cursor:
        with self._lock:
            return self.con.execute(sql, tuple(args))

    def transacao(self):
        """Transação; pode ser aninhada (só a de fora faz o COMMIT ou o ROLLBACK)."""
        banco = self

        class _T:
            def __enter__(self):
                banco._lock.acquire()
                if not banco.con.in_transaction:
                    banco.con.execute("BEGIN IMMEDIATE")
                    self.dono = True
                else:
                    self.dono = False
                return banco

            def __exit__(self, exc_type, exc, tb):
                try:
                    if self.dono:
                        banco.con.execute("ROLLBACK" if exc_type else "COMMIT")
                finally:
                    banco._lock.release()
                return False

        return _T()

    # ------------------------------------------------------------- LGPD
    def pseudonimo(self, identificador: str) -> str:
        """Pseudônimo estável do paciente (HMAC); o CPF não é armazenado."""
        limpo = "".join(ch for ch in identificador if ch.isalnum())
        return hmac.new(self._segredo, b"paciente:" + limpo.encode(), hashlib.sha256).hexdigest()[:20]

    @staticmethod
    def mascarar(identificador: str) -> str:
        d = "".join(ch for ch in identificador if ch.isdigit())
        if len(d) == 11:  # CPF
            return f"***.{d[3:6]}.{d[6:9]}-**"
        return (identificador[:2] + "*" * max(0, len(identificador) - 4) + identificador[-2:]) if len(identificador) > 4 else "****"

    # --------------------------------------------------------- auditoria
    def auditar(self, tipo: str, dados: Optional[dict] = None, usuario_id: Optional[int] = None,
                sessao_id: Optional[str] = None, midia: Optional[list] = None, ts: Optional[float] = None) -> int:
        dados = dados or {}
        midia = midia or []
        ts = time.time() if ts is None else ts
        with self._lock:
            row = self.con.execute("SELECT hash FROM auditoria ORDER BY id DESC LIMIT 1").fetchone()
            ant = row["hash"] if row else GENESIS
            corpo = _canon([ts, tipo, usuario_id, sessao_id, dados, midia])
            h = hmac.new(self._segredo, (ant + corpo).encode(), hashlib.sha256).hexdigest()
            cur = self.con.execute(
                "INSERT INTO auditoria(ts,tipo,usuario_id,sessao_id,dados,midia,hash_ant,hash) VALUES (?,?,?,?,?,?,?,?)",
                (ts, tipo, usuario_id, sessao_id, _canon(dados), _canon(midia), ant, h))
            return cur.lastrowid

    def verificar_cadeia(self) -> Dict[str, Any]:
        ant = GENESIS
        n = 0
        for r in self._q("SELECT * FROM auditoria ORDER BY id"):
            corpo = _canon([r["ts"], r["tipo"], r["usuario_id"], r["sessao_id"],
                            json.loads(r["dados"]), json.loads(r["midia"])])
            esperado = hmac.new(self._segredo, (ant + corpo).encode(), hashlib.sha256).hexdigest()
            if r["hash_ant"] != ant or r["hash"] != esperado:
                return {"integra": False, "registros": n, "primeiro_invalido": r["id"]}
            ant = r["hash"]
            n += 1
        return {"integra": True, "registros": n, "ultimo_hash": ant}

    def auditoria(self, desde: float = 0, ate: float = 9e12, tipo: Optional[str] = None,
                  usuario_id: Optional[int] = None, limite: int = 500) -> List[dict]:
        sql = "SELECT * FROM auditoria WHERE ts BETWEEN ? AND ?"
        args: list = [desde, ate]
        if tipo:
            sql += " AND tipo = ?"
            args.append(tipo)
        if usuario_id is not None:
            sql += " AND usuario_id = ?"
            args.append(usuario_id)
        sql += " ORDER BY id DESC LIMIT ?"
        args.append(limite)
        out = []
        for r in self._q(sql, args):
            d = dict(r)
            d["dados"] = json.loads(d["dados"])
            d["midia"] = json.loads(d["midia"])
            out.append(d)
        return out

    # ---------------------------------------------------------- usuários
    def criar_usuario(self, matricula: str, nome: str, perfil: str, senha_hash: Optional[str] = None,
                      digital_slot: Optional[int] = None, mega_id: Optional[int] = None) -> int:
        cur = self._x("INSERT INTO usuarios(matricula,nome,perfil,senha_hash,digital_slot,mega_id,criado_em) "
                      "VALUES (?,?,?,?,?,?,?)",
                      (matricula, nome, perfil, senha_hash, digital_slot, mega_id, time.time()))
        return cur.lastrowid

    def usuario(self, uid: Optional[int] = None, matricula: Optional[str] = None,
                digital_slot: Optional[int] = None, mega_id: Optional[int] = None) -> Optional[dict]:
        if uid is not None:
            r = self._q("SELECT * FROM usuarios WHERE id=?", (uid,))
        elif matricula is not None:
            r = self._q("SELECT * FROM usuarios WHERE matricula=?", (matricula,))
        elif mega_id is not None:
            r = self._q("SELECT * FROM usuarios WHERE mega_id=?", (mega_id,))
        else:
            r = self._q("SELECT * FROM usuarios WHERE digital_slot=?", (digital_slot,))
        return dict(r[0]) if r else None

    def proximo_mega_id(self) -> int:
        usados = {r[0] for r in self._q("SELECT mega_id FROM usuarios WHERE mega_id IS NOT NULL")}
        for i in range(1, 21):
            if i not in usados:
                return i
        raise ErroRegra("o Mega guarda no máximo 20 usuários")

    # ------------------------------------------------------- eventos do Mega
    def epoca_mega(self) -> int:
        return self._q("SELECT COALESCE(MAX(epoca), 1) FROM mega_eventos")[0][0]

    def registrar_mega_evento(self, ev: dict) -> str:
        """Guarda o evento do Mega. Devolve "novo", "repetido" (o Mega reenviou) ou "nova_epoca".

        "nova_epoca": o número de sequência voltou para trás com conteúdo diferente,
        ou seja, a EEPROM do Mega foi formatada ou a placa foi trocada. Sem isso,
        todo evento novo seria descartado como repetido (revisão independente, item 3).
        """
        with self.transacao():
            ep = self.epoca_mega()
            r = self.con.execute("SELECT boot,ms,tipo,usuario,valor FROM mega_eventos WHERE epoca=? AND seq=?",
                                 (ep, ev["seq"])).fetchone()
            maior = self.con.execute("SELECT COALESCE(MAX(seq), 0) FROM mega_eventos WHERE epoca=?", (ep,)).fetchone()[0]
            res = "novo"
            if r is not None:
                if tuple(r) == (ev["b"], ev["ms"], ev["t"], ev["u"], ev["v"]):
                    return "repetido"
                ep, res = ep + 1, "nova_epoca"
            elif ev["seq"] + FILA_MEGA < maior:          # mais velho que a fila do Mega inteira: não é reenvio
                ep, res = ep + 1, "nova_epoca"
            self.con.execute("INSERT INTO mega_eventos(epoca,seq,boot,ms,tipo,usuario,valor,recebido) "
                             "VALUES (?,?,?,?,?,?,?,?)",
                             (ep, ev["seq"], ev["b"], ev["ms"], ev["t"], ev["u"], ev["v"], time.time()))
        return res

    def mega_contiguo(self) -> Tuple[int, int]:
        """(último seq sem buraco desde o primeiro da época, maior seq recebido). O ACK do Mega é cumulativo."""
        ep = self.epoca_mega()
        r = self._q("SELECT MIN(seq) FROM mega_eventos e WHERE epoca=? AND NOT EXISTS "
                    "(SELECT 1 FROM mega_eventos WHERE epoca=e.epoca AND seq=e.seq+1)", (ep,))[0][0]
        m = self._q("SELECT COALESCE(MAX(seq), 0) FROM mega_eventos WHERE epoca=?", (ep,))[0][0]
        return (r or 0), m

    def mega_faltando(self, de: int, ate: int) -> List[int]:
        ep = self.epoca_mega()
        tem = {r[0] for r in self._q("SELECT seq FROM mega_eventos WHERE epoca=? AND seq BETWEEN ? AND ?", (ep, de, ate))}
        return [s for s in range(de, ate + 1) if s not in tem]

    def mega_eventos(self, limite: int = 200) -> List[dict]:
        return [dict(r) for r in self._q("SELECT * FROM mega_eventos ORDER BY epoca DESC, seq DESC LIMIT ?", (limite,))]

    def usuarios(self) -> List[dict]:
        return [{k: v for k, v in dict(r).items() if k != "senha_hash"} for r in self._q("SELECT * FROM usuarios ORDER BY nome")]

    def atualizar_usuario(self, uid: int, **campos) -> None:
        permitidos = {"nome", "perfil", "digital_slot", "mega_id", "senha_hash", "ativo", "tentativas", "bloqueado_ate"}
        sets = [k for k in campos if k in permitidos]
        if sets:
            self._x(f"UPDATE usuarios SET {', '.join(k + '=?' for k in sets)} WHERE id=?",
                    [campos[k] for k in sets] + [uid])

    def proximo_slot_digital(self) -> int:
        usados = {r[0] for r in self._q("SELECT digital_slot FROM usuarios WHERE digital_slot IS NOT NULL")}
        s = 0
        while s in usados:
            s += 1
        return s

    # ------------------------------------------- itens e compartimentos (RF10, RF12)
    def salvar_compartimento(self, cid: str, nome: str, climatizado: bool, ordem: int = 0) -> None:
        if not climatizado:
            # RF12: um compartimento com item que exige frio não pode deixar de ser climatizado
            ruins = self._q("SELECT e.item FROM estoque e JOIN itens i ON i.codigo=e.item "
                            "WHERE e.compartimento=? AND i.requer_refrigeracao=1", (cid,))
            if ruins:
                raise ErroRegra(f"{cid} guarda item que exige refrigeração ({ruins[0][0]}): não pode deixar de ser climatizado")
        self._x("INSERT INTO compartimentos(id,nome,climatizado,ordem) VALUES (?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET nome=excluded.nome, climatizado=excluded.climatizado, ordem=excluded.ordem",
                (cid, nome, int(climatizado), ordem))

    def compartimentos(self) -> List[dict]:
        return [dict(r) for r in self._q("SELECT * FROM compartimentos ORDER BY ordem, id")]

    def salvar_item(self, codigo: str, nome: str, unidade: str = "un", requer_refrigeracao: bool = False,
                    estoque_minimo: int = 0) -> None:
        if requer_refrigeracao:
            # RF12: um item que passa a exigir frio não pode continuar em compartimento comum
            ruins = self._q("SELECT e.compartimento FROM estoque e JOIN compartimentos c ON c.id=e.compartimento "
                            "WHERE e.item=? AND c.climatizado=0", (codigo,))
            if ruins:
                raise ErroRegra(f"item {codigo} está alocado em compartimento não climatizado: "
                                f"{', '.join(r[0] for r in ruins)} (RF12)")
        self._x("INSERT INTO itens(codigo,nome,unidade,requer_refrigeracao,estoque_minimo) VALUES (?,?,?,?,?) "
                "ON CONFLICT(codigo) DO UPDATE SET nome=excluded.nome, unidade=excluded.unidade, "
                "requer_refrigeracao=excluded.requer_refrigeracao, estoque_minimo=excluded.estoque_minimo",
                (codigo, nome, unidade, int(requer_refrigeracao), estoque_minimo))

    def item(self, codigo: str) -> Optional[dict]:
        r = self._q("SELECT * FROM itens WHERE codigo=?", (codigo,))
        return dict(r[0]) if r else None

    def itens(self) -> List[dict]:
        return [dict(r) for r in self._q("SELECT * FROM itens ORDER BY nome")]

    def alocar(self, compartimento: str, item: str) -> None:
        """RF10/RF12: define que `item` fica em `compartimento`."""
        it = self.item(item)
        comp = self._q("SELECT * FROM compartimentos WHERE id=?", (compartimento,))
        if not it or not comp:
            raise ErroRegra("item ou compartimento inexistente")
        if it["requer_refrigeracao"] and not comp[0]["climatizado"]:
            raise ErroRegra(f"'{it['nome']}' requer refrigeração e '{comp[0]['nome']}' não é climatizado (RF12)")
        self._x("INSERT OR IGNORE INTO estoque(compartimento,item,quantidade) VALUES (?,?,0)", (compartimento, item))

    def desalocar(self, compartimento: str, item: str) -> None:
        r = self._q("SELECT quantidade FROM estoque WHERE compartimento=? AND item=?", (compartimento, item))
        if r and r[0][0] > 0:
            raise ErroRegra("compartimento ainda tem saldo deste item; registre a retirada/ajuste antes")
        self._x("DELETE FROM estoque WHERE compartimento=? AND item=?", (compartimento, item))

    def estoque(self) -> List[dict]:
        return [dict(r) for r in self._q(
            "SELECT e.compartimento, c.nome AS compartimento_nome, c.climatizado, e.item, i.nome AS item_nome, "
            "i.unidade, e.quantidade, i.estoque_minimo, i.requer_refrigeracao "
            "FROM estoque e JOIN itens i ON i.codigo=e.item JOIN compartimentos c ON c.id=e.compartimento "
            "ORDER BY c.ordem, c.id, i.nome")]

    def saldo_item(self, item: str) -> int:
        r = self._q("SELECT COALESCE(SUM(quantidade),0) FROM estoque WHERE item=?", (item,))
        return int(r[0][0])

    def localizar(self, item: str) -> List[dict]:
        return [dict(r) for r in self._q(
            "SELECT e.compartimento, c.nome, e.quantidade FROM estoque e JOIN compartimentos c ON c.id=e.compartimento "
            "WHERE e.item=? ORDER BY e.quantidade DESC", (item,))]

    def movimentar(self, tipo: str, item: str, compartimento: str, quantidade: int, usuario_id: Optional[int],
                   paciente_ref: Optional[str] = None, prescricao_id: Optional[str] = None,
                   sessao_id: Optional[str] = None) -> int:
        """Lança movimento e atualiza saldo na MESMA transação. Retorna saldo após."""
        if quantidade <= 0 and tipo != "ajuste":
            raise ErroRegra("quantidade deve ser positiva")
        sinal = -1 if tipo == "retirada" else 1
        with self.transacao():
            r = self.con.execute("SELECT quantidade FROM estoque WHERE compartimento=? AND item=?",
                                 (compartimento, item)).fetchone()
            if r is None:
                raise ErroRegra(f"item {item} não está alocado no compartimento {compartimento}")
            novo = quantidade if tipo == "ajuste" else r[0] + sinal * quantidade
            if novo < 0:
                raise ErroRegra(f"saldo insuficiente de {item} em {compartimento} ({r[0]})")
            self.con.execute("UPDATE estoque SET quantidade=? WHERE compartimento=? AND item=?", (novo, compartimento, item))
            self.con.execute("INSERT INTO movimentos(ts,tipo,usuario_id,item,compartimento,quantidade,saldo_apos,"
                             "paciente_ref,prescricao_id,sessao_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
                             (time.time(), tipo, usuario_id, item, compartimento, quantidade, novo,
                              paciente_ref, prescricao_id, sessao_id))
        return novo

    def movimentos(self, desde: float = 0, ate: float = 9e12, usuario_id: Optional[int] = None,
                   item: Optional[str] = None, tipo: Optional[str] = None, limite: int = 1000) -> List[dict]:
        sql = ("SELECT m.*, u.nome AS usuario_nome, i.nome AS item_nome FROM movimentos m "
               "LEFT JOIN usuarios u ON u.id=m.usuario_id LEFT JOIN itens i ON i.codigo=m.item "
               "WHERE m.ts BETWEEN ? AND ?")
        args: list = [desde, ate]
        for campo, val in (("m.usuario_id", usuario_id), ("m.item", item), ("m.tipo", tipo)):
            if val is not None:
                sql += f" AND {campo}=?"
                args.append(val)
        sql += " ORDER BY m.id DESC LIMIT ?"
        args.append(limite)
        return [dict(r) for r in self._q(sql, args)]

    def itens_abaixo_minimo(self) -> List[dict]:
        return [dict(r) for r in self._q(
            "SELECT i.codigo, i.nome, i.estoque_minimo, COALESCE(SUM(e.quantidade),0) AS saldo "
            "FROM itens i LEFT JOIN estoque e ON e.item=i.codigo GROUP BY i.codigo "
            "HAVING saldo <= i.estoque_minimo AND i.estoque_minimo > 0 ORDER BY i.nome")]

    # ------------------------------------------------------- notificações (RF13)
    def notificar(self, tipo: str, mensagem: str, item: Optional[str] = None) -> Optional[int]:
        # evita duplicar notificação não lida igual
        r = self._q("SELECT id FROM notificacoes WHERE tipo=? AND COALESCE(item,'')=COALESCE(?, '') AND lida=0",
                    (tipo, item))
        if r:
            return None
        return self._x("INSERT INTO notificacoes(ts,tipo,mensagem,item) VALUES (?,?,?,?)",
                       (time.time(), tipo, mensagem, item)).lastrowid

    def notificacoes(self, apenas_nao_lidas: bool = True) -> List[dict]:
        sql = "SELECT * FROM notificacoes" + (" WHERE lida=0" if apenas_nao_lidas else "") + " ORDER BY id DESC LIMIT 200"
        return [dict(r) for r in self._q(sql)]

    def marcar_lida(self, nid: int) -> None:
        self._x("UPDATE notificacoes SET lida=1 WHERE id=?", (nid,))

    # ------------------------------------------------------- temperaturas
    def registrar_temperatura(self, frio, quente, ambiente, duty) -> None:
        self._x("INSERT INTO temperaturas(ts,frio,quente,ambiente,duty) VALUES (?,?,?,?,?)",
                (time.time(), frio, quente, ambiente, duty))

    def temperaturas(self, desde: float) -> List[dict]:
        return [dict(r) for r in self._q("SELECT * FROM temperaturas WHERE ts>=? ORDER BY ts", (desde,))]

    # ------------------------------------------------ journal da sessão (RNF07.1)
    def salvar_sessao(self, dados: Optional[dict]) -> None:
        if dados is None:
            self._x("DELETE FROM sessao_ativa WHERE id=1")
        else:
            self._x("INSERT INTO sessao_ativa(id,dados,atualizado) VALUES (1,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET dados=excluded.dados, atualizado=excluded.atualizado",
                    (_canon(dados), time.time()))

    def sessao_pendente(self) -> Optional[dict]:
        r = self._q("SELECT dados FROM sessao_ativa WHERE id=1")
        return json.loads(r[0][0]) if r else None

    # ----------------------------------------------------- outbox MV (RF04)
    def enfileirar_mv(self, payload: dict) -> int:
        return self._x("INSERT INTO outbox_mv(ts,payload) VALUES (?,?)", (time.time(), _canon(payload))).lastrowid

    def pendentes_mv(self, limite: int = 20) -> List[dict]:
        out = []
        for r in self._q("SELECT * FROM outbox_mv WHERE enviado IS NULL ORDER BY id LIMIT ?", (limite,)):
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out

    def marcar_mv(self, oid: int, ok: bool) -> None:
        if ok:
            self._x("UPDATE outbox_mv SET enviado=? WHERE id=?", (time.time(), oid))
        else:
            self._x("UPDATE outbox_mv SET tentativas=tentativas+1 WHERE id=?", (oid,))
