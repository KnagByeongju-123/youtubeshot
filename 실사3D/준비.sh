#!/bin/bash
# 실사 3D 준비: 블렌더(파이썬 모듈 bpy) + MPFB2(사람 만들기) + MakeHuman CC0 자료
# 사용: bash 실사3D/준비.sh   (저장소 맨 위 폴더에서, 약 3~5분)
set -e
cd "$(dirname "$0")/.."
if [ ! -x .bpy_venv/bin/python ]; then python3.11 -m venv .bpy_venv; .bpy_venv/bin/pip -q install bpy; fi
.bpy_venv/bin/python -c "import bpy;print('블렌더',bpy.app.version_string)"
export BLENDER_USER_RESOURCES=$PWD/models/blender_user
D=models/mpfb_dl; mkdir -p $D $BLENDER_USER_RESOURCES
UA="asset-fetcher/1.0"   # Poly Haven·MakeHuman 은 프로그램 이름이 없으면 403
if [ ! -d $BLENDER_USER_RESOURCES/extensions/user_default/mpfb ]; then
  URL=$(curl -s -A $UA https://extensions.blender.org/api/v1/extensions/ | python3 -c "import json,sys;print(next(e['archive_url'] for e in json.load(sys.stdin)['data'] if e['id']=='mpfb'))")
  curl -s -A $UA -L -o $D/mpfb.zip "$URL"
  .bpy_venv/bin/python -I 실사3D/_mpfb_설치.py $PWD/$D/mpfb.zip
fi
DATA=$BLENDER_USER_RESOURCES/extensions/.user/user_default/mpfb/data
for u in asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip functional/faceunits01.zip functional/visemes01.zip; do
  f=$D/$(basename $u); [ -f $f ] || curl -s -A $UA -L -o $f https://files.makehumancommunity.org/$u
  unzip -oq $f -d $DATA
done
echo "준비 끝: $DATA"
