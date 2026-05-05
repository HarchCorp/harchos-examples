# HarchOS Examples

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript 5](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![HarchOS SDK](https://img.shields.io/badge/HarchOS%20SDK-0.2.0-22C55E?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiMyMkM1NUUiIHN0cm9rZS13aWR0aD0iMiI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiLz48cGF0aCBkPSJNMTIgNnY2bDQgMiIvPjwvc3ZnPg==)](https://github.com/HarchCorp/harchos-sdk-python)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-D22128?logo=apache&logoColor=white)](./LICENSE)
[![GPU Hubs](https://img.shields.io/badge/GPUs-1%2C798-22C55E)](https://github.com/HarchCorp/harchos)
[![Carbon](https://img.shields.io/badge/Avg%20Carbon-47%20gCO2%2FkWh-22C55E)](https://github.com/HarchCorp/harchos)

Starter templates and example projects for common [HarchOS](https://github.com/HarchCorp/harchos) workflows. Covers GPU training, LLM inference, data pipelines, pricing, monitoring, and multi-region deployment — all with **carbon-aware scheduling** built in.

## Quick Start

```bash
# Install the HarchOS Python SDK
pip install harchos

# Install the HarchOS JS SDK (for TypeScript examples)
npm install harchos

# Clone this repo
git clone https://github.com/HarchCorp/harchos-examples.git
cd harchos-examples

# Pick an example and run
cd pricing/01-cost-estimate
python cost_estimate.py --gpu-type H100 --gpu-count 8 --hours 168
```

## Example Catalog

### PyTorch Training

| # | Example | Language | Difficulty | Description |
|---|---------|----------|-----------|-------------|
| 01 | [Basic ResNet-50](./pytorch-training/01-basic-resnet50/) | Python | 🟢 Beginner | Train ResNet-50 on CIFAR-10 with a single GPU |
| 02 | [Distributed DDP](./pytorch-training/02-distributed-ddp/) | Python | 🟡 Intermediate | Multi-node DDP training with gradient accumulation |
| 03 | [Carbon-Aware Training](./pytorch-training/03-carbon-aware-training/) | Python | 🔴 Advanced | Pause/resume training based on carbon intensity |

### LLM Inference

| # | Example | Language | Difficulty | Description |
|---|---------|----------|-----------|-------------|
| 01 | [Streaming Llama](./llm-inference/01-streaming-llama/) | Python + TypeScript | 🟢 Beginner | Streaming SSE inference with Python server + TypeScript client |
| 02 | [Quantized GPTQ](./llm-inference/02-quantized-gptq/) | Python | 🟡 Intermediate | 4-bit quantized LLM with throughput benchmarking |
| 03 | [RAG Pipeline](./llm-inference/03-rag-pipeline/) | Python | 🔴 Advanced | Retrieval-Augmented Generation with FAISS + LLM |

### Data Pipelines

| # | Example | Language | Difficulty | Description |
|---|---------|----------|-----------|-------------|
| 01 | [ETL Pipeline](./data-pipelines/01-etl-pipeline/) | Python | 🟢 Beginner | Extract-Transform-Load with CSV → Parquet |
| 02 | [Streaming Inference](./data-pipelines/02-streaming-inference/) | Python | 🟡 Intermediate | Real-time queue-based inference pipeline |

### 💰 Pricing

| # | Example | Language | Difficulty | Description |
|---|---------|----------|-----------|-------------|
| 01 | [Cost Estimator](./pricing/01-cost-estimate/) | Python + TypeScript | 🟢 Beginner | Calculate cost estimates for different GPU types and regions |
| 02 | [Billing History](./pricing/02-billing-history/) | Python + TypeScript | 🟡 Intermediate | Retrieve and analyze billing records with spending summaries |
| 03 | [Price Comparison](./pricing/03-price-comparison/) | Python + TypeScript | 🟡 Intermediate | Compare prices across regions, tiers, and GPU types with carbon adjustment |

### 📊 Monitoring

| # | Example | Language | Difficulty | Description |
|---|---------|----------|-----------|-------------|
| 01 | [Platform Metrics](./monitoring/01-platform-metrics/) | Python + TypeScript | 🟢 Beginner | Display platform-wide GPU, energy, and carbon metrics |
| 02 | [Health Check](./monitoring/02-health-check/) | Python + TypeScript | 🟢 Beginner | Detailed health check with sovereignty compliance and exit codes |
| 03 | [Carbon Dashboard](./monitoring/03-carbon-dashboard/) | Python + TypeScript | 🔴 Advanced | Comprehensive carbon metrics dashboard with green window detection |

### 🌍 Multi-Region

| # | Example | Language | Difficulty | Description |
|---|---------|----------|-----------|-------------|
| 01 | [Geo-Distributed](./multi-hub/01-geo-distributed/) | Python | 🟡 Intermediate | Multi-region deployment with latency-based routing |
| 02 | [Carbon-Optimized](./multi-hub/02-carbon-optimized/) | Python | 🔴 Advanced | Carbon-intensity-aware traffic routing across hubs |
| 03 | [Pricing-Optimized](./multi-region/03-pricing-optimized/) | Python + TypeScript | 🔴 Advanced | Deploy workloads optimized for pricing across regions with carbon and sovereignty constraints |
| 04 | [Monitoring Dashboard](./multi-region/04-monitoring-dashboard/) | Python + TypeScript | 🔴 Advanced | Cross-region monitoring dashboard with alerts |

## Requirements

- **Python 3.9+**
- **HarchOS Python SDK** (`pip install harchos`)
- **Node.js 18+** (for TypeScript examples only)
- **HarchOS JS SDK** (`npm install harchos`, for TypeScript examples)

## Project Structure

```
harchos-examples/
├── pytorch-training/              # GPU training examples
│   ├── 01-basic-resnet50/         #   Beginner: single-GPU training
│   ├── 02-distributed-ddp/        #   Intermediate: multi-node DDP
│   └── 03-carbon-aware-training/  #   Advanced: carbon-aware scheduling
├── llm-inference/                 # LLM serving examples
│   ├── 01-streaming-llama/        #   Beginner: SSE streaming (Python + TS)
│   ├── 02-quantized-gptq/         #   Intermediate: 4-bit GPTQ quantized
│   └── 03-rag-pipeline/           #   Advanced: RAG with FAISS
├── data-pipelines/                # Data processing examples
│   ├── 01-etl-pipeline/           #   Beginner: CSV → Parquet ETL
│   └── 02-streaming-inference/    #   Intermediate: real-time inference
├── pricing/                       # 💰 Pricing and billing examples
│   ├── 01-cost-estimate/          #   Beginner: cost estimation (Python + TS)
│   ├── 02-billing-history/        #   Intermediate: billing records (Python + TS)
│   └── 03-price-comparison/       #   Intermediate: cross-region comparison (Python + TS)
├── monitoring/                    # 📊 Platform monitoring examples
│   ├── 01-platform-metrics/       #   Beginner: platform metrics (Python + TS)
│   ├── 02-health-check/           #   Beginner: health monitoring (Python + TS)
│   └── 03-carbon-dashboard/       #   Advanced: carbon dashboard (Python + TS)
├── multi-hub/                     # Multi-hub deployment examples (legacy)
│   ├── 01-geo-distributed/        #   Intermediate: latency-based routing
│   └── 02-carbon-optimized/       #   Advanced: carbon-aware routing
├── multi-region/                  # 🌍 Multi-region deployment examples
│   ├── 03-pricing-optimized/      #   Advanced: pricing + carbon optimization (Python + TS)
│   └── 04-monitoring-dashboard/   #   Advanced: cross-region dashboard (Python + TS)
├── .github/workflows/ci.yml       # CI: lint, validate, structure check
├── README.md                      # This file
├── CONTRIBUTING.md                # Contribution guidelines
└── LICENSE                        # Apache 2.0
```

## SDK Resources Used

| Resource | Python SDK | JS SDK | API Endpoints |
|----------|-----------|--------|---------------|
| **Pricing** | `client.pricing.*` | `client.pricing.*` | `GET /v1/pricing/plans`, `POST /v1/pricing/estimate`, `GET /v1/pricing/billing/*` |
| **Monitoring** | `client.monitoring.*` | `client.monitoring.*` | `GET /v1/monitoring/metrics`, `GET /v1/monitoring/health/detailed` |
| **Regions** | `client.regions.*` | `client.regions.*` | `GET /v1/regions` |
| **Carbon** | `client.carbon.*` | — | `GET /v1/carbon/*` |
| **Hubs** | `client.hubs.*` | `client.hubs.*` | `GET /v1/hubs` |

## Best Practices

### Carbon-Aware Scheduling
- Always set a **carbon intensity threshold** (`--carbon-max`) before deploying
- Use **carbon-aware scheduling** to defer workloads during high-carbon periods
- Prefer **Ouarzazate** (18 gCO2/kWh) and **Dakhla** (32 gCO2/kWh) for green compute

### Sovereignty Enforcement
- Use `--sovereign-only` for workloads with data residency requirements
- Verify **compliance frameworks** (GDPR, CNDP, NDPR, PDPA) per region
- Ensure data stays within sovereignty boundaries

### Cost Optimization
- **Estimate costs before deploying** — use the pricing examples
- Compare **carbon-adjusted pricing** with `--include-carbon` for true cost
- Choose **enterprise tier** for 5%+ volume discounts on 8+ GPU deployments

### Monitoring
- Set up **continuous health checks** with `--watch` and exit codes
- Monitor **GPU utilization** for right-sizing (target 70-85%)
- Track **carbon metrics** to validate green scheduling effectiveness

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding new examples.

## License

Apache 2.0 — see [LICENSE](./LICENSE).
