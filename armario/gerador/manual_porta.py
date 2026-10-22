"""Escreve armario/MANUAL_PORTA.md. Chamado por porta_main.py; os números
saem do config.py, do porta.py e da validação, então o manual não fica
desatualizado em relação aos DXFs."""
from __future__ import annotations

import config as c
import montagem as M
import porta as P

L = P.L


def _estabilidade(massa_porta):
    area = sum(i.peca.poly.area * i.quantidade for i in M.montar_pecas() if i.grupo != "cupom") / 1e6
    m_arm = area * c.MATERIAL_T / 1000 * c.MDF_DENSIDADE
    m_porta = massa_porta + 0.7            # + LCD, leitor, teclado, dobradiça [est]
    y_porta = abs(P.Y_PORTA_INT) + c.PORTA_W / 2
    y_ponta = abs(P.Y_PORTA_INT) + c.PORTA_W
    # momentos em torno da borda da frente (kg·m): armário (centro a ~330 mm), coolers, caixa
    resiste = m_arm * 0.33 + 1.3 * 0.245 + 2.0 * 0.553
    tomba = m_porta * y_porta / 1000
    apoio = 10.0 * y_ponta / 1000
    return m_arm, m_porta, resiste, tomba, apoio


def escrever(caminho, arquivos, colocados, cupom, validacao):
    z_a, z_b = P.furos_dobradica()
    m_arm, m_porta, resiste, tomba, apoio = _estabilidade(validacao["massa_porta_kg_sem_componentes"])
    por_chapa = {}
    for p in colocados:
        por_chapa.setdefault(p.chapa, []).append(p.item.peca.codigo)
    T = c.MATERIAL_T
    xi0, xi1, zi0, zi1 = c.JANELA_INT
    linhas = []
    w = linhas.append
    w("# Manual da porta e das peças novas (v2.4)")
    w("")
    w("Gerado por `armario/gerador/porta_main.py`. Não edite à mão: mude o `config.py` e rode o gerador de novo.")
    w("Medidas em mm. Coordenadas do armário: olhando de frente, X para a direita, Y da frente para o fundo, Z para cima.")
    w("")
    w("**Ordem obrigatória:**")
    w("1. Cortar o **cupom de teste** e testar.")
    w("2. Ajustar o `config.py` com o que foi medido.")
    w("3. Rodar o gerador de novo.")
    w("4. Só então cortar as chapas 24 em diante.")
    w("")
    w("## 1. O que vai para a máquina")
    w("")
    w("| Arquivo | Peças |")
    w("|---|---|")
    w(f"| `00_CUPOM_PORTA_CORTE.dxf` + `00_CUPOM_PORTA_NOMES.dxf` | Cupom de teste, {len(cupom)} peças (cortar primeiro) |")
    for ch, _, _ in arquivos:
        grupos = sorted({cod.split("_")[0] + ("_" + cod.split("_")[1] if cod.startswith(("PORTA", "BERCO", "CAIXA", "BAIA", "BLOCO", "GABARITO")) else "")
                         for cod in por_chapa[ch]})
        n = len(por_chapa[ch])
        w(f"| `corte/CHAPA_{ch:02d}.dxf` + `gravacao/CHAPA_{ch:02d}_NOMES.dxf` | {n} peça{'s' if n > 1 else ''}: {', '.join(grupos)} |")
    w("")
    w(f"Valem as mesmas regras da V2.3:")
    w(f"- MDF de {T:g} mm, chapa de 1000 × 1000, área útil de 880 × 880 (peças entre 10 e 890), 6 mm entre peças.")
    w(f"- DXF em mm (INSUNITS = 4); corte em vermelho (ACI 1), gravação em azul (ACI 5).")
    w(f"- Folga de {c.FOLGA:.2f} mm por lado nos rasgos.")
    w("")
    w("Os mapas de corte estão em `mapas/`; a lista completa de peças, em `LISTA_PECAS_PORTA.csv`.")
    w("")
    w("![Cupom de teste](mapas/CUPOM_PORTA.png)")
    w("")
    for ch, _, _ in arquivos:
        w(f"![Chapa {ch}](mapas/CHAPA_{ch:02d}.png)")
        w("")
    w("## 2. Cupom de teste — o que conferir antes de cortar a porta")
    w("")
    w("| Peças do cupom | Teste | Se não servir, mude no `config.py` |")
    w("|---|---|---|")
    w(f"| CP_PELE + CP_LCD_1 a 4 + presilhas | O LCD encaixa: o vidro aparece inteiro na janela de {c.LCD_JANELA[0]:g} × {c.LCD_JANELA[1]:g}, "
      "a placa entra no rasgo da camada 4 e as presilhas apertam sem quebrar | `LCD_PLACA`, `LCD_MOLDURA`, `LCD_JANELA` |")
    w(f"| CP_PELE + CP_LEITOR_1 a 7 + presilhas | A face do AS608 encosta na janela de {c.AS608_JANELA[0]:g} × {c.AS608_JANELA[1]:g} "
      "e o dedo alcança a área de leitura inteira | `AS608_MODULO`, `AS608_JANELA` |")
    w(f"| CP_PELE (contorno gravado e rasgo) | O teclado cobre o contorno e o cabo flat passa no rasgo de "
      f"{c.TECLADO_FLAT[0]:g} × {c.TECLADO_FLAT[1]:g} | `TECLADO`, `TECLADO_FLAT` |")
    w("| CP_PELE (furos pequenos) | Os furos de teste servem para a dobradiça (3,5), M3 e M4 sem forçar | `DOB_FURO`, `FURO_M3` e `FURO_M4` do `hardware/layout.py` |")
    w(f"| CP_BLOCO_1 a 3 + CP_PORTA_PELE/MONT1/MONT2 + 150 mm de dobradiça | Os furos da dobradiça batem com os do bloco "
      f"(a cada {c.DOB_PASSO:g} mm) e as porcas M3 ficam presas no sextavado | `DOB_PASSO`, `DOB_PRIMEIRO_FURO`, "
      "`DOB_FURO_DA_DOBRA`, `DOB_ABA_ESP` |")
    w("| CP_BATENTE_* + CP_TRAVA_PLACA + a trava FE-91 | Parafusar a trava na placa e montar o batente. Empurrando o batente "
      "contra a lingueta, ela recolhe e estala na janela; puxando, não sai; com 12 V, sai | `TRAVA_*`, `BATENTE_*` |")
    w(f"| CP_PELTIER | A pastilha entra no quadrado de {L.FURO_PELTIER:g} mm com folga pequena | `FURO_PELTIER` do `hardware/layout.py` |")
    w(f"| CP_GRADE | Um dedo não passa pelos quadrados de {c.BERCO_GRADE_FURO:g} mm | `BERCO_GRADE_FURO` |")
    w("")
    w("## 3. A porta")
    w("")
    w("![Porta vista de frente](mapas/PORTA_FRENTE.png)")
    w("")
    w(f"- **Tipo:** porta-caixão, com duas peles de {T:g} mm e miolo de {c.PORTA_NUCLEO:g} mm. Uma folha só de 3 mm com "
      "880 × 880 empenaria e não seguraria dobradiça nem trava.")
    w(f"- **Espessura e massa:** **{P.PORTA_ESP:g} mm** e **{validacao['massa_porta_kg_sem_componentes']:.1f} kg** "
      f"sem componentes [calc, MDF a {c.MDF_DENSIDADE:g} kg/m³ est].")
    w(f"- **Tamanho:** {c.PORTA_W:g} × {c.PORTA_H:g} mm, de Z {c.PORTA_Z0:g} a {c.PORTA_Z0 + c.PORTA_H:g} e de X {P.X_PORTA0:g} a {P.X_PORTA1:g}. "
      "A mata-junta (30 mm, sendo 10 mm para fora da porta) cobre a borda da lateral direita.")
    w(f"- **Folga até as gavetas:** a face de dentro da porta fechada fica em Y = {P.Y_PORTA_INT:g}. Com a frente das gavetas em "
      f"Y = {c.FRENTE_GAVETA_Y:g} (`FRENTE_GAVETA_Y`, valor calculado), sobram **{validacao['folga_porta_gavetas_mm']:g} mm**.")
    w("- **Puxadores das gavetas: só embutidos** (furo ou rasgo na frente). Nada pode sair mais que 4 mm da frente.")
    w("- **Medir antes de cortar:**")
    w("  1. Encoste uma régua nas bordas da frente das duas laterais.")
    w("  2. Meça quanto cada gaveta e cada prateleira fica para fora ou para dentro.")
    w("  3. Ponha o maior valor para fora (negativo) em `FRENTE_GAVETA_Y` e rode o gerador.")
    w(f"  O gerador recusa se a folga ficar abaixo de {c.FOLGA_PORTA_GAVETA_MIN:g} mm.")
    w("- **O que fica no miolo:**")
    w("  - montante da dobradiça (8 camadas, porcas M3 presas na camada 2);")
    w("  - montante da trava (8 camadas, cava do puxador nas 4 de fora);")
    w("  - trilhos e nervuras em pé, encaixadas em meia-madeira;")
    w("  - moldura da janela de serviço;")
    w("  - molduras do LCD e do leitor, coladas na pele de fora;")
    w("  - canal dos cabos, no alto.")
    w(f"- **Janela de serviço:** a pele de dentro tem uma janela de {xi1 - xi0:g} × {zi1 - zi0:g} mm atrás do LCD e do leitor. "
      "Ela é fechada pela tampa traseira, presa por 4 parafusos M3 em colunas coladas.")
    w(f"- **Tampa traseira:** avança {c.CAIXA_TRASEIRA_PROF + T:g} mm para dentro do armário, na frente do compartimento entre "
      "a Prateleira 1 e o piso da câmera. **Deixem vazios os primeiros 10 mm dessa prateleira.**")
    w(f"- **Cabos:** correm no canal do alto do miolo e saem pela **borda de cima** da porta, a {c.SAIDA_CABOS_U[0]:g}–{c.SAIDA_CABOS_U[1]:g} mm "
      "da dobradiça. Dali, um laço de 15 cm até a caixa da eletrônica no tampo.")
    w("")
    w("### Ordem de montagem da porta")
    w("")
    w("1. Colar as camadas de cada montante (esquerdo 1→8, direito 1→8). No esquerdo, as porcas M3 já vão nos sextavados da camada 2.")
    w("2. Na pele de dentro, deitada com a face gravada para cima, colar:")
    w("   - os montantes;")
    w("   - os trilhos (o de cima com o entalhe da saída dos cabos junto da dobradiça);")
    w("   - as nervuras, encaixadas em meia-madeira;")
    w("   - a moldura da janela.")
    w("   Conferir o esquadro.")
    w("3. Na pele de fora, com a face gravada para cima (é o lado de dentro), colar as molduras do LCD (camadas 1–4) e do "
      "leitor (1–7), centradas nas janelas, com as porcas M3 nos sextavados da camada 1.")
    w("4. Passar os 3 cabos de rede pelo canal e pela saída de cima. Ligar o teclado pelo rasgo e deixar as pontas do LCD, "
      "do leitor e do buzzer na janela.")
    w("5. Fechar: cola em todas as nervuras e montantes, pele de fora por cima, peso espalhado por igual (livros) por 12 h.")
    w("6. Pela janela de serviço, montar o LCD e o leitor com as presilhas M3. Colar o buzzer atrás dos furinhos. Colar o teclado por fora.")
    w("7. Colar as 4 colunas da tampa traseira (a camada 1, com a porca, encostada na pele) e parafusar a tampa.")
    w("8. Colar a mata-junta (2 camadas, 2 trechos) na borda direita, por dentro, com 10 mm para fora da porta.")
    w("")
    w("## 4. Dobradiça, batente, trava e liberação de emergência")
    w("")
    w(f"- **Dobradiça piano:** cortada com {c.DOB_COMPRIMENTO:g} mm, de Z {c.DOB_Z0:g} a {c.DOB_Z0 + c.DOB_COMPRIMENTO:g}. "
      f"Corte de modo que o 1º furo da aba do armário fique a {c.DOB_PRIMEIRO_FURO:g} mm da ponta de baixo.")
    w(f"  - Aba do armário: **{len(z_a)} parafusos M3 × 10**, com as porcas presas no bloco.")
    w(f"  - Aba da porta: **{len(z_b)} parafusos M3 × 10**, com as porcas presas no montante.")
    w(f"- **Bloco da dobradiça** (3 camadas, 45 × {c.DOB_COMPRIMENTO:g}):")
    w(f"  - colado na face de fora da lateral esquerda, com a frente {c.AFASTAMENTO_PORTA:g} mm à frente da caixa;")
    w(f"  - preso por **{len(c.BLOCO_DOB_PARAFUSOS_Z)} parafusos M4 × 20** passantes, em Y {c.BLOCO_DOB_PARAFUSO_Y:g} e Z "
      + ", ".join(f"{z:g}" for z in c.BLOCO_DOB_PARAFUSOS_Z) + ";")
    w("  - os furos de cima são feitos usando o próprio bloco como gabarito: fure pelos furos dele, já colado.")
    w("- **A porta abre até 90°** (a dobradiça chega a 180° entre as abas). Não force além: os coolers ficam do lado esquerdo.")
    w(f"- **Trava FE-91:** corpo na face de dentro da lateral direita, em Z {c.TRAVA_Z:g}. A lingueta aponta para o meio "
      "do armário (−X), com o lado chanfrado virado para a frente. As medidas da trava não são publicadas: meçam e ajustem "
      "`TRAVA_*` antes de cortar o cupom.")
    w("- **Batente:** placa de 2 camadas na face de dentro da porta e braço de 2 camadas com a janela da lingueta. Ao fechar, "
      "o braço empurra o chanfro e a lingueta estala na janela.")
    w("- **Liberação de emergência (sem energia):**")
    w("  1. Os 2 parafusos M4 × 30 que prendem o batente na porta entram pela **cava do puxador**.")
    w("  2. Com uma chave Phillips, solte os dois: a porta abre e o batente fica preso na trava.")
    w("  3. Para fechar de novo, recoloque o batente e aperte os parafusos.")
    w("  Testem isso no cupom e de novo na porta montada, antes da banca.")
    w(f"- **Reed:** na face de dentro da lateral direita, em Z {c.REED_Z:g}, 6 mm atrás da borda. O ímã fica na mata-junta, na mesma altura.")
    w("")
    w("## 5. Checagem de colisão")
    w("")
    w("![Vista de cima com a porta a 0°, 45° e 90°](mapas/PORTA_COLISAO.png)")
    w("")
    w("Giram junto com a porta, em torno do eixo da dobradiça: a própria porta, a mata-junta, a tampa traseira, o batente e o ímã.")
    w("O gerador confere a cada 1° de 0 a 15° e a cada 5° até 90° se alguma dessas partes encosta em:")
    w("- laterais, base, tampo, prateleiras e divisórias;")
    w("- frentes das gavetas e tampa da baia fria;")
    w("- trava, reed e câmeras;")
    w("- bloco da dobradiça, coolers, berços e caixa da eletrônica.")
    w("")
    w(f"**Resultado: {validacao['colisoes_0_a_90_graus']} colisões.** Menores folgas:")
    w("")
    w("| Parte da porta | 0° | 45° | 90° |")
    w("|---|---|---|---|")
    fol = validacao["folgas_mm"]
    for parte in fol["0"]:
        cel = []
        for a in ("0", "45", "90"):
            d, ob = fol[a][parte]
            cel.append("—" if ob is None else f"{d:g} mm ({ob})")
        w(f"| {parte} | " + " | ".join(cel) + " |")
    w("")
    w("A folga de 1 mm entre a porta fechada e o bloco é a espessura da aba da dobradiça, que fica entre eles.")
    w("A lingueta só entra na conta com a porta fechada: para abrir, a trava recolhe a lingueta.")
    w("")
    w("## 6. Peças do armário")
    w("")
    w("- **Gabaritos de furação** (`GABARITO_LAT_E`, `GABARITO_LAT_D`):")
    w("  1. Encaixe a régua de encosto nos rasgos do gabarito.")
    w("  2. Apoie a borda \"MESA\" na mesa e encoste a régua na borda da frente da lateral.")
    w("  3. Fure pelos furos do gabarito.")
    w("  4. Nos quadrados das Peltier: risque por dentro da janela, fure os cantos com broca de 10 mm e termine com estilete.")
    w("- **Berços dos coolers** (`BERCO_1_*`, `BERCO_2_*`): placa na lateral (4 parafusos M4 × 20 passantes), duas "
      "mãos-francesas encaixadas e a grade por cima. A ventoinha do cooler fica sobre a grade, soprando para cima.")
    w(f"- **Baia fria** (`BAIA_*`):")
    w(f"  - 6 taquinhos (3 camadas cada) colados pela frente, com a face de cima em Z {c.BAIA_PISO_Z:g}; o piso desliza pela "
      "frente e apoia neles;")
    w("  - a tampa leva o bloco de EPS colado atrás e uma alça (furo de 28 mm);")
    w(f"  - isopor, cortado à mão em 50 mm:")
    w(f"    - piso: {c.COL_A_W:g} × {c.SHELF_DEPTH - 50:g}; teto: igual;")
    w(f"    - paredes laterais: {c.SHELF_DEPTH - 50:g} × {c.GAVETEIRO_Z[1] - c.BAIA_PISO_Z - T - 100:g}, com entalhe de 13 mm onde passa corrediça;")
    w(f"    - fundo: {c.COL_A_W - 100:g} × {c.GAVETEIRO_Z[1] - c.BAIA_PISO_Z - T - 100:g};")
    w(f"    - bloco da tampa: {c.COL_A_W - 102:g} × {c.GAVETEIRO_Z[1] - c.BAIA_PISO_Z - T - 102:g};")
    w("    - na parede esquerda, furos quadrados de 39 mm no isopor, na frente dos furos das Peltier, para os espaçadores.")
    w(f"- **Caixa da eletrônica** (`CAIXA_*`):")
    w(f"  - {c.CAIXA_INT[0]:g} × {c.CAIXA_INT[1]:g} × {c.CAIXA_INT[2]:g} mm por dentro, juntas de dente coladas;")
    w(f"  - presa no tampo por 3 parafusos M4 (use a base como gabarito), em X {c.CAIXA_XY[0]:g}, Y {c.CAIXA_XY[1]:g};")
    w("  - tampa com 4 parafusos M4 em cantos com porca presa;")
    w("  - **só abrir com a fonte fora da tomada.**")
    w("")
    w("## 7. Estabilidade e fixação (RNF14)")
    w("")
    w(f"- O armário pesa ≈ {m_arm:.0f} kg [calc pela área das peças, MDF a {c.MDF_DENSIDADE:g} kg/m³ est]. "
      f"A porta, com os componentes, ≈ {m_porta:.1f} kg.")
    w(f"- Com a porta aberta a 90°, o momento que tomba para a frente é ≈ {tomba:.1f} kg·m, contra ≈ {resiste:.1f} kg·m que "
      f"seguram (fator {resiste / tomba:.1f}). **Sozinho, não tomba.**")
    w(f"- Mas alguém apoiando **10 kg** na ponta da porta aberta soma {apoio:.1f} kg·m: **tomba**.")
    w("- **Mínimo para a banca:** prender a base na mesa com 2 grampos sargento (os da oficina da faculdade), um em cada canto da frente.")
    w("- **Para a parede (RNF14, fora do protótipo):** 2 cantoneiras metálicas no tampo, parafusadas na parede, com parafuso "
      "passante e arruela larga no tampo.")
    w("")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
