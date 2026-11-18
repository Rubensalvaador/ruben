#!/usr/bin/env python3
"""Generador PROCEDURAL de escenas (imágenes 1920x1080 y clips de 8 s) en el estilo del canal:
atardecer neón, ciudad costera, siluetas. 100 % original: sin modelos de IA, sin capturas, sin logos.

Cada prompt de escenas.json se traduce a un tipo de escena por palabras clave (playa, pantano,
puente, autopista, interior, cárcel, club, policía...) y se le añaden elementos (pareja en silueta,
luces de policía, lluvia, móviles...). Los clips animan las capas con paralaje y efectos.

Uso: python3 escenas_proc.py ../09-antes-de-jugar-212gb-ediciones [--solo E01] [--sin-clips]
"""
import json, math, random, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H = 1920, 1080
PAD = 160            # margen lateral para el paralaje
FPS, CLIP_SEG = 30, 8

PALETAS = {
    "atardecer": [(0, (16, 6, 46)), (.38, (110, 22, 112)), (.6, (255, 64, 120)), (.76, (255, 140, 60)), (1, (255, 200, 100))],
    "anochecer": [(0, (6, 4, 24)), (.5, (40, 14, 80)), (.8, (150, 30, 120)), (1, (255, 90, 120))],
    "noche":     [(0, (3, 3, 14)), (.6, (14, 8, 44)), (1, (60, 18, 90))],
    "amanecer":  [(0, (30, 40, 90)), (.5, (200, 110, 150)), (.8, (255, 170, 120)), (1, (255, 220, 160))],
}
NEON = [(255, 46, 136), (25, 227, 208), (255, 122, 26), (255, 210, 63), (170, 80, 255)]
TINTA = (12, 5, 26)


# ---------------------------------------------------------------- utilidades
def grad(w, h, stops, y0=0, y1=None):
    y1 = y1 or h
    t = np.clip((np.arange(h)[:, None] - y0) / max(1, y1 - y0), 0, 1)
    out = np.zeros((h, 1, 3))
    for i in range(len(stops) - 1):
        a, ca = stops[i]; b, cb = stops[i + 1]
        m = (t >= a) & (t <= b)
        k = np.where(m, (t - a) / max(1e-6, b - a), 0)
        out += m[..., None] * (np.array(ca) + (np.array(cb) - np.array(ca)) * k[..., None])
    return Image.fromarray(np.repeat(out, w, 1).clip(0, 255).astype("uint8"), "RGB")


def capa(w=W + 2 * PAD, h=H):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def glow(img, r=24, veces=2):
    g = img.filter(ImageFilter.GaussianBlur(r))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for _ in range(veces): out.alpha_composite(g)
    out.alpha_composite(img)
    return out


def mezcla(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


# ---------------------------------------------------------------- fondos
def cielo(rnd, paleta, horizonte, sol=True, sol_x=None, estrellas=False):
    w = W + 2 * PAD
    img = grad(w, H, PALETAS[paleta], 0, horizonte).convert("RGBA")
    d = ImageDraw.Draw(img)
    if estrellas or paleta == "noche":
        for _ in range(260):
            x, y = rnd.randrange(w), rnd.randrange(int(horizonte * 0.8))
            c = rnd.randint(120, 255); d.point((x, y), fill=(c, c, c, 255))
    if sol and paleta in ("atardecer", "anochecer", "amanecer"):
        r = int(H * rnd.uniform(0.17, 0.25)); cx = int(sol_x if sol_x is not None else w * rnd.uniform(0.35, 0.7)); cy = horizonte - int(r * 0.3)
        halo = capa(); dh = ImageDraw.Draw(halo)
        dh.ellipse([cx - r * 1.7, cy - r * 1.7, cx + r * 1.7, cy + r * 1.7], fill=(255, 110, 150, 90))
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(r * 0.6)))
        s = Image.new("L", (w, H), 0); ds = ImageDraw.Draw(s)
        ds.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        for k in range(7):
            yy = cy + int(r * (0.06 + k * 0.13)); ds.rectangle([cx - r, yy, cx + r, yy + 2 + k * 3], fill=0)
        sol_img = grad(w, H, [(0, (255, 240, 130)), (1, (255, 60, 140))], cy - r, cy + r)
        img.paste(sol_img, (0, 0), s)
    # bandas de nubes
    nub = capa(); dn = ImageDraw.Draw(nub)
    for _ in range(rnd.randint(3, 7)):
        y = rnd.randint(int(horizonte * 0.15), int(horizonte * 0.75)); x = rnd.randint(-200, w)
        dn.rounded_rectangle([x, y, x + rnd.randint(300, 900), y + rnd.randint(8, 22)], 10, fill=(255, 150, 190, rnd.randint(25, 70)))
    img.alpha_composite(nub.filter(ImageFilter.GaussianBlur(6)))
    return img


def skyline(rnd, base, alto_max, densidad=1.0, ventanas=True, color=TINTA):
    l = capa(); d = ImageDraw.Draw(l); x = -20
    while x < l.width:
        bw = rnd.randint(40, 130); bh = int(rnd.uniform(0.15, 1.0) ** 1.6 * alto_max) + 30
        d.rectangle([x, base - bh, x + bw, base], fill=color + (255,))
        if rnd.random() < .25: d.rectangle([x + bw // 2 - 3, base - bh - 40, x + bw // 2 + 3, base - bh], fill=color + (255,))
        if rnd.random() < .2:  # art déco escalonado
            d.rectangle([x + 10, base - bh - 18, x + bw - 10, base - bh], fill=color + (255,))
        if ventanas:
            for wy in range(base - bh + 10, base - 8, 16):
                for wx in range(x + 6, x + bw - 6, 13):
                    if rnd.random() < .16 * densidad:
                        d.rectangle([wx, wy, wx + 5, wy + 7], fill=rnd.choice(NEON) + (255,))
        x += bw + rnd.randint(-10, 8)
    return l


def agua(rnd, horizonte, color_ref=(255, 120, 160), fase=0.0):
    l = capa(); arr = np.zeros((H - horizonte, l.width, 4), "uint8")
    t = np.linspace(0, 1, H - horizonte)[:, None]
    arr[..., 0] = (60 * (1 - t) + 8 * t); arr[..., 1] = (16 * (1 - t) + 6 * t); arr[..., 2] = (84 * (1 - t) + 30 * t); arr[..., 3] = 255
    l.paste(Image.fromarray(arr, "RGBA"), (0, horizonte))
    d = ImageDraw.Draw(l); r2 = random.Random(7)
    cx = l.width * 0.5
    for k in range(60):
        yy = horizonte + int((H - horizonte) * (k / 60) ** 1.4) + 2
        ww = (380 - k * 4) * r2.uniform(.5, 1) * (1 + 0.15 * math.sin(fase * 6 + k))
        off = 40 * math.sin(fase * 3 + k * 0.7)
        if ww > 10: d.line([(cx - ww + off, yy), (cx + ww + off, yy)], fill=color_ref + (int(200 - k * 2.5),), width=2)
    return l


def suelo(horizonte, c1=(40, 14, 60), c2=(8, 4, 20)):
    l = capa(); g = grad(l.width, H - horizonte, [(0, c1), (1, c2)]).convert("RGBA"); l.paste(g, (0, horizonte)); return l


# ---------------------------------------------------------------- elementos
def palmera(d, x, base, alto, lado=1, color=TINTA):
    pts = [(x + math.sin(t / 10 * 1.4) * alto * .12 * lado, base - alto * t / 10) for t in range(11)]
    d.line(pts, fill=color + (255,), width=max(5, int(alto * .045)))
    tx, ty = pts[-1]
    for a in range(0, 360, 36):
        ang = math.radians(a + 7)
        hoja = [(tx + math.cos(ang) * alto * .36 * s, ty + math.sin(ang) * alto * .16 * s + alto * .14 * s * s) for s in [i / 7 for i in range(8)]]
        d.line(hoja, fill=color + (255,), width=max(4, int(alto * .028)))


def persona(d, x, base, alto, color=TINTA, pose=0):
    cab = alto * .12
    d.ellipse([x - cab / 2, base - alto, x + cab / 2, base - alto + cab], fill=color + (255,))
    hombro = base - alto + cab * 1.1
    d.polygon([(x - alto * .13, hombro), (x + alto * .13, hombro), (x + alto * .1, base - alto * .48), (x - alto * .1, base - alto * .48)], fill=color + (255,))
    d.polygon([(x - alto * .1, base - alto * .5), (x + alto * .1, base - alto * .5), (x + alto * .09 + pose * alto * .05, base), (x + alto * .02, base), (x, base - alto * .3), (x - alto * .02, base), (x - alto * .09, base)], fill=color + (255,))
    d.line([(x - alto * .13, hombro + 4), (x - alto * .16, base - alto * .45)], fill=color + (255,), width=int(alto * .05))
    d.line([(x + alto * .13, hombro + 4), (x + alto * .16 + pose * alto * .1, base - alto * .45 - pose * alto * .2)], fill=color + (255,), width=int(alto * .05))


def coche(d, x, base, largo, color=TINTA, luces=True, frente=1):
    h = largo * .28
    d.rounded_rectangle([x, base - h * .55, x + largo, base - h * .1], 12, fill=color + (255,))
    d.polygon([(x + largo * .22, base - h * .55), (x + largo * .35, base - h), (x + largo * .68, base - h), (x + largo * .8, base - h * .55)], fill=color + (255,))
    for cx in (x + largo * .2, x + largo * .8):
        d.ellipse([cx - h * .22, base - h * .32, cx + h * .22, base + h * .12], fill=(4, 2, 10, 255))
    if luces:
        fx = x + largo - 6 if frente > 0 else x + 2
        d.rectangle([fx - 4, base - h * .45, fx + 4, base - h * .32], fill=(255, 230, 160, 255))
        bx = x + 2 if frente > 0 else x + largo - 6
        d.rectangle([bx, base - h * .45, bx + 6, base - h * .32], fill=(255, 30, 60, 255))
    d.line([(x + 10, base - h * .5), (x + largo - 10, base - h * .5)], fill=(255, 120, 200, 140), width=2)


def barco(d, x, base, largo, color=TINTA, yate=False):
    d.polygon([(x, base - largo * .08), (x + largo, base - largo * .08), (x + largo * .88, base), (x + largo * .08, base)], fill=color + (255,))
    d.rectangle([x + largo * .3, base - largo * (.2 if yate else .15), x + largo * .7, base - largo * .08], fill=color + (255,))
    if yate:
        d.rectangle([x + largo * .38, base - largo * .28, x + largo * .62, base - largo * .2], fill=color + (255,))
        for k in range(8): d.ellipse([x + largo * (.32 + k * .05), base - largo * .15, x + largo * (.32 + k * .05) + 6, base - largo * .15 + 6], fill=NEON[k % 4] + (255,))


def aerodeslizador(d, x, base, largo, color=TINTA):
    d.polygon([(x, base - 12), (x + largo, base - 12), (x + largo * .95, base), (x + 5, base)], fill=color + (255,))
    r = largo * .22; cx = x + largo * .18
    d.ellipse([cx - r * .4, base - 12 - r * 1.6, cx + r * .4, base - 12], outline=color + (255,), width=6)
    d.rectangle([cx + 4, base - 12 - r, cx + 14, base - 12], fill=color + (255,))
    persona(d, x + largo * .55, base - 12, largo * .35)


def caiman(d, x, base, largo, color=TINTA, ojos=True):
    d.polygon([(x, base), (x + largo * .15, base - 10), (x + largo * .8, base - 14), (x + largo, base - 4), (x + largo * .8, base)], fill=color + (255,))
    for k in range(9): d.polygon([(x + largo * (.2 + k * .07), base - 12), (x + largo * (.235 + k * .07), base - 22), (x + largo * (.27 + k * .07), base - 12)], fill=color + (255,))
    if ojos: d.ellipse([x + largo * .86, base - 18, x + largo * .86 + 8, base - 10], fill=(255, 210, 63, 255))


def cipres(d, x, base, alto, color=TINTA):
    d.polygon([(x - 8, base), (x - 3, base - alto), (x + 3, base - alto), (x + 8, base)], fill=color + (255,))
    for k in range(6):
        y = base - alto + k * alto * .12; w = alto * (.12 + k * .03)
        d.ellipse([x - w, y - 10, x + w, y + 14], fill=color + (255,))


def pino(d, x, base, alto, color=TINTA):
    for k in range(5):
        y = base - alto + k * alto * .18; w = alto * (.08 + k * .06)
        d.polygon([(x, y - alto * .12), (x - w, y + alto * .14), (x + w, y + alto * .14)], fill=color + (255,))
    d.rectangle([x - 4, base - alto * .1, x + 4, base], fill=color + (255,))


def cartel_neon(l, x, y, w, h, color, forma="rect"):
    c = capa(); d = ImageDraw.Draw(c)
    if forma == "rect": d.rounded_rectangle([x, y, x + w, y + h], 14, outline=color + (255,), width=6)
    elif forma == "flecha": d.line([(x, y + h / 2), (x + w, y + h / 2), (x + w * .8, y), (x + w, y + h / 2), (x + w * .8, y + h)], fill=color + (255,), width=7)
    elif forma == "circulo": d.ellipse([x, y, x + w, y + w], outline=color + (255,), width=7)
    elif forma == "estrella":
        pts = [(x + w / 2 + math.cos(math.radians(-90 + i * 36)) * (w / 2 if i % 2 == 0 else w / 5), y + w / 2 + math.sin(math.radians(-90 + i * 36)) * (w / 2 if i % 2 == 0 else w / 5)) for i in range(11)]
        d.line(pts, fill=color + (255,), width=6)
    elif forma == "corazon":
        d.arc([x, y, x + w / 2, y + w / 2], 150, 360, fill=color + (255,), width=6); d.arc([x + w / 2, y, x + w, y + w / 2], 180, 30, fill=color + (255,), width=6)
        d.line([(x + w * .04, y + w * .35), (x + w / 2, y + w * .9), (x + w * .96, y + w * .35)], fill=color + (255,), width=6)
    l.alpha_composite(glow(c, 16, 2))



# ---------------------------------------------------------------- objetos en neón (sujeto principal de la escena)
def objeto(l, nombre, cx, cy, esc, color):
    d = ImageDraw.Draw(l); c = color + (255,); w = int(8 * esc / 100) + 4; S = esc
    if nombre == "consola":
        d.rounded_rectangle([cx - S * .5, cy - S * 1.2, cx + S * .5, cy + S * 1.2], int(S * .2), outline=c, width=w)
        d.line([(cx, cy - S * 1.1), (cx, cy + S * 1.1)], fill=c, width=max(2, w // 2))
    elif nombre == "mando":
        d.rounded_rectangle([cx - S * 1.2, cy - S * .5, cx + S * 1.2, cy + S * .4], int(S * .4), outline=c, width=w)
        d.ellipse([cx - S * 1.1, cy - S * .1, cx - S * .5, cy + S * .9], outline=c, width=w); d.ellipse([cx + S * .5, cy - S * .1, cx + S * 1.1, cy + S * .9], outline=c, width=w)
        d.line([(cx - S * .85, cy - S * .25), (cx - S * .85, cy + S * .05)], fill=c, width=w); d.line([(cx - S, cy - S * .1), (cx - S * .7, cy - S * .1)], fill=c, width=w)
        for dx, dy in ((.75, -.25), (.95, -.1), (.75, .05), (.55, -.1)): d.ellipse([cx + S * dx - 8, cy + S * dy - 8, cx + S * dx + 8, cy + S * dy + 8], outline=c, width=4)
    elif nombre == "disco":
        d.rounded_rectangle([cx - S * 1.4, cy - S * .35, cx + S * 1.4, cy + S * .35], 12, outline=c, width=w)
        for k in range(6): d.rectangle([cx - S * 1.1 + k * S * .3, cy - S * .15, cx - S * .95 + k * S * .3, cy + S * .15], outline=c, width=3)
    elif nombre == "reloj":
        d.ellipse([cx - S, cy - S, cx + S, cy + S], outline=c, width=w)
        for a in range(0, 360, 30): d.line([(cx + math.cos(math.radians(a)) * S * .82, cy + math.sin(math.radians(a)) * S * .82), (cx + math.cos(math.radians(a)) * S * .92, cy + math.sin(math.radians(a)) * S * .92)], fill=c, width=4)
        d.line([(cx, cy), (cx, cy - S * .7)], fill=c, width=w); d.line([(cx, cy), (cx - S * .1, cy - S * .5)], fill=c, width=w)
    elif nombre == "calendario":
        d.rounded_rectangle([cx - S, cy - S, cx + S, cy + S], 14, outline=c, width=w); d.line([(cx - S, cy - S * .55), (cx + S, cy - S * .55)], fill=c, width=w)
        for i in range(4):
            for j in range(3): d.rectangle([cx - S * .8 + i * S * .42, cy - S * .35 + j * S * .42, cx - S * .55 + i * S * .42, cy - S * .12 + j * S * .42], outline=c, width=3)
        d.ellipse([cx + S * .2 - 10, cy + S * .38, cx + S * .6, cy + S * .88], outline=NEON[0] + (255,), width=6)
    elif nombre == "precio":
        d.polygon([(cx - S * 1.2, cy - S * .5), (cx + S * .6, cy - S * .5), (cx + S * 1.2, cy), (cx + S * .6, cy + S * .5), (cx - S * 1.2, cy + S * .5)], outline=c, width=w)
        d.ellipse([cx + S * .45, cy - 12, cx + S * .45 + 24, cy + 12], outline=c, width=5)
        for k in range(3): d.line([(cx - S * .95, cy - S * .2 + k * S * .2), (cx + S * (.2 - k * .2), cy - S * .2 + k * S * .2)], fill=c, width=6)
    elif nombre == "movil":
        d.rounded_rectangle([cx - S * .55, cy - S, cx + S * .55, cy + S], int(S * .15), outline=c, width=w); d.line([(cx - S * .15, cy - S * .85), (cx + S * .15, cy - S * .85)], fill=c, width=5)
    elif nombre == "candado":
        d.rounded_rectangle([cx - S * .8, cy - S * .2, cx + S * .8, cy + S], 14, outline=c, width=w); d.arc([cx - S * .55, cy - S * .95, cx + S * .55, cy + S * .15], 180, 360, fill=c, width=w)
        d.ellipse([cx - 14, cy + S * .25, cx + 14, cy + S * .25 + 28], outline=c, width=5)
    elif nombre == "regalo":
        d.rectangle([cx - S, cy - S * .4, cx + S, cy + S], outline=c, width=w); d.rectangle([cx - S * 1.1, cy - S * .7, cx + S * 1.1, cy - S * .4], outline=c, width=w)
        d.line([(cx, cy - S * .7), (cx, cy + S)], fill=c, width=w); d.ellipse([cx - S * .6, cy - S * 1.1, cx, cy - S * .7], outline=c, width=w); d.ellipse([cx, cy - S * 1.1, cx + S * .6, cy - S * .7], outline=c, width=w)
    elif nombre == "arena":
        d.line([(cx - S * .6, cy - S), (cx + S * .6, cy - S), (cx + S * .05, cy), (cx + S * .6, cy + S), (cx - S * .6, cy + S), (cx - S * .05, cy), (cx - S * .6, cy - S)], fill=c, width=w)
        d.polygon([(cx - S * .35, cy + S * .9), (cx + S * .35, cy + S * .9), (cx, cy + S * .4)], fill=c)
    elif nombre == "escudo":
        d.line([(cx, cy - S), (cx + S * .8, cy - S * .6), (cx + S * .7, cy + S * .3), (cx, cy + S), (cx - S * .7, cy + S * .3), (cx - S * .8, cy - S * .6), (cx, cy - S)], fill=c, width=w)
        d.line([(cx - S * .3, cy), (cx - S * .05, cy + S * .3), (cx + S * .35, cy - S * .3)], fill=c, width=w)
    elif nombre == "coche":
        d.rounded_rectangle([cx - S * 1.4, cy - S * .2, cx + S * 1.4, cy + S * .3], 20, outline=c, width=w)
        d.line([(cx - S * .8, cy - S * .2), (cx - S * .45, cy - S * .7), (cx + S * .55, cy - S * .7), (cx + S * .9, cy - S * .2)], fill=c, width=w)
        for x in (cx - S * .85, cx + S * .85): d.ellipse([x - S * .3, cy + S * .05, x + S * .3, cy + S * .65], outline=c, width=w)
    elif nombre == "mapa":
        d.line([(cx - S * 1.2, cy - S * .8), (cx - S * .4, cy - S), (cx + S * .4, cy - S * .8), (cx + S * 1.2, cy - S), (cx + S * 1.2, cy + S * .8), (cx + S * .4, cy + S), (cx - S * .4, cy + S * .8), (cx - S * 1.2, cy + S), (cx - S * 1.2, cy - S * .8)], fill=c, width=w)
        d.line([(cx - S * .4, cy - S), (cx - S * .4, cy + S * .8)], fill=c, width=3); d.line([(cx + S * .4, cy - S * .8), (cx + S * .4, cy + S)], fill=c, width=3)
        d.ellipse([cx - 16, cy - 40, cx + 16, cy - 8], outline=NEON[0] + (255,), width=6)
    elif nombre == "billetes":
        for k in range(3): d.rectangle([cx - S * 1.1 + k * 18, cy - S * .5 - k * 22, cx + S * 1.1 + k * 18, cy + S * .5 - k * 22], outline=c, width=w)
        d.ellipse([cx - S * .3 + 36, cy - S * .3 - 44, cx + S * .3 + 36, cy + S * .3 - 44], outline=c, width=w)
    elif nombre == "camara":
        d.rounded_rectangle([cx - S, cy - S * .5, cx + S * .6, cy + S * .3], 10, outline=c, width=w); d.line([(cx - S * .2, cy - S * .5), (cx - S * .2, cy - S)], fill=c, width=w)
        d.ellipse([cx + S * .45, cy - S * .35, cx + S * .75, cy - S * .05], outline=NEON[0] + (255,), width=6)


OBJETOS = [("consola", ("console",)), ("mando", ("controller",)), ("disco", ("ssd", "drive", "storage")), ("reloj", ("clock", "stopwatch")),
           ("calendario", ("calendar",)), ("precio", ("price tag", "price")), ("movil", ("phone",)), ("candado", ("padlock", "lock")),
           ("regalo", ("gift",)), ("arena", ("hourglass",)), ("escudo", ("shield",)), ("mapa", ("map",)), ("billetes", ("cash", "money", "coin", "bills")),
           ("camara", ("security camera",)), ("coche", ("car key", "car keys"))]


def objetos_de(k):
    return [n for n, cl in OBJETOS if any(c in k for c in cl)]

# ---------------------------------------------------------------- tipos de escena
def esc_ciudad(rnd, P):
    hz = int(H * rnd.uniform(.58, .72))
    pal = P.get("paleta") or rnd.choice(["atardecer", "atardecer", "anochecer", "noche"])
    capas = [(cielo(rnd, pal, hz, estrellas=pal != "atardecer"), .1),
             (skyline(rnd, hz, H * .32, .6, color=(40, 12, 70)), .25),
             (skyline(rnd, hz, H * .22, 1.2), .45),
             (agua(rnd, hz), .55)]
    fr = capa(); d = ImageDraw.Draw(fr)
    palmera(d, PAD + 80, H, H * .9, 1); palmera(d, W + PAD - 60, H, H * .8, -1)
    capas.append((fr, 1.0)); return capas, ["agua", "ventanas"]


def esc_playa(rnd, P):
    hz = int(H * .55)
    capas = [(cielo(rnd, P.get("paleta", "atardecer"), hz), .1), (skyline(rnd, hz, H * .12, .8, color=(50, 16, 80)), .2), (agua(rnd, hz), .4)]
    arena = capa(); d = ImageDraw.Draw(arena)
    d.polygon([(0, H * .78), (arena.width * .4, H * .72), (arena.width, H * .76), (arena.width, H), (0, H)], fill=(60, 24, 70, 255))
    for k in range(rnd.randint(6, 14)):
        x = rnd.randint(0, arena.width); y = int(H * rnd.uniform(.8, .95)); c = rnd.choice(NEON)
        d.pieslice([x - 50, y - 40, x + 50, y + 20], 180, 360, fill=c + (255,)); d.line([(x, y - 10), (x, y + 40)], fill=TINTA + (255,), width=4)
    for k in range(rnd.randint(4, 12)): persona(d, rnd.randint(0, arena.width), int(H * rnd.uniform(.86, .98)), rnd.randint(70, 130), pose=rnd.random())
    palmera(d, PAD + 40, H, H * .95, 1); palmera(d, W + PAD - 20, H, H * .85, -1)
    capas.append((arena, 1.0)); return capas, ["agua"]


def esc_puente(rnd, P):
    hz = int(H * .6)
    capas = [(cielo(rnd, P.get("paleta", "atardecer"), hz), .1), (agua(rnd, hz, (25, 227, 208)), .35)]
    isl = capa(); d = ImageDraw.Draw(isl)
    for k in range(5):
        x = rnd.randint(0, isl.width); w = rnd.randint(120, 380)
        d.ellipse([x, hz - 18, x + w, hz + 22], fill=TINTA + (255,))
        for j in range(rnd.randint(1, 4)): palmera(d, x + rnd.randint(10, w), hz + 2, rnd.randint(60, 140), rnd.choice((-1, 1)))
    capas.append((isl, .3))
    pu = capa(); d = ImageDraw.Draw(pu); y = int(H * .74)
    d.rectangle([0, y, pu.width, y + 18], fill=TINTA + (255,))
    for x in range(0, pu.width, 120): d.rectangle([x, y + 18, x + 14, H], fill=TINTA + (255,))
    capas.append((pu, .7)); return capas, ["agua", "trafico_puente"]


def esc_pantano(rnd, P):
    hz = int(H * .62)
    capas = [(cielo(rnd, P.get("paleta", "atardecer"), hz), .1)]
    far = capa(); d = ImageDraw.Draw(far)
    for k in range(18): cipres(d, rnd.randint(0, far.width), hz + 4, rnd.randint(120, 300), (36, 12, 56))
    capas += [(far, .25), (agua(rnd, hz, (255, 140, 120)), .4)]
    near = capa(); d = ImageDraw.Draw(near)
    for k in range(260):
        x = rnd.randint(0, near.width); b = int(H * rnd.uniform(.82, 1.02)); h = rnd.randint(40, 160)
        d.line([(x, b), (x + rnd.randint(-25, 25), b - h)], fill=TINTA + (255,), width=rnd.randint(2, 5))
    k = P.get("kw", "")
    if "airboat" in k or "boat" in k: aerodeslizador(d, PAD + W * .45, int(H * .78), 320)
    if "alligator" in k or "gator" in k: caiman(d, PAD + W * .18, int(H * .8), 300)
    if "shack" in k or "cabin" in k:
        d.rectangle([PAD + W * .62, H * .55, PAD + W * .8, H * .72], fill=TINTA + (255,)); d.polygon([(PAD + W * .6, H * .55), (PAD + W * .71, H * .47), (PAD + W * .82, H * .55)], fill=TINTA + (255,))
        cartel_neon(near, int(PAD + W * .66), int(H * .6), 120, 40, NEON[0])
    capas.append((near, 1.0)); return capas, ["agua", "luciernagas"]


def esc_carretera(rnd, P):
    hz = int(H * .55)
    capas = [(cielo(rnd, P.get("paleta", "atardecer"), hz), .1), (skyline(rnd, hz, H * .14, .8, color=(46, 14, 76)), .2)]
    tierra = suelo(hz); d = ImageDraw.Draw(tierra); cx = tierra.width / 2
    d.polygon([(cx - 8, hz), (cx + 8, hz), (cx + W * .7, H), (cx - W * .7, H)], fill=(22, 10, 36, 255))
    for k in range(14):
        t0, t1 = (k / 14) ** 2, ((k + .45) / 14) ** 2
        d.polygon([(cx - 2 - t0 * 14, hz + t0 * (H - hz)), (cx + 2 + t0 * 14, hz + t0 * (H - hz)), (cx + 2 + t1 * 14, hz + t1 * (H - hz)), (cx - 2 - t1 * 14, hz + t1 * (H - hz))], fill=(255, 210, 63, 255))
    for lado in (-1, 1):
        for k in range(7):
            t = (k / 7) ** 1.7; x = cx + lado * (40 + t * W * .9); palmera(d, x, hz + t * (H - hz), 60 + t * 600, -lado)
    capas.append((tierra, .6))
    if "car" in P.get("kw", "") or "highway" in P.get("kw", "") or "drive" in P.get("kw", ""):
        cc = capa(); dc = ImageDraw.Draw(cc); coche(dc, cx - 230, H - 90, 460); capas.append((cc, 1.0))
    return capas, ["estelas"]


def esc_calle(rnd, P):
    hz = int(H * .5)
    capas = [(cielo(rnd, "noche" if rnd.random() < .6 else "anochecer", hz, sol=False), .1)]
    ed = capa(); d = ImageDraw.Draw(ed); cx = ed.width / 2
    for lado in (-1, 1):
        for k in range(6):
            x0 = cx + lado * (90 + k * 150); x1 = x0 + lado * 150
            top = hz - 140 - k * 70
            d.polygon([(x0, hz + 20), (x0, top), (x1, top - 40), (x1, H)], fill=(20 + k * 3, 8, 40, 255))
        for k in range(5):
            cartel_neon(ed, int(cx + lado * (200 + k * 160) - (0 if lado > 0 else 120)), int(hz - 120 - k * 30), 110, 50 + k * 8, rnd.choice(NEON), rnd.choice(["rect", "flecha", "circulo", "estrella", "corazon"]))
    capas.append((ed, .5))
    pi = suelo(int(H * .62), (30, 12, 50), (6, 3, 16)); dp = ImageDraw.Draw(pi)
    for k in range(40):
        x = rnd.randint(0, pi.width); y = rnd.randint(int(H * .65), H); c = rnd.choice(NEON)
        dp.line([(x, y), (x, y + rnd.randint(20, 90))], fill=c + (70,), width=rnd.randint(4, 14))
    capas.append((pi, .7)); return capas, ["lluvia"]


def esc_interior(rnd, P):
    base = capa(); base.paste(grad(base.width, H, [(0, (26, 10, 46)), (1, (10, 4, 22))]).convert("RGBA"))
    d = ImageDraw.Draw(base); k = P.get("kw", "")
    # ventana con ciudad y persianas
    wx0, wy0, wx1, wy1 = PAD + W * .52, H * .12, PAD + W * .92, H * .6
    vent = esc_ciudad(rnd, {"paleta": rnd.choice(["atardecer", "anochecer", "noche"])})[0]
    v = Image.new("RGBA", (base.width, H)); [v.alpha_composite(c) for c, _ in vent]
    v = v.resize((int(wx1 - wx0), int(wy1 - wy0)), Image.LANCZOS, box=(PAD, 0, PAD + W, H))
    base.paste(v, (int(wx0), int(wy0)))
    for y in range(int(wy0), int(wy1), 22): d.rectangle([wx0, y, wx1, y + 9], fill=(14, 6, 28, 230))
    d.rectangle([wx0, wy0, wx1, wy1], outline=TINTA + (255,), width=14)
    luz = capa(); dl = ImageDraw.Draw(luz)
    dl.polygon([(wx0, wy0), (wx1, wy0), (wx1 - 200, H), (wx0 - 500, H)], fill=(255, 60, 150, 40)); base.alpha_composite(luz.filter(ImageFilter.GaussianBlur(30)))
    # mesa
    d.rectangle([0, H * .72, base.width, H], fill=(16, 6, 30, 255)); d.line([(0, H * .72), (base.width, H * .72)], fill=(255, 46, 136, 160), width=3)
    obs = objetos_de(k)
    if obs and not any(s in k for s in ("board", "cork", "detective")):
        obs = obs[:2]; ol = capa()
        for i, n in enumerate(obs): objeto(ol, n, PAD + W * (.27 + i * .2) - (len(obs) - 1) * W * .05, H * .45, 170 if len(obs) == 1 else 130, NEON[(i + 1 + rnd.randint(0, 3)) % 5])
        base.alpha_composite(glow(ol, 26))
    elif any(s in k for s in ("board", "cork", "detective", "string", "polaroid")):
        bx0, by0 = PAD + W * .06, H * .1
        d.rectangle([bx0, by0, bx0 + W * .4, by0 + H * .5], fill=(70, 40, 40, 255), outline=TINTA + (255,), width=10)
        pts = []
        for i in range(7):
            x = bx0 + 40 + rnd.random() * (W * .4 - 160); y = by0 + 30 + rnd.random() * (H * .5 - 140)
            d.rectangle([x, y, x + 100, y + 80], fill=(220, 210, 200, 255)); d.rectangle([x + 8, y + 8, x + 92, y + 58], fill=(40 + i * 15, 20, 60, 255)); pts.append((x + 50, y + 4))
        for i in range(len(pts) - 1): d.line([pts[i], pts[i + 1]], fill=(230, 30, 60, 255), width=3)
    elif any(s in k for s in ("monitor", "screen", "tv", "television", "laptop", "pc", "console", "editing")):
        mx, my = PAD + W * .12, H * .3
        m = capa(); dm = ImageDraw.Draw(m); dm.rounded_rectangle([mx, my, mx + 560, my + 330], 14, fill=(255, 46, 136, 255)); base.alpha_composite(m.filter(ImageFilter.GaussianBlur(40)))
        d.rounded_rectangle([mx, my, mx + 560, my + 330], 14, fill=(30, 10, 50, 255), outline=(25, 227, 208, 255), width=5)
        mini = esc_ciudad(rnd, {"paleta": "atardecer"})[0]; vv = Image.new("RGBA", (base.width, H)); [vv.alpha_composite(c) for c, _ in mini]
        base.paste(vv.resize((530, 300), Image.LANCZOS, box=(PAD, 0, PAD + W, H)), (int(mx + 15), int(my + 15)))
        d.rectangle([mx + 250, my + 330, mx + 310, H * .72], fill=TINTA + (255,))
    elif any(s in k for s in ("gym", "punching", "dumbbell", "boxing")):
        x = PAD + W * .25; d.line([(x, 0), (x, H * .25)], fill=TINTA + (255,), width=6); d.rounded_rectangle([x - 60, H * .25, x + 60, H * .62], 40, fill=(120, 20, 60, 255))
    elif objetos_de(k):
        obs = objetos_de(k)[:2]; ol = capa()
        for i, n in enumerate(obs): objeto(ol, n, PAD + W * (.22 + i * .2), H * .52, 110, NEON[(i + 1 + rnd.randint(0, 3)) % 5])
        base.alpha_composite(glow(ol, 20))
    else:
        lx = PAD + W * .2
        d.polygon([(lx - 70, H * .52), (lx + 70, H * .52), (lx + 40, H * .44), (lx - 40, H * .44)], fill=(255, 122, 26, 255)); d.line([(lx, H * .52), (lx, H * .72)], fill=TINTA + (255,), width=8)
        lamp = capa(); ImageDraw.Draw(lamp).ellipse([lx - 300, H * .4, lx + 300, H * .9], fill=(255, 140, 60, 70)); base.alpha_composite(lamp.filter(ImageFilter.GaussianBlur(60)))
        for j in range(rnd.randint(2, 5)):
            x = PAD + rnd.uniform(.1, .45) * W; d.rectangle([x, H * .66, x + rnd.randint(60, 160), H * .72], fill=rnd.choice([(200, 190, 180), (40, 20, 60), (90, 40, 90)]) + (255,))
    return [(base, .0)], []


def esc_carcel(rnd, P):
    base = capa(); base.paste(grad(base.width, H, [(0, (20, 30, 60)), (1, (6, 8, 20))]).convert("RGBA")); d = ImageDraw.Draw(base); cx = base.width / 2
    d.polygon([(cx - 140, H * .38), (cx + 140, H * .38), (cx + W * .7, H), (cx - W * .7, H)], fill=(30, 40, 70, 255))
    for k in range(10):
        t = k / 10; x = cx - 140 - t * (W * .7 - 140); x2 = cx + 140 + t * (W * .7 - 140)
        for xx in (x, x2): d.line([(xx, H * .38 - 300 * (1 - t) - 200 * t), (xx, H * .38 + t * (H * .62))], fill=(8, 10, 24, 255), width=int(4 + t * 18))
    luz = capa(); dl = ImageDraw.Draw(luz)
    for k in range(5):
        y = H * (.08 + k * .02); dl.rectangle([cx - 200 + k * 30, y, cx + 200 - k * 30, y + 8], fill=(200, 230, 255, 255))
    base.alpha_composite(glow(luz, 20))
    if any(s in P.get("kw", "") for s in ("woman", "figure", "walking", "silhouette")): persona(d, cx, H * .82, 380)
    if "phone" in P.get("kw", ""):
        d.rectangle([cx + 260, H * .35, cx + 340, H * .55], fill=(60, 70, 90, 255)); d.line([(cx + 300, H * .55), (cx + 280, H * .72)], fill=(10, 10, 20, 255), width=5)
    return [(base, .0)], []


def esc_garaje(rnd, P):
    base = capa(); base.paste(grad(base.width, H, [(0, (14, 6, 30)), (1, (4, 2, 12))]).convert("RGBA")); d = ImageDraw.Draw(base)
    for k in range(5):
        x = PAD + W * (.1 + k * .2); cartel_neon(base, int(x), int(H * .1), 200, 8, NEON[k % len(NEON)])
    d.rectangle([0, H * .7, base.width, H], fill=(10, 4, 20, 255))
    n = 3 if any(s in P.get("kw", "") for s in ("row", "lineup", "parked", "meet", "three", "garage")) else 1
    for i in range(n):
        largo = 720 if n == 1 else 520; x = PAD + W / 2 - largo / 2 + (i - (n - 1) / 2) * 560
        coche(d, x, H * .74, largo, (24, 10, 44));
        refl = base.crop((int(x), int(H * .74 - largo * .28), int(x + largo), int(H * .74))).transpose(Image.FLIP_TOP_BOTTOM)
        refl.putalpha(70); base.alpha_composite(refl, (int(x), int(H * .74)))
        d.line([(x + 30, H * .74 - largo * .14), (x + largo - 30, H * .74 - largo * .14)], fill=(255, 46, 136, 220), width=3)
    return [(base, .0)], []


def esc_mar(rnd, P):
    hz = int(H * .58)
    capas = [(cielo(rnd, P.get("paleta", "atardecer"), hz), .1), (skyline(rnd, hz, H * .1, .6, color=(50, 16, 80)), .2), (agua(rnd, hz), .4)]
    b = capa(); d = ImageDraw.Draw(b); k = P.get("kw", "")
    yacht = "yacht" in k
    if "jet ski" in k or "jet-ski" in k:
        x = PAD + W * .4; d.polygon([(x, H * .8), (x + 160, H * .8), (x + 140, H * .83), (x + 10, H * .83)], fill=TINTA + (255,)); persona(d, x + 70, H * .8, 120)
    else:
        barco(d, PAD + W * .3, int(H * .8), 520 if yacht else 360, yacht=yacht)
    d.polygon([(PAD + W * .3, H * .8), (PAD + W * .05, H * .9), (PAD + W * .07, H * .92)], fill=(255, 255, 255, 90))
    capas.append((b, .9)); return capas, ["agua"]


def esc_bosque(rnd, P):
    hz = int(H * .6)
    capas = [(cielo(rnd, P.get("paleta", "amanecer" if "sunrise" in P.get("kw", "") or "dawn" in P.get("kw", "") else "atardecer"), hz), .1)]
    for j, (col, alt, dep) in enumerate([((70, 30, 90), 260, .2), ((40, 16, 60), 200, .4), (TINTA, 160, .8)]):
        l = capa(); d = ImageDraw.Draw(l)
        pts = [(x, hz + 40 * j - alt * (.5 + .5 * math.sin(x / (300 + j * 80) + j))) for x in range(0, l.width + 40, 40)]
        d.polygon(pts + [(l.width, H), (0, H)], fill=col + (255,))
        for x in range(0, l.width, 26 + j * 10):
            y = hz + 40 * j - alt * (.5 + .5 * math.sin(x / (300 + j * 80) + j)); pino(d, x, y + 10, 60 + j * 50, col)
        if j == 0: l = l.filter(ImageFilter.GaussianBlur(2))
        capas.append((l, dep))
    niebla = capa(); ImageDraw.Draw(niebla).rectangle([0, hz - 40, niebla.width, hz + 120], fill=(255, 190, 210, 60)); capas.insert(2, (niebla.filter(ImageFilter.GaussianBlur(40)), .3))
    return capas, ["luciernagas"]


def esc_industria(rnd, P):
    hz = int(H * .62)
    capas = [(cielo(rnd, "atardecer", hz), .1)]
    f = capa(); d = ImageDraw.Draw(f); x0 = PAD + W * .45
    for k in range(6):
        x = x0 + k * 110; h = rnd.randint(200, 420); d.rectangle([x, hz - h, x + 40, hz], fill=TINTA + (255,))
        humo = capa(); dh = ImageDraw.Draw(humo)
        for j in range(8): dh.ellipse([x - 20 - j * 12, hz - h - 60 - j * 50, x + 60 + j * 10, hz - h - j * 50], fill=(200, 140, 170, 50))
        f.alpha_composite(humo.filter(ImageFilter.GaussianBlur(14)))
    d.rectangle([x0 - 200, hz - 160, x0 + 700, hz], fill=TINTA + (255,))
    for k in range(30): d.rectangle([x0 - 180 + k * 30, hz - 120, x0 - 170 + k * 30, hz - 110], fill=(255, 210, 63, 255))
    capas += [(f, .3), (agua(rnd, hz), .4)]
    c = capa(); dc = ImageDraw.Draw(c)
    for k in range(60): dc.line([(k * 40 + rnd.randint(0, 20), H), (k * 40 + rnd.randint(-30, 30), H - rnd.randint(80, 200))], fill=TINTA + (255,), width=6)
    capas.append((c, 1.0)); return capas, ["agua"]


def esc_motel(rnd, P):
    hz = int(H * .58)
    capas = [(cielo(rnd, rnd.choice(["anochecer", "noche"]), hz, sol=False), .1)]
    m = capa(); d = ImageDraw.Draw(m); x0 = PAD + W * .12
    d.rectangle([x0, hz - 220, x0 + W * .76, hz + 60], fill=(30, 12, 50, 255))
    for k in range(9):
        x = x0 + 40 + k * W * .08; d.rectangle([x, hz - 150, x + 70, hz + 60], fill=(255, 190, 120, 255) if rnd.random() < .4 else (12, 6, 24, 255))
    cartel_neon(m, int(x0 + W * .58), int(hz - 420), 260, 140, NEON[0]); d.rectangle([x0 + W * .58 + 120, hz - 280, x0 + W * .58 + 140, hz - 220], fill=TINTA + (255,))
    capas.append((m, .4)); s = suelo(hz + 60, (34, 14, 50), (8, 4, 18)); ds = ImageDraw.Draw(s)
    coche(ds, PAD + W * .3, H * .9, 460); capas.append((s, .8)); return capas, ["parpadeo"]


def esc_club(rnd, P):
    base = capa(); base.paste(grad(base.width, H, [(0, (10, 2, 24)), (1, (2, 0, 8))]).convert("RGBA"))
    las = capa(); d = ImageDraw.Draw(las); cx = base.width / 2
    for k in range(14):
        ang = math.radians(200 + k * 10); c = NEON[k % 3]
        d.line([(cx, H * .1), (cx + math.cos(ang) * 2400, H * .1 - math.sin(ang) * 2400)], fill=c + (160,), width=4)
    base.alpha_composite(glow(las, 10))
    bola = capa(); db = ImageDraw.Draw(bola); db.ellipse([cx - 50, H * .05, cx + 50, H * .15], fill=(220, 220, 255, 255)); base.alpha_composite(glow(bola, 30))
    g = capa(); dg = ImageDraw.Draw(g)
    for k in range(40): persona(dg, rnd.randint(0, g.width), H + rnd.randint(0, 60), rnd.randint(260, 420), (6, 2, 14), pose=rnd.random())
    return [(base, 0), (g, .6)], ["laser"]


def esc_policia(rnd, P):
    capas, ef = esc_calle(rnd, P)
    pc = capa(); d = ImageDraw.Draw(pc); coche(d, PAD + W * .3, H * .9, 520, luces=True)
    luz = capa(); dl = ImageDraw.Draw(luz)
    dl.ellipse([PAD + W * .3 + 150, H * .7, PAD + W * .3 + 330, H * .8], fill=(255, 30, 60, 200)); dl.ellipse([PAD + W * .3 + 250, H * .7, PAD + W * .3 + 430, H * .8], fill=(40, 90, 255, 200))
    pc.alpha_composite(luz.filter(ImageFilter.GaussianBlur(50)))
    capas.append((pc, .9))
    if "helicopter" in P.get("kw", "") or "spotlight" in P.get("kw", ""):
        hl = capa(); dh = ImageDraw.Draw(hl); hx = PAD + W * .7
        dh.polygon([(hx, H * .12), (hx - 260, H), (hx + 140, H)], fill=(220, 230, 255, 60)); hl = hl.filter(ImageFilter.GaussianBlur(20))
        ImageDraw.Draw(hl).ellipse([hx - 40, H * .1, hx + 40, H * .14], fill=TINTA + (255,)); capas.append((hl, .3))
    return capas, ef + ["sirena"]


def esc_abstracto(rnd, P):
    base = capa(); base.paste(grad(base.width, H, [(0, (16, 6, 40)), (1, (4, 2, 14))]).convert("RGBA")); k = P.get("kw", "")
    l = capa(); cx, cy = base.width / 2, H / 2
    if "wheel" in k or "circular" in k:
        d = ImageDraw.Draw(l)
        for i in range(3): d.arc([cx - 300, cy - 300, cx + 300, cy + 300], i * 120 + 6, i * 120 + 114, fill=NEON[i] + (255,), width=60)
    elif "star" in k:
        for i in range(6): cartel_neon(l, int(cx - 600 + i * 210), int(cy - 80), 160, 0, NEON[i % 4], "estrella")
    elif "bubble" in k or "speech" in k or "comment" in k:
        d = ImageDraw.Draw(l)
        for i in range(9):
            x, y, w = rnd.randint(PAD, PAD + W - 300), rnd.randint(80, H - 300), rnd.randint(180, 320)
            c = rnd.choice(NEON); d.rounded_rectangle([x, y, x + w, y + w * .55], 30, outline=c + (255,), width=6)
            d.polygon([(x + 40, y + w * .55), (x + 80, y + w * .55), (x + 30, y + w * .75)], fill=c + (255,))
            for j in range(3): d.line([(x + 30, y + 30 + j * 30), (x + w - 40 - rnd.randint(0, 80), y + 30 + j * 30)], fill=c + (150,), width=8)
    elif "six" in k or "zone" in k or "infographic" in k or "map" in k:
        d = ImageDraw.Draw(l)
        pts = [(cx - 200, cy - 380), (cx + 120, cy - 360), (cx + 200, cy - 100), (cx + 180, cy + 200), (cx + 40, cy + 400), (cx - 60, cy + 300), (cx - 240, cy + 40)]
        d.polygon(pts, outline=NEON[1] + (255,), width=5)
        for i, (x, y) in enumerate([(cx + 60, cy + 10), (cx + 30, cy + 360), (cx - 40, cy + 120), (cx - 180, cy - 40), (cx - 30, cy - 150), (cx - 90, cy - 300)]):
            d.ellipse([x - 60, y - 60, x + 60, y + 60], fill=NEON[i % 5] + (120,), outline=NEON[i % 5] + (255,), width=4)
    elif objetos_de(k):
        obs = objetos_de(k)[:3]
        for i, n in enumerate(obs):
            objeto(l, n, cx + (i - (len(obs) - 1) / 2) * 520, cy - 40, 170 if len(obs) == 1 else 130, NEON[(i + rnd.randint(0, 4)) % 5])
    elif "bell" in k:
        d = ImageDraw.Draw(l); d.pieslice([cx - 160, cy - 200, cx + 160, cy + 140], 180, 360, outline=NEON[0] + (255,), width=10)
        d.line([(cx - 160, cy - 30), (cx - 190, cy + 120), (cx + 190, cy + 120), (cx + 160, cy - 30)], fill=NEON[0] + (255,), width=10); d.ellipse([cx - 30, cy + 130, cx + 30, cy + 190], outline=NEON[0] + (255,), width=10)
    else:
        d = ImageDraw.Draw(l)
        for i in range(rnd.randint(3, 7)):
            x = PAD + W * (.15 + i * .12); y = cy + rnd.randint(-200, 120); w = rnd.randint(140, 220)
            d.rounded_rectangle([x, y, x + w, y + w * 1.35], 18, outline=NEON[i % 5] + (255,), width=6)
            for j in range(4): d.line([(x + 25, y + 40 + j * 40), (x + w - 25 - j * 15, y + 40 + j * 40)], fill=NEON[i % 5] + (120,), width=7)
    base.alpha_composite(glow(l, 22))
    g = capa(); dg = ImageDraw.Draw(g)
    for x in range(0, g.width, 80): dg.line([(x, H * .8), (cx + (x - cx) * 3, H)], fill=(255, 46, 136, 90), width=2)
    for y in range(int(H * .8), H, 30): dg.line([(0, y), (g.width, y)], fill=(255, 46, 136, 90), width=2)
    base.alpha_composite(g)
    return [(base, 0)], ["pulso"]


def esc_banco(rnd, P):
    base = capa(); base.paste(grad(base.width, H, [(0, (30, 16, 50)), (1, (8, 4, 18))]).convert("RGBA")); d = ImageDraw.Draw(base); cx = base.width / 2
    for k in range(6):
        for lado in (-1, 1):
            x = cx + lado * (240 + k * 170); d.rectangle([x - 30 - k * 4, H * .1 - k * 10, x + 30 + k * 4, H * .78 + k * 30], fill=(50 + k * 8, 30, 70, 255))
    if "vault" in P.get("kw", "") or "safe" in P.get("kw", ""):
        d.ellipse([cx - 260, H * .2, cx + 260, H * .2 + 520], fill=(40, 30, 60, 255), outline=(255, 210, 63, 255), width=14)
        for a in range(0, 360, 45):
            d.line([(cx, H * .2 + 260), (cx + math.cos(math.radians(a)) * 180, H * .2 + 260 + math.sin(math.radians(a)) * 180)], fill=(255, 210, 63, 255), width=10)
        l = capa(); ImageDraw.Draw(l).ellipse([cx - 120, H * .2 + 140, cx + 120, H * .2 + 380], fill=(255, 220, 140, 120)); base.alpha_composite(l.filter(ImageFilter.GaussianBlur(40)))
    d.rectangle([0, H * .82, base.width, H], fill=(14, 8, 26, 255))
    return [(base, 0)], []


TIPOS = [  # (palabras clave, función) — gana la primera que coincida
    (("vault", "bank lobby", "bank interior", "casino", "jewelry", "blueprint of a bank"), esc_banco),
    (("prison", "jail", "interrogation", "jumpsuit", "visiting booth", "payphone", "prison gate"), esc_carcel),
    (("police", "patrol", "roadblock", "sirens", "helicopter", "ambulance", "evidence"), esc_policia),
    (("nightclub", "club interior", "dance", "dj", "mirror ball", "laser", "concert", "stage", "party at night", "crowd of silhouettes"), esc_club),
    (("swamp", "wetland", "airboat", "alligator", "mangrove", "cypress", "marsh", "fireflies"), esc_pantano),
    (("forest", "pine", "hunting", "campfire", "valley", "river winding", "misty hill", "national park", "canoe"), esc_bosque),
    (("refinery", "smokestack", "sugarcane", "farmland", "factory", "industrial"), esc_industria),
    (("motel", "gas station", "liquor store", "diner", "convenience store", "roadside bar", "parking lot", "store at night", "pawn shop"), esc_motel),
    (("bridge", "causeway", "islands", "keys", "stilt house", "marina", "dock"), esc_puente),
    (("yacht", "speedboat", "jet ski", "fishing boat", "sailboat", "seaplane", "boat"), esc_mar),
    (("beach", "boardwalk", "lifeguard", "sand", "pier", "drive-in"), esc_playa),
    (("highway", "road", "driving", "windshield", "street race", "convertible", "drift", "car's interior", "light trails", "junction"), esc_carretera),
    (("garage", "supercar", "muscle car", "sports car", "car meet", "workshop", "lineup", "classic american", "pickup", "suv", "motorcycle", "getaway"), esc_garaje),
    (("street", "alley", "neon sign", "sidewalk", "rain", "puddle", "market", "arcade"), esc_calle),
    (("desk", "room", "kitchen", "office", "studio", "gym", "locker", "monitor", "laptop", "television", "living room", "bedroom", "couch", "cork", "board", "notebook", "table", "closet", "attic", "server", "hallway", "corridor", "editing", "pc ", "console", "store aisle", "storage"), esc_interior),
    (("wheel", "icon", "bubble", "abstract", "infographic", "stars", "counter", "cards", "timeline", "progress", "neon light floating", "concept", "symbolic", "trophies", "podium", "bell"), esc_abstracto),
    (("skyline", "city", "rooftop", "balcony", "penthouse", "hotel", "art deco", "aerial"), esc_ciudad),
]


def elegir(prompt):
    k = prompt.lower()
    for claves, f in TIPOS:
        if any(c in k for c in claves): return f
    return esc_ciudad


def extras(capas, rnd, k):
    """Siluetas de personas encima de la escena según el prompt."""
    l = capa(); d = ImageDraw.Draw(l); hay = False
    base = H * .97
    if any(s in k for s in ("couple", "man and woman", "two silhouettes", "back to back", "her head on his shoulder")):
        persona(d, PAD + W * .44, base, 420); persona(d, PAD + W * .52, base, 390, pose=.3); hay = True
    elif any(s in k for s in ("a man's silhouette", "man seen from behind", "man's silhouette", "woman's silhouette", "person's silhouette", "lone figure", "silhouette of a woman", "rider silhouette")):
        persona(d, PAD + W * .3, base, 440); hay = True
    elif any(s in k for s in ("group of", "crowd", "silhouettes")) and "club" not in k:
        for i in range(rnd.randint(5, 9)): persona(d, PAD + W * rnd.uniform(.1, .9), base + rnd.randint(-10, 30), rnd.randint(260, 380), pose=rnd.random())
        hay = True
    if any(s in k for s in ("phone", "smartphone")):
        g = capa(); ImageDraw.Draw(g).rounded_rectangle([PAD + W * .62, H * .45, PAD + W * .62 + 120, H * .45 + 220], 16, fill=(120, 230, 255, 255)); l.alpha_composite(glow(g, 30)); hay = True
    if hay: capas.append((l, 1.0))
    return capas


def construir(e, semilla):
    rnd = random.Random(semilla)
    k = e["prompt"].lower()
    P = {"kw": k}
    if "night" in k or "midnight" in k: P["paleta"] = "noche" if rnd.random() < .5 else "anochecer"
    elif "dawn" in k or "sunrise" in k or "morning" in k: P["paleta"] = "amanecer"
    elif "dusk" in k: P["paleta"] = "anochecer"
    capas, ef = elegir(k)(rnd, P)
    capas = extras(capas, rnd, k)
    return capas, ef


# ---------------------------------------------------------------- render
def componer(capas, t, ef, rnd_seed, mover=True):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    for img, prof in capas:
        dx = int(PAD - (t * 2 - 1) * PAD * .8 * prof) if mover else PAD
        out.alpha_composite(img, (0, 0), (dx, 0, dx + W, H))
    if ef:
        fx = capa(W, H); d = ImageDraw.Draw(fx); r = random.Random(rnd_seed + int(t * 1000))
        if "lluvia" in ef:
            for _ in range(500):
                x, y = r.randrange(W), r.randrange(H); d.line([(x, y), (x - 6, y + 28)], fill=(200, 200, 255, 70), width=1)
        if "luciernagas" in ef:
            r2 = random.Random(rnd_seed)
            for i in range(60):
                x = r2.randrange(W) + 30 * math.sin(t * 6 + i); y = H * .55 + r2.randrange(int(H * .4)) + 20 * math.cos(t * 5 + i)
                a = int(140 + 110 * math.sin(t * 20 + i)); d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 230, 120, max(0, a)))
        if "estelas" in ef:
            for i in range(10):
                p = (t * 1.5 + i / 10) % 1; y = H * .55 + p ** 2 * H * .45; x = W / 2 + (1 if i % 2 else -1) * (40 + p ** 2 * W * .5)
                d.line([(x, y), (x + (1 if i % 2 else -1) * 30 * p, y + 20 * p)], fill=(255, 40, 70, 220) if i % 2 else (255, 240, 200, 220), width=int(2 + 8 * p))
        if "trafico_puente" in ef:
            for i in range(8):
                x = ((t * 0.6 + i / 8) % 1) * W; d.ellipse([x, H * .74 - 8, x + 14, H * .74], fill=(255, 230, 160, 255))
        if "sirena" in ef:
            c = (255, 30, 60, 60) if int(t * 16) % 2 else (40, 90, 255, 60); d.rectangle([0, 0, W, H], fill=c)
        if "laser" in ef or "pulso" in ef:
            a = int(30 + 25 * math.sin(t * 25)); d.rectangle([0, 0, W, H], fill=(255, 46, 136, max(0, a)))
        if "parpadeo" in ef and int(t * 9) % 4 == 0: d.rectangle([0, 0, W, H], fill=(0, 0, 0, 40))
        if "agua" in ef:
            for i in range(25):
                y = H * .62 + i * 16; x = W / 2 + 200 * math.sin(t * 4 + i)
                d.line([(x - 60, y), (x + 60, y)], fill=(255, 255, 255, 40), width=2)
        out.alpha_composite(fx.filter(ImageFilter.GaussianBlur(1)))
    # viñeta + grano para unificar el estilo
    return out.convert("RGB")


_VIGNETA = None


def acabado(img, rnd):
    global _VIGNETA
    if _VIGNETA is None:
        yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        _VIGNETA = np.clip(1.15 - .45 * r ** 2, .45, 1)[..., None]
    a = np.asarray(img, dtype=np.float32) * _VIGNETA
    a += np.random.default_rng(rnd).normal(0, 4, a.shape[:2])[..., None]
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def generar(carpeta: Path, solo=None, clips=True):
    data = json.loads((carpeta / "escenas.json").read_text())
    (carpeta / "escenas").mkdir(exist_ok=True)
    base_seed = sum(map(ord, carpeta.name))
    for i, e in enumerate(data["escenas"]):
        if solo and e["id"] not in solo: continue
        capas, ef = construir(e, base_seed + i * 31)
        png = carpeta / e["imagen"]
        acabado(componer(capas, .5, ef, i), i).save(png, optimize=True)
        msg = f'{e["id"]} {elegir(e["prompt"].lower()).__name__}'
        if clips and e["tipo"] == "CLIP":
            mp4 = carpeta / e["clip"]
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                  "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(mp4)], stdin=subprocess.PIPE)
            n = FPS * CLIP_SEG
            for f in range(n):
                p.stdin.write(acabado(componer(capas, f / (n - 1), ef, i), i * 1000 + f).tobytes())
            p.stdin.close(); p.wait(); msg += " + clip"
        print(msg, flush=True)


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]).resolve()
    solo = set(sys.argv[sys.argv.index("--solo") + 1].split(",")) if "--solo" in sys.argv else None
    generar(carpeta, solo, "--sin-clips" not in sys.argv)
