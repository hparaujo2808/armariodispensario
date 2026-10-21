# Armário Dispensador

rogi: Protótipo de dispensário eletrônico para medicamentos, feito como projeto de faculdade. É um armário de MDF com gaveteiro, e a porta só abre com senha. A enfermeira digita o código no teclado da porta, acompanha no display o que está digitando, a tranca solta, ela pega o que precisa nas gavetas e a porta volta a trancar. Duas gavetas têm pastilhas de resfriamento para o que precisa ficar frio.

rogi: Tudo roda local num Arduino Mega, sem internet e sem servidor. A senha é uma constante no código, porque aqui o objetivo é provar o funcionamento, não guardar remédio de verdade.

## Como funciona

1. O LCD da porta mostra `Digite a senha`.
2. A enfermeira digita 4 dígitos. Cada dígito aparece como `*`. A tecla `*` apaga e a `#` confirma.
3. Senha certa: bipe curto, o LCD mostra `Acesso liberado` e a trava solenoide recolhe.
4. Senha errada: bipe longo e a contagem de erros sobe. No terceiro erro seguido o teclado trava por 30 s, com contagem regressiva no display.
5. Ela abre a porta, usa as gavetas e fecha. A lingueta da trava é chanfrada e tranca sozinha quando a porta encosta. A tecla `D` encerra a sessão (corta a trava se ainda estiver solta e bloqueia as teclas do frio). Sem tecla nenhuma por 60 s, a sessão encerra sozinha.
6. As pastilhas Peltier das duas gavetas frias ligam e desligam pelas teclas `A` (C1) e `B` (C2), só durante a sessão.

## Hardware

| Parte | Componente |
|---|---|
| Controle | Arduino Mega 2560 |
| Porta | LCD 16x1 em paralelo (sem I2C), teclado de membrana 4x4, buzzer |
| Tranca | Trava solenoide 12 V, acionada por relé |
| Frio | 2 pastilhas Peltier TEC1-12703 com dissipador de alumínio (sem cooler), acionadas por relé |
| Energia | Fonte chaveada 12 V 10 A + regulador 12 V → 5 V para os relés |

O que comprar, com quantidade e para que serve cada peça: [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md).

Simulação do armário pronto, com a porta, o pinpad, o LCD, a trava e as gavetas frias: abra `docs/simulacao.html` no navegador.

Como cada peça se liga, por onde passa cada fio e os furos para fazer antes da cola: [docs/LIGACOES.md](docs/LIGACOES.md).

![Diagrama de ligações](docs/diagrama-ligacoes.svg)

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `firmware/armario_dispensador/` | Código do Arduino (abre na Arduino IDE) |
| `simulacao/` | Circuito do [Wokwi](https://wokwi.com) para testar sem as peças |
| `docs/simulacao.html` | Demonstração 3D do funcionamento completo, com a porta proposta |
| `docs/LIGACOES.md` | Mapa de pinos, cabos, caminhos e furos |
| `docs/gerar_diagrama.py` | Gera `docs/diagrama-ligacoes.svg` |

## Situação

- [x] Decisões de hardware
- [x] Lista de compras
- [x] Mapa de pinos e esquema de ligação
- [ ] Código: senha, LCD, teclado, bloqueio
- [ ] Código: tranca e fechamento
- [ ] Código: liga e desliga das pastilhas
- [ ] Simulação no Wokwi
- [ ] Montagem no armário

Fora do escopo por enquanto: o dispensador por gravidade e a câmera do compartimento de cima.
