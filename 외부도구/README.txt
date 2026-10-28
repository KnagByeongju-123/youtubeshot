외부 오픈소스 (그대로 가져와 씀, 각 폴더의 LICENSE 를 따름)
- speechmos/ : tarepan/SpeechMOS (MIT) — UTMOS22 strong 말소리 자연스러움 점수(1~5). 나레이션_겹침검사.py 가 씀
  바꾼 곳: utmos22/strong/model.py 의 torchaudio 를 16kHz 가 아닐 때만 불러오게 (이 서버 torch 에 맞는 torchaudio 가 없음)
  가중치(깃에 안 올림): models/utmos22_strong_step7459_v1.pt
    ← https://github.com/tarepan/SpeechMOS/releases/download/v1.0.0/utmos22_strong_step7459_v1.pt (약 410MB)
