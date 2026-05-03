# HarchOS Examples

Starter templates and example projects for common [HarchOS](https://github.com/HarchCorp/harchos) workflows.

## Categories

| Category | Description |
|---|---|
| **PyTorch Training** | Single-node, distributed, and carbon-aware training |
| **LLM Inference** | Streaming, quantized, and RAG inference pipelines |
| **Data Pipelines** | ETL and streaming data processing |
| **Multi-Hub Deployment** | Geo-distributed and carbon-optimized deployments |

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

## Examples

> Full catalog coming soon — see individual directories for details.

## Requirements

- Python 3.9+
- [HarchOS SDK](https://pypi.org/project/harchos/) (`pip install harchos`)

## License

Apache 2.0 — see [LICENSE](./LICENSE).
