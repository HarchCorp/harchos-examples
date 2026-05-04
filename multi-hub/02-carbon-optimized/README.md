# Carbon-Optimized Deployment on HarchOS

> **Difficulty:** Advanced  
> **Category:** Multi-Hub Deployment  
> **Time:** ~40 minutes

## Overview

Deploy an inference workload across HarchOS hubs with **automatic carbon optimization**. The deployment system:

1. Monitors real-time carbon intensity across all hub regions
2. Routes traffic to the greenest available hub
3. Scales replicas based on carbon/latency trade-off
4. Provides carbon footprint reports per request

This is the flagship HarchOS multi-hub feature — combine geo-distribution with sustainability.

## How It Works

```
                    ┌─────────────────────┐
                    │  Carbon Optimizer   │
                    │  ┌───────────────┐  │
                    │  │ Carbon Index  │  │
                    │  │ (real-time)   │  │
                    │  └───────┬───────┘  │
                    └──────────┼──────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
┌──────▼──────┐         ┌─────▼──────┐         ┌─────▼──────┐
│  EU Hub     │         │  US Hub    │         │  APAC Hub  │
│  🟢 45 g    │         │  🟡 180 g  │         │  🔴 310 g  │
│  (lowest)   │         │  (medium)  │         │  (highest) │
│  ← traffic  │         │            │         │            │
└─────────────┘         └────────────┘         └────────────┘
```

## Prerequisites

- Python 3.9+
- HarchOS CLI and SDK (`pip install harchos`)
- Access to HarchOS hubs with carbon monitoring

## Quick Start

```bash
# Install dependencies
pip install harchos

# Deploy with carbon optimization
python carbon_optimizer.py --hubs eu-west-1,us-east-1,apac-southeast-1 --max-carbon 200

# Monitor carbon levels
python carbon_optimizer.py --monitor

# Deploy via workload manifest
harchos workload apply workload.yaml
```

## Files

| File | Purpose |
|------|---------|
| `carbon_optimizer.py` | Carbon-optimized multi-hub deployment script |
| `workload.yaml` | HarchOS workload with carbon policy |
