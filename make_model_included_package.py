# -*- coding: utf-8 -*-
"""Create a portable transfer ZIP from a working Supertonic installation.

Requires Python 3.11. Does not copy a non-portable Windows virtualenv or
private configuration/API keys. Another PC needs Python 3.11; installer can
fetch platform-specific wheels via internet.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED, ZIP64_LIMIT
import sys

BASE = Path(__file__).resolve().parent
FILES = [
    'shorts_novel_maker_supertonic.py',
    '한국어_읽기.py',
    '읽기사전.txt',
    '읽기_미리보기.bat',
    '나레이션_검증.py',
    '썸네일_후보_만들기.py',
    '썸네일_후보_만들기.bat',
    '썸네일_합성.py',
    '쇼츠_자동.py',
    '영어_번역.py',
    '콘텐츠_정리.py',
    '새영상_한편만들기.bat',
    '썸네일_엔진.py',
    '썸네일_엔진_LICENSE.txt',
    '썸네일_편집기.py',
    '썸네일_영상캡처.py',
    '썸네일_편집기.bat',
    '콘텐츠_정리.bat',
    '유튜브_정책.py',
    'supertonic_local_worker.py',
    'supertonic_voice_test.py',
    'setup_supertonic_windows.bat',
    'run_shorts_supertonic.bat',
    'README_다른PC_설치방법.txt',
    'make_model_included_package.py',
    'make_model_included_package.bat',
    'shorts_novel_maker.py',
]
REQUIRED = [
    'onnx/text_encoder.onnx',
    'onnx/vector_estimator.onnx',
    'onnx/vocoder.onnx',
    'voice_styles/M1.json',
    'voice_styles/F2.json',
]

def main():
    model = BASE / 'supertonic_assets'
    missing = [f for f in REQUIRED if not (model/f).is_file()]
    missing += [f for f in FILES if not (BASE/f).is_file()]
    if missing:
        print('FAIL: Missing files:')
        for f in missing: print('  -', f)
        print('Run setup_supertonic_windows.bat on this working PC first.')
        return 1
    target = BASE / 'Supertonic_model_included_transfer.zip'
    candidates = []
    for f in FILES:
        candidates.append((BASE/f, f))
    for f in sorted(model.rglob('*')):
        if f.is_file() and '.cache' not in f.relative_to(model).parts:
            candidates.append((f, f.relative_to(BASE).as_posix()))
    total = sum(p.stat().st_size for p, _ in candidates)
    print('Packaging', len(candidates), 'files,', round(total/1024/1024), 'MiB of source data')
    try:
        with ZipFile(target, 'w', allowZip64=True) as z:
            for i, (p, arcname) in enumerate(candidates, 1):
                if i == 1 or i%20==0 or i==len(candidates):
                    print(f'  {i}/{len(candidates)}: {arcname}', flush=True)
                # ONNX tensor weights often offer limited gains from deflation.
                method = ZIP_STORED if p.suffix.lower() in ('.onnx', '.safetensors') else ZIP_DEFLATED
                z.write(p, arcname, compress_type=method, compresslevel=6)
        with ZipFile(target) as z:
            bad = z.testzip()
            if bad:
                raise RuntimeError('Corrupt member: ' + bad)
        print('SUCCESS: ', target)
        print('File size:', round(target.stat().st_size/1024/1024), 'MiB')
        print('IMPORTANT: Other PC still requires Python 3.11 and one-time pip package install.')
        print('IMPORTANT: No Python venv, passwords, projects or API keys were included.')
        return 0
    except Exception as ex:
        print('ERROR:',ex)
        try: target.unlink(missing_ok=True)
        except Exception: pass
        return 1

if __name__ == '__main__':
    sys.exit(main())
