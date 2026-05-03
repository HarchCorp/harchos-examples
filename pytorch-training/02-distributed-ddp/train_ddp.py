#!/usr/bin/env python3
"""Distributed Data Parallel ResNet-50 training for HarchOS.

Uses torch.distributed for multi-node, multi-GPU training. HarchOS
automatically sets MASTER_ADDR, MASTER_PORT, WORLD_SIZE, and RANK
environment variables when the workload is deployed.

Usage:
    # Local testing (2 GPUs on one node)
    torchrun --nproc_per_node=2 train_ddp.py --epochs 5

    # HarchOS deployment
    harchos workload apply workload.yaml
"""

import argparse
import os
import time

import torch
import torch.distributed as dist
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
from torchvision.models import resnet50, ResNet50_Weights
from torch.nn.parallel import DistributedDataParallel as DDP


def get_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="DDP ResNet-50 Training")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Per-GPU batch size")
    parser.add_argument("--lr", type=float, default=0.1, help="Base learning rate")
    parser.add_argument("--accum-steps", type=int, default=1, help="Gradient accumulation steps")
    parser.add_argument("--backend", type=str, default="nccl", help="Distributed backend")
    parser.add_argument("--output-dir", type=str, default="/output", help="Checkpoint directory")
    parser.add_argument("--num-workers", type=int, default=4, help="DataLoader workers")
    return parser.parse_args()


def setup_distributed():
    """Initialize the distributed process group.

    HarchOS injects the following environment variables:
      - MASTER_ADDR: address of the rank-0 node
      - MASTER_PORT: free port on the rank-0 node
      - WORLD_SIZE: total number of processes
      - RANK: global rank of this process
      - LOCAL_RANK: local rank within the node
    """
    dist.init_process_group(backend=os.getenv("DIST_BACKEND", "nccl"))
    local_rank = int(os.getenv("LOCAL_RANK", 0))
    torch.cuda.set_device(local_rank)
    return dist.get_rank(), dist.get_world_size(), local_rank


def cleanup():
    """Clean up the distributed process group."""
    if dist.is_initialized():
        dist.destroy_process_group()


def get_dataloaders(batch_size: int, rank: int, world_size: int, num_workers: int):
    """Create distributed samplers for CIFAR-10."""
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

    train_sampler = torch.utils.data.distributed.DistributedSampler(
        train_dataset, num_replicas=world_size, rank=rank, shuffle=True
    )
    val_sampler = torch.utils.data.distributed.DistributedSampler(
        val_dataset, num_replicas=world_size, rank=rank, shuffle=False
    )

    train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=batch_size, sampler=train_sampler,
        num_workers=num_workers, pin_memory=True,
    )
    val_loader = torch.utils.data.DataLoader(
        val_dataset, batch_size=batch_size, sampler=val_sampler,
        num_workers=num_workers, pin_memory=True,
    )

    return train_loader, val_loader, train_sampler, val_sampler


def build_model(local_rank: int) -> nn.Module:
    """Build ResNet-50 adapted for CIFAR-10 and wrap in DDP."""
    model = resnet50(weights=ResNet50_Weights.DEFAULT)
    model.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    model.maxpool = nn.Identity()
    model.fc = nn.Linear(model.fc.in_features, 10)

    model = model.to(local_rank)
    model = DDP(model, device_ids=[local_rank])
    return model


def train_one_epoch(model, loader, criterion, optimizer, device, epoch, accum_steps):
    """Train one epoch with gradient accumulation."""
    model.train()
    running_loss = 0.0
    total = 0
    optimizer.zero_grad()

    for batch_idx, (inputs, targets) in enumerate(loader):
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets) / accum_steps
        loss.backward()

        if (batch_idx + 1) % accum_steps == 0:
            optimizer.step()
            optimizer.zero_grad()

        running_loss += loss.item() * accum_steps * inputs.size(0)
        total += inputs.size(0)

        if (batch_idx + 1) % 50 == 0:
            print(f"  [Epoch {epoch}] batch {batch_idx + 1}/{len(loader)}, loss: {loss.item() * accum_steps:.4f}")

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

    # Aggregate across all ranks
    dist.all_reduce(torch.tensor([running_loss]).cuda())
    dist.all_reduce(torch.tensor([correct]).cuda())
    dist.all_reduce(torch.tensor([total]).cuda())

    avg_loss = running_loss / total
    accuracy = 100.0 * correct / total
    return avg_loss, accuracy


def main():
    args = get_args()
    rank, world_size, local_rank = setup_distributed()
    device = torch.device(f"cuda:{local_rank}")

    if rank == 0:
        print(f"World size: {world_size}, Device: {device}")

    # Data
    train_loader, val_loader, train_sampler, val_sampler = get_dataloaders(
        args.batch_size, rank, world_size, args.num_workers
    )

    # Model
    model = build_model(local_rank)
    criterion = nn.CrossEntropyLoss()
    # Scale learning rate linearly with world size
    lr = args.lr * world_size
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=5e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    os.makedirs(args.output_dir, exist_ok=True)
    best_accuracy = 0.0
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        train_sampler.set_epoch(epoch)  # Ensure proper shuffling across epochs

        if rank == 0:
            print(f"\nEpoch {epoch}/{args.epochs}")
            print("-" * 40)

        train_loss = train_one_epoch(
            model, train_loader, criterion, optimizer, device, epoch, args.accum_steps
        )
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        if rank == 0:
            print(f"Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

            if val_acc > best_accuracy:
                best_accuracy = val_acc
                ckpt_path = os.path.join(args.output_dir, "resnet50_ddp_best.pth")
                torch.save({
                    "epoch": epoch,
                    "model_state_dict": model.module.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "best_accuracy": best_accuracy,
                }, ckpt_path)
                print(f"  -> Saved best model ({val_acc:.2f}%) to {ckpt_path}")

    if rank == 0:
        elapsed = time.time() - start_time
        print(f"\nTraining complete in {elapsed:.1f}s — Best Val Acc: {best_accuracy:.2f}%")

    cleanup()


if __name__ == "__main__":
    main()
