# Vídeo do Bismark — sem legenda

**Vídeo pronto:** [`Bismark_sem_legenda.mp4`](Bismark_sem_legenda.mp4?raw=true)

1920×1080, 30 fps, 4:20, H.265 (HEVC) + o áudio original sem alteração. Foi usado H.265 para o vídeo inteiro caber num arquivo só abaixo do limite de 100 MB do GitHub com boa qualidade. O YouTube e o CapCut aceitam esse formato.

Vídeo original: release `bismark` (`1026.mp4`).

## O que foi feito

Foi retirada de todo o vídeo a legenda amarela (caixa amarela com letra preta, uma palavra por vez, embaixo no centro). O resto (imagem, áudio, duração) não mudou.

- **Cerca de 515 palavras** encontradas, em 5.389 dos 7.798 quadros.
- **A caixa amarela é opaca:** o que está atrás dela não existe naquele quadro. Então a imagem real foi buscada nos quadros vizinhos (até 2 s antes ou depois). No intervalo entre as palavras a caixa some, e as palavras curtas cobrem menos. Antes de copiar, o quadro vizinho é alinhado (compensa o zoom das fotos e as fotos que deslizam, como a figurinha do Bismark) e só é usado se a imagem em volta da caixa bater. Onde a caixa inteira não bate, a área é tentada em faixas estreitas.
- **Onde não deu para recuperar** (jogadores andando bem atrás da caixa), a área foi refeita a partir da imagem em volta, de forma suave e com o mesmo grão do vídeo. Nessas cenas pode ficar uma mancha leve e borrada no lugar da caixa.
- **Conferência:** o vídeo final foi varrido quadro a quadro com o mesmo detector da legenda. Não sobrou nenhuma caixa amarela.

As legendas em japonês e inglês que já vinham nas imagens de arquivo (por volta de 2:43–3:07 e 3:54–3:59) fazem parte das filmagens originais, não são a legenda amarela, e foram mantidas. Onde a caixa amarela ficava por cima delas, as letras que estavam embaixo da caixa não existem no vídeo e ficaram borradas.

## Arquivos técnicos

Os scripts estão em `scripts/`:

- `detect.py` acha a caixa amarela quadro a quadro e gera `boxes.npy`.
- `unsub.py` tira a caixa de um quadro.
- `render.py` processa um trecho do vídeo (só imagem).

Para refazer, salve o vídeo original como `scripts/original.mp4`, rode `python3 detect.py` e depois `python3 render.py saida.mp4 0 7798`. Por último, junte o áudio do original.
