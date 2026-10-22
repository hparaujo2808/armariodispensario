"""Firmware: testes da lógica compilados e rodados no PC, e compilação para o
Mega com arduino-cli (pulada se o arduino-cli não estiver instalado)."""
import os
import re
import shutil
import subprocess

import pytest

RAIZ = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
FW = os.path.join(RAIZ, "firmware")
LOGICA = os.path.join(FW, "armario_dispensador", "src", "logica")


def test_logica_no_pc(tmp_path):
    cxx = shutil.which("c++") or shutil.which("g++") or shutil.which("clang++")
    if not cxx:
        pytest.skip("sem compilador C++")
    fontes = [os.path.join(LOGICA, f) for f in sorted(os.listdir(LOGICA)) if f.endswith(".cpp")]
    exe = tmp_path / "teste"
    r = subprocess.run([cxx, "-std=c++17", "-Wall", "-Wextra", "-Werror", "-I", LOGICA, *fontes,
                        os.path.join(FW, "testes", "teste_logica.cpp"), "-o", str(exe)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    print(r.stdout)
    assert r.returncode == 0, r.stdout
    assert "0 falha(s)" in r.stdout


def test_compila_para_o_mega(tmp_path):
    cli = shutil.which("arduino-cli")
    if not cli:
        pytest.skip("arduino-cli não instalado")
    r = subprocess.run([cli, "compile", "--fqbn", "arduino:avr:mega", "--warnings", "default", "--build-path",
                        str(tmp_path), os.path.join(FW, "armario_dispensador")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    flash = int(re.search(r"uses (\d+) bytes \((\d+)%\) of program", r.stdout).group(2))
    ram = int(re.search(r"use (\d+) bytes \((\d+)%\) of dynamic", r.stdout).group(2))
    print(r.stdout)
    assert flash < 80 and ram < 75
