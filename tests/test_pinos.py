"""O mapa de pinos e a fiação de potência existem em um só lugar
(hardware/pinos.yaml e hardware/potencia.yaml). Estes testes falham se o
pinos.h, o LIGACOES.md ou os diagramas ficarem diferentes do que o
hardware/gerar.py produz, ou se os YAML tiverem erro elétrico."""
import os
import sys

import pytest

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "hardware"))
import furos  # noqa: E402
import gerar  # noqa: E402


@pytest.mark.parametrize("caminho", [gerar.PINOS_H, gerar.LIGACOES, gerar.SVG_SINAIS, gerar.SVG_POTENCIA])
def test_saida_gerada_bate_com_o_yaml(caminho):
    esperado = gerar.saidas()[caminho]
    with open(caminho, encoding="utf-8") as f:
        assert f.read() == esperado, f"{os.path.relpath(caminho, RAIZ)} desatualizado: rode python hardware/gerar.py"


def test_yaml_sem_erros():
    pinos, potencia = gerar.carregar()
    assert gerar.validar(pinos, potencia) == []


def test_furos_sem_conflito():
    assert furos.conferir() == []


def test_validacao_pega_erro():
    pinos, potencia = gerar.carregar()
    pinos["pinos"][0]["pino"] = 13                       # reservado
    pinos["pinos"][1]["pino"] = pinos["pinos"][2]["pino"]  # repetido
    potencia["trechos"][2]["corrente_a"] = 50            # acima do fio
    erros = " | ".join(gerar.validar(pinos, potencia))
    assert "reservado" in erros and "usado por" in erros and "mm²" in erros


def test_reles_iniciam_desligados():
    h = open(gerar.PINOS_H, encoding="utf-8").read()
    pinos, _ = gerar.carregar()
    saidas = [p for p in pinos["pinos"] if p["modo"] == "saida"]
    for p in saidas:
        if p["nome"].startswith("RELE"):
            assert p["ativo"] == "baixo"
    assert "SAIDAS_INATIVO" in h and h.count("HIGH") >= 4


def test_mega_nao_usa_vin():
    texto = open(gerar.LIGACOES, encoding="utf-8").read()
    assert "Vin fica sem nada" in texto
    pinos, _ = gerar.carregar()
    assert all("Vin" not in str(a) for a in pinos["alimentacao_mega"])
