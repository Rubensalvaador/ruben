#!/usr/bin/env python3
"""Monta el vídeo final 1920x1080 a partir de escenas/ (png/mp4), voz/ (mp3 por escena) y una música con licencia.

  python3 montaje.py ../01-mapa-leonida --musica ../musica/pista.mp3 [--quemar-subs] [--borrador]

- Cada escena dura lo que su voz + una pausa corta. Las imágenes llevan un movimiento lento (Ken Burns)
  y las escenas CLIP usan el clip de Veo y, si la voz es más larga, siguen con la imagen.
- Calcula los subtítulos reales (subtitulos.srt) a partir de la duración de cada mp3.
- La música se mezcla a -20 dB con "ducking" bajo la voz y fundidos al principio y al final.
- Añade 20 s de pantalla final (end screen) para los elementos de YouTube.
- --borrador: si falta la voz, usa silencio con la duración estimada (para probar la cadena).
"""
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from guion import trocear_subs, ts  # noqa: E402

W, H, FPS = 1920, 1080, 30
PAUSA = 0.35
END_SCREEN = 20


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(" ".join(map(str, cmd))[:300] + "\n" + r.stderr[-1500:])
    return r.stdout


def dur(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]))


def kenburns(img, segs, out, k):
    frames = int(segs * FPS) + 1
    z = "min(zoom+0.0006,1.18)" if k % 2 == 0 else "if(eq(on,0),1.18,max(zoom-0.0006,1.0))"
    x = "iw/2-(iw/zoom/2)" if k % 3 else "(iw-iw/zoom)*on/%d" % frames
    vf = (f"scale=2880:1620:force_original_aspect_ratio=increase,crop=2880:1620,"
          f"zoompan=z='{z}':x='{x}':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},format=yuv420p")
    sh(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf, "-t", f"{segs:.3f}", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "18", "-an", out])


def clip_seg(clip, img, segs, out, k, tmp):
    c = dur(clip)
    if segs <= c:
        sh(["ffmpeg", "-y", "-i", clip, "-t", f"{segs:.3f}", "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", out]); return
    a, b = tmp / f"{k}_a.mp4", tmp / f"{k}_b.mp4"
    sh(["ffmpeg", "-y", "-i", clip, "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", a])
    kenburns(img, segs - c, b, k)
    lista = tmp / f"{k}_l.txt"; lista.write_text(f"file '{a}'\nfile '{b}'\n")
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", out])


def main():
    carpeta = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    musica = Path(args[args.index("--musica") + 1]).resolve() if "--musica" in args else None
    borrador = "--borrador" in args
    quemar = "--quemar-subs" in args
    data = json.loads((carpeta / "escenas.json").read_text())
    tmp = carpeta / "_tmp"; tmp.mkdir(exist_ok=True)
    segs_v, audios, subs, t = [], [], [], 0.0
    caps, vistos = [], set()
    for k, e in enumerate(data["escenas"]):
        img = carpeta / e["imagen"]
        voz = carpeta / "voz" / f'{e["id"]}.mp3'
        if not img.exists():
            raise SystemExit(f"Falta la imagen {img}")
        if voz.exists():
            dv = dur(voz)
        elif borrador:
            dv = e["duracion"]
            voz = tmp / f'{e["id"]}_sil.wav'
            sh(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{dv:.3f}", voz])
        else:
            raise SystemExit(f"Falta la voz {voz}")
        segs = dv + PAUSA
        out = tmp / f"v{k:03d}.mp4"
        clip = carpeta / e["clip"] if e.get("clip") else None
        if clip and clip.exists():
            clip_seg(str(clip), str(img), segs, out, k, tmp)
        else:
            kenburns(str(img), segs, out, k)
        segs_v.append(out); audios.append((voz, segs))
        if e["capitulo"] not in vistos:
            vistos.add(e["capitulo"]); caps.append(f'{ts(t)} {e["capitulo"]}')
        subs += trocear_subs(e["texto"], t, dv)
        t += segs
        print(f'  escena {e["id"]} {segs:5.1f}s', flush=True)
    # pantalla final
    fin = tmp / "endscreen.mp4"
    kenburns(str(carpeta / data["escenas"][-1]["imagen"]), END_SCREEN, fin, 1)
    segs_v.append(fin)
    total = t + END_SCREEN
    # vídeo concatenado
    lista = tmp / "lista.txt"; lista.write_text("".join(f"file '{p}'\n" for p in segs_v))
    video = tmp / "video.mp4"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-c", "copy", video])
    # pista de voz: cada mp3 rellenado hasta su duración de escena
    partes = []
    for i, (a, s) in enumerate(audios):
        p = tmp / f"a{i:03d}.wav"
        sh(["ffmpeg", "-y", "-i", a, "-af", f"aresample=44100,aformat=channel_layouts=stereo,apad", "-t", f"{s:.3f}", p])
        partes.append(p)
    la = tmp / "la.txt"; la.write_text("".join(f"file '{p}'\n" for p in partes))
    vozpista = tmp / "voz.wav"
    sh(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", la, "-af", f"apad,loudnorm=I=-16:TP=-1.5:LRA=11", "-t", f"{total:.3f}", vozpista])
    # subtítulos reales
    srt = carpeta / "subtitulos.srt"
    srt.write_text("".join(f"{i}\n{ts(a, True)} --> {ts(b, True)}\n{x}\n\n" for i, (a, b, x) in enumerate(subs, 1)), encoding="utf-8")
    if not borrador:
        (carpeta / "capitulos.txt").write_text("\n".join(caps) + "\n", encoding="utf-8")  # tiempos reales -> volver a ejecutar subida.py
    # mezcla final
    salida = carpeta / ("video_borrador.mp4" if borrador else "video_final.mp4")
    vf = []
    if quemar:
        estilo = "FontName=Inter,FontSize=17,Bold=1,PrimaryColour=&H00FFFFFF,BackColour=&H90100418,BorderStyle=3,Outline=6,Shadow=0,MarginV=36,MarginL=230,MarginR=230"
        vf = ["-vf", f"subtitles={srt}:force_style='{estilo}'"]
    if musica:
        filtro = (f"[2:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},volume=-20dB,afade=t=in:d=3,afade=t=out:st={total-6:.3f}:d=6[m];"
                  f"[m][1:a]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md];"
                  f"[1:a][md]amix=inputs=2:duration=first:normalize=0[a]")
        cmd = ["ffmpeg", "-y", "-i", video, "-i", vozpista, "-i", musica, "-filter_complex", filtro, "-map", "0:v", "-map", "[a]"]
    else:
        cmd = ["ffmpeg", "-y", "-i", video, "-i", vozpista, "-map", "0:v", "-map", "1:a"]
    cmd += vf + ["-c:v", "libx264" if quemar else "copy", "-preset", "medium", "-crf", "18",
                 "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", salida]
    if not quemar:
        cmd = [c for c in cmd if c not in ("-preset", "medium", "-crf", "18")]
    sh(cmd)
    print(f"OK {salida} ({total/60:.1f} min)")


if __name__ == "__main__":
    main()
