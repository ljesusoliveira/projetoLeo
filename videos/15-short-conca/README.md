# Short "Conca: só ganhava menos que Messi e Cristiano Ronaldo"

**Vídeo pronto:** [`Short_Conca_9x16.mp4`](Short_Conca_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 31,7 s, H.264 + AAC, áudio em −14 LUFS.

**Sugestão de título no YouTube:** Ele Só Ganhava Menos Que Messi e Cristiano Ronaldo 💰 #shorts

Short feito a partir do vídeo longo "Conca: Só Ganhava Menos Que Messi e Cristiano Ronaldo" (release `conca`), seguindo a skill `short-documentario`. Narração original, sem música (o vídeo longo veio sem música). O Short para na pergunta "e o que aconteceu com ele depois da China…", sem contar o resto da carreira.

## Roteiro

| Tempo | Narração (origem no vídeo longo) | Imagem | Na tela / transição |
| --- | --- | --- | --- |
| 0:00–0:13 | "Dario Conca foi o melhor jogador do Brasileirão, levou o Fluminense a um título que não vinha havia 26 anos e, em 2011, virou o terceiro jogador mais bem pago do planeta, ganhando menos apenas que Messi e Cristiano Ronaldo." (0:00) | Conca com a Bola de Ouro (2:37), o abraço no Fluminense (0:00), o quadro da Bola de Ouro 2010 (2:39), o rosto (0:05), Conca no túnel (0:02) e um lance de jogo (2:42) | Placa BOLA DE OURO 2010, **26 ANOS** com flash e brilho, carimbo 2011 e o **ranking animado "OS MAIS BEM PAGOS DO PLANETA • 2011"**: CONCA em 3º, com MESSI e CRISTIANO RONALDO entrando acima dele no momento em que são falados |
| 0:13–0:15 | "Para isso, trocou o Brasil pela China." (0:13) | Conca apresentado com a camisa do Guangzhou (2:48) | Chicote; **BRASIL** é riscado e **CHINA** bate na tela com flash e tremida |
| 0:15–0:23 | "Baixinho, com menos de 1,70 m e cerca de 58 quilos, era o tipo de jogador que parecia frágil até a bola chegar no pé dele." (2:02) | Foto dele aos 15 anos, em sépia (2:11), e os dribles (0:20 e 0:26) | Desfoque que ganha foco, **1,70 M** e **58 KG** animados; a cor volta com chicote no drible |
| 0:23–0:27 | "Antes de embarcar, Conca foi aplaudido pela torcida no Engenhão, que pedia para ele ficar." (2:50) | Conca com a bandeira do Fluminense (2:50) e de braços abertos no estádio (2:52) | Placa ENGENHÃO • 2011, brilho quente; escurece |
| 0:27–0:30 | "E o que aconteceu com ele depois da China…" (0:25) | Conca em sépia, olhando para o céu (3:26) | Desfoque que ganha foco |
| 0:30–0:32 | (silêncio) | A mesma imagem, escurecida | VÍDEO COMPLETO NO CANAL, título do vídeo longo, INSCREVA-SE e TOQUE NO VÍDEO RELACIONADO |

## Edição

- **Narração original**, sem acelerar, cortada só nos silêncios. O texto saiu do **Whisper large-v3** e o áudio do Short foi transcrito de novo depois de pronto: as 5 frases estão inteiras.
- **Camada animada no Remotion** (`scripts/remotion/`): o ranking dos mais bem pagos, o BRASIL → CHINA, a altura e o peso e o encerramento.
- **Recorte** sempre dentro da área com imagem, sem pegar as faixas pretas nem os botões "INSCREVA-SE" do vídeo longo. Quadros de transição e de efeito do vídeo longo ficam de fora.
- **Áreas seguras:** tudo entre y = 289 e y = 1509 (limites: 288 e 1536).
- **Prévias:** pasta `previa/` (início, meio e fim).

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.

## Arquivos técnicos

`scripts/edl.json` é o roteiro (trechos da narração, imagens, transições, textos e legenda, no tempo da narração). `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
