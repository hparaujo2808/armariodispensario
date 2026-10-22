"""Gravação das câmeras a cada abertura da porta (RF07).

Duas webcams USB no notebook: a externa (quem está na porta) e a interna (o que
sai das gavetas). Começa a gravar quando o Mega avisa PORTA_ABERTA (ou abertura
sem autorização) e para em PORTA_FECHADA. Cada arquivo sai com o SHA-256, que
vai para a auditoria: se alguém trocar o vídeo, o hash não bate.

Fontes:
  - número (0, 1...): webcam pelo OpenCV, vídeo MJPG .avi + uma foto .jpg no início
  - "sim": arquivo de teste (para os testes e a demonstração sem câmera)
"""
from __future__ import annotations

import hashlib
import logging
import os
import threading
import time
from typing import List, Optional

log = logging.getLogger(__name__)


def sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


class _Gravacao:
    """Uma câmera gravando num arquivo, numa thread própria."""

    def __init__(self, nome: str, fonte, prefixo: str, fps: int, max_s: float):
        self.nome, self.fonte, self.prefixo, self.fps, self.max_s = nome, fonte, prefixo, fps, max_s
        self.arquivos: List[str] = []
        self.erro: Optional[str] = None
        self._parar = threading.Event()
        self._t = threading.Thread(target=self._rodar, daemon=True, name=f"camera-{nome}")
        self._t.start()

    def _rodar(self) -> None:
        if self.fonte == "sim":
            caminho = f"{self.prefixo}_{self.nome}.txt"
            with open(caminho, "w", encoding="utf-8") as f:
                f.write(f"video simulado da camera {self.nome} iniciado em {time.time():.3f}\n")
            self._parar.wait(self.max_s)
            with open(caminho, "a", encoding="utf-8") as f:
                f.write(f"fim em {time.time():.3f}\n")
            self.arquivos.append(caminho)
            return
        try:
            import cv2
        except ImportError:
            self.erro = "OpenCV não instalado (pip install opencv-python)"
            return
        cap = cv2.VideoCapture(int(self.fonte))
        if not cap.isOpened():
            self.erro = f"câmera {self.nome} (índice {self.fonte}) não abriu"
            return
        ok, quadro = cap.read()
        if not ok:
            self.erro = f"câmera {self.nome} não entrega imagem"
            cap.release()
            return
        foto = f"{self.prefixo}_{self.nome}.jpg"
        cv2.imwrite(foto, quadro)
        self.arquivos.append(foto)
        h, w = quadro.shape[:2]
        video = f"{self.prefixo}_{self.nome}.avi"
        out = cv2.VideoWriter(video, cv2.VideoWriter_fourcc(*"MJPG"), self.fps, (w, h))
        inicio = time.time()
        intervalo = 1.0 / self.fps
        while not self._parar.is_set() and time.time() - inicio < self.max_s:
            ok, quadro = cap.read()
            if ok:
                out.write(quadro)
            self._parar.wait(intervalo)
        out.release()
        cap.release()
        self.arquivos.append(video)

    def parar(self) -> None:
        self._parar.set()
        self._t.join(timeout=5)


class Cameras:
    def __init__(self, fontes: List[dict], pasta: str, fps: int = 10, max_s: float = 300.0):
        self.fontes = [f for f in fontes if f.get("fonte", "") != ""]
        self.pasta = pasta
        self.fps, self.max_s = fps, max_s
        self._atual: List[_Gravacao] = []

    @property
    def gravando(self) -> bool:
        return bool(self._atual)

    def iniciar(self, prefixo: str) -> None:
        if self._atual:
            return
        os.makedirs(os.path.dirname(prefixo), exist_ok=True)
        self._atual = [_Gravacao(f["nome"], f["fonte"], prefixo, self.fps, self.max_s) for f in self.fontes]

    def parar(self, base: str) -> tuple:
        """Para tudo e devolve (mídia [{arquivo, sha256, camera}], erros)."""
        midia, erros = [], []
        for g in self._atual:
            g.parar()
            if g.erro:
                erros.append(g.erro)
            for a in g.arquivos:
                midia.append({"camera": g.nome, "arquivo": os.path.relpath(a, base), "sha256": sha256_arquivo(a)})
        self._atual = []
        return midia, erros
