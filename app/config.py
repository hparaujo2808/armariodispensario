"""Configuração do app do notebook (arquivo JSON opcional + valores padrão)."""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import List, Optional


@dataclass
class Config:
    # identificação (hierarquia Central -> Satélite -> Dispensário)
    dispensario_id: str = "DISP-01"
    setor: str = "Clínica Médica - 3º andar"
    farmacia_satelite: str = "SAT-3"

    # pasta dos dados (banco, chave, vídeos). Relativa à pasta em que o app é iniciado.
    dados_dir: str = "dados"
    segredo_arquivo: str = ""        # vazio = <dados_dir>/segredo.key

    # Arduino Mega: "auto" procura na USB; "sim" usa o Mega simulado; ou o nome da porta (COM3, /dev/cu.usbmodem…)
    porta_serial: str = "auto"

    # câmeras (RF07): índice da webcam no OpenCV, "sim" (arquivo de teste) ou "" (nenhuma)
    cameras: List[dict] = field(default_factory=lambda: [{"nome": "externa", "fonte": 0}, {"nome": "interna", "fonte": 1}])
    video_fps: int = 10
    video_max_s: float = 300.0       # corta o clipe se a porta ficar aberta muito tempo

    # alarme da porta (RF09) e volume (RNF10) — enviados ao Mega
    alarme_porta_s: int = 30
    # Notebook fora do ar: o Mega libera só com a digital ou a senha (sem CPF nem vídeo).
    # Decisão da farmácia; com False, a porta só abre com o notebook funcionando.
    modo_autonomo: bool = True
    volume_dia: int = 40
    volume_noite: int = 10
    noite_inicio_h: int = 22
    noite_fim_h: int = 6

    # refrigeração (RF12, RNF08): faixa de alarme e setpoint mandado ao Mega
    setpoint_c: float = 5.0
    temp_min_c: float = 2.0
    temp_max_c: float = 8.0

    # sessão no quiosque
    sessao_inatividade_s: float = 90.0
    confirmacao_automatica_s: float = 180.0

    # senhas do painel
    max_tentativas_senha: int = 5
    bloqueio_s: int = 300

    # MV/RMV (RF03, RF04, RNF11). Vazio = sobe o MV simulado junto, na porta 8090
    mv_url: str = ""
    mv_token: str = ""
    mv_timeout_s: float = 5.0

    # retenção de mídia (LGPD, RNF05)
    midia_retencao_dias: int = 180

    # API (só nesta máquina)
    api_host: str = "127.0.0.1"
    api_porta: int = 8080

    @staticmethod
    def carregar(caminho: Optional[str] = None) -> "Config":
        cfg = Config()
        caminho = caminho or os.environ.get("DISPENSARIO_CONFIG", "config.json")
        if caminho and os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
            for k, v in dados.items():
                if not hasattr(cfg, k):
                    raise ValueError(f"opção de configuração desconhecida: {k}")
                setattr(cfg, k, v)
        return cfg

    @property
    def caminho_segredo(self) -> str:
        return self.segredo_arquivo or os.path.join(self.dados_dir, "segredo.key")

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("mv_token", None)
        return d
