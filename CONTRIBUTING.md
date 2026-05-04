# Contributing to HarchOS Examples

Thank you for your interest in contributing to HarchOS Examples! This guide will help you add new example projects that are consistent with the existing catalog.

## Adding a New Example

### 1. Choose a Category and Number

Examples are organized by category with sequential numbering:

- `pytorch-training/04-<name>/`
- `llm-inference/04-<name>/`
- `data-pipelines/03-<name>/`
- `multi-hub/03-<name>/`

Check existing examples to determine the next number.

### 2. Required Files

Every example **must** include:

| File | Purpose |
|------|---------|
| `README.md` | Overview, prerequisites, quick start, API/config docs |
| `*.py` | Self-contained, runnable source code |
| `workload.yaml` | HarchOS workload manifest |
| `requirements.txt` | Python dependencies (if any beyond `harchos`) |

### 3. README Template

Use this structure for your README:

```markdown
# <Title> on HarchOS

> **Difficulty:** Beginner | Intermediate | Advanced
> **Category:** <Category>
> **Time:** ~XX minutes

## Overview
<1-2 paragraph description>

## Prerequisites
- Python 3.9+
- HarchOS CLI (`pip install harchos`)
- <Any additional requirements>

## Quick Start
\`\`\`bash
pip install -r requirements.txt
python <script>.py
harchos workload apply workload.yaml
\`\`\`

## Configuration
| Parameter | Default | Description |
|-----------|---------|-------------|

## Files
| File | Purpose |
|------|---------|
```

### 4. Code Guidelines

- **Self-contained**: Every script must run independently — no shared modules
- **Graceful fallbacks**: If the `harchos` SDK is not installed, use simulated/placeholder data
- **Python 3.9+**: Use only features available in Python 3.9 and above
- **Type hints**: Add type annotations to all function signatures
- **Docstrings**: Every module and function should have a docstring
- **Error handling**: Wrap SDK calls in try/except with helpful error messages
- **Default arguments**: Scripts should work with sensible defaults (no required args)

### 5. Workload Manifest Guidelines

- Use `apiVersion: harchos.harchcorp.io/v1`
- Include `metadata.labels` with `category` and `difficulty`
- Set appropriate `resources` (GPU type, memory, CPU)
- Add `healthCheck` for long-running services
- Include `metrics` configuration

### 6. Testing Your Example

Before submitting a PR:

1. **Syntax check**: `python -m py_compile <script>.py`
2. **Local run**: Test the script locally (it should work without HarchOS)
3. **YAML validation**: Ensure `workload.yaml` is valid YAML with required fields
4. **README accuracy**: Verify all commands in the README actually work
5. **Difficulty rating**: Confirm the rating matches the actual complexity

### 7. Submit a Pull Request

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-new-example`
3. Add your example following the guidelines above
4. Update the top-level `README.md` catalog table
5. Commit with a descriptive message: `feat: add <name> example`
6. Open a PR against the `main` branch

## Code of Conduct

- Be respectful and constructive in all interactions
- Focus on what is best for the community
- Support fellow contributors, especially newcomers

## Questions?

Open an issue on [GitHub](https://github.com/HarchCorp/harchos-examples/issues) and we'll help you out.
