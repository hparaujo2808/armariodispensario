# Armário dispensador — revisão v2.3

Situação: **todas as chapas da v2 (01 a 15) já foram cortadas**. As chapas
16 a 21 da v2 eram sobra de uma versão anterior e não entram no móvel. A
LAT_E e a LAT_D foram coladas e precisam ser refeitas.

## O que vai para a máquina

| Chapa | Peça |
|---|---|
| CHAPA_22 | LAT_E |
| CHAPA_23 | LAT_D |

São as mesmas laterais da v2, **sem os 4 rasgos de prateleira**: as
prateleiras da v2 não têm aba, então os rasgos só enfraqueceriam a lateral.
Corte antes o `00_TESTES_CORTE.dxf` para calibrar. Material e regras de
corte: MDF 3 mm, chapa 1000 × 1000, área útil 880 × 880, DXF em mm.

## O que cortar à mão (retângulos simples, de sobra de MDF 3 mm)

| Peça | Medida | Qtd |
|---|---|---|
| DISP_RETENTOR | 192 × 284,6 mm | 1 |
| DISP_APOIO | 470 × 12 mm | 2 |
| Calço de altura (gabarito, não fica no móvel) | 90,7 mm de comprimento | 2 |

## Peças da v2

### Prontas (28)
TAMPO · BASE · DISP_PISTA · as 9 nervuras · todas as frentes e traseiras
das 8 gavetas (16 peças).

A BASE tem os furos girados (defeito da v2). Eles agora só marcam a posição
das divisórias.

### Prateleiras (4): usar como estão
P_CAM, PRAT_1, PRAT_2 e TETO_GAV da v2 são retângulos de 874 × 494 mm, sem
aba. Por isso a ordem muda: primeiro cole as 3 nervuras de lateral a
lateral, com a borda de baixo a **90,7 mm** acima da prateleira de baixo
(use os dois calços). Depois deslize a prateleira pela frente, apoiada
sobre as nervuras, e cole nas nervuras, nas laterais e no fundo falso.
Atrás, a face de baixo dela fica rente à borda de baixo do rasgo do fundo
falso, que serve de conferência. O TETO_GAV apoia direto nas divisórias.

### Com retrabalho manual (31)

| Peça | O que fazer |
|---|---|
| FUNDO | Linha a 3 mm da ponta dos dentes, em cima e embaixo; corte nas duas. Fica com 874 mm. |
| FUNDO_FALSO | Corte uma faixa de 3 mm em cima e outra embaixo. Fica com 874 mm. A borda de baixo dos 4 rasgos compridos fica a 396, 528, 659 e 791 mm da nova borda de baixo. |
| DIV_AB, DIV_BC, DIV_DISP | Corte fora os 2 dentes de cima e os 2 de baixo (20 × 3 mm cada), rente à borda. |
| DISP_LATERAL ×2 | Corte fora os 2 dentes de baixo. Depois risque uma reta de **245,9 mm** na ponta da frente (ponta baixa) a **333,0 mm** na ponta de trás, medindo da borda de baixo, e corte tudo acima dela. |
| 16 laterais de gaveta (A1 a C2, _LAT_E e _LAT_D) | Numa ponta, corte fora o pedaço de 15 × 3,1 mm que fecha o rasgo do fundo (a 6 mm da borda de baixo). Essa ponta vai para trás. |
| 8 fundos de gaveta (A1 a C2, _FUNDO) | Num lado curto (vira a frente), entalhe de 2,4 × 14,5 mm em cada canto. Na montagem, cole o fundo nos rasgos das laterais: ele não chega no rasgo da traseira. |

## Dispensador
- Os perfis cortados na reta nova deixam a pista entre **247 mm** (frente) e
  **333 mm** (fundo) acima da base, com inclinação de cerca de 10°.
- As tiras DISP_APOIO colam na face interna de cada perfil, rentes à borda
  inclinada. A pista apoia nelas.
- O retentor é um painel em pé na frente da baia, sobre a base, entre os
  perfis. Ele sobe 35 mm acima da pista.
- Vão livre acima da pista: cerca de 146 mm na frente e 60 mm no fundo.

## Verificação
As 68 peças foram montadas em 3D com o formato real das peças da v2, já com
o retrabalho, e com as laterais novas. Nenhum par de peças ocupa o mesmo
espaço. Fundo falso e traseiro engatam nas laterais novas, os fundos de
gaveta engatam nos rasgos das laterais e a pista apoia nas tiras. O teste é
geométrico: não avalia resistência nem estabilidade.

## Atenção
- Prateleiras sem aba ficam presas só por cola. Use cola em toda a borda e
  deixe curar bem antes de carregar. Se quiser reforçar, cole uma tira de
  sobra (494 × 10 mm) na lateral, logo abaixo de cada prateleira.
- Corrediças: parafuso não segura em MDF de 3 mm. Use parafuso M4 passante
  com porca e arruela larga.
- O manual em PDF e o desenho frontal da v2/v2.1 estão desatualizados. Use o
  manual 3D.

## Peças iguais entre si (se a gravação sumir, qualquer uma do grupo serve)
- LAT_E = LAT_D (novas) · P_CAM = PRAT_1 = PRAT_2 · as 9 nervuras · DIV_AB = DIV_BC = DIV_DISP · os 2 DISP_LATERAL
- Gavetas A: todas as frentes e traseiras (317 × 96) · todas as laterais (463 × 96) · os 4 fundos (315 × 455)
- Gavetas B e C: todas as frentes e traseiras (136 × 195) · todas as laterais (463 × 195) · os 4 fundos (134 × 455)
- O TETO_GAV é diferente: tem 6 furinhos, que ficam exatamente sobre as divisórias.
- Não usar: o DISP_RETENTOR antigo (192 × 48, chapa 09). Peças repetidas das chapas 16 a 21 servem de reserva.

## Ordem de montagem
1. Inventário · 2. Retrabalho · 3. Corrediças na LAT_E e caixa a seco, depois cola ·
4. Divisórias com as corrediças já presas (DIV_DISP junto com o 1º perfil) ·
5. Dispensador · 6. Prateleiras (nervuras antes de cada uma) · 7. Tampo · 8. Gaveta por gaveta.

## Corrediças (supondo 457 mm, até 45 mm de altura, 12,7 mm de espessura)
Centro do membro fixo, medido da borda de baixo da peça; começa a 3 mm da frente.

| Onde | Gavetas | Altura do centro |
|---|---|---|
| LAT_E (face interna) | A1, A2, A3, A4 | 53,4 · 151,8 · 250,2 · 348,6 |
| DIV_AB, face esquerda | A1 a A4 | 50,4 · 148,8 · 247,2 · 345,6 |
| DIV_AB, face direita | B1, B2 | 99,5 · 296,5 |
| DIV_BC, face esquerda | B1, B2 | 99,5 · 296,5 |
| DIV_BC, face direita | C1, C2 | 147,0 · 222,0 |
| DIV_DISP, face esquerda | C1, C2 | 147,0 · 222,0 (M4 × 16 atravessando DIV_DISP + perfil; porca no vão sob a rampa) |

Membro da gaveta: centro a 48 mm (A), 97,5 mm (B), 145 mm (C1) e 23 mm (C2) da borda de baixo da lateral da gaveta.
As alturas foram escolhidas para as porcas de um lado de cada divisória não baterem nas corrediças do outro lado.
Parafusos: cerca de 90 M4 × 12 e 6 M4 × 16, com porca e arruela larga.
