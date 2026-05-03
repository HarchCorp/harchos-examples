# Carbon-Aware Training on HarchOS

> **Difficulty:** Advanced  
> **Category:** PyTorch Training  
> **Time:** ~45 minutes

## Overview

Train ResNet-50 on CIFAR-10 with **carbon-aware scheduling** powered by the HarchOS SDK. The training script:

1. Queries real-time carbon intensity data from the HarchOS hub
2. Pauses training during high-carbon intensity periods
3. Automatically resumes when carbon intensity drops below a threshold
4. Logs carbon metrics alongside training metrics

This is a core HarchOS differentiator — sustainable AI compute that reduces your carbon footprint without manual intervention.

## How It Works

```
┌──────────────────────────────────────┐
│        Carbon-Aware Loop             │
│                                      │
│  1. Check carbon intensity (gCO2/kWh)│
│  2. If above threshold → sleep/pause │
│  3. If below threshold → train epoch │
│  4. Log carbon + training metrics    │
│  5. Repeat                           │
└──────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- HarchOS CLI and SDK (`pip install harchos`)
- A HarchOS hub with carbon monitoring enabled

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally (simulates carbon data)
python train_carbon_aware.py --epochs 10 --carbon-threshold 200

# Deploy to HarchOS
harchos workload apply workload.yaml
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--epochs` | 10 | Target number of training epochs |
| `--batch-size` | 64 | Training batch size |
| `--lr` | 0.01 | Initial learning rate |
| `--carbon-threshold` | 200 | Max carbon intensity in gCO2/kWh |
| `--poll-interval` | 300 | Carbon check interval in seconds |

## Files

| File | Purpose |
|------|---------|
| `train_carbon_aware.py` | Carbon-aware training script |
| `workload.yaml` | HarchOS workload with carbon policy |
| `requirements.txt` | Python dependencies |
