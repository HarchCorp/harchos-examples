#!/usr/bin/env python3
"""Basic ResNet-50 training on CIFAR-10 for HarchOS.

This script trains a ResNet-50 model on the CIFAR-10 dataset using a single
GPU. It is designed to run both locally for development and as a HarchOS
workload on remote GPU nodes.

Usage:
    python train.py --epochs 10 --batch-size 64 --lr 0.01
"""

import argparse
import os
import time

import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights


def get_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="ResNet-50 CIFAR-10 Training")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Training batch size")
    parser.add_argument("--lr", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--output-dir", type=str, default="/output", help="Checkpoint output directory")
    parser.add_argument("--num-workers", type=int, default=4, help="DataLoader worker count")
    return parser.parse_args()


def get_dataloaders(batch_size: int, num_workers: int):
    """Create CIFAR-10 train and validation DataLoaders."""
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
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True
    )

    return train_loader, val_loader


def build_model() -> nn.Module:
    """Build ResNet-50 adapted for CIFAR-10 (10 classes, 32x32 images)."""
    model = resnet50(weights=ResNet50_Weights.DEFAULT)
    # Adapt first conv layer for 32x32 images (smaller kernel, no stride)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    # Remove max-pool since images are already small
    model.maxpool = nn.Identity()
    # Replace classifier for 10 classes
    model.fc = nn.Linear(model.fc.in_features, 10)
    return model


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch and return average loss."""
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
    """Evaluate model and return (loss, accuracy)."""
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


def main():
    args = get_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Data
    train_loader, val_loader = get_dataloaders(args.batch_size, args.num_workers)
    print(f"Train samples: {len(train_loader.dataset)}, Val samples: {len(val_loader.dataset)}")

    # Model
    model = build_model().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # Output directory
    os.makedirs(args.output_dir, exist_ok=True)

    best_accuracy = 0.0
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        print(f"\nEpoch {epoch}/{args.epochs}")
        print("-" * 40)

        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

        # Save best checkpoint
        if val_acc > best_accuracy:
            best_accuracy = val_acc
            ckpt_path = os.path.join(args.output_dir, "resnet50_best.pth")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_accuracy": best_accuracy,
            }, ckpt_path)
            print(f"  -> Saved best model ({val_acc:.2f}%) to {ckpt_path}")

    elapsed = time.time() - start_time
    print(f"\nTraining complete in {elapsed:.1f}s — Best Val Acc: {best_accuracy:.2f}%")


if __name__ == "__main__":
    main()
