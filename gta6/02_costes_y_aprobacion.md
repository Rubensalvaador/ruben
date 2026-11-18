# 4 · Escenas: qué hay que generar y coste (PENDIENTE DE TU OK)

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

## Música con licencia
No puedo comprar ni descargar licencias por ti. Opciones:
- **Biblioteca de audio de YouTube** (gratis, sin reclamaciones). Descarga 2–3 pistas synthwave o retrowave y déjalas en `gta6/musica/`.
- Epidemic Sound o Artlist, si tienes suscripción; recuerda añadir tu canal a la licencia.

## Qué necesito de ti para seguir
1. **OK al plan de escenas** (A o B) y la **tarifa de Eviolite**, o acceso a su API o conector. Si no hay API, también puedes generar tú con `prompts.csv` y dejar los archivos en `NN-…/escenas/E01.png`, `E01.mp4`…
2. **Voz de ElevenLabs** (nombre o ID) y la clave. Te la pediré con un formulario seguro; nunca la pegues en el chat.
3. **Música:** pistas en `gta6/musica/`.
