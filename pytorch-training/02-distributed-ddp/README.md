# Distributed DDP Training on HarchOS

> **Difficulty:** Intermediate  
> **Category:** PyTorch Training  
> **Time:** ~30 minutes

## Overview

Train ResNet-50 on ImageNet (or CIFAR-10 as a lightweight fallback) using PyTorch Distributed Data Parallel (DDP) across multiple GPU nodes on HarchOS. This example demonstrates:

1. Multi-node, multi-GPU training with `torch.distributed`
2. HarchOS automatic rank/world-size injection via environment variables
3. Checkpoint saving from rank 0 only
4. Gradient accumulation for effective large-batch training

## Prerequisites

- Python 3.9+
- HarchOS CLI (`pip install harchos`)
- A HarchOS hub with at least 2 GPU nodes

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally with 2 GPUs
torchrun --nproc_per_node=2 train_ddp.py --epochs 5 --batch-size 64

# Deploy to HarchOS (multi-node)
harchos workload apply workload.yaml
```

## Architecture

```
┌─────────────┐     ┌─────────────┐
│   Node 0    │     │   Node 1    │
│  (Rank 0)   │◄───►│  (Rank 1)   │
│  GPU 0, 1   │     │  GPU 0, 1   │
└─────────────┘     └─────────────┘
        │                   │
        └─────┬─────────────┘
              ▼
      Shared Storage (/output)
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--epochs` | 10 | Number of training epochs |
| `--batch-size` | 64 | Per-GPU batch size |
| `--lr` | 0.1 | Initial learning rate (scaled by world size) |
| `--accum-steps` | 1 | Gradient accumulation steps |
| `--backend` | nccl | Distributed backend (nccl / gloo) |

## Files

| File | Purpose |
|------|---------|
| `train_ddp.py` | DDP training script |
| `workload.yaml` | HarchOS multi-node workload manifest |
| `requirements.txt` | Python dependencies |
