"""O gerador do armário roda, reproduz os DXFs já cortados e não mexe no
LEIA_PRIMEIRO.md escrito à mão."""
import filecmp
import os

import ezdxf
import shutil
import subprocess
import sys

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ARMARIO = os.path.join(RAIZ, "armario")
DXFS = ["corte/CHAPA_22.dxf", "corte/CHAPA_23.dxf", "gravacao/CHAPA_22_NOMES.dxf",
        "gravacao/CHAPA_23_NOMES.dxf", "00_TESTES_CORTE.dxf", "00_TESTES_NOMES.dxf"]


def assinatura(caminho):
    """Entidades do DXF (tipo, camada, cor, geometria arredondada), sem o
    cabeçalho, que muda a cada execução (data e identificadores)."""
    doc = ezdxf.readfile(caminho)
    out = []
    for e in doc.modelspace():
        t = e.dxftype()
        if t == "LWPOLYLINE":
            g = (tuple((round(x, 3), round(y, 3)) for x, y, *_ in e.get_points()), e.closed)
        elif t == "LINE":
            g = (tuple(round(v, 3) for v in e.dxf.start), tuple(round(v, 3) for v in e.dxf.end))
        elif t == "CIRCLE":
            g = (tuple(round(v, 3) for v in e.dxf.center), round(e.dxf.radius, 3))
        elif t == "TEXT":
            g = (e.dxf.text, tuple(round(v, 2) for v in e.dxf.insert))
        else:
            g = t
        out.append(repr((t, e.dxf.layer, e.dxf.get("color"), g)))
    return sorted(out), doc.header.get("$INSUNITS")


def test_gerador_reproduz_dxfs_e_preserva_leia_primeiro(tmp_path):
    copia = tmp_path / "armario"
    shutil.copytree(ARMARIO, copia, ignore=shutil.ignore_patterns("__pycache__"))
    env = dict(os.environ, MPLBACKEND="Agg")
    r = subprocess.run([sys.executable, "main.py"], cwd=copia / "gerador", env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert filecmp.cmp(copia / "LEIA_PRIMEIRO.md", os.path.join(ARMARIO, "LEIA_PRIMEIRO.md"), shallow=False)
    for f in DXFS:
        assert assinatura(copia / f) == assinatura(os.path.join(ARMARIO, f)), f
