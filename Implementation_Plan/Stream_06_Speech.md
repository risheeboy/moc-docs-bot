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


---

## Agent Prompt

### Agent 6: Speech Service (IndicConformer + IndicTTS)
```
Build a FastAPI speech service with:
- STT using AI4Bharat IndicConformer (purpose-built for Indian languages)
  for Hindi + English transcription
- TTS using AI4Bharat IndicTTS for Hindi voice synthesis
- Coqui TTS fallback for English voices
- Accept WAV/MP3/WebM audio input, output WAV/MP3
- Audio format conversion via ffmpeg
- Language detection from audio
- GPU acceleration for IndicConformer
```

