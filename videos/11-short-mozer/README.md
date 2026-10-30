# Short "Mozer, o ídolo do Flamengo que ficou fora de duas Copas"

**Vídeo pronto:** [`Short_Mozer_9x16.mp4`](Short_Mozer_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 34,8 s, H.264 + AAC, áudio em −14 LUFS.

**Sugestão de título no YouTube:** Ele Foi Convocado Para o Tetra… e Ficou de Fora #shorts

Short feito a partir do vídeo longo "Mozer O Ídolo do Flamengo Que Ficou Fora de Duas Copas do Mundo" (release `mozer`), seguindo a skill `short-documentario`. O vídeo longo veio sem música e sem transições: as transições foram criadas na edição, e o Short ficou sem música de fundo, só com a narração original.

O Short cria a pergunta (como ficou fora, se foi convocado?), mostra a glória no Flamengo, a Copa de 1986 perdida e o azar nas duas finais na Europa. Depois chega a 1994 e para em "e o que aconteceu às vésperas do tetra…". **A hepatite e o resto da carreira não aparecem.**

## Roteiro

| Tempo | Narração (origem no vídeo longo) | Imagem | Na tela | Transição / efeito |
| --- | --- | --- | --- | --- |
| 0:00–0:06 | "Mozer, o ídolo do Flamengo que ficou fora de duas Copas do Mundo, foi convocado para o tetra de 1994." (0:00) | Mozer na Seleção (0:02), no Flamengo (0:40), tomando água em preto e branco (3:26) e Seleção (2:59) | Carimbo 1994 | Primeiro quadro completo, punch-in no "Flamengo", escurecimento para o sépia e desfoque que ganha foco |
| 0:06–0:13 | "Em apenas 21 dias, conquistou a Libertadores, o Carioca e o Mundial de 1981, contra o Liverpool." (0:45) | Flamengo perfilado (0:51), foto do time (0:56) e comemoração (0:45) | 21 DIAS, carimbo 1981 | Chicote, punch-in e brilho quente no "Mundial" |
| 0:13–0:19 | "Já convocado para a Copa do México, Mozer torceu o joelho direito num treino, rompeu o menisco e foi cortado." (1:32) | Seleção perfilada (1:30) e Mozer com o casaco da CBF, em sépia (3:06) | Placa COPA DE 1986 • MÉXICO, CORTADO | Escurecimento na entrada, flash e tremida em "cortado" |
| 0:19–0:24 | "E na Europa, chegou a duas finais de Champions. Bateu o pênalti nas duas decisões e perdeu as duas." (0:14) | Benfica (1:41), Mozer no Olympique de Marseille (2:29), lance do Benfica (1:46) e Mozer de cabeça baixa (3:21) | Placas BENFICA × PSV e MARSEILLE × ESTRELA VERMELHA, PERDEU AS DUAS | Chicote, punch-ins, flash e tremida em "perdeu" |
| 0:24–0:31 | "Em 1994, o Parreira o chamou para a Copa dos Estados Unidos. Era a chance de fechar a carreira na seleção com um título." (3:03) | Foto da Seleção (2:55) e Seleção perfilada em preto e branco (3:13) | Carimbo 1994, placa COPA DOS ESTADOS UNIDOS | Brilho quente (esperança), aproximação lenta e escurecimento no fim |
| 0:31–0:33 | (respiro) "E o que aconteceu às vésperas do tetra…" (0:30) | Mozer de costas, camisa 4, em sépia (3:23) | — | Volta do escuro com desfoque que ganha foco |
| 0:33–0:35 | (silêncio) | Fundo escuro | VÍDEO COMPLETO NO CANAL, título do vídeo longo, INSCREVA-SE, TOQUE NO VÍDEO RELACIONADO | — |

## Edição

- **Narração original**, sem acelerar nem regravar, cortada só nos silêncios entre as frases. O áudio do Short foi transcrito de novo depois de pronto, e as 6 frases estão inteiras.
- **Sem música de fundo:** o vídeo longo veio sem música e os bancos livres de direitos não estão acessíveis no ambiente de edição.
- **Legenda revisada:** a transcrição automática errava os nomes. Na legenda estão Mozer, Parreira, Liverpool, Copa do México e pênalti.
- **Cor:** tom de cinema nas fases boas e sépia nas frustrações, com grão de filme e vinheta.
- **Áreas seguras:** título de y = 288 a 437 e legenda/placas de y = 1225 a 1509 (limites: 288 e 1536).
- **Prévias:** pasta `previa/` (início, meio e fim).

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo, para o link clicável aparecer no Short.

## Arquivos técnicos

`scripts/edl.json` é o roteiro (trechos da narração, imagens, transições, carimbos, textos grandes, placas e legenda, no tempo da narração). `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
