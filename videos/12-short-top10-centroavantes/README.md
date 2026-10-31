# Short "Quem é o maior centroavante do Brasil?" (Top 10 centroavantes)

**Vídeo pronto:** [`Short_Top10_Centroavantes_9x16.mp4`](Short_Top10_Centroavantes_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 57 s, H.264 + AAC, áudio em −14 LUFS.

**Sugestão de título no YouTube:** Quem É o Maior Centroavante do Brasil? 🤔 #shorts

Short feito a partir do vídeo longo "Top 10 Maiores Centroavantes do Brasil" (release `centravantes`), para levar quem assiste até o vídeo completo no canal. A contagem vai do #10 ao #2 e **o nº1 não aparece em nenhum momento**: nem imagem, nem nome. O Short termina no suspense, antes do primeiro lugar.

## Roteiro

| Tempo | O que aparece | Lance (origem no vídeo longo) |
| --- | --- | --- |
| 0:00–0:04 | Gancho: "QUEM É O MAIOR CENTROAVANTE DO BRASIL?" + narração original "Dez centroavantes, dez lendas, mas só um pode ser o maior da história do Brasil." | Drible do Ronaldo pela Seleção (7:55) |
| 0:04–0:09 | **#10 Serginho Chulapa**: maior artilheiro da história do São Paulo | Gol do São Paulo 5x1 Portuguesa Santista, 1977 (0:45) |
| 0:09–0:13 | **#9 Careca**: parceiro de Maradona no Napoli | Gol pela Seleção (0:59) |
| 0:13–0:17 | **#8 Adriano**: o Imperador | Arrancada e gol (2:13) |
| 0:17–0:20 | **#7 Vavá**: o Peito de Aço, bicampeão do mundo | Gol em imagem antiga (2:56) |
| 0:20–0:24 | **#6 Reinaldo**: 28 gols em 18 jogos no Brasileiro de 1977 | Gol (3:48) |
| 0:24–0:27 | **#5 Ademir de Menezes**: artilheiro da Copa de 1950 | Gol em imagem antiga (4:46) |
| 0:27–0:30 | **#4 Roberto Dinamite**: maior artilheiro da história do Brasileirão | Arrancada e gol (5:45) |
| 0:30–0:31 | "TOP 3" | — |
| 0:31–0:40 | **#3 Romário**: melhor jogador da Copa de 1994 | Drible pelo PSV (6:04) e dois gols (6:23 e 6:57) |
| 0:40–0:50 | **#2 Ronaldo Fenômeno**: 3 vezes melhor do mundo pela FIFA | Dribles (7:11), a arrancada e o gol pelo Barcelona (7:27) e a comemoração (7:33) |
| 0:50–0:57 | Tela escura com um "?" grande: "E O Nº1… VOCÊ JÁ SABE QUEM É?", depois "VÍDEO COMPLETO NO CANAL", o título do vídeo longo, "INSCREVA-SE" e "TOQUE NO VÍDEO RELACIONADO" | Nenhuma imagem do nº1 |

## Edição

- **Telas de posição** recriadas no vertical, no estilo do vídeo longo: número dourado (#F2C230) grande, nome em branco e faixa vermelha com o mesmo texto do vídeo longo. Fonte Bebas Neue.
- **Escada de posições** no alto (10, 9, 8 … 2 e um "?" vermelho no lugar do nº1), que acende a posição atual.
- **Batida original:** o vídeo longo não tem som nos lances, então a batida foi criada do zero (`scripts/musica.py`, sintetizada nota por nota, sem amostra de ninguém, ou seja, sem direito autoral). Ela tem 120 BPM e cada corte cai num tempo. Na entrada de cada jogador entra um impacto com prato; a contagem vai ficando mais cheia, explode no Top 3 e para no suspense, com um coração batendo.
- **Cortes secos** na batida durante a contagem, com ritmo crescente (de 4,5 s até 3 s por jogador). Flash na entrada do "TOP 3" e de cada jogador do Top 3, e escurecimento para o suspense.
- **Punch-in de 8%** no momento de cada gol.
- **Cor:** correção de cor e contraste em todos os lances. As imagens antigas do Vavá e do Ademir ganharam um preto e branco limpo (sem o tom roxo/sépia desbotado) e grão de filme. Os lances com tom esverdeado foram balanceados. As faixas pretas laterais das imagens antigas ficam fora do recorte.
- **Áreas seguras:** todos os textos ficam entre y = 290 e y = 1526 (limites: 288 e 1536).

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.

## Arquivos técnicos

`scripts/edl.json` é o roteiro (trechos, enquadramento, gols, textos das telas de posição), medido em tempos da batida. `musica.py` cria a batida, `audio.py` monta a trilha com a narração de abertura, `compose.py` e `overlay.py` fazem a imagem. `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
