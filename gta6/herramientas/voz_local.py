#!/usr/bin/env python3
"""Voz en off OFFLINE (sin coste ni claves): SVOX Pico, español de España, con
diccionario de pronunciación para los nombres en inglés y un retoque de audio
(tono algo más grave, ecualización, compresión y una sala corta) para que suene más cálida.

Requisito: apt-get install libttspico-utils
Uso: python3 voz_local.py ../01-mapa-leonida
Para cambiar luego a ElevenLabs: borrar voz/ y ejecutar voz_elevenlabs.py.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

PRONUNCIA = [  # (texto del guion, cómo debe leerlo una voz española)
    ("GTA Online", "ge te a onlain"), ("GTA+", "ge te a plus"), ("GTA", "ge te a"), ("PS5 Pro", "pe ese cinco pro"), ("PS5", "pe ese cinco"),
    ("PS4", "pe ese cuatro"), ("PS3", "pe ese tres"), ("PlayStation", "pleistéishon"), ("Xbox Series X y S", "équis box síries équis y ese"),
    ("Xbox Series", "équis box síries"), ("Xbox One", "équis box uan"), ("Xbox 360", "équis box trescientos sesenta"), ("Xbox", "équis box"), ("Series S", "síries ese"), ("Series X", "síries équis"),
    ("Rockstar Editor", "rókstar éditor"), ("Rockstar", "rókstar"), ("Take-Two", "teik tu"), ("Twitch", "tuich"), ("YouTube", "iutub"), ("Google", "gúgel"), ("Netflix", "nétflix"),
    ("Jason Duval", "yéison duval"), ("Jason", "yéison"), ("Lucia Caminos", "lusía caminos"), ("Lucia", "lusía"),
    ("Cal Hampton", "cal jámpton"), ("Brian Heder", "bráian jéder"), ("Brian", "bráian"), ("Boobie Ike", "búbi áik"), ("Boobie", "búbi"),
    ("Dre'Quan Priest", "drecuán príst"), ("Dre'Quan", "drecuán"), ("Real Dimez", "ríal dáims"), ("Bae-Luxe", "bei lux"), ("Roxy", "róxi"), ("Raul", "raúl"),
    ("Only Raw Records", "ónli ro récords"), ("Only Raw", "ónli ro"), ("Allied Crystal", "álaid crístal"),
    ("Vice City", "váis síti"), ("Grassrivers", "grasrívers"), ("Port Gellhorn", "port guéljorn"), ("Leonida Keys", "leonida kis"), ("Monte Kalaga", "monte kálaga"),
    ("Los Santos", "los santos"), ("Blaine County", "blein cáunti"), ("Las Venturas", "las venturas"), ("Paleto Bay", "paleto bei"), ("Cayo Perico", "cayo perico"),
    ("San Andreas", "san andréas"), ("Red Dead Redemption", "red ded redémpshon"), ("Red Dead Online", "red ded onlain"), ("Red Dead", "red ded"),
    ("Max Payne", "max pein"), ("Tommy Vercetti", "tómi verchéti"), ("Ray Liotta", "rei lióta"), ("Michael Mann", "máikel man"), ("Heat", "jit"),
    ("Michael", "máikel"), ("Franklin", "fránklin"), ("Trevor", "trévor"), ("Lester", "léster"), ("Lamar", "lamar"), ("Devin Weston", "dévin uéston"), ("Arthur Morgan", "árzur mórgan"), ("CJ", "si yei"),
    ("Strauss Zelnick", "stráus sélnik"), ("Karl Slatoff", "carl slátof"), ("Dan Clancy", "dan clánsi"),
    ("Extended Look", "exténded luk"), ("Vintage Vice City Pack", "víntach váis síti pak"), ("Ultimate", "áltimeit"),
    ("Love Is a Long Road", "lav is a long roud"), ("Tom Petty", "tom péti"), ("Hot Together", "jot tuguéder"), ("Pointer Sisters", "póinter sísters"),
    ("Flower in a Hurricane", "fláuer in a járiquein"), ("Justice", "yustís"), ("Tame Impala", "teim impala"), ("SZA", "sisa"),
    ("King Gizzard and the Lizard Wizard", "king guísard an de lísard uísard"), ("Bonnie y Clyde", "bóni y cláid"),
    ("Cfx.re", "ce efe equis punto erre e"), ("FiveM", "faiv em"), ("Mac", "mac"), ("Steam", "stim"), ("Florida Man", "flórida man"),
    ("Hombre de Florida", "hombre de flórida"), ("U.S. ARMY", "iu es ármi"), ("North Fort Law", "norz fort lo"),
    ("Zen 2", "sen dos"), ("AMD", "a eme de"), ("HDR", "ache de erre"), ("SSD", "ese ese de"), ("Rockstar Games", "rókstar géims"),
    ("Only", "ónli"), ("Marauder", "maróder"), ("Kortz", "korts"),
]
_RX = [(re.compile(r"(?<![\wáéíóúñ])" + re.escape(a) + r"(?![\wáéíóúñ])"), b) for a, b in PRONUNCIA]


def adaptar(texto):
    for rx, b in _RX: texto = rx.sub(b, texto)
    return texto.replace("—", ", ").replace("«", "").replace("»", "")


FILTRO = ("asetrate=16000*0.94,aresample=44100,atempo=1.04,"            # tono algo más grave sin cambiar la velocidad
          "highpass=f=70,lowpass=f=7600,equalizer=f=180:t=q:w=1:g=3,equalizer=f=3000:t=q:w=1.5:g=2,"
          "acompressor=threshold=-20dB:ratio=3:attack=10:release=200,aecho=0.8:0.5:35:0.12,"
          "loudnorm=I=-16:TP=-1.5:LRA=9")


def voz(texto, destino):
    with tempfile.TemporaryDirectory() as td:
        trozos = [t for t in re.split(r"(?<=[.?!])\s+", adaptar(texto)) if t.strip()]
        wavs = []
        for i, t in enumerate(trozos):  # pico2wave tiene límite de longitud: frase a frase
            w = Path(td) / f"{i}.wav"; subprocess.run(["pico2wave", "-l", "es-ES", "-w", str(w), t], check=True); wavs.append(w)
        lista = Path(td) / "l.txt"; lista.write_text("".join(f"file '{w}'\n" for w in wavs))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-af", FILTRO,
                        "-ar", "44100", "-b:a", "160k", str(destino)], check=True)


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]).resolve()
    escenas = json.loads((carpeta / "escenas.json").read_text())["escenas"]
    (carpeta / "voz").mkdir(exist_ok=True)
    for e in escenas:
        out = carpeta / "voz" / f'{e["id"]}.mp3'
        if out.exists() and out.stat().st_size > 1000: continue
        voz(e["texto"], out)
    print("voz OK", carpeta.name, len(escenas), "escenas")
