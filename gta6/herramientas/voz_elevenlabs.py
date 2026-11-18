#!/usr/bin/env python3
"""Genera la voz en off de cada escena con la API de ElevenLabs (un mp3 por escena).

Requisitos:
  - Variable ELEVENLABS_VOICE_ID con el ID de la voz elegida.
  - La clave de API la inyecta el proxy del entorno en la cabecera xi-api-key
    (o, en local, variable ELEVENLABS_API_KEY).
Uso: python3 voz_elevenlabs.py ../01-mapa-leonida [--solo E01,E02]
"""
import json, os, sys, time, urllib.request
from pathlib import Path

MODELO = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
AJUSTES = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True}


def tts(texto, voz, destino, anterior="", siguiente=""):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_192"
    cuerpo = {"text": texto, "model_id": MODELO, "voice_settings": AJUSTES,
              "previous_text": anterior, "next_text": siguiente}  # mantiene la entonación entre escenas
    req = urllib.request.Request(url, data=json.dumps(cuerpo).encode(), method="POST", headers={
        "Content-Type": "application/json", "Accept": "audio/mpeg",
        "xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "inyectada-por-proxy")})
    for intento in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                destino.write_bytes(r.read()); return
        except Exception as e:
            if intento == 3: raise
            time.sleep(2 ** intento * 3)


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]).resolve()
    solo = set(sys.argv[sys.argv.index("--solo") + 1].split(",")) if "--solo" in sys.argv else None
    voz = os.environ["ELEVENLABS_VOICE_ID"]
    escenas = json.loads((carpeta / "escenas.json").read_text())["escenas"]
    (carpeta / "voz").mkdir(exist_ok=True)
    for i, e in enumerate(escenas):
        if solo and e["id"] not in solo: continue
        out = carpeta / "voz" / f'{e["id"]}.mp3'
        if out.exists() and out.stat().st_size > 1000: continue
        tts(e["texto"], voz, out,
            escenas[i - 1]["texto"] if i else "", escenas[i + 1]["texto"] if i + 1 < len(escenas) else "")
        print("voz", e["id"], out.stat().st_size // 1024, "KB", flush=True)
