#!/usr/bin/env python3
"""Identidad visual del canal (versión final) sobre ilustraciones generadas para el vídeo 09:
  canal/avatar_800x800.png       foto de perfil (YouTube la recorta en círculo y la muestra a 98 px)
  canal/banner_2560x1440.jpg     banner (texto dentro de la zona segura de 1546x423)
  canal/banner_guia_zona_segura.jpg
  canal/marca_agua_150x150.png   marca de agua para los vídeos (Studio > Personalización > Marca)
  canal/vista_previa.jpg         cómo se ve todo junto
Uso: python3 canal_arte.py [ruta/a/fondo.png]   (por defecto 09-.../escenas/E06.png)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "canal"
NEGRA = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
ROSA, TURQ, NAR, AMA, TINTA = (255, 46, 136), (25, 227, 208), (255, 122, 26), (255, 210, 63), (14, 6, 34)


def glow(img, dibujar, radio=18, veces=2):
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0)); dibujar(ImageDraw.Draw(capa))
    g = capa.filter(ImageFilter.GaussianBlur(radio))
    for _ in range(veces): img.alpha_composite(g)
    img.alpha_composite(capa)


def oscurecer(img, alfa):
    return Image.blend(img, Image.new("RGB", img.size, TINTA), alfa)


def lupa(img, cx, cy, r, grosor, texto=True):
    """Lupa de neón (lente + mango) con «EL» dentro: el sello del canal."""
    import math
    ang = math.radians(45)
    x1, y1 = cx + (r + grosor * 0.2) * math.cos(ang), cy + (r + grosor * 0.2) * math.sin(ang)
    x2, y2 = cx + r * 1.85 * math.cos(ang), cy + r * 1.85 * math.sin(ang)
    def mango(d, col, w): d.line([(x1, y1), (x2, y2)], fill=col, width=w)
    glow(img, lambda d: mango(d, NAR + (255,), int(grosor * 1.7)), radio=grosor)
    ImageDraw.Draw(img).line([(x1, y1), (x2, y2)], fill=(255, 190, 120), width=int(grosor * 0.6))
    # lente oscura translúcida
    lente = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lente).ellipse([cx - r, cy - r, cx + r, cy + r], fill=TINTA + (150,)); img.alpha_composite(lente)
    glow(img, lambda d: d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=TURQ + (255,), width=grosor), radio=grosor)
    if texto:
        f = ImageFont.truetype(NEGRA, int(r * 0.92))
        pos = (cx, cy + r * 0.02)
        glow(img, lambda d: d.text(pos, "EL", font=f, fill=ROSA + (255,), anchor="mm"), radio=int(r * 0.12))
        ImageDraw.Draw(img).text(pos, "EL", font=f, fill=(255, 255, 255), anchor="mm",
                                 stroke_width=max(4, int(r * 0.05)), stroke_fill=ROSA)


def avatar(fondo):
    S = 800
    w, h = fondo.size; lado = h
    base = fondo.crop(((w - lado) // 2 + int(w * 0.08), 0, (w - lado) // 2 + int(w * 0.08) + lado, lado)).resize((S, S))
    img = oscurecer(base, 0.45).convert("RGBA")
    lupa(img, S * 0.45, S * 0.45, int(S * 0.27), 26)
    img.convert("RGB").save(OUT / "avatar_800x800.png")
    return img


def marca_agua():
    S = 600
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    lupa(img, S * 0.43, S * 0.43, int(S * 0.29), 30)
    img.resize((150, 150), Image.LANCZOS).save(OUT / "marca_agua_150x150.png")


def banner(fondo):
    W, H = 2560, 1440
    img = fondo.resize((W, int(fondo.height * W / fondo.width)))
    img = img.crop((0, (img.height - H) // 2, W, (img.height - H) // 2 + H)) if img.height >= H else img.resize((W, H))
    # banda oscura en la zona segura para que el texto se lea
    banda = Image.new("L", (W, H), 0); ImageDraw.Draw(banda).rectangle([0, H // 2 - 300, W, H // 2 + 300], fill=190)
    img = Image.composite(Image.new("RGB", (W, H), TINTA), img, banda.filter(ImageFilter.GaussianBlur(120))).convert("RGBA")
    sx0, sy0 = (W - 1546) // 2, (H - 423) // 2
    # sello a la izquierda dentro de la zona segura
    lupa(img, sx0 + 170, sy0 + 190, 128, 16)
    f1 = ImageFont.truetype(NEGRA, 150); f2 = ImageFont.truetype(BOLD, 50); f3 = ImageFont.truetype(NEGRA, 40)
    tx = sx0 + 420
    glow(img, lambda d: d.text((tx, sy0 + 130), "EXPEDIENTE", font=f1, fill=(255, 255, 255, 255), anchor="lm"), radio=16, veces=1)
    ImageDraw.Draw(img).text((tx, sy0 + 130), "EXPEDIENTE", font=f1, fill=(255, 255, 255), anchor="lm", stroke_width=5, stroke_fill=TINTA)
    glow(img, lambda d: d.text((tx, sy0 + 270), "LEONIDA", font=f1, fill=ROSA + (255,), anchor="lm"), radio=20)
    ImageDraw.Draw(img).text((tx, sy0 + 270), "LEONIDA", font=f1, fill=ROSA, anchor="lm", stroke_width=5, stroke_fill=TINTA)
    d = ImageDraw.Draw(img)
    sub = "GTA 6 en español · lo confirmado y la teoría, por separado"; tam = 50
    while f2.getbbox(sub)[2] > sx0 + 1546 - tx - 10:
        tam -= 2; f2 = ImageFont.truetype(BOLD, tam)
    d.text((tx + 4, sy0 + 380), sub, font=f2, fill=TURQ, anchor="lm", stroke_width=3, stroke_fill=TINTA)
    # cinta «cada semana» arriba a la derecha de la zona segura
    t = "VÍDEO NUEVO CADA SEMANA"; bb = f3.getbbox(t)
    x1 = sx0 + 1546; d.rounded_rectangle([x1 - bb[2] - 50, sy0 + 6, x1, sy0 + 62], radius=14, fill=AMA)
    d.text((x1 - 25, sy0 + 34), t, font=f3, fill=TINTA, anchor="rm")
    out = img.convert("RGB"); out.save(OUT / "banner_2560x1440.jpg", quality=92)
    guia = out.copy(); dg = ImageDraw.Draw(guia)
    dg.rectangle([sx0, sy0, sx0 + 1546, sy0 + 423], outline=(0, 255, 0), width=6)
    dg.rectangle([0, (H - 423) // 2, W - 1, (H + 423) // 2], outline=(255, 255, 0), width=3)
    guia.resize((1280, 720)).save(OUT / "banner_guia_zona_segura.jpg")
    return out


def vista_previa(ban, ava):
    """Simulación de la cabecera del canal en escritorio: banner recortado + avatar redondo + nombre."""
    W = 1600
    hb = int(W * 423 / 2560)
    franja = ban.crop((0, (1440 - 423) // 2, 2560, (1440 + 423) // 2)).resize((W, hb))
    img = Image.new("RGB", (W, hb + 300), (15, 15, 15)); img.paste(franja, (0, 0))
    a = ava.convert("RGB").resize((180, 180)); m = Image.new("L", (180, 180), 0); ImageDraw.Draw(m).ellipse([0, 0, 179, 179], fill=255)
    img.paste(a, (60, hb + 50), m)
    d = ImageDraw.Draw(img)
    d.text((270, hb + 85), "Expediente Leonida", font=ImageFont.truetype(BOLD, 56), fill=(241, 241, 241))
    d.text((272, hb + 160), "@ExpedienteLeonida · GTA 6 en español", font=ImageFont.truetype(BOLD, 28), fill=(170, 170, 170))
    for i, s in enumerate([98, 48, 24]):  # tamaños reales del avatar en YouTube
        p = ava.convert("RGB").resize((s, s), Image.LANCZOS); mk = Image.new("L", (s, s), 0); ImageDraw.Draw(mk).ellipse([0, 0, s - 1, s - 1], fill=255)
        img.paste(p, (W - 380 + i * 130, hb + 80 + (98 - s) // 2), mk)
    img.save(OUT / "vista_previa.jpg")


if __name__ == "__main__":
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "09-antes-de-jugar-212gb-ediciones" / "escenas" / "E06.png"
    fondo = Image.open(ruta).convert("RGB")
    ava = avatar(fondo); marca_agua(); ban = banner(fondo); vista_previa(ban, ava)
    print("canal: avatar, banner, guía, marca de agua y vista previa en", OUT)
