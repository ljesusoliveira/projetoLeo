# Short "Expulsões tão bizarras que parecem mentira"

**Vídeo pronto:** [`Short_Expulsoes_Bizarras_9x16.mp4`](Short_Expulsoes_Bizarras_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 58 s, H.264 + AAC, áudio em −14 LUFS.

Short feito a partir do vídeo longo "Expulsões Tão Bizarras Que Parecem Mentira no Futebol Brasileiro" (release `expulsoes`), para levar quem assiste até o vídeo completo no canal. Cada expulsão aparece completa (o lance, o cartão e a reação), com o áudio original do vídeo, sem música e sem apito.

## Roteiro

| Tempo | O que aparece |
| --- | --- |
| 0:00–0:14 | Gancho "ISSO ACONTECEU DE VERDADE 😳". **Expulsão #1:** o jogador comemora de cueca (congelado no auge, com impacto), toma o cartão vermelho e a polícia entra no campo |
| 0:14–0:24 | **Expulsão #2:** voadora no Fla-Flu: o lance ao vivo (congelado no contato), o replay em câmera lenta e a confusão com o árbitro |
| 0:24–0:34 | **Expulsão #3:** o jogador do Inter perde a linha, toma o vermelho e sai sem camisa |
| 0:34–0:45 | **Expulsão #4:** até o técnico: o árbitro mostra o vermelho e ele sai gesticulando pelo campo |
| 0:45–0:53 | **Expulsão #5:** a falta, a confusão e o chute perto do banco (congelado no impacto) |
| 0:53–0:55 | Suspense: "E ESSA NEM É A PIOR... 😳" e "AS MAIS BIZARRAS ESTÃO NO VÍDEO COMPLETO 👇" |
| 0:55–0:58 | Encerramento: "VÍDEO COMPLETO LÁ NO CANAL 🔥", título do vídeo longo, "INSCREVA-SE" e "TOQUE NO VÍDEO RELACIONADO" |

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo. Assim o link clicável aparece no Short, que é para onde o texto final aponta.
- O título usado no encerramento veio do nome do arquivo do vídeo longo. Se o título final for outro, troque `end_title` no `scripts/edl.json` e rode `build.sh` de novo.

## Arquivos técnicos

Os scripts estão em `scripts/`. `edl.json` é o roteiro (trechos do vídeo longo, enquadramento, etiquetas e congelamentos). `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
