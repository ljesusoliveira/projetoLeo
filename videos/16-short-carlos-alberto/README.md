# Short "Carlos Alberto Torres: o capitão do Tri que só jogou uma Copa"

**Vídeo pronto:** [`Short_Carlos_Alberto_9x16.mp4`](Short_Carlos_Alberto_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 34,1 s, H.264 + AAC, áudio em −14 LUFS.

**Sugestão de título no YouTube:** Capitão do Tri, Mas Só Jogou Uma Copa do Mundo 🏆 #shorts

Short feito a partir do vídeo longo "Carlos Alberto Torres: O Capitão do Tri Que Só Jogou Uma Copa" (release `torres`), seguindo a skill `short-documentario`. Usa só a narração original e não tem música, porque o vídeo longo também não tem. O Short termina na pergunta "e o que aconteceu com ele depois do Azteca…" e não conta o resto da vida dele.

**Sem pausas entre as frases:** os trechos da narração entram um colado no outro. Nenhum silêncio dentro da narração passa de 0,16 s; só a tela final tem o seu próprio silêncio.

## Roteiro

| Tempo | Narração (origem no vídeo longo) | Imagem | Na tela / transição |
| --- | --- | --- | --- |
| 0:00–0:13 | "Carlos Alberto Torres foi o capitão do Tri, marcou um dos gols mais bonitos da história das Copas e foi o último jogador a levantar a taça Jules Rimet. Mesmo assim, o lateral considerado por muitos o maior da história do Brasil disputou apenas uma Copa do Mundo na carreira." (0:00) | De braços cruzados com a camisa da seleção (0:00), ao lado do gol (2:34), levantando a Jules Rimet no Azteca (0:04), jovem (0:11), retrato em preto e branco com a camisa da CBD (2:39) e com os árbitros no sorteio da final (2:24) | Punch-in em "capitão", chicotes, flash na taça, placa ESTÁDIO AZTECA • 1970, brilho quente em "Jules Rimet", punch-in em "maior" e o **carimbo SÓ 1 COPA / MÉXICO 1970** batendo com flash e tremida |
| 0:13–0:23 | "Parecia o caminho natural até a Copa de 1966, na Inglaterra. Ele chegou a aparecer na lista inicial de 44 jogadores, mas ficou fora dos 22 convocados." (0:49) | Com um companheiro nos anos 60 (0:50), o time do Santos com as faixas (1:06) e o time do Santos (0:43), em sépia | Entra desfocado e ganha foco, carimbo 1966, placa INGLATERRA e a **lista animada**: o contador sobe até **44** em "lista inicial", o carimbo **FORA** bate em CARLOS ALBERTO e o número cai para **22** em "convocados" |
| 0:23–0:30 | "O rei rolou para a direita e Carlos Alberto apareceu em velocidade para bater de primeira e mandar a bola para as redes do goleiro Albertosi." (2:16) | Pelé, o camisa 10, de costas (1:17), e a jogada inteira do gol na final de 1970, desde Pelé com a bola até a comemoração (2:17) | Chicote, placa FINAL • BRASIL x ITÁLIA, o recorte acompanha a bola, punch-in em "de primeira" e flash quando a bola entra |
| 0:30–0:32 | "E o que aconteceu com ele depois do Azteca…" (0:24) | Carlos Alberto mais velho, sorrindo, em sépia (1:49) | Entra desfocado e ganha foco |
| 0:32–0:34 | (silêncio) | A mesma imagem, escurecida | VÍDEO COMPLETO NO CANAL, título do vídeo longo, INSCREVA-SE e TOQUE NO VÍDEO RELACIONADO |

## Edição

- **Narração original**, sem acelerar, cortada só no fim das frases. O texto saiu do **Whisper large-v3**. Depois de pronto, o áudio do Short foi transcrito de novo: as 4 partes estão inteiras, até o "Azteca" final.
- **Camada animada feita no Remotion** (`scripts/remotion/`): o carimbo SÓ 1 COPA, a lista de 1966 (44 → 22, FORA) e o encerramento. A lista não mostra nenhum outro nome, para não inventar quem estava nela.
- **Recorte:** fica sempre dentro da foto. Não pega o fundo escuro em volta das fotos estreitas nem os botões "INSCREVA-SE" do vídeo longo. Os quadros de transição do vídeo longo também ficam de fora.
- **Áreas seguras:** todo o conteúdo fica entre y = 304 e y = 1509 (limites: 288 e 1536).
- **Prévias:** pasta `previa/`, com imagens do início, do meio e do fim.

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.

## Arquivos técnicos

`scripts/edl.json` é o roteiro: trechos da narração, imagens, transições, textos e legenda, tudo no tempo da narração. `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
