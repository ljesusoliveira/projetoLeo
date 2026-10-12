# Vídeo do Jobson — sem legenda

**Vídeo pronto:** [`Jobson_sem_legenda.mp4`](Jobson_sem_legenda.mp4?raw=true)

1920×1080, 30 fps, 4:26, H.265 (HEVC) + o áudio original sem alteração. Foi usado H.265 para o vídeo inteiro caber num arquivo só abaixo do limite de 100 MB do GitHub com boa qualidade. O YouTube e o CapCut aceitam esse formato.

Vídeo original: release `jobson` (`1012.mp4`).

## O que foi feito

Foi retirada a legenda de todo o vídeo: o texto branco com contorno preto sobre a faixa escura, na parte de baixo da imagem. O resto (imagem, áudio, duração) não mudou.

- **90 legendas** encontradas, em 4.814 dos 7.990 quadros.
- **Faixa escura:** ela é preta com cerca de 70% de opacidade, então a imagem de trás continuava lá, só escurecida. Em vez de borrar, o fundo foi recuperado clareando a faixa na medida exata do escurecimento.
- **Letras:** onde ficavam as letras não sobra imagem por trás. Essa linha foi preenchida com uma transição suave entre o que está logo acima e logo abaixo.
- **Conferência:** o vídeo final foi varrido quadro a quadro com o detector de legendas e revisado visualmente (um quadro a cada 0,4 s). Não sobrou legenda.

Onde o fundo tem detalhes passando bem atrás das letras (números de camisa, escudos, placas), essa linha fica um pouco borrada.

## Arquivos técnicos

Os scripts estão em `scripts/`:

- `detect.py` acha as legendas quadro a quadro e gera `legendas.json`.
- `unsub.py` tira a legenda de um quadro.
- `render.py` processa o vídeo inteiro.

Para refazer, salve o vídeo original como `scripts/original.mp4` e rode `python3 detect.py` e depois `python3 render.py saida.mp4`.
