# HarchOS Examples

Starter templates and example projects for common [HarchOS](https://github.com/HarchCorp/harchos) workflows.

## Quick Start

```bash
# Install the HarchOS CLI
pip install harchos

# Clone this repo
git clone https://github.com/HarchCorp/harchos-examples.git
cd harchos-examples

# Pick an example and deploy
cd pytorch-training/01-basic-resnet50
harchos workload apply workload.yaml
```

## Example Catalog

### PyTorch Training

| # | Example | Difficulty | Description |
|---|---------|-----------|-------------|
| 01 | [Basic ResNet-50](./pytorch-training/01-basic-resnet50/) | 🟢 Beginner | Train ResNet-50 on CIFAR-10 with a single GPU |
| 02 | [Distributed DDP](./pytorch-training/02-distributed-ddp/) | 🟡 Intermediate | Multi-node DDP training with gradient accumulation |
| 03 | [Carbon-Aware Training](./pytorch-training/03-carbon-aware-training/) | 🔴 Advanced | Pause/resume training based on carbon intensity |

### LLM Inference

| # | Example | Difficulty | Description |
|---|---------|-----------|-------------|
| 01 | [Streaming Llama](./llm-inference/01-streaming-llama/) | 🟢 Beginner | Streaming SSE inference with Python server + TypeScript client |
| 02 | [Quantized GPTQ](./llm-inference/02-quantized-gptq/) | 🟡 Intermediate | 4-bit quantized LLM with throughput benchmarking |
| 03 | [RAG Pipeline](./llm-inference/03-rag-pipeline/) | 🔴 Advanced | Retrieval-Augmented Generation with FAISS + LLM |

### Data Pipelines

| # | Example | Difficulty | Description |
|---|---------|-----------|-------------|
| 01 | [ETL Pipeline](./data-pipelines/01-etl-pipeline/) | 🟢 Beginner | Extract-Transform-Load with CSV → Parquet |
| 02 | [Streaming Inference](./data-pipelines/02-streaming-inference/) | 🟡 Intermediate | Real-time queue-based inference pipeline |

### Multi-Hub Deployment

| # | Example | Difficulty | Description |
|---|---------|-----------|-------------|
| 01 | [Geo-Distributed](./multi-hub/01-geo-distributed/) | 🟡 Intermediate | Multi-region deployment with latency-based routing |
| 02 | [Carbon-Optimized](./multi-hub/02-carbon-optimized/) | 🔴 Advanced | Carbon-intensity-aware traffic routing across hubs |

## Requirements

- **Python 3.9+**
- **HarchOS SDK** (`pip install harchos`)
- **Node.js 18+** (for TypeScript examples only)

## Project Structure

```
harchos-examples/
├── pytorch-training/          # GPU training examples
│   ├── 01-basic-resnet50/     #   Beginner: single-GPU training
│   ├── 02-distributed-ddp/    #   Intermediate: multi-node DDP
│   └── 03-carbon-aware-training/ # Advanced: carbon-aware scheduling
├── llm-inference/             # LLM serving examples
│   ├── 01-streaming-llama/    #   Beginner: SSE streaming (Python + TS)
│   ├── 02-quantized-gptq/     #   Intermediate: 4-bit GPTQ quantized
│   └── 03-rag-pipeline/       #   Advanced: RAG with FAISS
├── data-pipelines/            # Data processing examples
│   ├── 01-etl-pipeline/       #   Beginner: CSV → Parquet ETL
│   └── 02-streaming-inference/ #  Intermediate: real-time inference
├── multi-hub/                 # Multi-hub deployment examples
│   ├── 01-geo-distributed/    #   Intermediate: latency-based routing
│   └── 02-carbon-optimized/   #   Advanced: carbon-aware routing
├── .github/workflows/ci.yml   # CI: lint, validate, structure check
├── README.md                  # This file
├── CONTRIBUTING.md            # Contribution guidelines
└── LICENSE                    # Apache 2.0
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding new examples.

## License

Apache 2.0 — see [LICENSE](./LICENSE).
