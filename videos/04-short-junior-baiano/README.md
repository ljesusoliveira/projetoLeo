# Short "As faltas mais duras de Júnior Baiano"

**Vídeo pronto:** [`Short_Junior_Baiano_9x16.mp4`](Short_Junior_Baiano_9x16.mp4?raw=true)

1080×1920 (vertical 9:16), 30 fps, 51 s, H.264 + AAC, áudio em −14 LUFS.

Short feito a partir do vídeo longo das faltas do Júnior Baiano (release `junior-baiano`), para levar quem assiste até o vídeo completo no canal. Cada falta aparece inteira: a chegada, o contato e o adversário no chão.

## Roteiro

| Tempo | O que aparece |
| --- | --- |
| 0:00–0:02 | Gancho: o próprio Júnior Baiano na entrevista, com a frase dele na tela: "EU NUNCA FUI MALDOSO" 😇 |
| 0:02–0:10 | "SERÁ? 🤨" com parada de fita, e a falta #1 (voadora), congelada no contato com flash e impacto |
| 0:10–0:18 | Falta #2 (por trás) e a reação dele de braços abertos: "QUEM, EU? 🤷" |
| 0:18–0:37 | Faltas #3 a #7, incluindo a da Copa de 98 |
| 0:37–0:46 | Falta #8: o adversário voa (congelado no impacto), cartão vermelho com apito e ele rindo: "E AINDA RIU 😂" |
| 0:46–0:48 | Suspense: "E ESSA NEM É A PIOR... 😳" e "AS PIORES ESTÃO NO VÍDEO COMPLETO 👇" |
| 0:48–0:51 | Encerramento: "VÍDEO COMPLETO LÁ NO CANAL 🔥", título do vídeo longo, "INSCREVA-SE" e "TOQUE NO VÍDEO RELACIONADO" |

## Trilha sonora

A música de fundo do vídeo longo foi retirada. No lugar entrou uma trilha original no estilo phonk (cowbell, 808 e bateria, 130 BPM), criada do zero pelo `scripts/music.py`. Como foi gerada aqui, ela não usa música de ninguém e não tem direitos autorais de terceiros.

- A trilha acompanha a edição: começa abafada na frase do gancho, "explode" no "SERÁ?", para nos congelamentos para o impacto ficar sozinho, fecha no suspense e termina com um impacto no encerramento.
- A voz do Júnior Baiano no gancho foi separada da música antiga com um modelo de separação de voz (`scripts/separate.py`).
- Nos lances o vídeo longo só tinha a música de fundo, então ali ficam a trilha nova e os efeitos (impacto em cada contato, apito no cartão vermelho).

## Ao publicar no YouTube

- No YouTube Studio, em **Vídeo relacionado**, escolha o vídeo longo. Assim o link clicável aparece no Short, que é para onde o texto final aponta.
- O título do vídeo longo usado no encerramento é "As faltas mais duras de Júnior Baiano" (tirado do nome do arquivo). Se o título final for outro, troque `title` no `scripts/edl.json` e rode `build.sh` de novo.

## Arquivos técnicos

Os scripts estão em `scripts/`. `edl.json` é o roteiro (trechos do vídeo longo, enquadramento, etiquetas e momentos de impacto). `build.sh` refaz tudo a partir do vídeo longo salvo como `scripts/original.mp4`.
