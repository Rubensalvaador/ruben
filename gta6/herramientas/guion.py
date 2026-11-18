#!/usr/bin/env python3
"""Lee un guion.md y genera escenas.json, prompts.csv, subtitulos_borrador.srt y capitulos.txt.

Formato del guion:
  ## Nombre del capítulo
  ### E01 · IMG|CLIP · prompt visual en inglés
  Texto de la narración...

Uso: python3 guion.py ../01-mapa-leonida   (o sin argumentos para procesar todos)
"""
import csv, json, math, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PALABRAS_POR_SEGUNDO = 2.55  # ~153 ppm, ritmo típico de voz en off en español
PAUSA_ESCENA = 0.35          # segundos de respiro entre escenas
CLIP_SEG = 8                 # duración de cada clip de Veo

ESTILO = json.loads((RAIZ / "herramientas" / "estilo.json").read_text())


def parse(path: Path):
    capitulos, escenas, cap = [], [], None
    actual = None
    for linea in path.read_text(encoding="utf-8").splitlines():
        if linea.startswith("## "):
            cap = linea[3:].strip()
            capitulos.append(cap)
        elif linea.startswith("### "):
            m = re.match(r"###\s+(E\d+)\s+·\s+(IMG|CLIP)\s+·\s+(.+)", linea)
            if not m:
                raise ValueError(f"Cabecera de escena mal formada: {linea}")
            actual = {"id": m[1], "tipo": m[2], "prompt": m[3].strip(), "capitulo": cap, "texto": ""}
            escenas.append(actual)
        elif actual and linea.strip() and not linea.startswith("<!--") and not linea.startswith("# "):
            actual["texto"] += (" " if actual["texto"] else "") + linea.strip()
    return capitulos, escenas


def ts(seg, srt=False):
    h, r = divmod(seg, 3600)
    m, s = divmod(r, 60)
    if srt:
        ms = int(round((s - int(s)) * 1000))
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"
    return f"{int(m)}:{int(s):02d}" if h == 0 else f"{int(h)}:{int(m):02d}:{int(s):02d}"


def trocear_subs(texto, inicio, dur, max_chars=84):
    """Divide el texto de una escena en bloques de subtítulo de ≤2 líneas."""
    bloques = []
    for frase in re.split(r"(?<=[.?!:])\s+", texto):
        trozos, buf = [], ""
        for f in re.split(r"(?<=[,;])\s+", frase):
            if not buf or len(buf) < 18 or len(buf) + len(f) + 1 <= max_chars:
                buf = (buf + " " + f).strip()
            else:
                trozos.append(buf); buf = f
        trozos.append(buf)
        for f in trozos:
            while len(f) > max_chars:
                corte = f.rfind(" ", 0, max_chars // 2 + max_chars // 4) if len(f) < max_chars * 1.5 else f.rfind(" ", 0, max_chars)
                bloques.append(f[:corte]); f = f[corte + 1:]
            if bloques and len(f) < 18 and len(bloques[-1]) + len(f) < max_chars + 12:
                bloques[-1] += " " + f
            else:
                bloques.append(f)
    total = sum(len(b) for b in bloques) or 1
    t, out = inicio, []
    for b in bloques:
        d = dur * len(b) / total
        out.append((t, t + d, b)); t += d
    return out


def procesar(carpeta: Path):
    capitulos, escenas = parse(carpeta / "guion.md")
    t = 0.0
    subs, caps_ts, visto = [], [], set()
    for e in escenas:
        palabras = len(e["texto"].split())
        dur = palabras / PALABRAS_POR_SEGUNDO
        e.update(palabras=palabras, inicio=round(t, 2), duracion=round(dur, 2),
                 prompt_completo=f'{e["prompt"]}, {ESTILO["sufijo"]}',
                 negativo=ESTILO["negativo"],
                 imagen=f'escenas/{e["id"]}.png',
                 clip=f'escenas/{e["id"]}.mp4' if e["tipo"] == "CLIP" else None)
        if e["capitulo"] not in visto:
            visto.add(e["capitulo"]); caps_ts.append((t, e["capitulo"]))
        subs += trocear_subs(e["texto"], t, dur)
        t += dur + PAUSA_ESCENA
    total = t
    (carpeta / "escenas.json").write_text(json.dumps({
        "duracion_estimada_seg": round(total, 1),
        "palabras": sum(e["palabras"] for e in escenas),
        "imagenes": len(escenas),
        "clips": sum(e["tipo"] == "CLIP" for e in escenas),
        "segundos_clip": CLIP_SEG * sum(e["tipo"] == "CLIP" for e in escenas),
        "escenas": escenas}, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(carpeta / "prompts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["escena", "modelo", "prompt", "negativo", "formato", "archivo_destino"])
        for e in escenas:
            w.writerow([e["id"], "Nano Banana (imagen 16:9)", e["prompt_completo"], e["negativo"], "1920x1080", e["imagen"]])
            if e["tipo"] == "CLIP":
                w.writerow([e["id"], f"Veo 3.1 Lite ({CLIP_SEG}s, sin audio, desde la imagen)", e["prompt_completo"], e["negativo"], "1920x1080", e["clip"]])
    with open(carpeta / "subtitulos_borrador.srt", "w", encoding="utf-8") as f:
        for i, (a, b, txt) in enumerate(subs, 1):
            f.write(f"{i}\n{ts(a, True)} --> {ts(b, True)}\n{txt}\n\n")
    # YouTube exige que el primer capítulo empiece en 0:00 y que cada uno dure ≥10 s
    lineas = [f"{ts(a)} {c}" for a, c in caps_ts]
    (carpeta / "capitulos.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return carpeta.name, total, escenas


if __name__ == "__main__":
    dirs = [Path(a).resolve() for a in sys.argv[1:]] or sorted(p for p in RAIZ.iterdir() if (p / "guion.md").exists())
    for d in dirs:
        nombre, total, esc = procesar(d)
        gancho = esc[0]["duracion"]
        print(f"{nombre:38s} {total/60:5.1f} min  {sum(e['palabras'] for e in esc):5d} palabras  "
              f"{len(esc):3d} escenas  {sum(e['tipo']=='CLIP' for e in esc)} clips  gancho {gancho:.0f}s")
