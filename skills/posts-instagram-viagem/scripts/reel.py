"""Renderiza um Reel a partir de um projeto JSON. Uso: reel.py <projeto.json> <rapido|final> <saida.mp4>
Escreve tambem <saida>.cortes.json com os instantes (s) de cada limite de cena (inicio do dissolve),
usado por cortar_stories.py. Variaveis de ambiente: HW=1 (VAAPI, so p/ rascunho), REUSE=1 (reaproveita segmentos)."""
import subprocess, sys, os, json
from PIL import Image, ImageDraw, ImageFont

cfg = json.load(open(sys.argv[1]))
modo, saida = sys.argv[2], os.path.abspath(sys.argv[3])
ROOT = cfg["pasta"]
os.chdir(ROOT)
R = modo == "rapido"
W, H = (540, 960) if R else (1080, 1920)
K = W / 1080
T = os.path.abspath(cfg.get("tmp", "saida/_tmp")) + f"_{modo}"
os.makedirs(T, exist_ok=True)
N = "/usr/share/fonts/truetype/noto/"
SERIF_I = N + "NotoSerifDisplay-Italic.ttf"
SANS = N + "NotoSansDisplay-Regular.ttf"
TIT = cfg.get("titulo", {"nome": "", "marca": "", "local": ""})
TM = ("libplacebo=tonemapping=bt.2390:gamut_mode=perceptual:contrast_recovery=0.3:colorspace=bt709:"
      "color_primaries=bt709:color_trc=bt709:range=tv:format=yuv420p,eq=saturation=1.1")
XF = 0.5
HW = bool(os.environ.get("HW"))
HWUP = "format=nv12,hwupload" if HW else "null"
VA_IN = ["-vaapi_device", "/dev/dri/renderD128"] if HW else []
VA_DEC = ["-hwaccel", "vaapi", "-hwaccel_device", "/dev/dri/renderD128"] if HW else []

scenes = [(s["src"], s["ss"], s["d"], s.get("cap", "")) for s in cfg["cenas"]]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print("ERRO", " ".join(cmd)[:200], r.stderr[-600:], flush=True); sys.exit(1)

def is_hdr(p):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=color_transfer", "-of", "csv=p=0", p], capture_output=True, text=True).stdout
    return o.strip().startswith("smpte2084")

def card_png(path, text, d):
    """Cartao claro D, desenhado em 1080x1920 e reduzido."""
    S = 1080
    im = Image.new("RGBA", (S, 1920), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    BR = (74, 52, 38, 255); BR2 = (122, 92, 70, 255)
    if text == "@TITLE":
        f1 = ImageFont.truetype(SERIF_I, 130); f2 = ImageFont.truetype(SANS, 34); f3 = ImageFont.truetype(SERIF_I, 42)
        def tw(t, f, sp=0): return sum(dr.textlength(c, font=f) for c in t) + sp * (len(t) - 1)
        box = [140, 1390, S - 140, 1730]
        dr.rounded_rectangle(box, radius=28, fill=(255, 250, 241, 222))
        def put(t, f, y, col, sp=0, dx=0):
            x = (S - tw(t, f, sp)) / 2 + dx
            for c in t:
                dr.text((x, y), c, font=f, fill=col); x += dr.textlength(c, font=f) + sp
        put(TIT["nome"], f1, 1426, BR)
        put(TIT["marca"].upper(), f2, 1590, BR2, 9)
        t3 = TIT["local"]; w3 = tw(t3, f3, 1); pin = 34
        x3 = (S - (w3 + pin)) / 2 + pin
        y3 = 1644
        for c in t3:
            dr.text((x3, y3), c, font=f3, fill=BR2); x3 += dr.textlength(c, font=f3) + 1
        cx = (S - (w3 + pin)) / 2 + 12; cy = y3 + 24; r = 11
        dr.polygon([(cx - r * .85, cy + r * .6), (cx + r * .85, cy + r * .6), (cx, cy + r * 2.3)], fill=BR2)
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BR2)
        dr.ellipse([cx - r * .42, cy - r * .42, cx + r * .42, cy + r * .42], fill=(255, 250, 241, 255))
    else:
        sz = 70
        ls = text.split("\n")
        while True:
            f = ImageFont.truetype(SERIF_I, sz)
            ws = [dr.textlength(l, font=f) for l in ls]
            if max(ws) + 130 <= 900 or sz <= 52: break
            sz -= 2
        bw = max(ws) + 130; bh = len(ls) * 84 + 56
        cy = 1570
        box = [(S - bw) / 2, cy - bh / 2, (S + bw) / 2, cy + bh / 2]
        dr.rounded_rectangle(box, radius=28, fill=(255, 250, 241, 222))
        y = box[1] + 28
        for l, w in zip(ls, ws):
            dr.text(((S - w) / 2, y), l, font=f, fill=BR); y += 84
    if W != S:
        im = im.resize((W, H), Image.LANCZOS)
    im.save(path)

segs = []
for i, (src, ss, d, txt) in enumerate(scenes):
    out = f"{T}/s{i:02d}.mp4"
    segs.append((out, d))
    L = d + (XF if i < len(scenes) - 1 else 0)
    if os.path.exists(out) and os.environ.get("REUSE"):
        continue
    hdr = is_hdr(src)
    pre = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=bicubic," + TM + ",") if hdr else ""
    fit = (f"split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
           f"boxblur=luma_radius={int(40*K)}:luma_power=2,eq=brightness=-0.05[bg];"
           f"[b]scale={W}:{H}:force_original_aspect_ratio=decrease:flags=bicubic[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,fps=30,format=yuv420p")
    enc = ["-preset", "ultrafast", "-crf", "27"] if R else ["-preset", "fast", "-crf", "16"]
    codec = ["-c:v", "h264_vaapi", "-qp", "27" if R else "17"] if HW else ["-c:v", "libx264"] + enc
    pixf = [] if HW else ["-pix_fmt", "yuv420p"]
    inp = VA_DEC + ["-ss", f"{ss}", "-t", f"{L}", "-i", src]
    if txt:
        png = f"{T}/cap{i:02d}.png"; card_png(png, txt, d)
        fc = (f"[0:v]{pre}{fit}[b];[1:v]format=rgba,fade=t=in:st=0.4:d=0.6:alpha=1,fade=t=out:st={d-0.9}:d=0.5:alpha=1[t];"
              f"[b][t]overlay=0:0:format=auto,format=yuv420p,{HWUP}[o]")
        run(["ffmpeg", "-v", "error", "-y", "-threads", "2"] + VA_IN + inp + ["-loop", "1", "-t", f"{L}", "-i", png,
             "-filter_complex", fc, "-map", "[o]", "-r", "30", "-an"] + codec + pixf + [out])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-threads", "2"] + VA_IN + inp + ["-vf", pre + fit + "," + HWUP, "-r", "30", "-an"] + codec + pixf + [out])
    print("cena", i, "hdr" if hdr else "", flush=True)

def xchain(files, durs):
    """durs = parte visivel de cada arquivo; cada arquivo tem +XF de cauda (menos o ultimo)."""
    ins = []; fc = ""; prev = "[0:v]"; acc = durs[0]
    for f in files: ins += ["-i", f]
    for k in range(1, len(files)):
        lab = f"[x{k}]"
        fc += f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={acc:.3f}{lab};"
        prev = lab; acc += durs[k]
    return ins, fc.rstrip(";"), prev, acc

CH = 6
chunks = []
for c in range(0, len(segs), CH):
    part = segs[c:c + CH]; files = [o for o, _ in part]; durs = [d for _, d in part]
    if len(files) == 1:
        chunks.append((files[0], durs[0])); continue
    outc = f"{T}/chunk{c//CH:02d}.mp4"
    ins, fc, prev, tot = xchain(files, durs)
    crf = "12" if not R else "27"
    if HW:
        fc += f";{prev}{HWUP}[hw]"; prev = "[hw]"
        cod = ["-c:v", "h264_vaapi", "-qp", "27" if R else "13"]
    else:
        cod = ["-c:v", "libx264", "-preset", "ultrafast" if R else "fast", "-crf", crf, "-pix_fmt", "yuv420p"]
    run(["ffmpeg", "-v", "error", "-y", "-threads", "2", "-filter_complex_threads", "1"] + VA_IN + ins +
        ["-filter_complex", fc, "-map", prev] + cod + ["-r", "30", outc])
    chunks.append((outc, tot))
files = [o for o, _ in chunks]; durs = [d for _, d in chunks]
ins, fc, prev, tot = xchain(files, durs)
if not fc:
    fc = '[0:v]null[x0]'; prev = '[x0]'
enc = ["-preset", "ultrafast", "-crf", "27"] if R else ["-preset", "slow", "-crf", "17"]
if HW:
    fc += f";{prev}{HWUP}[hw]"; prev = "[hw]"
    cod = ["-c:v", "h264_vaapi", "-qp", "27" if R else "17"]
else:
    cod = ["-c:v", "libx264"] + enc + ["-pix_fmt", "yuv420p"]
run(["ffmpeg", "-v", "error", "-y", "-threads", "2", "-filter_complex_threads", "1"] + VA_IN + ins +
    ["-filter_complex", fc, "-map", prev] + cod + ["-r", "30", "-movflags", "+faststart", saida])
print("duracao", round(tot, 2), flush=True)
b = []; acc = 0.0
for _, d in segs[:-1]:
    acc += d; b.append(round(acc, 3))
json.dump({"duracao": round(tot, 3), "limites": b}, open(saida + ".cortes.json", "w"))
