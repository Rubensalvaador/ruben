# Expediente Leonida · 10 vídeos largos sobre GTA 6

Canal de YouTube en español: análisis de GTA 6 separando **dato confirmado** de **especulación**.

## Estructura
```
gta6/
├── 01_investigacion.md          ← búsquedas, datos de demanda y por qué estos 10 temas
├── 02_costes_y_aprobacion.md    ← imágenes/clips por vídeo, fórmula de créditos, lo que falta para generar
├── canal/                       ← nombres, «acerca de», logo y banner (maquetas)
├── herramientas/                ← scripts (ver abajo) + estilo visual + metadatos
└── NN-tema/
    ├── guion.md                 ← guion de ~15 min, con capítulos y escenas
    ├── escenas.json             ← escenas con texto, tiempos, prompt e imagen/clip de destino
    ├── prompts.csv              ← prompts para Nano Banana / Veo 3.1 Lite
    ├── subtitulos_borrador.srt  ← subtítulos con tiempos estimados (los reales los genera montaje.py)
    ├── capitulos.txt            ← capítulos para la descripción
    ├── miniatura.jpg            ← 1280x720 (fondo provisional; versión final sobre imagen Nano Banana)
    ├── subida.md                ← 3 títulos, descripción con capítulos, 10 etiquetas, ajustes de Studio
    ├── escenas/                 ← (pendiente) E01.png, E01.mp4…
    └── voz/                     ← (pendiente) E01.mp3…
```

## Herramientas
| Script | Qué hace |
|---|---|
| `herramientas/guion.py` | Lee los `guion.md` y genera `escenas.json`, `prompts.csv`, `capitulos.txt` y los subtítulos de borrador. También informa de la duración, las escenas y la duración del gancho |
| `herramientas/voz_elevenlabs.py` | Genera un mp3 por escena con la API de ElevenLabs (`ELEVENLABS_VOICE_ID`) y mantiene la entonación entre escenas |
| `herramientas/montaje.py` | Monta el vídeo en 1920x1080 a 30 fps: Ken Burns sobre las imágenes, clips de Veo, voz normalizada a -16 LUFS, música a -20 dB con ducking, subtítulos (en archivo y opcionalmente quemados) y 20 s de pantalla final. Reescribe los capítulos con los tiempos reales. **Probado** con material provisional |
| `herramientas/arte.py` | Miniaturas, logo y banner. `miniaturas --fondo escenas/E01.png` para la versión final |
| `herramientas/musica.py` | Compone las 3 pistas synthwave originales de `musica/` |
| `herramientas/subida.py` | Genera `subida.md` a partir de `metadatos.json` y `capitulos.txt` |

Flujo por vídeo, cuando haya escenas y voz:
```bash
cd gta6/herramientas
python3 voz_elevenlabs.py ../01-mapa-leonida
python3 montaje.py ../01-mapa-leonida --musica ../musica/pista1.mp3 --quemar-subs
python3 subida.py            # actualiza los capítulos con los tiempos reales
python3 arte.py miniaturas --fondo escenas/E01.png
```

## Estado de cada vídeo
| # | Vídeo | Guion | Escenas (img/clips) | Voz | Montaje | Miniatura | Títulos, descripción y etiquetas |
|---|---|---|---|---|---|---|---|
| 01 | Mapa de Leonida | ✅ 15,2 min | ⏳ 41 / 7 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 02 | Jason y Lucia | ✅ 15,3 min | ⏳ 41 / 5 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 03 | Personajes confirmados | ✅ 15,0 min | ⏳ 45 / 6 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 04 | Secretos de los tráileres | ✅ 15,1 min | ⏳ 43 / 5 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 05 | Mecánicas (Extended Look) | ✅ 15,0 min | ⏳ 47 / 6 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 06 | Vehículos | ✅ 15,0 min | ⏳ 48 / 6 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 07 | Misiones y atracos | ✅ 15,1 min | ⏳ 45 / 5 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 08 | PC y requisitos | ✅ 15,0 min | ⏳ 45 / 5 | ⏳ | ⏳ | 🟡 provisional | ✅ |
| 09 | Antes de jugar (212 GB) | ✅ 15,0 min | ✅ 44 / 2 | ✅ Piper | ✅ 12:41 | ✅ | ✅ |
| 10 | GTA 6 Online | ✅ 14,8 min* | ⏳ 46 / 5 | ⏳ | ⏳ | 🟡 provisional | ✅ |

\*Más 20 s de pantalla final; todos superan los 15 min. Las duraciones están estimadas a unas 153 palabras por minuto, así que la voz real puede variar ±10 %.
⏳ = bloqueado por el acceso a Eviolite y ElevenLabs (ver `02_costes_y_aprobacion.md`). **Música: ✅ 3 pistas originales en `musica/`.**

## Pendiente a mano
1. **Dar acceso a Eviolite**: conector `https://eviolite.app/api/mcp` en claude.ai y una sesión nueva, o una API key como network secret. Las decisiones del plan ya están tomadas.
2. **Dar acceso a ElevenLabs** (API key como network secret con la cabecera `xi-api-key`). La voz ya está elegida (ver `02_costes_y_aprobacion.md`).
3. ~~Música~~ ✅ hecha (`musica/`, original).
4. **Revisar cada guion** contra la web oficial de Rockstar. Desde aquí no se pudo abrir y los datos vienen de la prensa vía buscador. Hay que prestar especial atención a: el precio y lo que incluye la Ultimate, la fecha de la precarga, los 30 fps (marcado como rumor), las descripciones de las regiones y lo que dicen exactamente las fichas de los personajes.
5. **Comprobar las sugerencias de YouTube** y la competencia en español (no se pudieron consultar desde aquí).
6. **Crear el canal** (comprobar que `@ExpedienteLeonida` está libre) y subir el logo y el banner.
7. Al subir: sustituir `{enlace_siguiente}`, `{musica}` y `{playlist}` en las descripciones, subir `subtitulos.srt`, configurar la pantalla final y marcar «contenido alterado» si alguna imagen parece realista.
