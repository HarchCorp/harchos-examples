#!/usr/bin/env python3
"""Carbon-aware ResNet-50 training for HarchOS.

This script integrates with the HarchOS Carbon API to schedule training
during periods of low carbon intensity. When the grid carbon intensity
exceeds a configurable threshold, training is paused automatically and
resumed once the intensity drops.

Usage:
    python train_carbon_aware.py --epochs 10 --carbon-threshold 200
"""

import argparse
import os
import time
from datetime import datetime, timezone

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights

try:
    from harchos import CarbonClient, MetricsLogger
    HARCHOS_AVAILABLE = True
except ImportError:
    HARCHOS_AVAILABLE = False
    print("[WARN] harchos SDK not installed — using simulated carbon data")


# ---------------------------------------------------------------------------
# Carbon intensity helpers
# ---------------------------------------------------------------------------

class SimulatedCarbonClient:
    """Fallback carbon client that generates plausible simulated data."""

    def __init__(self, baseline: float = 150.0, amplitude: float = 100.0):
        self.baseline = baseline
        self.amplitude = amplitude

    def get_intensity(self, region: str = "eu-west-1") -> dict:
        """Return a simulated carbon intensity reading.

        Uses a sinusoidal pattern to mimic day/night carbon variation.
        """
        hour = datetime.now(timezone.utc).hour
        # Simulate higher carbon during peak hours (8-18)
        variation = self.amplitude * (0.5 + 0.5 * __import__("math").sin(
            2 * __import__("math").pi * (hour - 6) / 24
        ))
        intensity = max(0, self.baseline + variation - self.amplitude / 2)
        return {
            "region": region,
            "intensity_gco2_kwh": round(intensity, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "simulated",
        }


def create_carbon_client() -> object:
    """Create a carbon client — real or simulated."""
    if HARCHOS_AVAILABLE:
        client = CarbonClient()
        return client
    return SimulatedCarbonClient()


# ---------------------------------------------------------------------------
# Training logic (reused from 01-basic-resnet50)
# ---------------------------------------------------------------------------

def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Carbon-Aware ResNet-50 Training")
    parser.add_argument("--epochs", type=int, default=10, help="Target epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate")
    parser.add_argument("--output-dir", type=str, default="/output", help="Output directory")
    parser.add_argument("--carbon-threshold", type=float, default=200.0,
                        help="Max carbon intensity in gCO2/kWh")
    parser.add_argument("--poll-interval", type=int, default=300,
                        help="Seconds between carbon intensity checks")
    parser.add_argument("--region", type=str, default="eu-west-1",
                        help="Carbon intensity region")
    parser.add_argument("--num-workers", type=int, default=4, help="DataLoader workers")
    return parser.parse_args()


def get_dataloaders(batch_size: int, num_workers: int):
    """Create CIFAR-10 DataLoaders."""
    transform_train = transforms.Compose([
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    transform_val = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_dataset = torchvision.datasets.CIFAR10(
        root="./data", train=True, download=True, transform=transform_train
    )
    val_dataset = torchvision.datasets.CIFAR10(
        root="./data", train=False, download=True, transform=transform_val
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )
    return train_loader, val_loader


def build_model() -> nn.Module:
    """Build ResNet-50 for CIFAR-10."""
    model = resnet50(weights=ResNet50_Weights.DEFAULT)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.maxpool = nn.Identity()
    model.fc = nn.Linear(model.fc.in_features, 10)
    return model


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    running_loss = 0.0
    total = 0
    for batch_idx, (inputs, targets) in enumerate(loader):
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
        total += inputs.size(0)
        if (batch_idx + 1) % 100 == 0:
            print(f"  batch {batch_idx + 1}/{len(loader)}, loss: {loss.item():.4f}")
    return running_loss / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    """Evaluate the model."""
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, targets in loader:
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        running_loss += loss.item() * inputs.size(0)
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
    avg_loss = running_loss / total
    accuracy = 100.0 * correct / total
    return avg_loss, accuracy


# ---------------------------------------------------------------------------
# Carbon-aware orchestration
# ---------------------------------------------------------------------------

def wait_for_low_carbon(carbon_client, threshold: float, poll_interval: int,
                        region: str, epoch: int):
    """Pause training until carbon intensity drops below threshold.

    Logs waiting status and polls at the specified interval.
    """
    while True:
        data = carbon_client.get_intensity(region=region)
        intensity = data["intensity_gco2_kwh"]
        source = data.get("source", "live")
        ts = data.get("timestamp", "N/A")

        if intensity <= threshold:
            print(f"  ✅ Carbon intensity {intensity:.1f} gCO2/kWh ≤ {threshold} — resuming training")
            return intensity

        print(f"  ⏸  Carbon intensity {intensity:.1f} gCO2/kWh > {threshold} — "
              f"pausing epoch {epoch} (source: {source}, time: {ts})")
        print(f"     Next check in {poll_interval}s...")
        time.sleep(poll_interval)


def main():
    args = get_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Carbon threshold: {args.carbon_threshold} gCO2/kWh")
    print(f"Carbon poll interval: {args.poll_interval}s")
    print(f"Region: {args.region}")

    # Carbon client
    carbon_client = create_carbon_client()

    # Optional HarchOS metrics logger
    metrics_logger = None
    if HARCHOS_AVAILABLE:
        try:
            metrics_logger = MetricsLogger()
        except Exception:
            print("[WARN] Could not initialize HarchOS MetricsLogger")

    # Data and model
    train_loader, val_loader = get_dataloaders(args.batch_size, args.num_workers)
    model = build_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    os.makedirs(args.output_dir, exist_ok=True)

    # Carbon-aware training loop
    best_accuracy = 0.0
    total_carbon_wait_time = 0.0
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        print(f"\n{'='*50}")
        print(f"Epoch {epoch}/{args.epochs}")
        print(f"{'='*50}")

        # Wait for low-carbon window
        wait_start = time.time()
        intensity = wait_for_low_carbon(
            carbon_client, args.carbon_threshold, args.poll_interval,
            args.region, epoch
        )
        wait_time = time.time() - wait_start
        total_carbon_wait_time += wait_time

        if wait_time > 0:
            print(f"  Carbon wait time: {wait_time:.0f}s")

        # Train
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        # Log metrics
        print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        print(f"Carbon Intensity at epoch end: {intensity:.1f} gCO2/kWh")

        if metrics_logger:
            try:
                metrics_logger.log({
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "val_accuracy": val_acc,
                    "carbon_intensity_gco2_kwh": intensity,
                    "carbon_wait_seconds": wait_time,
                })
            except Exception as e:
                print(f"[WARN] Metrics logging failed: {e}")

        # Save best
        if val_acc > best_accuracy:
            best_accuracy = val_acc
            ckpt_path = os.path.join(args.output_dir, "resnet50_carbon_aware_best.pth")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_accuracy": best_accuracy,
                "carbon_intensity": intensity,
            }, ckpt_path)
            print(f"  -> Saved best model ({val_acc:.2f}%) to {ckpt_path}")

    # Summary
    elapsed = time.time() - start_time
    training_time = elapsed - total_carbon_wait_time

    print(f"\n{'='*50}")
    print("TRAINING COMPLETE")
    print(f"{'='*50}")
    print(f"  Total wall time:     {elapsed:.1f}s")
    print(f"  Training time:       {training_time:.1f}s")
    print(f"  Carbon wait time:    {total_carbon_wait_time:.1f}s")
    print(f"  Carbon savings:      {total_carbon_wait_time / max(elapsed, 1) * 100:.1f}% of wall time spent waiting for clean energy")
    print(f"  Best Val Accuracy:   {best_accuracy:.2f}%")


if __name__ == "__main__":
    main()
