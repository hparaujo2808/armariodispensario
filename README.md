# Armário Dispensador

Protótipo de dispensário eletrônico de medicamentos e insumos, do Projeto Aplicado do IBMEC-BH (Gustavo, Henrique, Júlia, Miguel e Pedro), feito para a rede Mario Penna. É um armário de MDF com gaveteiro e uma baia refrigerada. A porta só abre depois da autenticação na porta e da conferência da prescrição do paciente. Cada abertura fica registrada, com quem abriu, quando, o que saiu e o vídeo das duas câmeras.

Escopo: `Dispensários Eletrônicos.docx` (Fase 1, RF01–RF13 e RNF01–RNF14). A revisão completa do projeto está em [docs/AUDITORIA.md](docs/AUDITORIA.md) (a seção 10 traz a revisão independente de 23/10 e o que ficou em aberto) e as decisões, em [docs/DECISOES.md](docs/DECISOES.md).

## Como funciona

1. **Na porta:** a enfermeira põe o dedo no leitor, ou digita o ID + `#` e a senha + `#` no teclado. O LCD mostra cada passo. Depois de 3 erros, o teclado bloqueia por 30 s.
2. **No notebook** (fazendo o papel do monitor touch): ela digita o CPF ou o código da receita. O sistema consulta o MV e mostra os itens e a gaveta de cada um.
3. Ela confere e toca em **Liberar porta**. A trava solta por no máximo 3 s.
4. Com a porta aberta, as **duas câmeras gravam**: a externa, no tampo, mostra quem está na porta; a interna mostra as gavetas. Se a porta ficar aberta mais de 30 s, toca um alarme de volume baixo.
5. Ela fecha a porta (a lingueta tranca sozinha) e **confirma as quantidades** que tirou. Isso é a dupla confirmação: os itens são conferidos antes de abrir e depois de fechar.
6. O sistema baixa o estoque e avisa a logística se algum item chegar ao mínimo. Também grava a auditoria, que não pode ser alterada, com o vídeo e o hash de cada arquivo, e informa o MV.

**Baia fria:** fica no lugar das gavetas A3 e A4, com duas Peltier, isopor de 50 mm e controle automático com setpoint de 5 °C (faixa de 2 a 8 °C).

**Se o notebook cair:** o Arduino continua funcionando sozinho e guarda os eventos para mandar depois. Nesse modo a porta abre só com a digital ou a senha, sem CPF nem vídeo. A farmácia decide se aceita (`modo_autonomo` na configuração do app).

## Arquitetura

| Parte | O que faz | Onde |
|---|---|---|
| Arduino Mega 2560 | Porta e segurança física: teclado, LCD, leitor de digital AS608, trava, sensor de porta, 3 DS18B20, controle da baia fria, buzzer, watchdog, fila de eventos na EEPROM | [firmware/](firmware/LEIA_ME.md) |
| Notebook | Quiosque (CPF), MV simulado, auditoria em SQLite, gravação das câmeras, painel da farmácia e da logística | [app/](app/) |
| Armário | MDF 3 mm, 880 × 880 × 700 mm (V2.3), porta-caixão de 30 mm, baia fria, berços dos coolers, caixa da eletrônica no tampo | [armario/](armario/MANUAL_PORTA.md) |
| Eletrônica | Fonte 12 V 10 A, fusíveis, relés, 2 × TEC1-12703 com cooler por fora da lateral esquerda, fiação sem solda | [docs/LIGACOES.md](docs/LIGACOES.md) |

**Fontes únicas:**
- pinos: `hardware/pinos.yaml`;
- fiação de potência: `hardware/potencia.yaml`;
- posições: `hardware/layout.py`;
- medidas do armário: `armario/gerador/config.py`.

O `pinos.h` do firmware, as tabelas do LIGACOES.md, os diagramas, os furos, a simulação do Wokwi e a simulação 3D são **gerados** desses arquivos, e um teste falha se algum deles ficar diferente.

## Por onde começar

| Quero… | Arquivo |
|---|---|
| Comprar o que falta | [LISTA-DE-COMPRAS.md](LISTA-DE-COMPRAS.md) |
| Cortar a porta e as peças novas | [armario/MANUAL_PORTA.md](armario/MANUAL_PORTA.md) — **primeiro o cupom de teste** |
| Ligar os fios | [docs/LIGACOES.md](docs/LIGACOES.md) |
| Ligar na tomada pela primeira vez | [docs/SEGURANCA.md](docs/SEGURANCA.md) e depois [docs/TESTES_DE_BANCADA.md](docs/TESTES_DE_BANCADA.md) |
| Gravar o Arduino | [firmware/LEIA_ME.md](firmware/LEIA_ME.md) |
| Ver o armário em 3D | [docs/simulacao.html](docs/simulacao.html) (abrir no navegador) |

## Como rodar o app do notebook

Precisa de Python 3.10 ou mais novo, no Windows ou no macOS. Na pasta do repositório:

```bash
python -m venv .venv
```

No macOS, ative o ambiente com `source .venv/bin/activate`; no Windows, com `.venv\Scripts\activate`. Depois:

```bash
pip install -r requirements.txt
```

**Sem o armário** (Arduino e câmeras simulados). Esta é a demonstração que roda em qualquer notebook:

```bash
python -m app --sim
```

**Com o armário** (Arduino na USB, webcams 0 e 1):

```bash
python -m app
```

O navegador abre o quiosque (`http://127.0.0.1:8080/`) e o painel (`http://127.0.0.1:8080/painel`). O MV simulado sobe junto, na porta 8090.

### Usuários de demonstração (trocar antes de mostrar a alguém de fora)

| Quem | Na porta (ID + senha) | No painel |
|---|---|---|
| Ana Enfermeira (enfermagem) | 1 + 1357 | — |
| Lucas Logística | 2 + 2468 | 2001 / logistica2026 |
| Fernanda Farmácia | 3 + 3579 | 3001 / farmacia2026 |
| Administrador | — | admin / admin2026 |

CPFs de teste do MV simulado (fictícios): `11122233344`, `55566677788` e a receita `RX000103`.

## Testes

```bash
pytest -q
```

Em 23/10/2026: **43 testes passando**. Eles cobrem:
- os 32 testes da lógica do firmware, rodados no PC, e a compilação para o Mega (12% da flash, 26% da RAM);
- o app com o Mega simulado (fluxo da banca, auditoria, LGPD, recuperação, API);
- os geradores do armário e da porta, com checagem de colisão e de folgas;
- o mapa de pinos, a fiação e os furos;
- a simulação 3D.

## Roteiro da banca

1. Mostrar o armário fechado e a simulação 3D (`docs/simulacao.html`).
2. Na porta, errar a senha 3 vezes: o teclado bloqueia (RNF03).
3. Autenticar com a digital (RF01) ou com o ID e a senha (RF02).
4. No notebook, digitar o CPF `11122233344`. Os itens vêm do MV (RF03, RF04) e a insulina aparece na baia fria (RF12).
5. Liberar, abrir, retirar e fechar. Mostrar o clipe gravado (RF07) e o registro com usuário e horário (RF05).
6. Confirmar uma quantidade diferente da prescrita: aparece a divergência na auditoria (dupla confirmação).
7. Deixar a porta aberta 30 s: alarme de volume baixo (RF09, RNF10).
8. No painel:
   - estoque e alerta de mínimo (RF08, RF13);
   - temperatura da baia (RNF08);
   - auditoria com a verificação de integridade (RNF04);
   - CPF guardado só mascarado (RNF05).
9. Tirar a fonte da tomada por 15 s no meio de uma retirada: nada se perde (RNF07.1).
10. Abrir a porta pela liberação de emergência: soltar os 2 parafusos na cava do puxador.

## O que está fora do escopo, e por quê

- **Dispensação automática item a item:** fora da Fase 1 pelo escopo. O dispensador por gravidade da baia da direita é só uma rampa passiva, sem sensor nem motor.
- **Integração com o MV real:** o hospital ainda não liberou a API. O app usa um MV simulado com o mesmo contrato (`app/mv_client.py`); para trocar pelo real, muda só esse arquivo.
- **Monitor touch dedicado:** a tela do notebook faz esse papel na demonstração.
- **Fixação na parede (RNF14):** para a banca, a base fica presa na mesa com grampos. A fixação na parede está descrita no manual da porta.

## Situação de cada parte (23/10/2026)

| Parte | Situação |
|---|---|
| Auditoria do material antigo | Pronta ([docs/AUDITORIA.md](docs/AUDITORIA.md)) |
| Arquitetura e refrigeração | Decididas ([docs/DECISOES.md](docs/DECISOES.md)) |
| Lista de compras | Pronta, com links de 22/10. Falta comprar |
| Fiação, testes de bancada e segurança | Prontos no papel. **Nada medido ainda** |
| Porta e peças novas | DXFs prontos. **Cortar primeiro o cupom de teste** e ajustar as medidas reais |
| Firmware | Compila e passa nos testes no PC. **Não testado na placa** |
| Simulação Wokwi | Diagrama pronto. Não rodou (o Wokwi pede conta) |
| App do notebook | Fluxo completo testado no navegador com o Mega simulado. **Não testado com o Mega e as webcams de verdade** |
| Montagem no armário | Não começou |

Números que ainda dependem da bancada: corrente da trava, resistência térmica dos coolers, temperatura real da baia, medidas da trava e do reed, posição real das frentes das gavetas.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `app/` | App do notebook (Python, FastAPI) |
| `firmware/` | Firmware do Mega e testes da lógica |
| `hardware/` | Fontes únicas de pinos, potência, posições e furos, e o gerador |
| `armario/` | Gerador do armário (V2.3 + porta v2.4), DXFs, mapas e manual |
| `calculos/` | Contas térmicas e de montagem |
| `docs/` | Auditoria, decisões, ligações, testes, segurança, simulação 3D |
| `simulacao/` | Diagrama do Wokwi |
| `tests/` | `pytest` de tudo |
| `legado/` | Versões abandonadas, com o motivo em `LEIA_ME.md` |
