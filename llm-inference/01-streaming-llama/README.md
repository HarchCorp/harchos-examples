# Streaming Llama Inference on HarchOS

> **Difficulty:** Beginner  
> **Category:** LLM Inference  
> **Time:** ~20 minutes

## Overview

Deploy a streaming Llama-2-7B inference endpoint on HarchOS. Supports both Python and TypeScript clients. This example demonstrates:

1. Loading a Llama-2-7B model with HuggingFace Transformers
2. Token-by-token streaming via Server-Sent Events (SSE)
3. A minimal Python server and a TypeScript client

## Prerequisites

- Python 3.9+
- Node.js 18+ (for TypeScript client)
- HarchOS CLI (`pip install harchos`)

## Quick Start

### Python Server

```bash
pip install -r requirements.txt  # or: pip install torch transformers harchos
python inference.py --port 8080
```

### TypeScript Client

```bash
cd 01-streaming-llama
npm install
npx ts-node inference.ts
```

### Deploy to HarchOS

```bash
harchos workload apply workload.yaml
```

## API

### POST /generate

**Request:**
```json
{
  "prompt": "Explain quantum computing in simple terms",
  "max_tokens": 256,
  "temperature": 0.7
}
```

**Response:** SSE stream of JSON objects:
```json
{"token": "Quantum", "finished": false}
{"token": " computing", "finished": false}
...
{"token": "", "finished": true, "usage": {"prompt_tokens": 8, "completion_tokens": 42}}
```

### GET /health

Returns `{"status": "ok", "model": "meta-llama/Llama-2-7b-chat-hf"}`

## Files

| File | Purpose |
|------|---------|
| `inference.py` | Python streaming inference server |
| `inference.ts` | TypeScript client for streaming inference |
| `workload.yaml` | HarchOS workload manifest |
