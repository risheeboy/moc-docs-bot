# Speech Service (Stream 6)

FastAPI-based Speech Service for the RAG-based Hindi & English, Search & QA System.

**Port:** 8003
**Service Name:** `speech-service`

## Overview

This service provides:
- **Speech-to-Text (STT):** AI4Bharat IndicConformer for Hindi & English transcription
- **Text-to-Speech (TTS):** AI4Bharat IndicTTS for Hindi + Coqui TTS for English
- **Audio Processing:** Format conversion (WAV/MP3/WebM/OGG) via ffmpeg
- **Language Detection:** Automatic language detection from audio

## Architecture

```
speech-service/
├── Dockerfile                          # nvidia/cuda base for GPU inference
├── requirements.txt                    # Python dependencies (pinned versions)
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI application
│   ├── config.py                       # Environment-based configuration
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py                   # GET /health
│   │   ├── stt.py                      # POST /stt
│   │   └── tts.py                      # POST /tts
│   ├── services/
│   │   ├── __init__.py
│   │   ├── indic_conformer_stt.py      # AI4Bharat IndicConformer STT
│   │   ├── indic_tts.py                # AI4Bharat IndicTTS for Hindi
│   │   ├── coqui_tts.py                # Coqui TTS for English
│   │   ├── audio_processor.py          # Audio format conversion
│   │   └── language_detect.py          # Language detection
│   └── utils/
│       ├── __init__.py
│       └── metrics.py                  # Prometheus metrics
├── models/                             # Model cache directory
│   └── .gitkeep
└── tests/
    ├── __init__.py
    ├── conftest.py                     # Test fixtures
    ├── test_stt.py                     # STT endpoint tests
    ├── test_tts.py                     # TTS endpoint tests
    ├── test_health.py                  # Health check tests
    └── test_services.py                # Service unit tests
```

## API Endpoints

### Health Check

**GET /health**

Returns service health status and dependency information (format from Shared Contracts §5).

```json
{
  "status": "healthy",
  "service": "speech-service",
  "version": "1.0.0",
  "uptime_seconds": 3612,
  "timestamp": "2026-02-24T10:30:00Z",
  "dependencies": {
    "gpu": { "status": "healthy", "latency_ms": 0.5 },
    "models": { "status": "healthy", "latency_ms": 0.0 }
  }
}
```

### Speech-to-Text

**POST /stt**

Convert audio file to text using IndicConformer.

**Request:** multipart/form-data
- `audio` (binary, required): Audio file (WAV, MP3, WebM, OGG)
- `language` (string, optional): Language code (`"hi"`, `"en"`, or `"auto"` for auto-detection)

**Response:**
```json
{
  "text": "Transcribed text here",
  "language": "hi",
  "confidence": 0.94,
  "duration_seconds": 3.5
}
```

**Error Codes:**
- `INVALID_AUDIO_FORMAT` (400): Unsupported audio format
- `INVALID_LANGUAGE` (400): Unsupported language code
- `PAYLOAD_TOO_LARGE` (413): Audio file exceeds 50MB limit
- `PROCESSING_FAILED` (422): No speech detected in audio
- `MODEL_LOADING` (503): Models still loading
- `INTERNAL_ERROR` (500): Unexpected error

### Text-to-Speech

**POST /tts**

Generate audio from text using IndicTTS (Hindi) or Coqui TTS (English).

**Request:** JSON
```json
{
  "text": "Text to synthesize",
  "language": "hi",
  "format": "mp3",
  "voice": "default"
}
```

**Response:** Binary audio data
- Content-Type: `audio/mpeg` or `audio/wav`
- Headers:
  - `X-Duration-Seconds`: Duration of generated audio
  - `X-Language`: Language of synthesis

**Error Codes:**
- `INVALID_LANGUAGE` (400): Unsupported language
- `INVALID_REQUEST` (400): Empty text or invalid format
- `PAYLOAD_TOO_LARGE` (413): Text exceeds 5000 character limit
- `MODEL_LOADING` (503): Models still loading
- `INTERNAL_ERROR` (500): Processing error

### Metrics

**GET /metrics**

Prometheus metrics in text format.

**Key Metrics:**
- `speech_stt_duration_seconds`: STT inference duration
- `speech_tts_duration_seconds`: TTS inference duration
- `speech_stt_requests_total`: Total STT requests
- `speech_tts_requests_total`: Total TTS requests
- `speech_gpu_available`: GPU availability (1=yes, 0=no)
- `speech_models_loaded`: Number of loaded models

## Configuration

Configuration is read from environment variables (from Shared Contracts §3):

```bash
# Service metadata
APP_ENV=production                          # production | staging | development
APP_DEBUG=false
APP_LOG_LEVEL=INFO                          # DEBUG | INFO | WARNING | ERROR

# STT Configuration
SPEECH_STT_MODEL=ai4bharat/indicconformer-hi-en
SPEECH_SAMPLE_RATE=16000

# TTS Configuration - Hindi
SPEECH_TTS_HINDI_MODEL=ai4bharat/indic-tts-hindi

# TTS Configuration - English
SPEECH_TTS_ENGLISH_MODEL=coqui/tts-english

# Model cache
HF_HOME=/app/models                         # HuggingFace model cache
```

## Running

### Docker

```bash
docker build -t speech-service:1.0.0 .

docker run --gpus all \
  -p 8003:8003 \
  -e SPEECH_SAMPLE_RATE=16000 \
  -e APP_LOG_LEVEL=INFO \
  -v model-cache:/app/models \
  speech-service:1.0.0
```

### Local Development (with GPU)

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_stt.py -v
pytest tests/test_tts.py -v
pytest tests/test_health.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

## Dependencies

### Key Libraries

- **FastAPI:** Web framework
- **Uvicorn:** ASGI server
- **PyTorch + CUDA:** GPU-accelerated inference
- **Transformers:** Model loading and inference
- **Librosa:** Audio processing
- **Soundfile:** WAV/audio file I/O
- **ffmpeg-python:** Audio format conversion wrapper

### AI4Bharat Models

- **IndicConformer:** Speech-to-Text (ai4bharat/indicconformer-hi-en)
- **IndicTTS:** Hindi Text-to-Speech (ai4bharat/indic-tts-hindi)
- **Coqui TTS:** English Text-to-Speech fallback

Models are downloaded automatically on first use from HuggingFace and cached in `/app/models`.

## Design Decisions

### STT (Speech-to-Text)

**IndicConformer** was chosen over Whisper because:
- Purpose-built for Indian languages
- Better Hindi accuracy than Whisper
- Lower latency for real-time use
- GPU-efficient for large batch processing

### TTS (Text-to-Speech)

- **Hindi:** AI4Bharat IndicTTS with VITS voice models
- **English:** Coqui TTS as production fallback
- Both support streaming and batch synthesis

### Audio Processing

- **Input formats:** WAV, MP3, WebM, OGG (via ffmpeg)
- **Output formats:** WAV, MP3
- **Sample rate:** 16kHz for STT, 22.05kHz for TTS
- **Normalization:** Pre-processing to improve STT accuracy

## Performance

### Hardware Requirements

- **GPU:** NVIDIA GPU with CUDA 12.1+ (strongly recommended)
- **Memory:** 12+ GB VRAM recommended for IndicConformer + TTS
- **CPU Fallback:** ~10x slower than GPU

### Latency (typical with GPU)

- **STT:** 200-500ms for 3-5 second audio
- **TTS:** 300-800ms for typical sentences
- **Model Loading:** 30-60 seconds on first startup

### Throughput

- **Concurrent STT:** 2-4 parallel requests (GPU dependent)
- **Concurrent TTS:** 2-4 parallel requests
- **Batch TTS:** Efficient for multiple sentences

## Monitoring

### Health Checks

Health endpoint checks:
- GPU availability and memory usage
- Model loading status (STT, Hindi TTS, English TTS)
- System resources (CPU, memory)

Endpoint returns:
- `healthy`: All dependencies OK
- `degraded`: Non-critical issues (e.g., GPU unavailable but CPU fallback OK)
- `unhealthy`: Critical dependency failure → HTTP 503

### Logging

- Structured JSON logging with request ID propagation
- All logs include: timestamp, level, service, request_id, message
- PII sanitized (no phone numbers, emails, or full queries logged)

### Metrics

Prometheus metrics exposed at `/metrics`:
- Request counts and latencies per operation
- Audio duration histograms
- Model loading times
- GPU memory usage
- Error counts by type

## Known Limitations

1. **Model Loading:** First request takes 30-60s (models loading from HuggingFace)
2. **Concurrent Requests:** Limited by GPU VRAM (typically 2-4 parallel)
3. **Audio Duration:** Max 5 minutes per STT request
4. **Text Length:** Max 5000 characters for TTS per request
5. **Languages:** Currently Hindi (hi) and English (en) only
6. **Streaming:** Not yet implemented (synchronous responses only)

## Future Enhancements

- [ ] WebSocket support for real-time streaming STT
- [ ] Model quantization for lower memory usage
- [ ] Support for more Indian languages (Tamil, Telugu, etc.)
- [ ] Voice cloning for TTS
- [ ] Emotion preservation in speech synthesis
- [ ] Multi-speaker TTS
- [ ] Custom domain adaptation for STT

## References

### Shared Contracts

- **§1:** Service Registry (port 8003 as `speech-service`)
- **§3:** Environment variables (SPEECH_* prefix)
- **§4:** Standard error response format
- **§5:** Health check format
- **§6:** Structured logging format
- **§8.3:** STT/TTS API contracts
- **§9:** Language codes (hi, en)
- **§11:** Prometheus metrics

### External Resources

- [AI4Bharat IndicConformer](https://github.com/AI4Bharat/indicconformer)
- [AI4Bharat IndicTTS](https://github.com/AI4Bharat/indic-tts)
- [Coqui TTS](https://github.com/coqui-ai/TTS)
- [HuggingFace Model Hub](https://huggingface.co)
