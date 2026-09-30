"""
Phase 4: Theological Keyword Penalty Loss Function
Step 99: Loss function variant penalizing semantic distortion of theological keywords.
Step 100: Training on formal/literal <-> dynamic/functional translation slider scale.

The loss combines:
1. Standard cross-entropy translation loss
2. A theological keyword penalty that amplifies loss for mistranslated sacred terms
3. An alignment regularization term to encourage faithful source-target mapping
"""

from typing import Dict, List, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# Canonical theological keyword token IDs by category
# These will be populated from the actual tokenizer vocabulary at runtime
THEOLOGICAL_KEYWORD_CATEGORIES = {
    "divine_names":     ["YHWH", "Elohim", "Adonai", "Kyrios", "Theos"],
    "covenant_terms":   ["chesed", "berit", "diatheke", "shalom", "pistis"],
    "soteriological":   ["kaphar", "nasa", "soteria", "hilasterion", "dikaioo"],
    "eschatological":   ["sheol", "hades", "gehenna", "olam", "aion"],
    "christological":   ["Messiah", "Christos", "Logos", "Immanuel", "Kyrios"],
    "untranslatable":   ["Urim", "Thummim", "selah", "tetragrammaton", "anathema"],
}


class TheologicalPenaltyLoss(nn.Module):
    """
    Custom loss function for biblical translation training.

    Combines cross-entropy with:
    - Theological keyword penalty (Step 99): amplifies loss when the model
      mistranslates tokens tagged as theologically significant.
    - Alignment regularization (Step 96): encourages cross-attention
      alignment scores to be sharp (concentrated) rather than diffuse.
    - Formality conditioning weight (Step 100): adjusts loss contribution
      based on the target translation register (formal vs. dynamic).

    Args:
        vocab_size: Target vocabulary size
        theological_token_ids: Dict mapping category -> list of token IDs
        keyword_penalty_weight: Multiplier for theological keyword loss (default 3.0)
        alignment_reg_weight: Weight for alignment entropy regularization
        label_smoothing: Label smoothing epsilon for cross-entropy
        ignore_index: Token ID to ignore in loss (padding token)
    """

    def __init__(
        self,
        vocab_size: int,
        theological_token_ids: Optional[Dict[str, List[int]]] = None,
        keyword_penalty_weight: float = 3.0,
        alignment_reg_weight: float = 0.1,
        label_smoothing: float = 0.1,
        ignore_index: int = -100,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.keyword_penalty_weight = keyword_penalty_weight
        self.alignment_reg_weight = alignment_reg_weight
        self.ignore_index = ignore_index

        # Base cross-entropy loss with label smoothing (Step 101 optimization)
        self.ce_loss = nn.CrossEntropyLoss(
            label_smoothing=label_smoothing,
            ignore_index=ignore_index,
            reduction="none",
        )

        # Build theological keyword mask over vocabulary
        self.theological_token_ids = theological_token_ids or {}
        self._build_keyword_mask(vocab_size)

    def _build_keyword_mask(self, vocab_size: int):
        """
        Create a binary mask over the vocabulary where 1.0 = theological keyword.
        This mask is used to amplify loss on mistranslated sacred terms.
        """
        mask = torch.zeros(vocab_size, dtype=torch.float32)
        for category, token_ids in self.theological_token_ids.items():
            for tid in token_ids:
                if 0 <= tid < vocab_size:
                    mask[tid] = 1.0
        self.register_buffer("keyword_mask", mask)

    def _compute_keyword_penalty(
        self,
        logits: torch.Tensor,   # (B, T, V)
        targets: torch.Tensor,  # (B, T)
    ) -> torch.Tensor:
        """
        Compute additional penalty loss for theological keyword tokens.
        When a target token is a theological keyword, its loss is amplified
        by keyword_penalty_weight to discourage semantic distortion.
        """
        B, T, V = logits.size()

        # Identify positions where the target is a theological keyword
        valid_targets = targets.clone()
        valid_targets[targets == self.ignore_index] = 0  # avoid index error
        keyword_positions = self.keyword_mask[valid_targets]  # (B, T) binary
        keyword_positions[targets == self.ignore_index] = 0.0

        if keyword_positions.sum() == 0:
            return torch.tensor(0.0, device=logits.device)

        # Standard CE on keyword positions only
        flat_logits = logits.view(-1, V)
        flat_targets = targets.view(-1)
        per_token_loss = self.ce_loss(flat_logits, flat_targets).view(B, T)

        keyword_loss = (per_token_loss * keyword_positions).sum() / (keyword_positions.sum() + 1e-8)
        return keyword_loss * self.keyword_penalty_weight

    def _compute_alignment_regularization(
        self, alignment_scores: List[torch.Tensor]
    ) -> torch.Tensor:
        """
        Regularize cross-attention alignment scores to be sharp (low entropy).
        Diffuse attention over the source is penalized; peaked attention rewarded.
        This encourages faithful token-level alignment (Step 96).

        alignment_scores: list of (B, Tgt, Src) per decoder layer
        """
        if not alignment_scores:
            return torch.tensor(0.0)

        # Use the last decoder layer's alignment scores
        attn = alignment_scores[-1]  # (B, Tgt, Src)
        attn = attn.clamp(min=1e-9)  # numerical stability

        # Entropy: H = -sum(p * log(p)) over source dimension
        entropy = -(attn * attn.log()).sum(dim=-1)  # (B, Tgt)
        return entropy.mean() * self.alignment_reg_weight

    def forward(
        self,
        logits: torch.Tensor,                          # (B, T, V)
        targets: torch.Tensor,                         # (B, T)
        alignment_scores: Optional[List[torch.Tensor]] = None,
        formality_weight: float = 1.0,                 # Step 100: 0.0=formal, 1.0=dynamic
    ) -> Dict[str, torch.Tensor]:
        """
        Compute the full Theological Penalty Loss.

        Returns a dict with individual loss components for logging:
          - "loss": total training loss (backward target)
          - "ce_loss": base cross-entropy loss
          - "keyword_penalty": theological keyword amplification loss
          - "alignment_reg": alignment entropy regularization
        """
        B, T, V = logits.size()

        # 1. Base cross-entropy loss
        flat_logits = logits.view(-1, V)
        flat_targets = targets.view(-1)
        per_token_ce = self.ce_loss(flat_logits, flat_targets).view(B, T)

        # Mask padding
        valid_mask = (targets != self.ignore_index).float()
        ce = (per_token_ce * valid_mask).sum() / (valid_mask.sum() + 1e-8)

        # 2. Theological keyword penalty (Step 99)
        keyword_penalty = self._compute_keyword_penalty(logits, targets)

        # 3. Alignment regularization (Step 96 quality enforcement)
        align_reg = torch.tensor(0.0, device=logits.device)
        if alignment_scores is not None:
            align_reg = self._compute_alignment_regularization(alignment_scores)

        # 4. Combine — formality_weight modulates keyword strictness
        # At formality_weight=0 (formal/literal), keyword penalty is maximized
        # At formality_weight=1 (dynamic/functional), keyword penalty is softened
        effective_keyword_weight = 1.0 + (1.0 - formality_weight)
        total_loss = ce + (keyword_penalty * effective_keyword_weight) + align_reg

        return {
            "loss": total_loss,
            "ce_loss": ce.detach(),
            "keyword_penalty": keyword_penalty.detach(),
            "alignment_reg": align_reg.detach(),
        }
