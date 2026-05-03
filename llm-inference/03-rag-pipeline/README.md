# RAG Pipeline on HarchOS

> **Difficulty:** Advanced  
> **Category:** LLM Inference  
> **Time:** ~40 minutes

## Overview

Build a Retrieval-Augmented Generation (RAG) pipeline that combines document retrieval with LLM generation. The pipeline:

1. **Indexes** documents into a FAISS vector store using sentence embeddings
2. **Retrieves** the top-k most relevant chunks for a given query
3. **Generates** a grounded answer using the retrieved context
4. **Serves** the pipeline via a simple HTTP API

This is a production-ready pattern for building knowledge-augmented LLM applications.

## Architecture

```
User Query
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Embed      │────►│   FAISS      │────►│   LLM        │
│   Query      │     │   Retrieve   │     │   Generate   │
└──────────────┘     └──────────────┘     └──────────────┘
                           ▲                     │
                    ┌──────┴──────┐               │
                    │  Document   │               ▼
                    │  Index      │          ┌──────────┐
                    └─────────────┘          │ Response │
                                             └──────────┘
```

## Prerequisites

- Python 3.9+
- HarchOS CLI (`pip install harchos`)
- A HarchOS hub with at least 1 GPU

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Index sample documents and start server
python rag_pipeline.py --port 8080

# Query the RAG pipeline
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is HarchOS?"}'

# Deploy to HarchOS
harchos workload apply workload.yaml
```

## API

### POST /query
```json
{"question": "What is HarchOS?", "top_k": 3, "max_tokens": 256}
```

### POST /index
```json
{"documents": [{"title": "Doc1", "content": "..."}]}
```

### GET /health
Returns health and index stats.

## Files

| File | Purpose |
|------|---------|
| `rag_pipeline.py` | Complete RAG pipeline with FAISS + LLM |
| `workload.yaml` | HarchOS workload manifest |
| `requirements.txt` | Python dependencies |
