# Edição de vídeos — skill do Claude Code

Skill (`posts-instagram-viagem`) para montar **Reels, stories e posts de Instagram** a partir de fotos e vídeos de uma viagem: legenda em "cartão claro", música contínua, stories cortados nos limites de cena, suporte a vídeo HDR de celular (tone mapping).

## Instalar
```bash
cp -r skills/posts-instagram-viagem ~/.claude/skills/
```
Depois, no Claude Code, peça "monte o Reel da viagem" e a skill é carregada.

## Requisitos
`ffmpeg` (com libplacebo p/ HDR; VAAPI opcional), Python 3 + Pillow, fontes Noto Serif Display / Noto Sans Display.

## Conteúdo
- `SKILL.md` — fluxo, regras e estilo de legenda
- `scripts/reel.py` — render do Reel a partir de um projeto JSON
- `scripts/musica.sh` — aplica a música com fades
- `scripts/cortar_stories.py` — corta o Reel em stories nos limites de cena
- `scripts/foto_story.py` — foto 1080×1920 com fundo desfocado
- `exemplo/projeto_exemplo.json` — modelo de projeto

> Adapte nomes e caminhos no `SKILL.md` ao seu caso. Render pesado: limite a memória (ex.: `systemd-run --user --scope -p MemoryMax=3200M`).
