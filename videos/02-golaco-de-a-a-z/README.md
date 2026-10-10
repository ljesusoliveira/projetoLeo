# Golaço de A a Z — sem as legendas dos jogadores

Vídeo de 9:50 (1920×1080, 60 fps) com os 26 golaços, de A (Arrascaeta) a Z (Zé Rafael). As legendas de cada gol (letra, nome do jogador, placar e ano) foram apagadas. O resto não mudou, incluindo o áudio e o logo do canto.

## Vídeo pronto, em 5 partes

O GitHub não aceita arquivos acima de 100 MB, então o vídeo foi dividido entre um gol e outro. Baixe as 5 partes e coloque em sequência no CapCut para ter o vídeo inteiro.

| Parte | Gols | Duração |
| --- | --- | --- |
| [Parte 1](Golaco_de_A_a_Z_parte1_A-E.mp4?raw=true) | A a E | 2:07 |
| [Parte 2](Golaco_de_A_a_Z_parte2_F-J.mp4?raw=true) | F a J | 2:06 |
| [Parte 3](Golaco_de_A_a_Z_parte3_K-O.mp4?raw=true) | K a O | 1:48 |
| [Parte 4](Golaco_de_A_a_Z_parte4_P-T.mp4?raw=true) | P a T | 1:42 |
| [Parte 5](Golaco_de_A_a_Z_parte5_U-Z.mp4?raw=true) | U a Z (com os 8 s de tela preta do final original) | 2:08 |

## Como as legendas foram apagadas

- A legenda é seguida quadro a quadro: entra deslizando com fade, fica parada e sai letra por letra. Em cada fase o texto é apagado e o fundo é preenchido com a imagem em volta.
- No gramado o resultado fica limpo. Sobre torcida, rede ou placas pode ficar uma mancha leve onde estava o texto, mais visível nos ~0,3 s da saída da legenda.

## Arquivos técnicos

Os scripts estão em `scripts/`. `segments.json` tem o início e o fim de cada um dos 26 gols, com jogador, jogo e ano. `build.sh` refaz tudo a partir do vídeo original (release `video-gols`) salvo como `scripts/original.mp4`.
