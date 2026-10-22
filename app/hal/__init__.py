from .base import Mega


def criar_mega(cfg, relogio=None) -> Mega:
    """`porta_serial` = "sim" usa o Mega simulado; "auto" procura o Arduino na USB."""
    if cfg.porta_serial == "sim":
        from .mega_simulado import MegaSimulado
        return MegaSimulado(relogio) if relogio else MegaSimulado()
    from .serial_mega import MegaSerial
    return MegaSerial(cfg.porta_serial)


__all__ = ["Mega", "criar_mega"]
