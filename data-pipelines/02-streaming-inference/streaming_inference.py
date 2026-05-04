#!/usr/bin/env python3
"""Streaming inference pipeline for HarchOS.

Processes data items from a source queue, runs ML model inference on each,
and publishes enriched results to an output sink. Designed for continuous,
event-driven inference workloads.

This example uses a sentiment analysis model (DistilBERT SST-2) but the
pattern applies to any model: classification, NER, translation, etc.

Usage:
    python streaming_inference.py
    python streaming_inference.py --model distilbert-base-uncased-finetuned-sst-2-english
    python streaming_inference.py --batch-size 8 --poll-interval 5
"""

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

try:
    from transformers import pipeline  # noqa: F401
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("[WARN] transformers not installed — using mock inference")

try:
    from harchos import HarchOSClient
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Queue / Source abstraction
# ---------------------------------------------------------------------------

class FileQueue:
    """Simple file-based queue for demonstration.

    Items are JSON files in an input directory. Processed items are moved
    to a completed directory. In production, replace with Redis, Kafka, etc.
    """

    def __init__(self, input_dir: str, output_dir: str, completed_dir: str = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.completed_dir = Path(completed_dir or os.path.join(output_dir, "_completed"))

        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

    def poll(self) -> list:
        """Return list of unprocessed item paths."""
        return sorted(self.input_dir.glob("*.json"))

    def complete(self, item_path: Path):
        """Move processed item to completed directory."""
        dest = self.completed_dir / item_path.name
        item_path.rename(dest)

    def publish(self, result: dict):
        """Write inference result to output directory."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        output_path = self.output_dir / f"result_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)


class MockQueue:
    """In-memory queue that generates sample items for testing."""

    def __init__(self, num_items: int = 20):
        self.items = [
            {
                "id": i,
                "text": text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i, text in enumerate([
                "This product is amazing! Best purchase ever.",
                "Terrible experience. Would not recommend.",
                "It's okay, nothing special but gets the job done.",
                "Absolutely love it! Five stars all the way.",
                "Waste of money. Broke after one day.",
                "Pretty decent quality for the price.",
                "Outstanding service and fast delivery!",
                "The worst customer service I've ever experienced.",
                "Neutral about this — neither good nor bad.",
                "Highly recommended! Will buy again.",
                "Disappointed with the quality. Expected better.",
                "Great value, works as advertised.",
                "Not worth the hype. Very mediocre.",
                "Exceeded my expectations! Fantastic product.",
                "Returned it immediately. Awful quality.",
                "Solid product. No complaints so far.",
                "Life-changing! I can't believe how good this is.",
                "Complete garbage. Save your money.",
                "Average product. Does what it says, nothing more.",
                "Incredible! A must-have for everyone.",
            ])
        ]
        self.index = 0
        self.output_dir = Path("/tmp/streaming_inference_output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def poll(self) -> list:
        """Return next batch of items (simulates new arrivals)."""
        if self.index >= len(self.items):
            return []
        items = self.items[self.index:self.index + 3]  # Return 3 at a time
        self.index += len(items)
        return items

    def complete(self, item):
        """No-op for mock queue."""
        pass

    def publish(self, result: dict):
        """Write result to output directory."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        output_path = self.output_dir / f"result_{timestamp}.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)


# ---------------------------------------------------------------------------
# Inference engine
# ---------------------------------------------------------------------------

class InferenceEngine:
    """Loads a model and runs inference on batches of items."""

    def __init__(self, model_name: str, device: str = "auto", batch_size: int = 8):
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = self._resolve_device(device)
        self._pipeline = None

    def _resolve_device(self, device: str) -> int:
        """Resolve device string to device index for pipeline."""
        if device == "auto":
            return 0 if torch.cuda.is_available() else -1
        if device == "cpu":
            return -1
        return int(device)

    def load(self):
        """Load the model pipeline."""
        if self._pipeline is not None:
            return

        if TRANSFORMERS_AVAILABLE:
            print(f"Loading model: {self.model_name}...")
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                device=self.device,
                top_k=None,  # Return all labels
            )
            print("Model loaded")
        else:
            print("Using mock inference engine")

    def infer_batch(self, items: list) -> list:
        """Run inference on a batch of items."""
        texts = [item["text"] for item in items]

        if self._pipeline is not None:
            # Real inference
            results = self._pipeline(texts, truncation=True, max_length=512)
            # pipeline returns list of list of dicts for top_k=None
            if isinstance(results[0], list):
                # Multiple labels returned
                enriched = []
                for item, scores in zip(items, results):
                    top = max(scores, key=lambda x: x["score"])
                    enriched.append({
                        **item,
                        "prediction": top["label"],
                        "confidence": round(top["score"], 4),
                        "all_scores": {s["label"]: round(s["score"], 4) for s in scores},
                        "model": self.model_name,
                        "inference_timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                return enriched
            else:
                # Single label
                enriched = []
                for item, result in zip(items, results):
                    enriched.append({
                        **item,
                        "prediction": result["label"],
                        "confidence": round(result["score"], 4),
                        "model": self.model_name,
                        "inference_timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                return enriched
        else:
            # Mock inference
            import random
            return [
                {
                    **item,
                    "prediction": random.choice(["POSITIVE", "NEGATIVE"]),
                    "confidence": round(random.uniform(0.6, 0.99), 4),
                    "model": "mock",
                    "inference_timestamp": datetime.now(timezone.utc).isoformat(),
                }
                for item in items
            ]


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(args):
    """Main streaming inference loop."""
    engine = InferenceEngine(
        model_name=args.model,
        device=args.device,
        batch_size=args.batch_size,
    )
    engine.load()

    # Set up queue
    if args.input_dir and os.path.isdir(args.input_dir):
        queue = FileQueue(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
        )
        print(f"Using file queue: {args.input_dir} -> {args.output_dir}")
    else:
        queue = MockQueue(num_items=20)
        print("Using mock queue with sample data")

    # Metrics logger (optional)
    harchos_client = None
    if HARCHOS_AVAILABLE:
        try:
            harchos_client = HarchOSClient(api_key=os.environ.get("HARCHOS_API_KEY", ""))
        except Exception:
            pass

    print(f"\nStarting streaming pipeline (poll every {args.poll_interval}s)")
    print("Press Ctrl+C to stop\n")

    total_processed = 0
    total_errors = 0

    try:
        while True:
            items = queue.poll()

            if not items:
                if args.once:
                    print("No items found, exiting (--once mode)")
                    break
                time.sleep(args.poll_interval)
                continue

            # Process in batches
            for i in range(0, len(items), args.batch_size):
                batch = items[i:i + args.batch_size]
                try:
                    start = time.time()
                    results = engine.infer_batch(batch)
                    elapsed = time.time() - start

                    for result in results:
                        queue.publish(result)

                    total_processed += len(batch)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Processed {len(batch)} items in {elapsed:.3f}s "
                          f"({len(batch)/elapsed:.1f} items/s)")

                    if harchos_client:
                        try:
                            pass  # HarchOS client initialized; use for metrics tracking
                        except Exception:
                            pass

                except Exception as e:
                    total_errors += 1
                    print(f"[ERROR] Batch inference failed: {e}")
                    for item in batch:
                        queue.publish({
                            **item,
                            "error": str(e),
                            "status": "failed",
                        })

            # Mark items as completed (for FileQueue)
            if isinstance(queue, FileQueue):
                for item_path in queue.poll():
                    try:
                        queue.complete(item_path)
                    except Exception:
                        pass
            elif isinstance(queue, MockQueue):
                pass  # MockQueue doesn't need completion

            if args.once:
                break

    except KeyboardInterrupt:
        print("\n\nStopping pipeline...")

    print("\nPipeline Summary:")
    print(f"  Total processed: {total_processed}")
    print(f"  Total errors:    {total_errors}")
    print(f"  Output dir:      {queue.output_dir}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Streaming Inference Pipeline")
    parser.add_argument("--model", type=str,
                        default="distilbert-base-uncased-finetuned-sst-2-english",
                        help="HuggingFace model for inference")
    parser.add_argument("--input-dir", type=str, default=None,
                        help="Input directory (file queue)")
    parser.add_argument("--output-dir", type=str, default="/data/output",
                        help="Output directory for results")
    parser.add_argument("--device", type=str, default="auto",
                        help="Device: auto, cpu, or GPU index")
    parser.add_argument("--batch-size", type=int, default=8,
                        help="Inference batch size")
    parser.add_argument("--poll-interval", type=int, default=5,
                        help="Seconds between queue polls")
    parser.add_argument("--once", action="store_true",
                        help="Process available items and exit")
    args = parser.parse_args()

    run_pipeline(args)


if __name__ == "__main__":
    main()
