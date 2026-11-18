#!/usr/bin/env python3
"""Voz en off con Piper (TTS neuronal, offline y gratis): voz es_ES «davefx» (masculina, España).
Suena mucho más natural que pico2wave (voz_local.py). Reutiliza su diccionario de pronunciación.

Requisitos: pip install piper-tts  y los modelos en herramientas/modelos/ (no van a git):
  https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx
  https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json
Uso: python3 voz_piper.py ../09-antes-de-jugar-212gb-ediciones [--voz es_ES-sharvard-medium] [--rehacer]
"""
import json, subprocess, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from voz_local import adaptar  # noqa: E402

MODELOS = Path(__file__).parent / "modelos"
VELOCIDAD = 1.0       # length_scale de Piper: >1 más lento
FILTRO = ("highpass=f=70,equalizer=f=200:t=q:w=1:g=1.5,equalizer=f=3500:t=q:w=1.5:g=1.5,"
          "acompressor=threshold=-20dB:ratio=2.5:attack=10:release=200,loudnorm=I=-16:TP=-1.5:LRA=9")


def voz(texto, destino, modelo):
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "v.wav"
        subprocess.run(["piper", "-m", str(modelo), "-f", str(wav), "--length-scale", str(VELOCIDAD),
                        "--sentence-silence", "0.25"], input=adaptar(texto), text=True, check=True, capture_output=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-af", FILTRO,
                        "-ar", "44100", "-b:a", "160k", str(destino)], check=True)


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]).resolve()
    args = sys.argv[2:]
    nombre = args[args.index("--voz") + 1] if "--voz" in args else "es_ES-davefx-medium"
    modelo = MODELOS / f"{nombre}.onnx"
    if not modelo.exists():
        raise SystemExit(f"Falta el modelo {modelo} (ver cabecera del script)")
    escenas = json.loads((carpeta / "escenas.json").read_text())["escenas"]
    (carpeta / "voz").mkdir(exist_ok=True)
    for e in escenas:
        out = carpeta / "voz" / f'{e["id"]}.mp3'
        if "--rehacer" not in args and out.exists() and out.stat().st_size > 1000:
            continue
        voz(e["texto"], out, modelo)
        print(" ", e["id"], flush=True)
    print("voz OK", carpeta.name, len(escenas), "escenas,", nombre)
