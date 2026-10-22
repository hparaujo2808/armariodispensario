"""Gera o pacote completo do armário v2 em ../ (ao lado deste script)."""
from __future__ import annotations

import json
import os

import config as c
import montagem as M
import nesting as N
import exportar as E
import relatorios as R
import posicoes as POS

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def main():
    itens = M.montar_pecas()
    itens_cupom = [i for i in itens if i.grupo == "cupom"]
    itens_moveis = [i for i in itens if i.grupo != "cupom"]

    a_cortar = N.descontar_ja_cortadas(itens_moveis, M.resolver_ja_cortadas(itens))
    colocados = N.empacotar(a_cortar, primeira_chapa=c.PRIMEIRA_CHAPA)
    problemas = N.validar_sem_sobreposicao(colocados)
    if problemas:
        raise SystemExit("Validação de nesting falhou:\n" + "\n".join(problemas))
    n_chapas = N.n_chapas(colocados)

    colocados_cupom = N.empacotar(itens_cupom)
    problemas_cupom = N.validar_sem_sobreposicao(colocados_cupom)
    if problemas_cupom:
        raise SystemExit("Validação do cupom de teste falhou:\n" + "\n".join(problemas_cupom))

    # -- DXFs -------------------------------------------------------------
    pasta_corte = os.path.join(RAIZ, "corte")
    pasta_grav = os.path.join(RAIZ, "gravacao")
    E.gerar_dxfs(colocados, pasta_corte, pasta_grav)

    # cupom de teste vira 00_TESTES_CORTE.dxf / 00_TESTES_NOMES.dxf na raiz
    tmp_cupom_corte = os.path.join(RAIZ, "_tmp_cupom_corte")
    tmp_cupom_grav = os.path.join(RAIZ, "_tmp_cupom_grav")
    E.gerar_dxfs(colocados_cupom, tmp_cupom_corte, tmp_cupom_grav)
    os.replace(os.path.join(tmp_cupom_corte, "CHAPA_01.dxf"), os.path.join(RAIZ, "00_TESTES_CORTE.dxf"))
    os.replace(os.path.join(tmp_cupom_grav, "CHAPA_01_NOMES.dxf"), os.path.join(RAIZ, "00_TESTES_NOMES.dxf"))
    os.rmdir(tmp_cupom_corte)
    os.rmdir(tmp_cupom_grav)

    # -- mapas PNG -------------------------------------------------------------
    pasta_mapas = os.path.join(RAIZ, "mapas")
    E.gerar_mapas(colocados, pasta_mapas)

    # -- relatórios -------------------------------------------------------------
    R.gerar_lista_pecas(itens, os.path.join(RAIZ, "LISTA_PECAS.csv"))
    R.gerar_validacao(itens, colocados, n_chapas, os.path.join(RAIZ, "VALIDACAO.json"))

    with open(os.path.join(RAIZ, "MONTAGEM_REFORCOS.md"), "w", encoding="utf-8") as f:
        f.write(POS.montagem_markdown())
    with open(os.path.join(RAIZ, "POSICOES_MONTAGEM.json"), "w", encoding="utf-8") as f:
        json.dump({"nervuras": POS.nervuras_posicao()}, f, indent=2, ensure_ascii=False)

    n_pecas = sum(i.quantidade for i in itens)
    # O LEIA_PRIMEIRO.md é escrito à mão desde a v2.3: o gerador não mexe nele
    # (o modelo em relatorios.py ainda é o texto da v2.1).

    # SHA256 por último, depois que todo o resto já foi escrito — só cobre a saída
    R.gerar_sha256(
        RAIZ, os.path.join(RAIZ, "SHA256.json"),
        subpastas=["corte", "gravacao", "mapas"],
        arquivos=[
            "00_TESTES_CORTE.dxf", "00_TESTES_NOMES.dxf", "LISTA_PECAS.csv",
            "VALIDACAO.json", "MONTAGEM_REFORCOS.md", "POSICOES_MONTAGEM.json",
            "LEIA_PRIMEIRO.md",
        ],
    )

    print(f"OK: {n_pecas} peças no móvel; {sum(i.quantidade for i in a_cortar)} a cortar em "
          f"{n_chapas} chapas (CHAPA_{c.PRIMEIRA_CHAPA:02d} a CHAPA_{c.PRIMEIRA_CHAPA+n_chapas-1:02d}) "
          f"+ cupom de teste. Pacote em {RAIZ}")


if __name__ == "__main__":
    main()
