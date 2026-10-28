# Short "O triste fim de Mário Sérgio"

**Vídeo pronto:** [`Short_Mario_Sergio_9x16.mp4`](Short_Mario_Sergio_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 35 s (34,7 s), H.264 + AAC, áudio em −14 LUFS.

Short feito a partir do vídeo longo "O Triste Fim de Mário Sérgio, o Gênio Indomável do Futebol Brasileiro" (release `mario-sergio`), para levar quem assiste até o vídeo completo no canal. O áudio é a própria narração do vídeo longo, com a trilha que já vem nela, sem trocar a música. Ela foi cortada só nas pausas entre as frases, então nenhuma frase fica pela metade. A legenda da narração fica embaixo do vídeo, com as palavras-chave em amarelo, para quem assiste sem som.

## Roteiro

| Tempo | Narração | Imagem |
| --- | --- | --- |
| 0:00–0:04 | Gancho: "Ele estava no avião que levava a Chapecoense para a final da Copa Sul-Americana." | Rosto dele, a delegação da Chape e o avião da LaMia. Destaque "NO AVIÃO DA CHAPECOENSE ✈️" |
| 0:04–0:13 | "Antes disso, viveu uma carreira em que a genialidade e a confusão andaram sempre juntas. Foi campeão do mundo, ficou fora de uma Copa por muito pouco e chegou a disparar um revólver para o alto." | Uma imagem para cada frase: Tóquio, a Seleção com a 11 e a entrevista com flash no "revólver". Destaques "CAMPEÃO DO MUNDO 🏆", "FORA DA COPA DE 82 ❌" e "DISPAROU UM REVÓLVER 💥" |
| 0:13–0:19 | "Com a perna esquerda fazia o que queria com a bola. Olhava pra um lado e passava para o outro, e por isso os colegas o chamavam de Vesgo." | O drible dele pelo São Paulo e uma aproximação nos olhos, congelada no "VESGO 👀" |
| 0:19–0:25 | "O Grêmio contratou só para a decisão do Mundial de Clubes, em Tóquio, contra o Hamburgo. Mário Sérgio era campeão do mundo." | Time do Grêmio e lances da final de 1983, congelada com flash em "CAMPEÃO DO MUNDO 🏆" |
| 0:25–0:26 | (pausa) | A cor some e entra "33 ANOS DEPOIS..." |
| 0:26–0:31 | "O avião caiu perto de Medellín e 71 pessoas morreram. Mário Sérgio tinha 66 anos." | Destroços, caixões da Chapecoense e a foto dele como comentarista, com "1950 – 2016 🕊️" |
| 0:31–0:35 | "Mário Sérgio foi genial e foi problema, mas nunca foi indiferente." | Encerramento: "VÍDEO COMPLETO LÁ NO CANAL 🔥", título do vídeo longo, "INSCREVA-SE" e "TOQUE NO VÍDEO RELACIONADO" |

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo. Assim o link clicável aparece no Short, que é para onde o texto final aponta.
- O título usado no encerramento é o nome do arquivo do vídeo longo. Se o título final for outro, troque `end_title` no `scripts/edl.json` e rode `build.sh` de novo.

## Arquivos técnicos

Os scripts estão em `scripts/`. `edl.json` é o roteiro: trechos da narração, de onde vem cada imagem, enquadramento, destaques e legenda. Os tempos da narração foram tirados de uma transcrição automática (Whisper) do vídeo longo. `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
