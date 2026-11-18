#!/usr/bin/env python3
"""Compone pistas synthwave originales (sin samples ni material de terceros) para usar de fondo.
Al ser generadas aquí desde cero, no hay licencias de terceros ni reclamaciones de Content ID.
Uso: python3 musica.py  -> gta6/musica/*.mp3
"""
import subprocess
from pathlib import Path
import numpy as np

SR = 44100
RAIZ = Path(__file__).resolve().parent.parent
NOTAS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def f(nota, octava):
    return 440.0 * 2 ** ((NOTAS[nota] + 12 * (octava - 4) - 9) / 12)


def saw(fr, n, det=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * fr * (1 + det)) % 1) - 1


def lowpass(x, corte):
    a = np.exp(-2 * np.pi * corte / SR)
    y = np.empty_like(x); acc = 0.0
    # filtro de un polo, vectorizado por bloques
    from scipy.signal import lfilter  # noqa
    return lfilter([1 - a], [1, -a], x)


def env(n, ataque, cola):
    e = np.ones(n)
    a = min(int(ataque * SR), n); c = min(int(cola * SR), n - a)
    e[:a] = np.linspace(0, 1, a)
    if c > 0: e[n - c:] = np.linspace(1, 0, c)
    return e


def pista(nombre, bpm, acordes, raiz_bajo, semilla, compases=64):
    rng = np.random.default_rng(semilla)
    beat = 60 / bpm; compas = 4 * beat
    n_total = int(compas * compases * SR)
    pad = np.zeros(n_total); bajo = np.zeros(n_total); arp = np.zeros(n_total); bat = np.zeros(n_total)
    nc = int(compas * SR)
    for c in range(compases):
        acorde = acordes[c % len(acordes)]
        i0 = c * nc
        # pad: 3 notas, 2 osciladores desafinados
        p = sum(saw(f(nt, oc), nc, d) for nt, oc in acorde for d in (-0.004, 0.004))
        pad[i0:i0 + nc] += lowpass(p, 900 + 500 * np.sin(c / 6)) * env(nc, 0.4, 0.4) * 0.09
        # bajo en corcheas
        nt, oc = raiz_bajo[c % len(raiz_bajo)]
        nn = int(beat / 2 * SR)
        for k in range(8):
            s = i0 + k * nn
            bajo[s:s + nn] += lowpass(saw(f(nt, oc), nn), 380) * env(nn, 0.005, 0.12) * 0.32
        # arpegio en semicorcheas (a partir del compás 8)
        if c >= 8:
            ns = int(beat / 4 * SR)
            notas = [(acorde[i % 3][0], acorde[i % 3][1] + 1) for i in (0, 1, 2, 1)]
            for k in range(16):
                nt2, oc2 = notas[k % 4]
                s = i0 + k * ns
                arp[s:s + ns] += lowpass(saw(f(nt2, oc2), ns), 2200) * env(ns, 0.003, 0.08) * 0.05
        # batería suave (a partir del compás 4): bombo en 1 y 3, caja en 2 y 4, charles en corcheas
        if c >= 4:
            nb = int(0.35 * SR); t = np.arange(nb) / SR
            kick = np.sin(2 * np.pi * (45 + 90 * np.exp(-t * 30)) * t) * np.exp(-t * 9) * 0.55
            nsn = int(0.25 * SR); tn = np.arange(nsn) / SR
            snare = lowpass(rng.standard_normal(nsn), 3500) * np.exp(-tn * 18) * 0.18
            nh = int(0.05 * SR)
            for b in range(4):
                s = i0 + int(b * beat * SR)
                if b in (0, 2): bat[s:s + nb] += kick[: n_total - s]
                else: bat[s:s + nsn] += snare[: n_total - s]
                for h in (0, 0.5):
                    sh = s + int(h * beat * SR)
                    bat[sh:sh + nh] += np.diff(rng.standard_normal(nh + 1)) * np.exp(-np.arange(nh) / SR * 80) * 0.035
    # eco sencillo en el arpegio y "sidechain" del pad con el bombo
    d = int(beat * 0.75 * SR); arp[d:] += arp[:-d] * 0.35
    lfo = 1 - 0.35 * np.clip(np.cos(2 * np.pi * np.arange(n_total) / (beat * SR)) , 0, 1) ** 4
    mezcla = pad * lfo + bajo * lfo + arp + bat
    mezcla *= env(n_total, 0.02, 0.02)  # sin fundidos largos: la pista se repite en bucle y montaje.py hace los fundidos
    mezcla = np.tanh(mezcla * 1.4) / np.tanh(1.4)
    est = np.stack([mezcla, np.roll(mezcla, int(0.012 * SR)) * 0.96], 1)
    est /= np.abs(est).max() * 1.12
    out = RAIZ / "musica"; out.mkdir(exist_ok=True)
    wav = out / f"{nombre}.wav"
    import wave
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((est * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5", "-b:a", "192k", out / f"{nombre}.mp3"], check=True)
    wav.unlink()
    print(nombre, f"{n_total / SR / 60:.1f} min")


if __name__ == "__main__":
    pista("01_atardecer_en_leonida", 92, [[("A", 3), ("C", 4), ("E", 4)], [("F", 3), ("A", 3), ("C", 4)], [("C", 4), ("E", 4), ("G", 4)], [("G", 3), ("B", 3), ("D", 4)]],
          [("A", 1), ("F", 1), ("C", 2), ("G", 1)], 1)
    pista("02_autopista_neon", 104, [[("D", 3), ("F", 3), ("A", 3)], [("A#", 2), ("D", 3), ("F", 3)], [("F", 3), ("A", 3), ("C", 4)], [("C", 3), ("E", 3), ("G", 3)]],
          [("D", 1), ("A#", 0), ("F", 1), ("C", 1)], 2)
    pista("03_expediente_nocturno", 84, [[("E", 3), ("G", 3), ("B", 3)], [("C", 3), ("E", 3), ("G", 3)], [("A", 2), ("C", 3), ("E", 3)], [("B", 2), ("D#", 3), ("F#", 3)]],
          [("E", 1), ("C", 1), ("A", 0), ("B", 0)], 3)
