# Local LLM Setup — Ollama + Faster-Whisper

This guide explains how to run the Social Content Archiver entirely locally, without any paid API calls, using **Ollama** for LLM inference and **Faster-Whisper** for audio transcription.

## Prerequisites

- **GPU**: NVIDIA GPU with 8 GB+ VRAM (e.g. RTX 4060)
- **RAM**: 16 GB+ system RAM (32 GB recommended)
- **Docker**: Docker Desktop with GPU support enabled
- **NVIDIA Container Toolkit**: Required for GPU passthrough to Docker

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    App Container                 │
│                                                  │
│  ┌──────────────┐  ┌─────────────────────────┐  │
│  │ Faster-      │  │ OpenAI Python SDK        │  │
│  │ Whisper      │  │ (pointed at Ollama URL)  │  │
│  │ (CPU)        │  │                          │  │
│  └──────┬───────┘  └────────────┬─────────────┘  │
│         │                       │                 │
│    transcription         chat / vision            │
│    (local)               requests                 │
└─────────┼───────────────────────┼─────────────────┘
          │                       │
          ▼                       ▼
   ┌──────────┐          ┌───────────────┐
   │ CPU/RAM  │          │ Ollama Server │
   │ (32 GB)  │          │ (GPU, 8 GB)   │
   └──────────┘          └───────────────┘
```

The key insight is that Ollama exposes an **OpenAI-compatible API**. The existing `openai` Python SDK talks to Ollama by simply changing the `base_url`. No abstract provider interface is needed.

## Quick Start

### 1. Configure environment

Copy `.env.example` to `.env` and set the provider to local:

```env
LLM_PROVIDER=ollama
TRANSCRIPTION_PROVIDER=faster-whisper
```

### 2. Start services

```bash
# Start app + Redis + Ollama
docker compose --profile local up -d
```

### 3. Pull models (first time only)

```bash
docker exec social-archiver-ollama ollama pull llama3.3
docker exec social-archiver-ollama ollama pull llava
```

### 4. Run the pipeline

```bash
docker compose run --rm app run
```

## Configuration Reference

### Environment Variables

| Variable | Values | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | `openai`, `ollama` | `openai` | LLM backend for chat and vision |
| `OLLAMA_BASE_URL` | URL | `http://localhost:11434/v1` | Ollama server endpoint |
| `LLM_CHAT_MODEL` | model name | *(auto)* | Override chat model name |
| `LLM_VISION_MODEL` | model name | *(auto)* | Override vision model name |
| `TRANSCRIPTION_PROVIDER` | `openai`, `faster-whisper` | `openai` | Transcription backend |
| `FASTER_WHISPER_MODEL` | `tiny`, `base`, `small`, `medium`, `large-v3` | `small` | Faster-Whisper model size |
| `FASTER_WHISPER_DEVICE` | `cpu`, `cuda` | `cpu` | Faster-Whisper compute device |
| `FASTER_WHISPER_COMPUTE_TYPE` | `int8`, `float16`, `float32` | `int8` | Numeric precision |

### Default Models Per Provider

| Task | OpenAI | Ollama |
|---|---|---|
| Chat / Analysis / Tagging / Synthesis | `gpt-4o-mini` | `llama3.3` (8B) |
| Vision / Image Analysis | `gpt-4o-mini` | `llava` (7B) |
| Transcription | `whisper-1` (API) | Faster-Whisper `small` (local) |
| Embeddings | `all-MiniLM-L6-v2` | No change (already local) |

## Hardware Requirements

### RTX 4060 (8 GB VRAM) + 32 GB RAM

| Component | VRAM | RAM | Notes |
|---|---|---|---|
| `llama3.3` 8B (Q4) | ~5 GB | — | Fast inference on GPU |
| `llava` 7B | ~5 GB | — | Vision model |
| Faster-Whisper `small` | — | ~1 GB | Runs on CPU |
| sentence-transformers | — | ~1 GB | Embeddings, CPU |

**Note**: `llama3.3` and `llava` cannot run simultaneously on 8 GB VRAM. Ollama handles model swapping automatically — it unloads one model and loads the other when needed. This adds ~2-3 seconds of latency per swap, which is fine for a batch pipeline.

## Files Modified

### Core — Provider Abstraction

**`src/config.py`** — Central configuration hub

Added settings:
- `LLM_PROVIDER`, `OLLAMA_BASE_URL` — choose between OpenAI and Ollama
- `LLM_CHAT_MODEL`, `LLM_VISION_MODEL` — optional model overrides
- `TRANSCRIPTION_PROVIDER`, `FASTER_WHISPER_MODEL`, `FASTER_WHISPER_DEVICE`, `FASTER_WHISPER_COMPUTE_TYPE` — transcription backend config

Added factory functions:
- `get_llm_client()` — returns an `openai.OpenAI` client pointing at either the real OpenAI API or the local Ollama server
- `get_chat_model()` — resolves the chat model name based on provider
- `get_vision_model()` — resolves the vision model name based on provider

### Modules — Client Swap (3-4 lines each)

Each module replaced:
```python
import openai
self.client = openai.OpenAI(api_key=settings.openai_api_key)
model="gpt-4o-mini",
```
With:
```python
from ..config import get_llm_client, get_chat_model
self.client = get_llm_client()
model=get_chat_model(),
```

| File | API calls updated |
|---|---|
| `src/processors/content_analyzer.py` | 1 chat completion |
| `src/processors/visual_analysis.py` | 1 vision completion |
| `src/tagging/tagger.py` | 1 chat completion |
| `src/knowledge_base/synthesizer.py` | 3 chat completions (synthesis, summary, fact-check) |

### Transcription — Dual Backend

**`src/processors/transcription.py`** — Rewrote to support two backends:

- **OpenAI mode**: Uses `client.audio.transcriptions.create()` (existing behavior)
- **Faster-Whisper mode**: Uses `faster_whisper.WhisperModel.transcribe()` locally

The `transcribe_video()` and `transcribe()` methods are unchanged — they delegate to `transcribe_audio()`, which dispatches to the appropriate backend.

### Config Files

| File | Changes |
|---|---|
| `config/config.yaml` | Added `providers` section with model defaults. Added `faster_whisper` settings under `processors.transcription`. |
| `.env.example` | Added all new environment variables with documentation. Reorganized into logical sections. |
| `requirements.txt` | Added `faster-whisper>=1.0.0`. |

### Docker

**`Dockerfile`**:
- Pre-downloads the Faster-Whisper `small` model during build (avoids download at first run)
- Adds `LLM_PROVIDER` and `TRANSCRIPTION_PROVIDER` default env vars

**`docker-compose.yml`**:
- Added `ollama` service with NVIDIA GPU reservation
- Uses Docker Compose `profiles: [local]` — Ollama only starts when explicitly requested
- App service passes provider env vars through to the container

## Usage Modes

### Cloud Mode (default)

Uses OpenAI APIs. Requires `OPENAI_API_KEY`.

```bash
docker compose up
```

### Local Mode (free)

Uses Ollama + Faster-Whisper. No API key needed.

```bash
# Set in .env
LLM_PROVIDER=ollama
TRANSCRIPTION_PROVIDER=faster-whisper

# Start everything
docker compose --profile local up
```

### Hybrid Mode

Mix providers — e.g., use Ollama for chat but OpenAI for transcription:

```env
LLM_PROVIDER=ollama
TRANSCRIPTION_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### Without Docker

Install Ollama natively from [ollama.com](https://ollama.com), then:

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull models
ollama pull llama3.3
ollama pull llava

# Terminal 3: Run the app
LLM_PROVIDER=ollama TRANSCRIPTION_PROVIDER=faster-whisper python -m src.main run
```

## Troubleshooting

### Ollama not responding

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check container logs
docker logs social-archiver-ollama
```

### GPU not detected by Ollama

Ensure the NVIDIA Container Toolkit is installed:
```bash
nvidia-smi                          # Should show your GPU
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi  # Should work in Docker
```

### Faster-Whisper model download slow

The first run downloads the model (~500 MB for `small`). This is cached for subsequent runs. If using Docker, the model is pre-downloaded during the image build.

### JSON parsing issues with local models

Local models (llama3.3, llava) may occasionally produce invalid JSON. If you see parsing errors, try:
- Using a larger model: `LLM_CHAT_MODEL=llama3.1:70b` (requires more VRAM)
- Reducing temperature (already set low: 0.2-0.4)

### Out of VRAM

If you see CUDA OOM errors:
- Use a smaller chat model: `LLM_CHAT_MODEL=llama3.2:3b`
- Use a smaller vision model: `LLM_VISION_MODEL=llava:7b`
- Run Faster-Whisper on CPU (default): `FASTER_WHISPER_DEVICE=cpu`

## Cost Comparison

| Setup | Monthly cost (est. 1000 posts) |
|---|---|
| Full OpenAI (gpt-4o-mini + Whisper) | ~$5-15 |
| Full Local (Ollama + Faster-Whisper) | $0 (electricity only) |
| Hybrid (Ollama + OpenAI Whisper) | ~$1-3 |
