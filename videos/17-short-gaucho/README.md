# Short "Do Palmeiras ao Flamengo: a vingança mais improvável do futebol?"

**Vídeo pronto:** [`Short_Gaucho_9x16.mp4`](Short_Gaucho_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 34,5 s, H.264 + AAC, áudio em −14 LUFS.

**Sugestão de título no YouTube:** O Centroavante Que Foi Pro Gol e Pegou 2 Pênaltis do Flamengo 🧤 #shorts

Short feito a partir do vídeo longo "Do Palmeiras ao Flamengo: A Vingança Mais Improvável do Futebol?" (release `gaucho`), seguindo a skill `short-documentario`. Usa só a narração original e não tem música. O Short termina na volta do Gaúcho ao Flamengo, que é o gancho do título. O que veio depois (Itália, Cuiabá e a doença) fica para o vídeo longo.

**Sem pausas entre as frases:** os trechos da narração entram um colado no outro. As duas pausas longas da própria narração ("decidir jogos. / Mesmo assim" e "Aldair. / Os dois") foram aparadas. Nenhum silêncio dentro da narração passa de 0,15 s; só a tela final tem o seu próprio silêncio.

## Roteiro

| Tempo | Narração (origem no vídeo longo) | Imagem | Na tela / transição |
| --- | --- | --- | --- |
| 0:00–0:10 | "Gaúcho era centroavante, mas entrou para a história do futebol brasileiro como goleiro. Numa noite no Maracanã, ele calçou as luvas, defendeu dois pênaltis e derrubou o Flamengo, o clube que o revelou." (0:00) | Foto em P&B com a camisa do Palmeiras (0:59), de camisa de goleiro com o placar ao fundo (1:24), parado no gol à noite (2:15), o pênalti defendido (0:06) e ele ajoelhado no gol na comemoração (0:09) | Punch-in em "centroavante" e "goleiro", chicotes, entrada desfocada, placa MARACANÃ • 17/11/1988 e flash na defesa |
| 0:10–0:20 | "Um centroavante improvisado debaixo das traves do Maracanã, diante de cobradores que estavam acostumados a decidir jogos. Mesmo assim, antes das cobranças, Gaúcho avisou que ia pegar e que o Palmeiras ia ganhar." (1:49) | Close com o placar PALMEIRAS (2:21), sentado no gol com a camisa 1 (1:38), os jogadores do Flamengo (1:01), um atacante do Flamengo com a bola (1:13) e a entrevista depois do jogo, emocionado (1:40) | Chicotes, punch-in, brilho quente em "pegar" e punch-in em "ganhar" |
| 0:20–0:28 | "Defendeu as cobranças de Zinho e também a de Aldair. Os dois seriam campeões do mundo pela seleção brasileira na Copa de 1994." (2:04) | As defesas na disputa (2:03), a festa (2:26) e o time do Palmeiras em sépia (2:29) | Flash na defesa. **Gráfico animado:** ZINHO e ALDAIR entram com a luva e "DEFENDEU" quando cada nome é falado; em "os dois", o quadro cresce para o centro e cada nome ganha o selo **★ CAMPEÃO DO MUNDO • 1994** |
| 0:28–0:33 | "E pouco mais de um ano depois, voltou ao Flamengo para virar ídolo justamente da torcida rubro-negra." (0:09) | Gaúcho com a camisa do Flamengo acenando (0:25) e com a faixa "RUBRO-NEGROS" ao fundo (2:38) | Chicote com a cor voltando, carimbo 1990 e brilho quente em "ídolo" |
| 0:33–0:34 | (silêncio) | A mesma imagem, escurecida | VÍDEO COMPLETO NO CANAL, título do vídeo longo, INSCREVA-SE e TOQUE NO VÍDEO RELACIONADO |

## Edição

- **Narração original**, sem acelerar, cortada só no fim das frases. O texto saiu do **Whisper large-v3**. Depois de pronto, o áudio do Short foi transcrito de novo: as frases estão inteiras, até o "revelou" do gancho.
- **Camada animada feita no Remotion** (`scripts/remotion/`): os pênaltis defendidos (ZINHO e ALDAIR com o selo de campeão do mundo em 1994) e o encerramento.
- **Recorte:** fica sempre dentro da imagem. Não pega as faixas pretas das imagens de TV, a marca d'água de baixo, os botões "INSCREVA-SE" do vídeo longo, as defesas em close (que têm o botão por cima) nem os quadros de transição.
- **Áreas seguras:** todo o conteúdo fica entre y = 304 e y = 1509 (limites: 288 e 1536).
- **Prévias:** pasta `previa/`, com imagens do início, do meio e do fim.

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.

## Arquivos técnicos

`scripts/edl.json` é o roteiro: trechos da narração, imagens, transições, textos e legenda, tudo no tempo da narração. `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
