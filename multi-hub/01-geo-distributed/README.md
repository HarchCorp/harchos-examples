# Geo-Distributed Deployment on HarchOS

> **Difficulty:** Intermediate  
> **Category:** Multi-Hub Deployment  
> **Time:** ~30 minutes

## Overview

Deploy an inference service across multiple HarchOS hubs in different geographic regions. Traffic is automatically routed to the nearest healthy hub based on client latency.

This example demonstrates:

1. Deploying a model to multiple hubs simultaneously
2. Latency-based traffic routing
3. Health checking and automatic failover
4. Centralized monitoring across hubs

## Architecture

```
                    ┌─────────────────┐
                    │   HarchOS Hub   │
                    │   Orchestrator  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
     ┌──────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
     │  EU Hub     │  │  US Hub    │  │  APAC Hub  │
     │  (eu-west)  │  │  (us-east) │  │  (apac-se) │
     │  L4 GPU     │  │  A100 GPU  │  │  L4 GPU    │
     └─────────────┘  └────────────┘  └────────────┘
```

## Prerequisites

- Python 3.9+
- HarchOS CLI and SDK (`pip install harchos`)
- Access to at least 2 HarchOS hubs

## Quick Start

```bash
# Install dependencies
pip install harchos

# Deploy to multiple hubs
python deploy_geo.py --hubs eu-west-1,us-east-1,apac-southeast-1

# Check deployment status
python deploy_geo.py --status

# Deploy via workload manifest
harchos workload apply workload.yaml
```

## Files

| File | Purpose |
|------|---------|
| `deploy_geo.py` | Multi-hub deployment script using HarchOS SDK |
| `workload.yaml` | HarchOS multi-hub workload manifest |
