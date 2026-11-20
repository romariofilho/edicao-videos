"""Foto -> story 1080x1920 (fundo desfocado, foto inteira centralizada). Uso: foto_story.py <foto> <saida.jpg>
Converte HEIC/qualquer formato via ffmpeg; respeita a rotacao EXIF."""
import sys, subprocess
src, out = sys.argv[1:3]
W, H = 1080, 1920
fc = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=luma_radius=40:luma_power=2,eq=brightness=-0.05[bg];"
      f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", fc, "-frames:v", "1", "-q:v", "2", out], check=True)
