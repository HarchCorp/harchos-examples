#!/usr/bin/env python3
"""GPTQ quantized model deployment for HarchOS.

Loads a GPTQ-quantized LLM, runs a quick benchmark, and starts an HTTP
inference server. GPTQ reduces model memory by ~3-4x with minimal quality
loss, enabling larger models on cost-effective GPU instances.

Usage:
    python deploy_quantized.py --model TheBloke/Llama-2-7B-Chat-GPTQ
    python deploy_quantized.py --model TheBloke/Llama-2-7B-Chat-GPTQ --port 8080
"""

import argparse
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ---------------------------------------------------------------------------
# Quantized model loader
# ---------------------------------------------------------------------------

class GPTQModelManager:
    """Manages loading and inference for GPTQ-quantized models."""

    def __init__(self, model_name: str, device: str = "auto"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None

    def load(self):
        """Load the GPTQ-quantized model and tokenizer."""
        if self._model is not None:
            return

        print(f"Loading GPTQ model: {self.model_name}...")
        load_start = time.time()

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, use_fast=True
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map=self.device,
            # GPTQ-specific kwargs — transformers handles these automatically
            # when the model config indicates GPTQ quantization
        )
        self._model.eval()

        elapsed = time.time() - load_start
        vram_mb = torch.cuda.memory_allocated() / 1024 / 1024 if torch.cuda.is_available() else 0
        print(f"Model loaded in {elapsed:.1f}s")
        print(f"VRAM allocated: {vram_mb:.0f} MB")

    @property
    def model(self):
        self.load()
        return self._model

    @property
    def tokenizer(self):
        self.load()
        return self._tokenizer

    def generate(self, prompt: str, max_tokens: int = 256,
                 temperature: float = 0.7, top_p: float = 0.9) -> dict:
        """Generate a complete response (non-streaming for simplicity)."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        input_length = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=max(temperature, 1e-8),
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        new_tokens = outputs[0][input_length:]
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        return {
            "prompt": prompt,
            "completion": text,
            "usage": {
                "prompt_tokens": input_length,
                "completion_tokens": len(new_tokens),
            },
        }

    def benchmark(self, prompt: str = "The future of AI is",
                  max_tokens: int = 128, num_runs: int = 5) -> dict:
        """Run a simple throughput benchmark."""
        print(f"\nRunning benchmark ({num_runs} runs, {max_tokens} max tokens)...")
        latencies = []
        tokens_per_sec = []

        for i in range(num_runs):
            start = time.time()
            result = self.generate(prompt, max_tokens=max_tokens)
            elapsed = time.time() - start

            latency = elapsed
            tps = result["usage"]["completion_tokens"] / max(elapsed, 1e-6)

            latencies.append(latency)
            tokens_per_sec.append(tps)
            print(f"  Run {i+1}: {latency:.2f}s, {tps:.1f} tokens/s")

        avg_latency = sum(latencies) / len(latencies)
        avg_tps = sum(tokens_per_sec) / len(tokens_per_sec)

        bench = {
            "model": self.model_name,
            "avg_latency_seconds": round(avg_latency, 3),
            "avg_tokens_per_second": round(avg_tps, 1),
            "num_runs": num_runs,
            "max_tokens": max_tokens,
        }
        print(f"\nBenchmark results: {json.dumps(bench, indent=2)}")
        return bench


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

model_manager: Optional[GPTQModelManager] = None


class QuantizedInferenceHandler(BaseHTTPRequestHandler):
    """HTTP handler for quantized model inference."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            vram = 0
            if torch.cuda.is_available():
                vram = torch.cuda.memory_allocated() / 1024 / 1024
            self._set_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "model": model_manager.model_name,
                "vram_mb": round(vram, 0),
            }).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        if self.path == "/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))

            prompt = body.get("prompt", "")
            max_tokens = body.get("max_tokens", 256)
            temperature = body.get("temperature", 0.7)
            top_p = body.get("top_p", 0.9)

            if not prompt:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "prompt is required"}).encode())
                return

            result = model_manager.generate(
                prompt, max_tokens=max_tokens, temperature=temperature, top_p=top_p
            )
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())

        elif self.path == "/benchmark":
            result = model_manager.benchmark()
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="GPTQ Quantized Model Server")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--model", type=str, default="TheBloke/Llama-2-7B-Chat-GPTQ")
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--skip-benchmark", action="store_true",
                        help="Skip startup benchmark")
    args = parser.parse_args()

    global model_manager
    model_manager = GPTQModelManager(model_name=args.model, device=args.device)
    model_manager.load()

    # Run benchmark on startup
    if not args.skip_benchmark:
        model_manager.benchmark()

    server = HTTPServer((args.host, args.port), QuantizedInferenceHandler)
    print(f"\nGPTQ Inference Server running on http://{args.host}:{args.port}")
    print(f"  POST /generate   — generate text")
    print(f"  POST /benchmark  — run throughput benchmark")
    print(f"  GET  /health     — health check")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
