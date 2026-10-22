"""Gerador da porta (v2.4): roda, valida e não mexe no que já foi cortado."""
import filecmp
import os
import re
import shutil
import subprocess
import sys

import ezdxf
import pytest

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ARMARIO = os.path.join(RAIZ, "armario")


def _copia(tmp_path):
    shutil.copytree(ARMARIO, tmp_path / "armario", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(os.path.join(RAIZ, "hardware"), tmp_path / "hardware", ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path / "armario"


def _rodar(copia):
    env = dict(os.environ, MPLBACKEND="Agg")
    return subprocess.run([sys.executable, "porta_main.py"], cwd=copia / "gerador", env=env, capture_output=True, text=True)


@pytest.fixture(scope="module")
def gerado(tmp_path_factory):
    copia = _copia(tmp_path_factory.mktemp("porta"))
    r = _rodar(copia)
    assert r.returncode == 0, r.stdout + r.stderr
    return copia


def test_dxfs_para_a_maquina(gerado):
    arquivos = sorted((gerado / "corte").glob("CHAPA_2[4-9].dxf")) + [gerado / "00_CUPOM_PORTA_CORTE.dxf"]
    assert len(arquivos) >= 2
    for a in arquivos:
        doc = ezdxf.readfile(a)
        assert doc.header["$INSUNITS"] == 4
        for e in doc.modelspace():
            assert e.dxftype() == "LWPOLYLINE" and e.closed and e.dxf.color == 1, a.name
            for x, y, *_ in e.get_points():
                assert 10 - 1e-6 <= x <= 890 + 1e-6 and 10 - 1e-6 <= y <= 890 + 1e-6, a.name
        if a.name.startswith("00_"):
            nomes = a.with_name(a.name.replace("CORTE", "NOMES"))
        else:
            nomes = gerado / "gravacao" / a.name.replace(".dxf", "_NOMES.dxf")
        grav = ezdxf.readfile(nomes)
        assert all(e.dxf.color == 5 for e in grav.modelspace())


def test_nao_mexe_no_que_ja_foi_cortado(gerado):
    for f in ("LEIA_PRIMEIRO.md", "corte/CHAPA_22.dxf", "corte/CHAPA_23.dxf"):
        assert filecmp.cmp(gerado / f, os.path.join(ARMARIO, f), shallow=False), f


def test_validacao_e_manual(gerado):
    import json
    v = json.loads((gerado / "VALIDACAO_PORTA.json").read_text(encoding="utf-8"))
    assert v["colisoes_0_a_90_graus"] == 0
    assert v["folga_porta_gavetas_mm"] >= 5
    assert v["pecas_cupom"] > 0
    manual = (gerado / "MANUAL_PORTA.md").read_text(encoding="utf-8")
    assert "LIBERAÇÃO" in manual.upper() and "cupom" in manual.lower()


def test_recusa_folga_pequena(tmp_path):
    copia = _copia(tmp_path)
    cfg = copia / "gerador" / "config.py"
    cfg.write_text(re.sub(r"^FRENTE_GAVETA_Y = .*$", "FRENTE_GAVETA_Y = -6.0", cfg.read_text(encoding="utf-8"),
                          flags=re.M), encoding="utf-8")
    r = _rodar(copia)
    assert r.returncode != 0 and "folga porta" in (r.stdout + r.stderr)


def test_repositorio_atualizado(gerado):
    """Os DXFs e o manual commitados batem com o que o gerador produz hoje."""
    for f in ("MANUAL_PORTA.md", "VALIDACAO_PORTA.json"):
        assert (gerado / f).read_text(encoding="utf-8") == open(os.path.join(ARMARIO, f), encoding="utf-8").read(), \
            f"{f} desatualizado: rode python porta_main.py em armario/gerador"
