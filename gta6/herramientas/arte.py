#!/usr/bin/env python3
"""Genera miniaturas (1280x720), logo (800x800) y banner (2560x1440) con el estilo del canal.

Las miniaturas se pueden regenerar sobre una imagen de fondo de Nano Banana:
  python3 arte.py miniaturas --fondo escenas/E01.png
Sin --fondo usa un atardecer neón procedural (100 % original, sin material del juego).
"""
import json, math, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
FUENTE = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FUENTE_MED = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
CANAL = "EXPEDIENTE LEONIDA"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def atardecer(w, h, semilla=0, sol_x=0.68):
    rnd = random.Random(semilla)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    stops = [(0.0, (18, 6, 48)), (0.35, (120, 20, 110)), (0.58, (255, 70, 120)), (0.72, (255, 150, 60)), (1.0, (255, 196, 90))]
    horizonte = int(h * 0.70)
    for y in range(horizonte):
        t = y / horizonte
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                c = lerp(stops[i][1], stops[i + 1][1], (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0]))
        d.line([(0, y), (w, y)], fill=c)
    # sol con franjas
    r = int(h * 0.30); cx, cy = int(w * sol_x), horizonte - int(r * 0.35)
    sol = Image.new("L", (w, h), 0); ds = ImageDraw.Draw(sol)
    ds.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    for k in range(7):
        yy = cy + int(r * (0.05 + k * 0.13)); hh = 3 + k * 3
        ds.rectangle([cx - r, yy, cx + r, yy + hh], fill=0)
    capa_sol = Image.new("RGB", (w, h))
    dsol = ImageDraw.Draw(capa_sol)
    for y in range(cy - r, cy + r):
        t = (y - (cy - r)) / (2 * r)
        dsol.line([(cx - r, y), (cx + r, y)], fill=lerp((255, 236, 120), (255, 60, 140), t))
    halo = sol.filter(ImageFilter.GaussianBlur(h * 0.06))
    img = Image.composite(Image.new("RGB", (w, h), (255, 120, 160)), img, halo.point(lambda v: v // 3))
    img.paste(capa_sol, (0, 0), sol)
    d = ImageDraw.Draw(img)
    # skyline
    x = 0
    while x < w:
        bw = rnd.randint(int(w * 0.02), int(w * 0.06)); bh = rnd.randint(int(h * 0.05), int(h * 0.30))
        if abs(x - cx) < r * 0.6: bh = int(bh * 0.5)
        d.rectangle([x, horizonte - bh, x + bw, horizonte], fill=(28, 10, 52))
        for wy in range(horizonte - bh + 8, horizonte - 6, 14):
            for wx in range(x + 5, x + bw - 5, 11):
                if rnd.random() < 0.18:
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=rnd.choice([(255, 60, 160), (40, 230, 220), (255, 200, 90)]))
        x += bw + rnd.randint(0, 6)
    # agua con reflejo
    for y in range(horizonte, h):
        t = (y - horizonte) / (h - horizonte)
        d.line([(0, y), (w, y)], fill=lerp((60, 14, 80), (8, 6, 26), t))
    for k in range(40):
        yy = horizonte + int((h - horizonte) * (k / 40) ** 1.3)
        ww = int(r * (1.2 - k / 50)) * rnd.uniform(0.6, 1.0)
        d.line([(cx - ww, yy), (cx + ww, yy)], fill=(255, 120, 150), width=2)
    # palmeras
    def palmera(px, base, alto, lado):
        tronco = [(px + math.sin(t / 10) * alto * 0.12 * lado, base - alto * t / 10) for t in range(11)]
        d.line(tronco, fill=(10, 4, 20), width=max(6, int(alto * 0.045)))
        tx, ty = tronco[-1]
        for a in range(0, 360, 40):
            ang = math.radians(a + rnd.randint(-10, 10))
            pts = [(tx + math.cos(ang) * alto * 0.38 * s, ty + math.sin(ang) * alto * 0.20 * s + (alto * 0.12 * s * s)) for s in [i / 6 for i in range(7)]]
            d.line(pts, fill=(10, 4, 20), width=max(5, int(alto * 0.03)))
    palmera(int(w * 0.05), h, int(h * 0.85), 1)
    palmera(int(w * 0.95), h, int(h * 0.75), -1)
    return img


def texto_neon(img, lineas, acento, zona=(0.05, 0.10, 0.62, 0.92)):
    w, h = img.size
    x0, y0, x1, y1 = int(w * zona[0]), int(h * zona[1]), int(w * zona[2]), int(h * zona[3])
    # oscurecer zona de texto para contraste
    sombra = Image.new("L", (w, h), 0); ImageDraw.Draw(sombra).rectangle([0, 0, x1 + 40, h], fill=150)
    sombra = sombra.filter(ImageFilter.GaussianBlur(80))
    img = Image.composite(Image.new("RGB", (w, h), (8, 4, 20)), img, sombra)
    tam = []
    alto_disp = (y1 - y0) / len(lineas)
    for ln in lineas:
        s = int(alto_disp * 0.95)
        while s > 20:
            f = ImageFont.truetype(FUENTE, s)
            bb = f.getbbox(ln)
            if bb[2] - bb[0] <= (x1 - x0) and bb[3] - bb[1] <= alto_disp * 0.88: break
            s -= 4
        tam.append((ln, f))
    total = sum(f.getbbox(ln)[3] for ln, f in tam)
    y = y0 + ((y1 - y0) - total) // 2
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
    posiciones = []
    for i, (ln, f) in enumerate(tam):
        posiciones.append((x0, y - f.getbbox(ln)[1], ln, f, (255, 255, 255) if i == 0 else acento))
        y += f.getbbox(ln)[3] - f.getbbox(ln)[1] + int(h * 0.025)
    for x, yy, ln, f, col in posiciones:
        dc.text((x, yy), ln, font=f, fill=col + (255,) if isinstance(col, tuple) else col, stroke_width=0)
    glow = capa.filter(ImageFilter.GaussianBlur(18))
    img = img.convert("RGBA"); img.alpha_composite(glow); img.alpha_composite(glow)
    borde = Image.new("RGBA", (w, h), (0, 0, 0, 0)); db = ImageDraw.Draw(borde)
    for x, yy, ln, f, col in posiciones:
        db.text((x + 6, yy + 8), ln, font=f, fill=(0, 0, 0, 200))
    img.alpha_composite(borde.filter(ImageFilter.GaussianBlur(3)))
    for x, yy, ln, f, col in posiciones:
        ImageDraw.Draw(img).text((x, yy), ln, font=f, fill=col, stroke_width=max(3, f.size // 28), stroke_fill=(10, 4, 24))
    return img.convert("RGB")


def hex2rgb(hx):
    return tuple(int(hx[i:i + 2], 16) for i in (1, 3, 5))


def _glow_texto(img, pos, txt, f, col, borde=(10, 4, 24), glow=16):
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(capa).text(pos, txt, font=f, fill=col + (255,))
    g = capa.filter(ImageFilter.GaussianBlur(glow)); img.alpha_composite(g); img.alpha_composite(g)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).text((pos[0] + 5, pos[1] + 7), txt, font=f, fill=(0, 0, 0, 210))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
    ImageDraw.Draw(img).text(pos, txt, font=f, fill=col, stroke_width=max(3, f.size // 26), stroke_fill=borde)


def miniatura_guia(base, m):
    """Diseño de «guía»: etiqueta del juego, cifra grande con barra, subtítulo y casillas con los temas."""
    W, H = 1280, 720
    dx = m.get("fondo_x", 0)  # desplaza el fondo a la derecha para que lo importante no quede bajo el texto
    if dx:
        esc = base.resize((W + dx // 2, H + dx // 2 * H // W))
        lienzo = base.resize((W, H)).filter(ImageFilter.GaussianBlur(30))
        mk = Image.new("L", esc.size, 0); ImageDraw.Draw(mk).rectangle([60, 0, esc.width, esc.height], fill=255)
        lienzo.paste(esc, (dx, (H - esc.height) // 2), mk.filter(ImageFilter.GaussianBlur(40))); base = lienzo
    img = base.convert("RGBA")
    # degradado oscuro a la izquierda para que el texto se lea
    grad = Image.new("L", (W, H), 0); dg = ImageDraw.Draw(grad)
    for x in range(W):
        dg.line([(x, 0), (x, H)], fill=int(235 * max(0.0, min(1.0, (820 - x) / 520))))
    img = Image.composite(Image.new("RGBA", (W, H), (8, 4, 22, 255)), img, grad)
    d = ImageDraw.Draw(img)
    acento = hex2rgb(m["acento"]); rosa, turq = (255, 46, 136), (25, 227, 208)
    x0 = 56
    # etiqueta del juego
    fe = ImageFont.truetype(FUENTE, 50); t = m.get("etiqueta", "")
    if t:
        bb = fe.getbbox(t); d.rounded_rectangle([x0, 40, x0 + bb[2] + 44, 40 + 74], radius=16, fill=rosa)
        d.text((x0 + 22, 40 + 37), t, font=fe, fill=(255, 255, 255), anchor="lm")
    # cifra grande
    f1 = ImageFont.truetype(FUENTE, 210)
    _glow_texto(img, (x0 - 6, 118), m["linea1"], f1, (255, 255, 255))
    # barra de almacenamiento
    by, bw, bh = 352, 600, 40; llen = m.get("barra", 0.88)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).rounded_rectangle([x0, by, x0 + bw, by + bh], radius=20, outline=turq + (255,), width=6)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, by, x0 + bw, by + bh], radius=20, fill=(20, 10, 40), outline=turq, width=4)
    relleno = Image.new("RGBA", (int(bw * llen), bh - 12)); dr = ImageDraw.Draw(relleno)
    for x in range(relleno.width):
        dr.line([(x, 0), (x, relleno.height)], fill=lerp(rosa, (255, 150, 40), x / relleno.width) + (255,))
    mk = Image.new("L", relleno.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0, 0, relleno.width - 1, relleno.height - 1], radius=14, fill=255)
    img.paste(relleno, (x0 + 6, by + 6), mk)
    # subtítulo
    f2 = ImageFont.truetype(FUENTE, 92)
    _glow_texto(img, (x0 - 2, 412), m["linea2"], f2, acento, glow=12)
    # casillas con los temas
    d = ImageDraw.Draw(img); fp = ImageFont.truetype(FUENTE, 36); x = x0; y = 560
    for p in m.get("puntos", []):
        bb = fp.getbbox(p); ancho = 62 + bb[2] + 24
        d.rounded_rectangle([x, y, x + ancho, y + 66], radius=14, fill=(10, 4, 24), outline=turq, width=3)
        d.rounded_rectangle([x + 14, y + 15, x + 50, y + 51], radius=7, fill=turq)
        d.line([(x + 21, y + 34), (x + 29, y + 43), (x + 44, y + 23)], fill=(10, 4, 24), width=6, joint="curve")
        d.text((x + 62, y + 34), p, font=fp, fill=(255, 255, 255), anchor="lm")
        x += ancho + 16
    # canal
    fc = ImageFont.truetype(FUENTE_MED, 24)
    bb = fc.getbbox(CANAL); d.rounded_rectangle([W - 40 - bb[2] - 36, 40, W - 40, 84], radius=10, fill=(10, 4, 24))
    d.text((W - 40 - 18, 62), CANAL, font=fc, fill=turq, anchor="rm")
    return img.convert("RGB")


def miniaturas(fondo=None):
    meta = json.loads((RAIZ / "herramientas" / "metadatos.json").read_text())
    for i, (carpeta, m) in enumerate(meta.items()):
        fondo_m = m["miniatura"].get("fondo", fondo)
        if fondo_m and (RAIZ / carpeta / fondo_m).exists():
            base = Image.open(RAIZ / carpeta / fondo_m).convert("RGB").resize((1280, 720))
        else:
            base = atardecer(1280, 720, semilla=i, sol_x=0.74)
        if "puntos" in m["miniatura"]:
            miniatura_guia(base, m["miniatura"]).save(RAIZ / carpeta / "miniatura.jpg", quality=92)
            print("miniatura", carpeta, "(guía)"); continue
        img = texto_neon(base, [m["miniatura"]["linea1"], m["miniatura"]["linea2"]], hex2rgb(m["miniatura"]["acento"]))
        d = ImageDraw.Draw(img)
        f = ImageFont.truetype(FUENTE_MED, 26)
        d.rounded_rectangle([1280 - 330, 24, 1280 - 24, 70], radius=10, fill=(10, 4, 24))
        d.text((1280 - 316, 33), "EXPEDIENTE LEONIDA", font=f, fill=(25, 227, 208))
        img.save(RAIZ / carpeta / "miniatura.jpg", quality=92)
        print("miniatura", carpeta)


def logo():
    w = h = 800
    img = Image.new("RGB", (w, h), (14, 6, 34)); d = ImageDraw.Draw(img)
    # sol de franjas dentro de un círculo
    sol = atardecer(w, h, semilla=7, sol_x=0.5)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).ellipse([40, 40, w - 40, h - 40], fill=255)
    img.paste(sol, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.ellipse([40, 40, w - 40, h - 40], outline=(25, 227, 208), width=14)
    f = ImageFont.truetype(FUENTE, 300)
    txt = "EL"
    bb = f.getbbox(txt)
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dc = ImageDraw.Draw(capa)
    pos = ((w - (bb[2] - bb[0])) // 2 - bb[0], (h - (bb[3] - bb[1])) // 2 - bb[1] - 20)
    dc.text(pos, txt, font=f, fill=(255, 255, 255, 255), stroke_width=12, stroke_fill=(255, 46, 136, 255))
    img = img.convert("RGBA"); img.alpha_composite(capa.filter(ImageFilter.GaussianBlur(14))); img.alpha_composite(capa)
    img.convert("RGB").save(RAIZ / "canal" / "logo_800x800.png")
    print("logo")


def banner():
    w, h = 2560, 1440
    img = atardecer(w, h, semilla=3, sol_x=0.5)
    # zona segura de YouTube: 1546x423 centrada
    sx0, sy0 = (w - 1546) // 2, (h - 423) // 2
    img = texto_neon(img, [CANAL], (255, 255, 255), zona=(sx0 / w, (sy0 + 10) / h, (sx0 + 1546) / w, (sy0 + 290) / h))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FUENTE_MED, 52)
    sub = "GTA 6 · DATOS CONFIRMADOS, TEORÍAS SEÑALADAS"
    bb = f.getbbox(sub)
    d.text(((w - (bb[2] - bb[0])) // 2, sy0 + 320), sub, font=f, fill=(25, 227, 208), stroke_width=3, stroke_fill=(10, 4, 24))
    img.save(RAIZ / "canal" / "banner_2560x1440.png")
    guia = img.copy(); dg = ImageDraw.Draw(guia)
    dg.rectangle([sx0, sy0, sx0 + 1546, sy0 + 423], outline=(0, 255, 0), width=4)
    dg.rectangle([(w - 2560) // 2, (h - 423) // 2, w, (h + 423) // 2], outline=(255, 255, 0), width=2)
    guia.resize((1280, 720)).save(RAIZ / "canal" / "banner_guia_zona_segura.png")
    print("banner")


if __name__ == "__main__":
    que = sys.argv[1] if len(sys.argv) > 1 else "todo"
    fondo = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--fondo" else None
    if que in ("todo", "miniaturas"): miniaturas(fondo)
    if que in ("todo", "logo"): logo()
    if que in ("todo", "banner"): banner()
