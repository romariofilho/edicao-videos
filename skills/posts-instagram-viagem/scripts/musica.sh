#!/bin/bash
# uso: musica.sh <reel_sem_audio.mp4> <musica.mp3> <inicio_na_musica_s> <saida.mp4>
# Fade-in 1,5 s e fade-out 4 s no fim; video copiado sem recodificar.
V="$1"; M="$2"; SS="$3"; OUT="$4"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$V")
FO=$(python3 -c "print(round($DUR-4,2))")
ffmpeg -v error -y -i "$V" -ss "$SS" -i "$M" -map 0:v -map 1:a -t "$DUR" \
  -af "afade=t=in:st=0:d=1.5,afade=t=out:st=$FO:d=4" -c:v copy -c:a aac -b:a 192k -movflags +faststart "$OUT"
