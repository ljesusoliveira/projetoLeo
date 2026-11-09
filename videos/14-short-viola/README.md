# Short "Viola: provocou o Palmeiras e depois vestiu a camisa do rival"

**Vídeo pronto:** [`Short_Viola_9x16.mp4`](Short_Viola_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 34,8 s, H.264 + AAC, áudio em −14 LUFS.

**Sugestão de título no YouTube:** Ele Imitou um Porco na Cara do Palmeiras… e Depois Vestiu a Camisa Deles #shorts

Short feito a partir do vídeo longo "Viola: Provocou o Palmeiras e Depois Vestiu a Camisa do Rival" (release `viola`), seguindo a skill `short-documentario`. A narração é a original, sem música (o vídeo longo veio sem música). O Short para na pergunta "se você fosse palmeirense, perdoaria o Viola?", sem contar o resto da carreira.

## Roteiro

| Tempo | Narração (origem no vídeo longo) | Imagem | Na tela / transição |
| --- | --- | --- | --- |
| 0:00–0:06 | "Viola imitou um porco na cara da torcida do Palmeiras numa final de campeonato paulista, e virou o maior vilão do rival." (0:00) | A foto do Viola de quatro (0:00), ele no chão no Morumbi (1:19) e o close sendo abraçado (1:23) | Punch-in no "porco", placa FINAL DO PAULISTA, chicote, flash e o carimbo **VILÃO** caindo girando |
| 0:06–0:23 | "A imagem rodou o país, só que a resposta veio no jogo de volta, em 12 de junho de 1993. O Palmeiras fez 3x0 no tempo normal e, na prorrogação, Evair converteu um pênalti. 4x0. Era o fim de um jejum de 16 anos sem título, e a torcida alviverde passou a devolver a provocação ao atacante." (1:26) | A comemoração (1:26), o jogo de volta à noite (1:32), o pênalti com a bola entrando no "4 a 0" (1:38), Evair comemorando (1:42) e o rosto do Viola (1:45) | Desfoque que ganha foco, chicote, carimbo 12.06.1993, **4 x 0** com flash, brilho dourado, placa 16 ANOS SEM TÍTULO; a cor some no rosto do Viola |
| 0:23–0:30 | "E aí veio a reviravolta. No segundo semestre de 1996, voltou ao Brasil para jogar justamente no Palmeiras." (2:59) | Viola rindo (2:45), a figurinha do Valencia (2:41) e Viola com a camisa do Palmeiras (0:05) | Escurecimento, **REVIRAVOLTA** entrando com desfoque de movimento, carimbo 1996, placa VALENCIA • ESPANHA, flash e tremida no "Palmeiras" |
| 0:30–0:33 | "E aí, se você fosse palmeirense, perdoaria o Viola?" (4:13) | Tela dividida: a foto de 1993 x Viola com a camisa do Palmeiras (3:13) | **1993 PROVOCOU** x **1996 VESTIU A CAMISA**, com o **VS** no meio |
| 0:33–0:35 | (silêncio) | A tela dividida escurecida | VÍDEO COMPLETO NO CANAL, título do vídeo longo, INSCREVA-SE e TOQUE NO VÍDEO RELACIONADO |

## Edição

- **Narração original**, sem acelerar, cortada só nos silêncios. Os tempos de cada palavra saíram do **Whisper large-v3** (o modelo mais preciso), e o áudio do Short foi transcrito de novo depois de pronto: as 4 frases estão inteiras.
- **Camada animada no Remotion** (`scripts/remotion/`): o carimbo VILÃO, o REVIRAVOLTA, os rótulos da tela dividida e o encerramento, com animações de mola (spring).
- **Legenda** em blocos curtos, com as palavras de impacto em amarelo; título fixo no alto conversando com o título do vídeo longo.
- **Recorte** sempre dentro da área com imagem (as faixas pretas das fotos ficam de fora) e longe dos botões "INSCREVA-SE" do vídeo longo.
- **Áreas seguras:** tudo entre y = 289 e y = 1509 (limites: 288 e 1536).
- **Prévias:** pasta `previa/` (início, meio e fim).

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.

## Arquivos técnicos

`scripts/edl.json` é o roteiro (trechos da narração, imagens, transições, textos e legenda, no tempo da narração). `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`. As ferramentas de transcrição ficam em `ferramentas/` na raiz do projeto.
