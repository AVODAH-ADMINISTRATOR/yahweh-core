"""
Phase 4: Distributed Training Script
Step 93: Setup distributed training across multi-node GPU clusters (DeepSpeed)
Step 94: Domain-specific continuous pre-training (CPT)
Step 95: Supervised fine-tuning (SFT) on verified parallel alignments
Step 101: Mixed-precision training (BF16/FP16)
Step 102: Gradient accumulation steps
Step 108: Hyperparameter tuning optimization
Step 110: Early stopping criteria based on validation loss plateaus
Step 112: Checkpointing pipelines
Step 113: Training stability monitoring (gradient explosion/vanishing)

Usage (multi-node, 8x GPU):
  deepspeed --num_gpus=8 --num_nodes=2 train.py \
    --config config.yaml \
    --deepspeed deepspeed_config.json \
    --train_data data/train.parquet \
    --val_data data/val.parquet
"""

import argparse
import logging
import math
import os
import time
from pathlib import Path
from typing import Dict, Optional

import torch
import torch.distributed as dist
import yaml

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YahwehEngine Phase 4 Training — DeepSpeed Multi-GPU"
    )
    parser.add_argument("--config", type=str, default="config.yaml")
    parser.add_argument("--deepspeed", type=str, default="deepspeed_config.json")
    parser.add_argument("--train_data", type=str, required=True)
    parser.add_argument("--val_data", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="checkpoints/")
    parser.add_argument("--resume_from", type=str, default=None,
                        help="Resume from checkpoint path")
    parser.add_argument("--local_rank", type=int, default=-1,
                        help="Set by DeepSpeed for distributed training")
    # Step 100: Translation formality register
    parser.add_argument("--formality_weight", type=float, default=0.5,
                        help="0.0=Formal/Literal, 1.0=Dynamic/Functional")
    return parser.parse_args()


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def setup_logging(rank: int, output_dir: str):
    level = logging.INFO if rank in (-1, 0) else logging.WARNING
    logging.basicConfig(
        format="[%(asctime)s] [Rank %(process)d] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
    )
    if rank in (-1, 0):
        Path(output_dir).mkdir(parents=True, exist_ok=True)


def is_main_process(local_rank: int) -> bool:
    return local_rank in (-1, 0)


def compute_gradient_norm(model) -> float:
    """Step 113: Monitor gradient norms to detect explosion/vanishing."""
    total_norm = 0.0
    for p in model.parameters():
        if p.grad is not None:
            param_norm = p.grad.detach().data.norm(2)
            total_norm += param_norm.item() ** 2
    return math.sqrt(total_norm)


def train_epoch(
    engine,
    train_loader,
    criterion,
    step: int,
    config: dict,
    formality_weight: float,
    scaler=None,
) -> Dict[str, float]:
    """Run one training epoch. Returns aggregate loss metrics."""
    engine.train()
    total_loss = 0.0
    total_ce = 0.0
    total_keyword_penalty = 0.0
    total_align_reg = 0.0
    num_batches = 0

    grad_accum_steps = config["training"].get("gradient_accumulation_steps", 4)

    for batch_idx, batch in enumerate(train_loader):
        # Move batch to device
        src_tokens = batch["src_tokens"].to(engine.device)
        decoder_input = batch["decoder_input"].to(engine.device)
        labels = batch["labels"].to(engine.device)
        src_padding_mask = batch["src_key_padding_mask"].to(engine.device)
        lang_ids = batch["lang_ids"].to(engine.device)

        # Forward pass
        logits, alignment_scores = engine(
            src_tokens=src_tokens,
            tgt_tokens=decoder_input,
            lang_id=lang_ids,
            src_key_padding_mask=src_padding_mask,
        )

        # Compute theological penalty loss (Step 99)
        loss_dict = criterion(
            logits=logits,
            targets=labels,
            alignment_scores=alignment_scores,
            formality_weight=formality_weight,
        )
        loss = loss_dict["loss"] / grad_accum_steps

        # Backward pass (DeepSpeed handles the optimizer step)
        engine.backward(loss)

        if (batch_idx + 1) % grad_accum_steps == 0:
            # Step 113: Log gradient norm before clipping
            grad_norm = compute_gradient_norm(engine.module)
            engine.step()
            step += 1

            if is_main_process(engine.local_rank) and step % config["training"].get("log_steps", 100) == 0:
                logger.info(
                    f"Step {step:6d} | "
                    f"loss={loss_dict['loss'].item():.4f} | "
                    f"ce={loss_dict['ce_loss'].item():.4f} | "
                    f"keyword={loss_dict['keyword_penalty'].item():.4f} | "
                    f"align={loss_dict['alignment_reg'].item():.4f} | "
                    f"grad_norm={grad_norm:.3f}"
                )

        total_loss += loss_dict["loss"].item()
        total_ce += loss_dict["ce_loss"].item()
        total_keyword_penalty += loss_dict["keyword_penalty"].item()
        total_align_reg += loss_dict["alignment_reg"].item()
        num_batches += 1

    return {
        "train/loss": total_loss / max(num_batches, 1),
        "train/ce_loss": total_ce / max(num_batches, 1),
        "train/keyword_penalty": total_keyword_penalty / max(num_batches, 1),
        "train/alignment_reg": total_align_reg / max(num_batches, 1),
        "step": step,
    }


@torch.no_grad()
def validate(engine, val_loader, criterion, formality_weight: float) -> Dict[str, float]:
    """Evaluate on validation set. Returns validation metrics."""
    engine.eval()
    total_loss = 0.0
    num_batches = 0

    for batch in val_loader:
        src_tokens = batch["src_tokens"].to(engine.device)
        decoder_input = batch["decoder_input"].to(engine.device)
        labels = batch["labels"].to(engine.device)
        src_padding_mask = batch["src_key_padding_mask"].to(engine.device)
        lang_ids = batch["lang_ids"].to(engine.device)

        logits, alignment_scores = engine(
            src_tokens=src_tokens,
            tgt_tokens=decoder_input,
            lang_id=lang_ids,
            src_key_padding_mask=src_padding_mask,
        )
        loss_dict = criterion(logits, labels, alignment_scores, formality_weight)
        total_loss += loss_dict["loss"].item()
        num_batches += 1

    return {"val/loss": total_loss / max(num_batches, 1)}


def main():
    args = parse_args()
    config = load_config(args.config)

    # --- Initialize DeepSpeed distributed environment ---
    try:
        import deepspeed
        deepspeed.init_distributed()
        local_rank = int(os.environ.get("LOCAL_RANK", 0))
        torch.cuda.set_device(local_rank)
        device = torch.device(f"cuda:{local_rank}")
    except ImportError:
        logger.warning("DeepSpeed not found — falling back to single-GPU/CPU mode.")
        local_rank = -1
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    setup_logging(local_rank, args.output_dir)
    logger.info(f"Training on device: {device}")

    # --- Build Model ---
    from model_architecture import build_yahweh_engine
    model_cfg = config.get("model", {})
    model = build_yahweh_engine(
        size=model_cfg.get("size", "base"),
        src_vocab_size=model_cfg.get("src_vocab_size", 64000),
        tgt_vocab_size=model_cfg.get("tgt_vocab_size", 64000),
        use_flash_attention=model_cfg.get("use_flash_attention", True),
    )
    logger.info(
        f"Model: {model_cfg.get('size', 'base')} | "
        f"Parameters: {sum(p.numel() for p in model.parameters()):,}"
    )

    # --- Build Loss ---
    from loss import TheologicalPenaltyLoss
    criterion = TheologicalPenaltyLoss(
        vocab_size=model_cfg.get("tgt_vocab_size", 64000),
        keyword_penalty_weight=config["training"].get("keyword_penalty_weight", 3.0),
        alignment_reg_weight=config["training"].get("alignment_reg_weight", 0.1),
        label_smoothing=config["training"].get("label_smoothing", 0.1),
    )

    # --- Build DataLoaders ---
    from dataset import build_dataloaders
    train_loader, val_loader = build_dataloaders(
        train_path=args.train_data,
        val_path=args.val_data,
        batch_size=config["training"].get("per_gpu_batch_size", 4),
        num_workers=config["training"].get("num_workers", 4),
        max_src_len=config["training"].get("max_src_len", 512),
        max_tgt_len=config["training"].get("max_tgt_len", 512),
    )

    # --- Initialize DeepSpeed Engine ---
    training_cfg = config["training"]
    optimizer_cfg = {
        "type": "AdamW",
        "params": {
            "lr": training_cfg.get("learning_rate", 2e-5),
            "betas": [0.9, 0.95],
            "eps": 1e-8,
            "weight_decay": training_cfg.get("weight_decay", 0.1),
        }
    }

    if local_rank != -1:
        engine, optimizer, _, lr_scheduler = deepspeed.initialize(
            model=model,
            model_parameters=model.parameters(),
            config=args.deepspeed,
        )
    else:
        # Fallback: standard PyTorch training (CPU/single GPU)
        engine = model.to(device)
        engine.device = device
        engine.local_rank = local_rank
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=training_cfg.get("learning_rate", 2e-5),
            weight_decay=training_cfg.get("weight_decay", 0.1),
        )

    # --- Checkpointing: Resume if specified (Step 112) ---
    from checkpoint import CheckpointManager
    ckpt_manager = CheckpointManager(
        output_dir=args.output_dir,
        keep_last_n=config["training"].get("keep_last_n_checkpoints", 3),
    )
    start_epoch = 0
    global_step = 0
    if args.resume_from:
        start_epoch, global_step = ckpt_manager.load(engine, args.resume_from)
        logger.info(f"Resumed from {args.resume_from} at epoch {start_epoch}, step {global_step}")

    # --- Early Stopping (Step 110) ---
    best_val_loss = float("inf")
    patience = training_cfg.get("early_stopping_patience", 5)
    patience_counter = 0
    num_epochs = training_cfg.get("num_epochs", 10)

    # --- Training Loop ---
    logger.info(f"Starting training for {num_epochs} epochs...")
    for epoch in range(start_epoch, num_epochs):
        epoch_start = time.time()

        train_metrics = train_epoch(
            engine, train_loader, criterion,
            global_step, config, args.formality_weight,
        )
        global_step = train_metrics.pop("step")

        val_metrics = validate(engine, val_loader, criterion, args.formality_weight)
        val_loss = val_metrics["val/loss"]

        epoch_time = time.time() - epoch_start

        if is_main_process(local_rank):
            logger.info(
                f"Epoch {epoch + 1}/{num_epochs} ({epoch_time:.1f}s) | "
                f"Train Loss: {train_metrics['train/loss']:.4f} | "
                f"Val Loss: {val_loss:.4f}"
            )

            # Save checkpoint (Step 112)
            ckpt_manager.save(engine, epoch + 1, global_step, val_loss)

            # Early stopping (Step 110)
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                ckpt_manager.save_best(engine, epoch + 1, global_step, val_loss)
                logger.info(f"  ✓ New best val_loss: {best_val_loss:.4f}")
            else:
                patience_counter += 1
                logger.info(
                    f"  ✗ No improvement. Patience: {patience_counter}/{patience}"
                )
                if patience_counter >= patience:
                    logger.info("Early stopping triggered. Training complete.")
                    break

    if is_main_process(local_rank):
        logger.info(f"Training complete. Best val_loss: {best_val_loss:.4f}")
        logger.info(f"Best model saved to: {args.output_dir}/best/")


if __name__ == "__main__":
    main()
