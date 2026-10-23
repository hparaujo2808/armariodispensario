# Versões abandonadas

Arquivos que já valeram e foram substituídos. Ficam aqui para consulta. Não usar para montar nem para comprar.

| Arquivo | Até quando valeu | Por que foi abandonado |
|---|---|---|
| `LISTA-DE-COMPRAS-2026-10-21.md` | 21/10/2026 | Kit de 2 Peltier sem cooler, que esquenta a gaveta e passa do limite da pastilha (`docs/AUDITORIA.md`, item 1). Sem biometria, sensor de porta nem sensor de temperatura. Os itens desta lista **já foram comprados** e continuam sendo usados (veja a seção "Já temos" da lista nova) |
| `LIGACOES-2026-10-21.md`, `gerar_diagrama-2026-10-21.py`, `diagrama-ligacoes-2026-10-21.svg` | 21/10/2026 | Pinos escritos à mão no script, gavetas C1/C2 trocadas, rota dos cabos cruzando as nervuras, sem sensor de porta, sem biometria, Peltier sem cooler, Mega no Vin. Substituídos por `hardware/pinos.yaml`, `hardware/potencia.yaml`, `hardware/gerar.py` e o `docs/LIGACOES.md` novo |
| `vao_de_tras-2026-10-22.py` | 22/10/2026 | Coolers e eletrônica dentro do vão de trás, com 16 furos de 38 mm no traseiro. Não dá para montar se o traseiro já estiver colado (pior caso pedido pelo grupo em 22/10). Substituído por `calculos/coolers_externos.py` (coolers do lado de fora da lateral esquerda) |
| `simulacao-2026-10-21.html` | 22/10/2026 | Simulação 3D escrita à mão: Peltier sem cooler, teclas A/B para o frio, gavetas numeradas de cima para baixo, porta de 6 mm, câmera atrás de um furo na porta. Substituída por `docs/simulacao.html`, gerada por `docs/gerar_simulacao.py` |

Outras versões antigas (Raspberry Pi com placa própria, Pi com módulos, Pi com reconhecimento facial) estão em `referencias_externas/`, fora do git. O resumo delas está em `docs/AUDITORIA.md`, seção 1.
