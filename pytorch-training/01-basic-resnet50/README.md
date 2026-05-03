# Basic ResNet-50 Training on HarchOS

> **Difficulty:** Beginner  
> **Category:** PyTorch Training  
> **Time:** ~15 minutes

## Overview

Train a ResNet-50 model on CIFAR-10 using a single GPU node on HarchOS. This is the simplest possible training example and demonstrates the core workflow:

1. Write a standard PyTorch training script
2. Package it as a HarchOS workload manifest
3. Deploy with `harchos workload apply`

## Prerequisites

- Python 3.9+
- HarchOS CLI (`pip install harchos`)
- A HarchOS hub with at least 1 GPU node

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally
python train.py --epochs 2 --batch-size 32

# Deploy to HarchOS
harchos workload apply workload.yaml
```

## What It Does

- Downloads CIFAR-10 automatically via `torchvision`
- Trains ResNet-50 (modified for 32×32 CIFAR images) for configurable epochs
- Logs training loss and validation accuracy to HarchOS metrics
- Saves the best checkpoint to `/output/resnet50_best.pth`

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--epochs` | 10 | Number of training epochs |
| `--batch-size` | 64 | Training batch size |
| `--lr` | 0.01 | Initial learning rate |
| `--output-dir` | /output | Checkpoint output directory |

## Files

| File | Purpose |
|------|---------|
| `train.py` | Self-contained training script |
| `workload.yaml` | HarchOS workload manifest |
| `requirements.txt` | Python dependencies |
