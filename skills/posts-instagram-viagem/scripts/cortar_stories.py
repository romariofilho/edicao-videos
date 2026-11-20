"""Corta o Reel (com musica) em partes de story nos limites de cena, sem quebrar a musica.
Uso: cortar_stories.py <reel_musica.mp4> <reel.mp4.cortes.json> <pasta_saida> [alvo=16] [min=10] [max=24] [crf=27] [preset=ultrafast]
Corta no INICIO do dissolve (limite de cena). Cada parte e recodificada (libx264 + AAC 192k, 30 fps).
Como as partes seguem o audio original, postadas em sequencia a musica continua exatamente.
Para o publico final use crf 17 / preset slow."""
import sys, json, subprocess, os
reel, cj, out = sys.argv[1:4]
alvo = float(sys.argv[4]) if len(sys.argv) > 4 else 16
mn = float(sys.argv[5]) if len(sys.argv) > 5 else 10
mx = float(sys.argv[6]) if len(sys.argv) > 6 else 24
crf = sys.argv[7] if len(sys.argv) > 7 else "27"
pre = sys.argv[8] if len(sys.argv) > 8 else "ultrafast"
c = json.load(open(cj)); pts = [0.0] + c["limites"] + [c["duracao"]]
n = len(pts); INF = 1e18
best = [INF] * n; prev = [-1] * n; best[0] = 0
for j in range(1, n):
    for i in range(j):
        d = pts[j] - pts[i]
        if best[i] < INF and d <= mx and (d >= mn or j == n - 1):
            cost = best[i] + (d - alvo) ** 2
            if cost < best[j]: best[j] = cost; prev[j] = i
if best[n - 1] >= INF: sys.exit("sem solucao: afrouxe min/max")
cuts = []; j = n - 1
while j > 0: cuts.append(j); j = prev[j]
idx = [0] + cuts[::-1]
os.makedirs(out, exist_ok=True)
for k in range(len(idx) - 1):
    a, b = pts[idx[k]], pts[idx[k + 1]]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b-a:.3f}", "-i", reel,
        "-c:v", "libx264", "-preset", pre, "-crf", crf, "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{out}/parte_{k+1:02d}.mp4"], check=True)
    print(f"parte_{k+1:02d}: {a:.1f}-{b:.1f}s ({b-a:.1f}s)")
