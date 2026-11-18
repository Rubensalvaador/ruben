#!/usr/bin/env bash
# Produce de principio a fin los vídeos indicados (o todos): escenas, clips, voz, montaje, miniatura y ficha de subida.
# Uso: ./producir.sh 09-antes-de-jugar-212gb-ediciones 08-gta6-pc-requisitos ...
set -euo pipefail
cd "$(dirname "$0")"
declare -A MUSICA=([01]=01_atardecer_en_leonida [04]=01_atardecer_en_leonida [07]=01_atardecer_en_leonida [10]=01_atardecer_en_leonida
                   [02]=02_autopista_neon [05]=02_autopista_neon [08]=02_autopista_neon
                   [03]=03_expediente_nocturno [06]=03_expediente_nocturno [09]=03_expediente_nocturno)
VIDEOS=("$@"); [ ${#VIDEOS[@]} -eq 0 ] && VIDEOS=($(cd .. && ls -d [0-9][0-9]-*))
for v in "${VIDEOS[@]}"; do
  n=${v:0:2}; d=../$v
  echo "== $v: escenas"; python3 escenas_proc.py $d
  echo "== $v: voz";     python3 voz_local.py $d
  echo "== $v: montaje"; python3 montaje.py $d --musica ../musica/${MUSICA[$n]}.mp3 --quemar-subs
  rm -rf $d/_tmp
  echo "== $v: listo"
done
python3 subida.py >/dev/null
python3 arte.py miniaturas --fondo escenas/E01.png
echo "TODO OK"
