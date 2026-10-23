"""Protocolo serial com o Arduino Mega (o mesmo de firmware/.../src/logica/protocolo.h).

Uma mensagem por linha:  $<CORPO>*<CRC-8 do corpo em 2 hex>\\n
CRC-8 com polinômio 0x07, valor inicial 0.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

# Eventos do Mega (enum class Ev em src/logica/tipos.h): nomes que chegam no campo t=
EVENTOS = {
    "BOOT", "AUTH_OK", "AUTH_FALHA", "BLOQUEIO", "LIBERADO", "PORTA_ABERTA", "PORTA_FECHADA", "PORTA_ABERTA_TEMPO",
    "ABERTURA_NAO_AUTORIZADA", "LIBERACAO_EXPIROU", "CANCELADO", "TEMP_ALARME", "TEMP_NORMAL", "SENSOR_FALHA",
    "CORTE_QUENTE", "ENERGIA_FALTA", "ENERGIA_VOLTA", "DIGITAL_CADASTRADA", "SENHA_ALTERADA", "RECUPERADO",
    "MODO_AUTONOMO", "FRIO_SEM_EFEITO",
}
METODOS = {0: "nenhum", 1: "digital", 2: "senha", 3: "notebook"}


def crc8(texto: str) -> int:
    c = 0
    for b in texto.encode("ascii"):
        c ^= b
        for _ in range(8):
            c = ((c << 1) ^ 0x07) & 0xFF if c & 0x80 else (c << 1) & 0xFF
    return c


def empacotar(corpo: str) -> bytes:
    return f"${corpo}*{crc8(corpo):02X}\n".encode("ascii")


def analisar(linha: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """Devolve (tipo, campos) ou None se a linha estiver malformada ou o CRC não bater."""
    linha = linha.strip()
    if not linha.startswith("$") or "*" not in linha:
        return None
    corpo, _, crc = linha[1:].rpartition("*")
    try:
        if int(crc[:2], 16) != crc8(corpo):
            return None
    except ValueError:
        return None
    partes = corpo.split()
    if not partes:
        return None
    campos = {}
    for p in partes[1:]:
        if "=" not in p:
            return None
        k, _, v = p.partition("=")
        campos[k] = v
    return partes[0], campos


def evento(campos: Dict[str, str]) -> dict:
    """Converte os campos de uma linha EV em dicionário com números."""
    return {"seq": int(campos["seq"]), "t": campos["t"], "u": int(campos.get("u", 0)), "v": int(campos.get("v", 0)),
            "ms": int(campos.get("ms", 0)), "b": int(campos.get("b", 0))}
