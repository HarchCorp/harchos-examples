#!/usr/bin/env python3
"""Streaming Llama-2-7B inference server for HarchOS.

Provides a lightweight HTTP server with Server-Sent Events (SSE) streaming
for token-by-token generation. Designed to run as a HarchOS inference
workload.

Usage:
    python inference.py --port 8080
    python inference.py --port 8080 --model meta-llama/Llama-2-7b-chat-hf
"""

import argparse
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


# ---------------------------------------------------------------------------
# Model manager — loads and caches the model
# ---------------------------------------------------------------------------

class ModelManager:
    """Singleton-style model manager that lazily loads the LLM."""

    def __init__(self, model_name: str, device: str = "auto"):
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None

    def load(self):
        """Load model and tokenizer (called once on first request)."""
        if self._model is not None:
            return

        print(f"Loading model: {self.model_name}...")
        load_start = time.time()

        self._tokenizer = AutoTokenizer.from_pretrained(
            self.model_name, use_fast=True
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=dtype,
            device_map=self.device,
        )
        self._model.eval()

        elapsed = time.time() - load_start
        print(f"Model loaded in {elapsed:.1f}s on {self._model.device}")

    @property
    def model(self):
        self.load()
        return self._model

    @property
    def tokenizer(self):
        self.load()
        return self._tokenizer

    def generate_stream(self, prompt: str, max_tokens: int = 256,
                        temperature: float = 0.7, top_p: float = 0.9):
        """Generate tokens one by one and yield each as a dict."""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        input_length = inputs["input_ids"].shape[1]

        # Use the model's built-in streaming via generate with callback
        generated_tokens = []
        past_key_values = None

        current_input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        for step in range(max_tokens):
            with torch.no_grad():
                outputs = self.model(
                    input_ids=current_input_ids,
                    attention_mask=attention_mask,
                    past_key_values=past_key_values,
                    use_cache=True,
                )

            logits = outputs.logits[:, -1, :] / max(temperature, 1e-8)

            # Top-p (nucleus) sampling
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(
                torch.softmax(sorted_logits, dim=-1), dim=-1
            )
            # Remove tokens with cumulative probability above threshold
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = False
            indices_to_remove = sorted_indices_to_remove.scatter(
                1, sorted_indices, sorted_indices_to_remove
            )
            logits[indices_to_remove] = float("-inf")

            probs = torch.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            token_text = self.tokenizer.decode(next_token[0], skip_special_tokens=True)
            generated_tokens.append(next_token.item())

            yield {
                "token": token_text,
                "finished": False,
            }

            # Check for EOS
            if next_token.item() == self.tokenizer.eos_token_id:
                break

            # Prepare next step
            past_key_values = outputs.past_key_values
            current_input_ids = next_token
            attention_mask = torch.cat([
                attention_mask,
                torch.ones((1, 1), device=attention_mask.device, dtype=attention_mask.dtype)
            ], dim=1)

        # Final message with usage stats
        yield {
            "token": "",
            "finished": True,
            "usage": {
                "prompt_tokens": input_length,
                "completion_tokens": len(generated_tokens),
            },
        }


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

model_manager: Optional[ModelManager] = None


class InferenceHandler(BaseHTTPRequestHandler):
    """HTTP handler with /generate (SSE) and /health endpoints."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._set_headers()
            info = {"status": "ok", "model": model_manager.model_name}
            self.wfile.write(json.dumps(info).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())

    def do_POST(self):
        if self.path != "/generate":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid JSON"}).encode())
            return

        prompt = data.get("prompt", "")
        max_tokens = data.get("max_tokens", 256)
        temperature = data.get("temperature", 0.7)
        top_p = data.get("top_p", 0.9)

        if not prompt:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "prompt is required"}).encode())
            return

        # SSE response
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        for chunk in model_manager.generate_stream(
            prompt, max_tokens=max_tokens, temperature=temperature, top_p=top_p
        ):
            event_data = json.dumps(chunk)
            self.wfile.write(f"data: {event_data}\n\n".encode())
            self.wfile.flush()

    def log_message(self, format, *args):
        """Override to include timestamps."""
        print(f"[{self.log_date_time_string()}] {format % args}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Streaming Llama Inference Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    parser.add_argument("--model", type=str, default="meta-llama/Llama-2-7b-chat-hf",
                        help="HuggingFace model identifier")
    parser.add_argument("--device", type=str, default="auto", help="Device map")
    args = parser.parse_args()

    global model_manager
    model_manager = ModelManager(model_name=args.model, device=args.device)

    server = HTTPServer((args.host, args.port), InferenceHandler)
    print(f"Server running on http://{args.host}:{args.port}")
    print(f"  POST /generate  — streaming inference")
    print(f"  GET  /health    — health check")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
