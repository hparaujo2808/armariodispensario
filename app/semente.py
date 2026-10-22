"""Carga inicial: compartimentos do armário (V2.3 + baia fria), itens de demonstração e usuários da banca.

Numeração das gavetas: 1 é a de baixo (docs/DECISOES.md). A3 e A4 viraram a baia fria.
A lista de itens é provisória: deve ser definida com a farmácia (Ponto a validar 1 do escopo).
"""
from __future__ import annotations

from typing import Optional

from .auth import gerar_hash
from .storage import Banco

COMPARTIMENTOS = [
    ("A1", "Gaveta A1 (coluna A, embaixo)", False), ("A2", "Gaveta A2 (coluna A)", False),
    ("BAIA_FRIA", "Baia fria (coluna A, em cima)", True),
    ("B1", "Gaveta B1 (embaixo)", False), ("B2", "Gaveta B2 (em cima)", False),
    ("C1", "Gaveta C1 (embaixo)", False), ("C2", "Gaveta C2 (em cima)", False),
    ("PRAT_BAIXO", "Prateleira acima das gavetas", False), ("PRAT_MEIO", "Prateleira do meio", False),
    ("PRAT_ALTO", "Prateleira de cima", False), ("DISPENSADOR", "Rampa de rolos (por gravidade)", False),
]

# codigo, nome, unidade, refrigerado, mínimo, compartimento, saldo inicial
ITENS = [
    ("INS-NPH", "Insulina NPH 100 UI/mL 10 mL", "fr", True, 2, "BAIA_FRIA", 6),
    ("INS-REG", "Insulina regular 100 UI/mL 10 mL", "fr", True, 2, "BAIA_FRIA", 4),
    ("SER-1ML", "Seringa de insulina 1 mL c/ agulha", "un", False, 20, "A1", 100),
    ("SER-10", "Seringa 10 mL", "un", False, 20, "A2", 80),
    ("SF-10", "Soro fisiológico 0,9% 10 mL", "amp", False, 20, "B1", 60),
    ("GAZ-10", "Compressa de gaze 7,5x7,5 (pct 10)", "pct", False, 10, "B2", 40),
    ("LUV-M", "Luva de procedimento M (cx 100)", "cx", False, 2, "C1", 6),
    ("CAT-22", "Cateter intravenoso 22G", "un", False, 10, "C2", 40),
    ("FRA-G", "Fralda geriátrica G", "un", False, 16, "PRAT_BAIXO", 48),
    ("FRA-M", "Fralda geriátrica M", "un", False, 16, "PRAT_MEIO", 48),
    ("ABS-G", "Absorvente geriátrico", "un", False, 10, "PRAT_ALTO", 30),
    ("ATA-10", "Atadura de crepe 10 cm", "rl", False, 5, "DISPENSADOR", 12),
]

# Usuários da demonstração. A senha da PORTA fica no Mega (só o hash); a do PAINEL fica aqui (scrypt).
# O usuário 1 do Mega já vem com a senha 1357 do firmware. Troquem tudo antes de usar com gente de fora.
USUARIOS_DEMO = [
    # matrícula, nome, perfil, senha do painel, número no Mega, senha da porta
    ("1001", "Ana Enfermeira", "enfermagem", None, 1, "1357"),
    ("2001", "Lucas Logística", "logistica", "logistica2026", 2, "2468"),
    ("3001", "Fernanda Farmácia", "farmacia", "farmacia2026", 3, "3579"),
]


def semear(db: Banco, senha_admin: str, mega=None, demo: bool = True) -> None:
    for ordem, (cid, nome, clim) in enumerate(COMPARTIMENTOS):
        db.salvar_compartimento(cid, nome, clim, ordem)
    if not db.usuario(matricula="admin"):
        db.criar_usuario("admin", "Administrador (TI)", "admin", gerar_hash(senha_admin))
    if not demo:
        return
    for cod, nome, un, refr, mn, comp, saldo in ITENS:
        db.salvar_item(cod, nome, un, refr, mn)
        db.alocar(comp, cod)
        atual = [e for e in db.estoque() if e["compartimento"] == comp and e["item"] == cod][0]["quantidade"]
        if atual == 0 and saldo:
            db.movimentar("reposicao", cod, comp, saldo, None)
    for mat, nome, perfil, senha, mega_id, senha_porta in USUARIOS_DEMO:
        if not db.usuario(matricula=mat):
            db.criar_usuario(mat, nome, perfil, gerar_hash(senha) if senha else None, mega_id=mega_id)
        if mega is not None and mega_id != 1:
            mega.definir_senha(mega_id, senha_porta)
    db.auditar("CARGA_INICIAL", {"compartimentos": len(COMPARTIMENTOS), "itens_demo": demo})


def senha_porta_demo(mega_id: int) -> Optional[str]:
    for _, _, _, _, m, s in USUARIOS_DEMO:
        if m == mega_id:
            return s
    return None
