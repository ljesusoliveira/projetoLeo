# projetoLeo

Edição de Shorts (9:16) para o canal **Bastidores do Futebol** (YouTube e redes sociais).

## Entregas

| Arquivo | O que é |
| --- | --- |
| `entregas/Short_Momentos_Bizarros_9x16.mp4` | Short "Momentos mais bizarros do futebol brasileiro": 1080×1920, 30 fps, 2:49, H.264 + AAC, áudio em −14 LUFS |

Para baixar pelo navegador, abra o arquivo no GitHub e clique em **Download raw file**.

## Como o Short foi montado

- As faixas pretas do vídeo exportado do CapCut viraram fundo desfocado do próprio lance (cada um dos 12 lances tem o recorte certo).
- Correção leve de contraste e saturação e nitidez suave no vídeo.
- Título fixo no topo, selo "Bastidores do Futebol", gancho "Assista até o final" no começo e barra de progresso com divisões por lance.
- Chamadas para o vídeo completo e para a inscrição em 0:53, 1:48 e no final, com botão "Inscreva-se".
- Áudio original tratado: corte de graves inúteis, compressão leve e volume padronizado em −14 LUFS (pico −1,4 dBTP), o padrão do YouTube.

Os scripts estão em `shorts/momentos-bizarros/` (`build.sh` refaz tudo a partir do `original.mp4`).

## Golaço de A a Z — sem as legendas dos jogadores

Vídeo de 9:50 (1920×1080, 60 fps) do release `video-gols`, com as legendas de cada gol apagadas (letra, nome do jogador, placar e ano). O resto do vídeo, incluindo o logo do canto e o áudio, não foi alterado.

- `shorts/golacos-a-z/segments.json`: início e fim de cada um dos 26 gols, jogador, jogo e ano.
- A legenda é seguida quadro a quadro: entra deslizando com fade, fica parada e sai letra por letra. Em cada fase o texto é apagado e o fundo é preenchido com a imagem em volta.
- No gramado o resultado fica limpo. Sobre torcida, rede ou placas pode ficar uma mancha leve onde estava o texto, mais visível nos ~0,3 s da saída da legenda.

Os scripts estão em `shorts/golacos-a-z/` (`build.sh` refaz tudo a partir do `original.mp4`).
