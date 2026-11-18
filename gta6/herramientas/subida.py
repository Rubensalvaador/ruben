#!/usr/bin/env python3
"""Genera subida.md (títulos, descripción con capítulos, etiquetas) para cada vídeo."""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
meta = json.loads((RAIZ / "herramientas" / "metadatos.json").read_text())
orden = list(meta)
PIE = """—
🔎 En Expediente Leonida separamos siempre lo CONFIRMADO (tráileres, web y anuncios oficiales de Rockstar/Take-Two) de la ESPECULACIÓN, que se dice en voz alta.

⚠️ Canal no afiliado a Rockstar Games ni a Take-Two Interactive. Grand Theft Auto, GTA y Rockstar Games son marcas de sus respectivos propietarios.
🎨 Todas las imágenes y clips son ilustraciones originales generadas con IA (sin capturas, logotipos ni material oficial del juego).
🎵 Música: {musica}
📺 Serie completa de GTA 6: {playlist}
"""

for i, (carpeta, m) in enumerate(meta.items()):
    caps = (RAIZ / carpeta / "capitulos.txt").read_text().strip()
    sig = orden[(i + 1) % len(orden)]
    desc = f"""{m['intro']}

⏱️ CAPÍTULOS
{caps}

▶️ Siguiente vídeo: {meta[sig]['titulos'][0]} → {{enlace_siguiente}}

{PIE}
#GTA6 #GTAVI #Leonida"""
    md = f"""# Ficha de subida · {carpeta}

## Títulos (elige uno; el primero es el recomendado)
1. {m['titulos'][0]}
2. {m['titulos'][1]}
3. {m['titulos'][2]}

## Miniatura
`miniatura.jpg` (1280x720) · texto: **{m['miniatura']['linea1']} / {m['miniatura']['linea2']}**
Versión final: regenerar sobre la imagen de Nano Banana con `python3 herramientas/arte.py miniaturas --fondo escenas/E01.png`.

## Descripción (copiar y pegar; sustituir lo que va entre llaves)
```
{desc}
```
> Los minutos de los capítulos se calculan a partir del guion. Tras montar con la voz real, `montaje.py` reescribe `subtitulos.srt`; vuelve a ejecutar `guion.py` + `subida.py` si cambian los tiempos, o ajústalos a mano viendo el vídeo.

## Etiquetas (10)
{", ".join(m['etiquetas'])}

## Ajustes en YouTube Studio
- Idioma: español · Subtítulos: subir `subtitulos.srt`
- Contenido alterado o sintético: las ilustraciones no son realistas; actívalo si alguna escena lo parece (política de YouTube).
- Público: no creado para niños · Categoría: Videojuegos
- Pantalla final (últimos 20 s): «{meta[sig]['titulos'][0]}» + botón de suscripción
"""
    (RAIZ / carpeta / "subida.md").write_text(md, encoding="utf-8")
    print("subida.md", carpeta)
