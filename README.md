# projetoLeo

Edições de vídeo para o canal **Bastidores do Futebol** (YouTube e redes sociais).

Cada vídeo tem a sua pasta dentro de `videos/`. Lá dentro ficam o vídeo pronto para baixar, um README explicando o que foi feito e uma pasta `scripts/` com os arquivos técnicos da edição (não precisa mexer neles).

| Pasta | Vídeo | Formato |
| --- | --- | --- |
| [`videos/01-short-momentos-bizarros`](videos/01-short-momentos-bizarros) | Short "Momentos mais bizarros do futebol brasileiro" | Vertical 9:16, 2:49 |
| [`videos/02-golaco-de-a-a-z`](videos/02-golaco-de-a-a-z) | "Golaço de A a Z" sem as legendas dos jogadores | Horizontal 16:9, 9:50, em 5 partes |

## Como baixar um vídeo

Abra a pasta do vídeo, clique no arquivo `.mp4` e depois no botão **Download raw file** (seta para baixo, no canto direito).

## Branches

Tudo fica na branch principal, então é só olhar ela. Quando o Claude trabalha num vídeo novo, ele usa uma branch própria (com nome `claude/...`) e, no fim, as mudanças são juntadas na principal.

Para um vídeo novo, a pasta segue a numeração: `videos/03-nome-do-video`.
