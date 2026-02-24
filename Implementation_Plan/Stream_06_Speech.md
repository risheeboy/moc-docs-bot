### STREAM 6: Speech Services (IndicConformer STT + IndicTTS)

**Agent Goal:** Build the speech-to-text and text-to-speech service using **AI4Bharat IndicConformer** (STT) and **AI4Bharat IndicTTS** (TTS) as specified in the Design document.

**Files to create:**
```
speech-service/
├── Dockerfile                      # nvidia/cuda base for GPU inference
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app
│   ├── config.py                   # Model paths, languages, sample rates
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── stt.py                  # POST /stt (audio → text)
│   │   ├── tts.py                  # POST /tts (text → audio)
│   │   └── health.py               # GET /health
│   ├── services/
│   │   ├── __init__.py
│   │   ├── indic_conformer_stt.py  # AI4Bharat IndicConformer for Hindi+English STT
│   │   ├── indic_tts.py            # AI4Bharat IndicTTS for Hindi voices
│   │   ├── coqui_tts.py            # Coqui TTS fallback for English voices
│   │   ├── audio_processor.py      # Audio format conversion (ffmpeg wrapper)
│   │   └── language_detect.py      # Detect spoken language from audio
│   └── utils/
│       ├── __init__.py
│       └── metrics.py
├── models/                         # Directory for downloaded voice models
│   └── .gitkeep
└── tests/
    ├── test_stt.py
    ├── test_tts.py
    └── fixtures/
        ├── sample_hindi.wav
        └── sample_english.wav
```

**Key technical decisions (from Design):**
- **STT:** AI4Bharat **IndicConformer** — purpose-built for Indian languages, better Hindi accuracy than Whisper
- **TTS Hindi:** AI4Bharat **IndicTTS** with Hindi VITS voice models
- **TTS English:** Coqui TTS as fallback for English
- **Audio formats:** Accept WAV, MP3, OGG, WebM; output WAV or MP3
- **Streaming:** WebSocket support for real-time STT

**Requires:** GPU for IndicConformer inference. No code dependencies on other streams.

---

**Shared Contracts Reference (from `01_Shared_Contracts.md`):**
- §1 Service Registry: this service runs on port 8003 as `speech-service`
- §3 Environment Variables: read `SPEECH_*` variables
- §4 Error Response Format: use standard error format; use `INVALID_AUDIO_FORMAT` for unsupported audio
- §5 Health Check Format: `/health` must check GPU availability, return format from §5
- §6 Log Format: structured JSON logging with service name `speech-service`
- §8.3 API Contract: implement exact `/stt` and `/tts` schemas from §8.3
- §9 Language Codes: accept language codes from §9 (at minimum `hi` and `en`)
- §11 Prometheus Metrics: expose `speech_stt_duration_seconds`, `speech_tts_duration_seconds`

---

## Agent Prompt

### Agent 6: Speech Service (IndicConformer + IndicTTS)
```
Build a FastAPI speech service with:
PREREQUISITE: Read 00_Overview.md and 01_Shared_Contracts.md first.
Port 8003. Use exact STT/TTS API schemas from §8.3, language codes from §9.

- STT using AI4Bharat IndicConformer (purpose-built for Indian languages)
  for Hindi + English transcription
- TTS using AI4Bharat IndicTTS for Hindi voice synthesis
- Coqui TTS fallback for English voices
- Accept WAV/MP3/WebM audio input, output WAV/MP3
- Audio format conversion via ffmpeg
- Language detection from audio
- GPU acceleration for IndicConformer
```

