# Vídeo 09 · registro de producción (18/11/2026)

## Créditos de Eviolite
- Saldo al empezar esta tarea: **1.591** → al acabar: **1.433** → **158 gastados** (tope aprobado: 160; además, 3 de la prueba anterior de E02 que no se pudo descargar).
- Nano Banana 2 (`sg_nano_banana_2`, 2K, landscape): **3 créditos/imagen**. Veo 3.1 Lite (`sg_veo_lite`, 8 s, 1080p): **4 créditos/clip**.
- 44 imágenes válidas (132) + 2 clips (8) = 140. Los **18 restantes se perdieron en 6 llamadas** que devolvieron un error 502 o «server draining» del conector **después de cobrar**, sin devolver el enlace ni el id (no se pudieron recuperar con `eviolite_estado`). Afectó a E03, E08, E27 (dos veces), E32 y E37, que se regeneraron.

## Qué hay en `escenas/` (no se sube a git)
- `E01.png` … `E44.png`: 1920x1080, recortadas desde 2K.
- `E01.mp4` (clip de Veo **recortado a 5 s**: a partir de 5,1 s aparecía el texto «100%» en neón; el resto de la escena va con Ken Burns sobre `E01.png`).
- `E44.mp4` (clip de Veo de 7,8 s, sin texto).
- **E07 y E14 se quedaron sin clip** para no pasar del tope de créditos tras las pérdidas: el montaje usa su imagen con Ken Burns.

## Retoques locales (sin gastar créditos)
Texto legible generado por la IA, desenfocado con PIL:
- E19: carteles de neón «HOTEL» y otros de la calle de la postal.
- E30: precios «$29.99» de las dos etiquetas.
- E32: calendario con «SAVINGS GOAL: SUNSET».

Revisadas y aceptadas: E04 (un «18» borroso en el calendario), E03 y E41 (números de reloj), E05, E24 y E25 (consolas con un diseño parecido al de modelos reales, aunque sin logos).

## Resultado
- Voz: `voz_local.py` (pico2wave, es-ES), 44 pistas en `voz/`, 16,4 min.
- `video_final.mp4`: **17:01** (1.020,9 s), 1920x1080 a 30 fps, voz a -16 LUFS, música `03_expediente_nocturno.mp3` con ducking, subtítulos quemados y 20 s de pantalla final.
- `subtitulos.srt` y `capitulos.txt` con los tiempos reales; `subida.md` regenerado.
- Corregido `montaje.py`: los márgenes de los subtítulos quemados estaban en píxeles de 1080p, pero libass usa la escala 384x288 para los SRT, así que salían palabra a palabra.

## Pendiente a mano
- Escuchar la voz completa: pico2wave es una voz sintética básica. Si no convence, cambiarla por la de ElevenLabs (`voz_elevenlabs.py`) y volver a ejecutar `montaje.py` y `subida.py`.
- Al subir: marcar «contenido alterado o sintético» y sustituir `{enlace_siguiente}`, `{musica}` y `{playlist}` en la descripción.
