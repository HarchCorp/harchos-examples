# Quantized GPTQ Inference on HarchOS

> **Difficulty:** Intermediate  
> **Category:** LLM Inference  
> **Time:** ~25 minutes

## Overview

Deploy a GPTQ-quantized LLM for memory-efficient inference on HarchOS. GPTQ reduces model size by ~3-4x with minimal accuracy loss, enabling large models on smaller GPUs.

This example demonstrates:

1. Loading a GPTQ-quantized model with AutoGPTQ / transformers
2. Benchmarking throughput and latency vs. FP16 baseline
3. Deploying as a cost-optimized HarchOS inference workload

## Why GPTQ?

| Property | FP16 | GPTQ (4-bit) |
|----------|------|--------------|
| Model size (7B) | ~14 GB | ~4 GB |
| GPU memory required | 16 GB+ | 6 GB+ |
| Throughput | Baseline | ~1.5-2x higher |
| Quality loss | — | <1% on most benchmarks |

## Prerequisites

- Python 3.9+
- HarchOS CLI (`pip install harchos`)
- GPU with at least 8 GB VRAM

## Quick Start

```bash
# Install dependencies
pip install auto-gptq transformers accelerate harchos

# Run benchmark + server
python deploy_quantized.py --model TheBloke/Llama-2-7B-Chat-GPTQ --port 8080

# Deploy to HarchOS
harchos workload apply workload.yaml
```

## Files

| File | Purpose |
|------|---------|
| `deploy_quantized.py` | GPTQ model loader, benchmark, and inference server |
| `workload.yaml` | HarchOS workload with cost-optimized resources |
