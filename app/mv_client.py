"""Integração com o sistema de gestão hospitalar MV/RMV (RF03, RF04, RNF11).

A API real do MV não foi disponibilizada ainda (Premissa 1 / Ponto a validar 3).
Por isso a integração é um ADAPTADOR com contrato mínimo e documentado:

  GET  {mv_url}/prescricoes?identificador=<cpf|codigo_receita>
       -> {"prescricao_id", "paciente": {"nome", "leito"}, "itens": [{"codigo","descricao","quantidade","posologia"}]}
  POST {mv_url}/dispensacoes   (corpo = registro de retirada; idempotente por "sessao_id")

Quando o contrato real for conhecido, só esta classe muda (RNF11: o MV não é alterado).
As confirmações de retirada vão para a fila `outbox_mv` e são reenviadas até o
MV confirmar (funciona com a rede fora do ar).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

import httpx

log = logging.getLogger(__name__)


class ErroMV(Exception):
    pass


@dataclass
class ItemPrescrito:
    codigo: str
    descricao: str
    quantidade: int
    posologia: str = ""


@dataclass
class Prescricao:
    prescricao_id: str
    paciente_nome: str
    leito: str
    itens: List[ItemPrescrito] = field(default_factory=list)


class ClienteMV:
    def __init__(self, url: str, token: str = "", timeout: float = 5.0, transporte: Optional[httpx.BaseTransport] = None):
        cab = {"Authorization": f"Bearer {token}"} if token else {}
        self.http = httpx.Client(base_url=url, headers=cab, timeout=timeout, transport=transporte)

    def consultar_prescricao(self, identificador: str) -> Optional[Prescricao]:
        try:
            r = self.http.get("/prescricoes", params={"identificador": identificador})
        except httpx.HTTPError as e:
            raise ErroMV(f"MV indisponível: {e}") from e
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise ErroMV(f"MV respondeu {r.status_code}")
        d = r.json()
        return Prescricao(
            prescricao_id=str(d["prescricao_id"]),
            paciente_nome=d["paciente"]["nome"],
            leito=d["paciente"].get("leito", ""),
            itens=[ItemPrescrito(str(i["codigo"]), i["descricao"], int(i["quantidade"]), i.get("posologia", ""))
                   for i in d["itens"]],
        )

    def informar_dispensacao(self, payload: dict) -> bool:
        try:
            r = self.http.post("/dispensacoes", json=payload)
            return r.status_code in (200, 201, 409)   # 409 = já recebida (idempotência)
        except httpx.HTTPError as e:
            log.warning("falha ao enviar dispensação ao MV: %s", e)
            return False
