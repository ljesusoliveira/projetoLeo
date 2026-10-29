# Short "O triste fim de Catê"

**Vídeo pronto:** [`Short_Cate_9x16.mp4`](Short_Cate_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 32 s, H.264 + AAC, áudio em −14 LUFS.

Short no estilo trailer de documentário, feito a partir do vídeo longo "O Triste Fim de Catê, o Campeão do Mundo pelo São Paulo" (release `cate`), seguindo a skill `short-documentario` do projeto. Ele é a ponte para o vídeo completo: abre com o mistério do fim, mostra a glória com o São Paulo de Telê, vira no pesadelo na Itália e para na pergunta "o que aconteceu naquela manhã de dezembro…" sobre a imagem do carro batido: uma pista do que aconteceu, **sem contar o final**.

## Roteiro

| Tempo | Narração (origem no vídeo longo) | Imagem | Na tela |
| --- | --- | --- | --- |
| 0:00–0:09 | "O triste fim de Catê, o campeão do mundo pelo São Paulo, aconteceu numa manhã de chuva, no fim de 2011, numa estrada da Serra Gaúcha. Ele tinha apenas 38 anos." (0:00) | Retrato no São Paulo, Catê com a bola, fotos dele mais velho em preto e branco com chuva e o close sorrindo, jovem | CAMPEÃO DO MUNDO, 2011, 38 ANOS |
| 0:09–0:15 | "Antes disso, o garoto do interior do Rio Grande do Sul fez parte de um dos times mais vitoriosos da história do futebol brasileiro." (0:09) | Foto do chute, entrevista jovem, time do São Paulo e Telê | Placas CRUZ ALTA • RS, SÃO PAULO e TELÊ SANTANA |
| 0:15–0:19 | "Fez parte do grupo que venceu o Barcelona e depois o Milan e foi bicampeão mundial em Tóquio." (0:59) | Gol e comemoração do São Paulo | BICAMPEÃO MUNDIAL (com flash) |
| 0:19–0:27 | "Em 1998, por indicação do ex-companheiro Toninho Cerezo, ele foi contratado pela Sampdoria, da Itália. Mas a temporada foi um pesadelo." (2:16) | Foto da Sampdoria e close de Catê com a camisa da Sampdoria, perdendo a cor | 1998, placa SAMPDORIA • ITÁLIA, PESADELO |
| 0:27–0:30 | (pausa) "E o que aconteceu naquela manhã de dezembro…" (0:28) | O carro batido (0:03 do vídeo longo), em preto e branco com chuva, entrando desfocado e ganhando foco | — |
| 0:30–0:32 | (silêncio) | Fundo escuro | VÍDEO COMPLETO NO CANAL, título, INSCREVA-SE, TOQUE NO VÍDEO RELACIONADO |

## Edição

- **Narração original**, sem acelerar nem regravar, cortada só nos silêncios entre as frases. O áudio do Short foi transcrito de novo depois de pronto, para conferir que nenhuma palavra ficou cortada.
- **Sem música nem efeitos extras:** os bancos livres de direitos (Pixabay e YouTube Audio Library) não estavam acessíveis no ambiente de edição.
- **O final não aparece:** só o carro batido aparece, como pista, junto com a pergunta. A narração do acidente e as imagens do caminhão ficaram de fora.
- **Cor como narrativa:** o passado aparece colorido e quente, e 2011 em preto e branco frio, com chuva. Tem grão de filme, vinheta, "punch" nos cortes e movimento constante.
- **Legenda queimada:** blocos curtos em Montserrat ExtraBold, com nomes, anos e números em amarelo.
- **Áreas seguras:** título a partir de y = 293 e legenda até y = 1530, longe dos 15% de cima e dos 20% de baixo.
- **Prévias:** pasta `previa/` (início, meio e fim).

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.
- O título do encerramento veio do nome do arquivo do vídeo longo. Se o título final for outro, troque `end_title` no `scripts/edl.json` e rode `build.sh` de novo.

## Arquivos técnicos

`scripts/edl.json` é o roteiro: trechos da narração, imagens, textos, placas e legenda, marcados no tempo da narração. `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
