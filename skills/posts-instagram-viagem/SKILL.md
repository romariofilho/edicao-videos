---
name: posts-instagram-viagem
description: Produz Reels, stories e posts de Instagram a partir de fotos/vídeos de uma viagem — legenda "cartão claro", Reel com música, stories cortados nos limites de cena com a música contínua, fotos intercaladas, vídeos HDR de celular. Use quando o usuário pedir Reel, stories, post, legendas ou "montar o conteúdo da viagem".
---

# Posts de Instagram da viagem

Pasta típica: `~/Imagens/<AAAA-MM> - <lugar>/` com `Pessoa1/` e `Pessoa2/` (vídeos/fotos de cada celular; clipes de celular recente podem ser **HDR**), música `.mp3`, e `saida/` para tudo que geramos.

## Regras permanentes
- **Nunca apagar/alterar originais.** Versão nova = nome novo (`..._v2`, `_v3`); só apagar rascunhos que EU gerei.
- **Claude nunca publica nem faz login.** Pode preencher o compositor/subir ao Drive do usuário quando pedido; só o usuário toca "Compartilhar". Perguntar antes de tornar algo público/compartilhado.
- **Rascunho de baixa qualidade primeiro** (modo `rapido`), mostrar o plano antes de render pesado. **Render final só quando o usuário pedir**.
- Termos e perfis: definir com o usuário no início (nomes do lugar, @ a marcar, palavras a evitar).

## Máquina (15 GB RAM; /tmp = RAM)
- Render pesado SEMPRE: `systemd-run --user --scope -q -p MemoryMax=3200M -p MemorySwapMax=0 <cmd>`; checar `free -h`.
- Temporários em `saida/_tmp*` (disco), nunca no scratchpad/`/tmp`.
- **Rascunho com aceleração**: `HW=1` (VAAPI Intel, `/dev/dri/renderD128`) — ~2,2× mais rápido (389 s vs 874 s p/ 2:15), arquivo menor. **Final: CPU libx264** (sem `HW`).
- Cuidado: `pkill -f`/`pgrep -f` mata o próprio shell; usar PID.

## Fluxo do Reel
1. Escolher cenas e escrever um projeto JSON (modelo em `exemplo/projeto_exemplo.json`): `cenas[] = {src, ss (início s), d (duração visível), cap}`, `titulo{nome,marca,local}`, `musica`, `musica_inicio`. `cap:"@TITLE"` = cartão de título; texto com `\n` = legenda de 1–2 linhas.
2. Render: `systemd-run ... env HW=1 python3 -I scripts/reel.py projeto.json rapido saida/_reel.mp4`. Gera também `saida/_reel.mp4.cortes.json` (limites de cena).
   - Vídeo 9:16 por cena com fundo desfocado (blur-fit), 30 fps, xfade 0,5 s. **Duração total = soma dos `d`** (cada segmento tem +0,5 s de cauda; offset = soma acumulada).
   - HDR (`color_transfer=smpte2084`, clipes de celular HDR): tone map libplacebo bt.2390 + saturação 1,1 já automático.
   - Montagem em blocos de 6 cenas com `-filter_complex_threads 1` (evita estourar RAM).
3. Música: `scripts/musica.sh saida/_reel.mp4 musica.mp3 <início> saida/reel_<nome>_rascunho_musica.mp4` (fade-in 1,5 s, fade-out 4 s).
4. Mostrar ao usuário; ajustar legenda/cenas; novo nome a cada versão.

## Legenda — estilo D "cartão claro" (aprovado, posição BAIXA)
- Cartão creme arredondado (rgba 255,250,241,222; raio 28), texto marrom (74,52,38), fonte **Noto Serif Display Italic** 70 px (reduz até ≥52 se largura+130 > 900), centralizado em **y=1570** (de 1920), altura de linha 84, padding 130×56. Fade-in em 0,4 s (0,6 s), fade-out 0,9 s antes do fim.
- Título: caixa [140,1390,940,1730], nome 130 px y=1426, "MARCA" Noto Sans Display 34 px espaçado (9) y=1590, local 42 px y=1644 com ícone de pin.
- Já foi pedido **mais baixo** duas vezes (não atrapalhar a imagem). A barra de UI do Instagram cobre o rodapé do Reel; se o texto sumir, subir um pouco, mas só com o OK do usuário.
- Estilos descartados (A editorial, B caixa-alta, C faixa, E dourado, F cinema): amostras em `saida/legendas_amostras/`.

## Stories
- **Cortar o Reel em partes, não regravar**: `python3 scripts/cortar_stories.py reel_musica.mp4 reel.mp4.cortes.json saida/stories_vN/rascunho [alvo 16] [min 10] [max 24]`. Corta no início do dissolve (limite de cena) por programação dinâmica; **não precisa ser 15 s exatos** (pode passar). Postando as partes em ordem a **música continua exatamente** de onde parou.
- **Fotos complementares**: gerar contact sheets numeradas, escolher 6–10 não usadas nos posts, `scripts/foto_story.py foto saida/stories_vN/fotos/apos_parte_XX_foto_a.jpg` (1080×1920, blur-fit), intercalar após as partes. Fotos ficam **sem música** (5 s; o usuário adiciona no app se quiser). Avisar que pode haver repetição com posts anteriores.
- Escrever `ordem.md` + `.html` com a sequência numerada (parte/foto), e mostrar prévia (`fotos_sel.jpg`).
- Envio ao celular (via adb): `adb push` para `/sdcard/Movies/<pasta>/`; se "device not found", pedir para reconectar o cabo. `adb input text` não aceita acentos.
- `SendUserFile`: ≤30 MiB para quem vê pelo celular/web; arquivos maiores só no desktop → usar Drive (sem compartilhar) ou adb.

## Texto
Legendas/hashtags em `saida/legendas.md/.html`: tom caloroso e simples, primeira pessoa do plural, marcar os perfis certos, sem inventar fatos sobre o lugar.

## Preferências aprendidas
- **Legenda com moderação**: pouca legenda nas cenas; muita deixa o Reel "chato". Não legendar o que é auto-explicativo (paisagem, refeição, vista). Deixar só nas cenas que contam algo (título, momento, despedida).
- **Música**: analisar a energia da faixa e começar no ponto em que ela entra; fade-in curto (0,4 s) nesse caso, não 1,5 s.
- **Seleção**: o usuário pede cenas específicas pelo nome do arquivo; usar a timeline de quadros (a cada 3–4 s) para escolher o trecho certo. Pente fino: olhar todos os clipes, não só os primeiros.
