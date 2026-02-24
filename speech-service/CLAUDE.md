# Speech Service

FastAPI on port 8003. Speech-to-text (STT) + text-to-speech (TTS) for Hindi and English (GPU-required).

## Key Files

- `app/main.py` — FastAPI application
- `app/services/stt.py` — IndicConformer speech-to-text
- `app/services/tts.py` — IndicTTS (Hindi) + Coqui TTS (English)
- `app/services/audio_processor.py` — WAV resampling, validation
- `app/config.py` — Audio and model configuration

## Endpoints

- `POST /transcribe` — Audio to text (STT)
- `POST /synthesize` — Text to audio (TTS)
- `POST /transcribe-and-chat` — STT + LLM + TTS pipeline
- `GET /health` — Health check

## Audio Format

- Format: WAV (16-bit PCM)
- Sample rate: 16 kHz (mono)
- Max file: 2 hours

## Language Support

- STT: Hindi (hi), English (en)
- TTS: Hindi (hi), English (en)

## GPU Requirements

- IndicConformer: GPU required
- Coqui TTS: CPU-capable but GPU faster

## Dependencies

- AI4Bharat IndicConformer (STT)
- Coqui TTS (English TTS)
- IndicTTS (Hindi TTS, broken)
- librosa (audio processing)
- SoundFile (WAV I/O)

## Known Issues

1. **IndicTTS placeholder** — Returns zero-filled array. Awaiting AI4Bharat model release.
2. **CORS misconfiguration** — Uses `allow_origins=["*"]`. Fix: restrict to ALB.
3. **Hardcoded STT threshold** — Confidence=0.85 should be configurable.
