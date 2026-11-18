# 4 · Escenas: qué hay que generar y coste

## Decisiones tomadas (me pediste que eligiera yo)
- **Plan A**: 1 imagen por escena (445 en total) y 54 clips de 8 s de Veo 3.1 Lite. Es lo más barato que mantiene el ritmo, porque el movimiento Ken Burns evita las imágenes estáticas. Si un vídeo retiene mal, se rehacen solo sus escenas largas con una segunda imagen.
- **Orden de generación**: vídeo 09 primero, como piloto, para revisar el estilo y el coste real antes de hacer los otros 9. Después 08, 10 y el resto por número.
- **Voz**: narrador masculino en **español de España**, tono documental cercano. Buscarla en la Voice Library de ElevenLabs con los filtros Spanish, Spain y Narration. Si no hay ninguna que convenza, la de respaldo es la voz prediseñada **«Adam» (`pNInz6obpgDQGcFmaJgB`)** con el modelo `eleven_multilingual_v2`, aunque tiene algo de acento. Ajustes en `herramientas/voz_elevenlabs.py`: estabilidad 0.45, similitud 0.8, estilo 0.15.
- **Música**: ✅ **hecha**. Son 3 pistas synthwave **compuestas desde cero** con `herramientas/musica.py`, sin samples ni material de terceros, así que no hay licencias que pagar ni reclamaciones de Content ID. Están en `musica/`:
  - `01_atardecer_en_leonida.mp3` → vídeos 01, 04, 07 y 10
  - `02_autopista_neon.mp3` → vídeos 02, 05 y 08
  - `03_expediente_nocturno.mp3` → vídeos 03, 06 y 09
  Si prefieres algo más profesional, cámbialas por pistas de la Biblioteca de audio de YouTube con el mismo nombre de archivo.


## Tarifa real de Eviolite (de tu captura, 18/11/2026)
- Pack de 400 créditos por 8 € (unos 100 clips de Veo 3.1 Lite), pack de 1.200 por 20 €, o a medida a 1,67 céntimos el crédito. Los créditos de los packs no caducan.
- **Plan Creator a 19 €/mes:** 1.600 créditos (unos 400 clips de Veo 3.1 Lite), más imágenes de **Meta AI incluidas** (hasta 300 al día).
- De ahí sale que **1 clip de Veo 3.1 Lite cuesta unos 4 créditos**. La captura **no muestra lo que cuesta una imagen de Nano Banana** (N créditos): se ve al elegir el modelo en el generador.

| Vídeo | Imágenes | Clips | Créditos en clips | Total = clips + imágenes × N |
|---|---|---|---|---|
| 01-mapa-leonida | 41 | 7 | 28 | 28 + 41·N |
| 02-jason-lucia-historia | 41 | 5 | 20 | 20 + 41·N |
| 03-personajes-confirmados | 45 | 6 | 24 | 24 + 45·N |
| 04-secretos-trailers | 43 | 5 | 20 | 20 + 43·N |
| 05-mecanicas-extended-look | 47 | 6 | 24 | 24 + 47·N |
| 06-vehiculos-trailers | 48 | 6 | 24 | 24 + 48·N |
| 07-misiones-atracos | 45 | 5 | 20 | 20 + 45·N |
| 08-gta6-pc-requisitos | 45 | 5 | 20 | 20 + 45·N |
| 09-antes-de-jugar-212gb-ediciones | 44 | 4 | 16 | 16 + 44·N |
| 10-gta6-online | 46 | 5 | 20 | 20 + 46·N |
| **TOTAL** | **445** | **54** | **216** | **216 + 445·N** |

- **Si N = 2:** 216 + 890 = **1.106 créditos**. Con el plan Creator (1.600 créditos) **sobra para los 10 vídeos**, con unos 490 de margen para repetir escenas.
- **Si N = 3:** 216 + 1.335 = **1.551 créditos**, justo dentro del plan.
- **Si N > 3:** las imágenes de relleno se hacen con Meta AI, que va incluido en el plan, y Nano Banana se reserva para las escenas clave y las miniaturas.

**Elección: plan Creator (19 €, un mes).** Es el que deja más créditos por euro (1,19 céntimos el crédito, frente a 1,67 en pack) e incluye imágenes de Meta AI como red de seguridad. Puedes cancelarlo al acabar el mes.

No se ha generado **nada** todavía. Como pediste, esperamos a tu OK. Además hay dos bloqueos:
1. **No hay acceso a Eviolite desde esta sesión.** No aparece ningún conector ni API de Eviolite, y tampoco he encontrado su tabla de precios en la web. Por eso **no puedo darte la cifra exacta en créditos**: te doy las cantidades exactas por vídeo y la fórmula. Con tu tarifa sale el número al momento.
2. **ElevenLabs, «voz X»:** falta saber qué voz quieres (nombre o ID) y una clave de API.

## Plan de generación por vídeo
- **Imagen (Nano Banana, 16:9, 1920x1080):** 1 por escena. Las escenas duran unos 20 s y llevan un movimiento lento de cámara (Ken Burns).
- **Clip (Veo 3.1 Lite, 8 s, sin audio, a partir de la imagen de la escena):** solo en las escenas clave: el gancho, los momentos fuertes y el cierre.
- Los prompts están listos en `NN-…/prompts.csv`. Usan el estilo común de `herramientas/estilo.json` y un prompt negativo que excluye texto, logos, capturas y personajes oficiales.

| Vídeo | Imágenes | Clips de 8 s | Segundos de Veo | Créditos = img × **P_img** + seg × **P_seg_veo** |
|---|---|---|---|---|
| 01 Mapa de Leonida | 41 | 7 | 56 | 41·P_img + 56·P_seg |
| 02 Jason y Lucia | 41 | 5 | 40 | 41·P_img + 40·P_seg |
| 03 Personajes | 45 | 6 | 48 | 45·P_img + 48·P_seg |
| 04 Secretos de los tráileres | 43 | 5 | 40 | 43·P_img + 40·P_seg |
| 05 Mecánicas | 47 | 6 | 48 | 47·P_img + 48·P_seg |
| 06 Vehículos | 48 | 6 | 48 | 48·P_img + 48·P_seg |
| 07 Misiones y atracos | 45 | 5 | 40 | 45·P_img + 40·P_seg |
| 08 PC y requisitos | 45 | 5 | 40 | 45·P_img + 40·P_seg |
| 09 Antes de jugar | 44 | 4 | 32 | 44·P_img + 32·P_seg |
| 10 GTA 6 Online | 46 | 5 | 40 | 46·P_img + 40·P_seg |
| **TOTAL** | **445** | **54** | **432** | 445·P_img + 432·P_seg |

Si Eviolite cobra **por clip** y no por segundo, usa 54·P_clip. Suma un **~15 % de margen** para repetir las imágenes que salgan mal, por ejemplo con texto colado o rostros reconocibles.

**Opción B, más dinámica:** 2 imágenes por escena (unos 10 s cada una). Son 890 imágenes en total y mejora la retención, pero duplica el coste en imágenes.

### Referencia de mercado (NO son precios de Eviolite)
Otras plataformas con los mismos modelos publican, por ejemplo, unos 3–120 créditos por imagen de Nano Banana y unos 40–100 créditos por segundo de Veo 3.1. La horquilla es enorme, así que hace falta la tarifa real de Eviolite.

## Voz (ElevenLabs)
Unos 12.500–13.000 caracteres por vídeo, **127.108 caracteres en total**, con el modelo `eleven_multilingual_v2`. Los créditos de ElevenLabs equivalen más o menos a caracteres según el plan, así que haría falta un plan con unos 130 K caracteres o más, más margen para repeticiones.


## Qué falta para generar (bloqueado)
Esta sesión **no tiene red hacia `eviolite.app` ni hacia `api.elevenlabs.io`**, y los formularios para guardar las claves se rechazaron. Para desbloquearlo, elige una de estas vías:
1. **Eviolite como conector (recomendado):** en https://claude.ai/customize/connectors, añade un conector personalizado con la URL `https://eviolite.app/api/mcp`, autorízalo y **abre una sesión nueva** sobre esta rama. Los conectores se cargan al empezar la sesión.
2. **Claves de API:** créalas en Eviolite (My account) y en ElevenLabs y guárdalas como *network secrets* en la configuración del entorno de la nube (`eviolite.app`; `api.elevenlabs.io` con la cabecera `xi-api-key`). Con eso se abren también esos dominios.
3. **Manual:** genera tú en Eviolite con `NN-…/prompts.csv` y deja `escenas/E01.png`, `E01.mp4`… Y la voz en `voz/E01.mp3`… Lo demás se monta con `montaje.py`.
