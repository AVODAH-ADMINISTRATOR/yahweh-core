"""
Phase 4: Unit Tests for Model Architecture
Verification Plan: Lightweight CPU-based tests to validate tensor dimensions,
cross-attention alignment shapes, RoPE correctness, and loss computation.

Runs without DeepSpeed or GPU — suitable for CI/CD pipeline validation.

Usage:
  pytest tests/test_model.py -v
"""

import math
import pytest
import torch
import torch.nn as nn

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from model_architecture import (
    YahwehTranslationEngine,
    BiblicalCrossAttention,
    RotaryEmbedding,
    build_yahweh_engine,
    apply_rotary_emb,
)
from loss import TheologicalPenaltyLoss
from dataset import (
    BiblicalVerseAlignment,
    BiblicalParallelDataset,
    TranslationRegister,
)


# ---- Fixtures ----

@pytest.fixture
def debug_model():
    """Instantiate the smallest 'debug' model for fast CPU testing."""
    return build_yahweh_engine(
        size="debug",
        src_vocab_size=1000,
        tgt_vocab_size=1000,
        use_flash_attention=False,  # CPU: no FlashAttention
    )


@pytest.fixture
def cross_attn():
    return BiblicalCrossAttention(
        d_model=256,
        num_heads=4,
        dropout=0.0,
        use_flash_attention=False,
    )


@pytest.fixture
def rope():
    return RotaryEmbedding(dim=64, max_seq_len=512)


# ---- RoPE Tests (Step 97) ----

class TestRotaryEmbedding:
    def test_output_shape(self, rope):
        """RoPE should return q, k tensors with unchanged shape."""
        B, H, T, Dh = 2, 4, 32, 64
        q = torch.randn(B, H, T, Dh)
        k = torch.randn(B, H, T, Dh)
        q_rot, k_rot = rope(q, k, seq_len=T)
        assert q_rot.shape == q.shape, f"Q shape mismatch: {q_rot.shape} != {q.shape}"
        assert k_rot.shape == k.shape, f"K shape mismatch: {k_rot.shape} != {k.shape}"

    def test_values_differ_from_input(self, rope):
        """RoPE should modify the query/key values (not identity)."""
        B, H, T, Dh = 1, 2, 16, 64
        q = torch.ones(B, H, T, Dh)
        k = torch.ones(B, H, T, Dh)
        q_rot, k_rot = rope(q, k, seq_len=T)
        assert not torch.allclose(q, q_rot), "RoPE should rotate Q values"

    def test_different_positions_differ(self, rope):
        """Tokens at different positions should have different rotations."""
        Dh = 64
        q = torch.ones(1, 1, 10, Dh)
        k = torch.ones(1, 1, 10, Dh)
        q_rot, _ = rope(q, k, seq_len=10)
        # Position 0 and position 5 should differ
        assert not torch.allclose(q_rot[0, 0, 0], q_rot[0, 0, 5])

    def test_extended_sequence_length(self, rope):
        """RoPE cache should extend when seq_len exceeds initial max."""
        B, H, T, Dh = 1, 2, 600, 64  # > initial max_seq_len=512
        q = torch.randn(B, H, T, Dh)
        k = torch.randn(B, H, T, Dh)
        q_rot, k_rot = rope(q, k, seq_len=T)
        assert q_rot.shape == (B, H, T, Dh)


# ---- Cross-Attention Tests (Step 96) ----

class TestBiblicalCrossAttention:
    def test_output_shapes(self, cross_attn):
        """Cross-attention should output correct context and alignment shapes."""
        B, Tgt, Src, D = 2, 10, 20, 256
        decoder_hidden = torch.randn(B, Tgt, D)
        encoder_hidden = torch.randn(B, Src, D)

        context, alignment = cross_attn(decoder_hidden, encoder_hidden)

        assert context.shape == (B, Tgt, D), f"Context shape: {context.shape}"
        assert alignment.shape == (B, Tgt, Src), f"Alignment shape: {alignment.shape}"

    def test_alignment_sums_to_one(self, cross_attn):
        """Attention weights over source dimension must sum to 1 (softmax)."""
        B, Tgt, Src, D = 2, 8, 15, 256
        decoder_hidden = torch.randn(B, Tgt, D)
        encoder_hidden = torch.randn(B, Src, D)

        _, alignment = cross_attn(decoder_hidden, encoder_hidden)
        row_sums = alignment.sum(dim=-1)  # (B, Tgt)
        assert torch.allclose(row_sums, torch.ones_like(row_sums), atol=1e-4), \
            f"Alignment rows don't sum to 1. Max deviation: {(row_sums - 1).abs().max().item()}"

    def test_kg_embedding_fusion(self, cross_attn):
        """Cross-attention with KG embeddings should not raise and should change output."""
        B, Tgt, Src, D = 2, 8, 12, 256
        decoder_hidden = torch.randn(B, Tgt, D)
        encoder_hidden = torch.randn(B, Src, D)
        kg_embeddings = torch.randn(B, Src, D)

        context_no_kg, _ = cross_attn(decoder_hidden, encoder_hidden, kg_embeddings=None)
        context_with_kg, _ = cross_attn(decoder_hidden, encoder_hidden, kg_embeddings=kg_embeddings)

        # KG embeddings should change the attended context
        assert not torch.allclose(context_no_kg, context_with_kg), \
            "KG embeddings should modify the cross-attention output"

    def test_padding_mask(self, cross_attn):
        """Padded source positions should receive zero attention weight."""
        B, Tgt, Src, D = 1, 5, 10, 256
        decoder_hidden = torch.randn(B, Tgt, D)
        encoder_hidden = torch.randn(B, Src, D)

        # Mask the last 5 source positions (padding)
        mask = torch.zeros(B, Src, dtype=torch.bool)
        mask[:, 5:] = True  # True = masked (ignore)

        _, alignment = cross_attn(decoder_hidden, encoder_hidden, key_padding_mask=mask)
        masked_attn = alignment[:, :, 5:]  # Should be ~0
        assert masked_attn.abs().max().item() < 1e-4, \
            f"Masked positions received non-zero attention: {masked_attn.abs().max().item()}"


# ---- Full Model Forward Pass Tests (Steps 91, 96, 97) ----

class TestYahwehTranslationEngine:
    def test_forward_output_shapes(self, debug_model):
        """End-to-end forward pass should output correct logit dimensions."""
        B, Src, Tgt = 2, 30, 20
        vocab = 1000
        src = torch.randint(0, vocab, (B, Src))
        tgt = torch.randint(0, vocab, (B, Tgt))

        logits, alignments = debug_model(src, tgt)

        assert logits.shape == (B, Tgt, vocab), f"Logit shape: {logits.shape}"
        assert len(alignments) == debug_model.decoder_layers.__len__(), \
            "Should have one alignment matrix per decoder layer"

    def test_alignment_layers_shape(self, debug_model):
        """Each decoder layer's alignment should be (B, Tgt, Src)."""
        B, Src, Tgt = 2, 25, 15
        src = torch.randint(0, 1000, (B, Src))
        tgt = torch.randint(0, 1000, (B, Tgt))

        _, alignments = debug_model(src, tgt)
        for i, alignment in enumerate(alignments):
            assert alignment.shape == (B, Tgt, Src), \
                f"Layer {i} alignment shape: {alignment.shape}, expected ({B}, {Tgt}, {Src})"

    def test_encoder_output_shape(self, debug_model):
        """Encoder output should match (B, Src, d_model)."""
        B, Src = 3, 40
        src = torch.randint(0, 1000, (B, Src))
        enc_out = debug_model.encode(src)
        assert enc_out.shape == (B, Src, debug_model.d_model)

    def test_lang_id_conditioning(self, debug_model):
        """Language ID conditioning should produce different outputs for different languages."""
        B, Src, Tgt = 1, 20, 10
        src = torch.randint(0, 1000, (B, Src))
        tgt = torch.randint(0, 1000, (B, Tgt))

        lang_en = torch.tensor([0])
        lang_es = torch.tensor([1])

        logits_en, _ = debug_model(src, tgt, lang_id=lang_en)
        logits_es, _ = debug_model(src, tgt, lang_id=lang_es)

        assert not torch.allclose(logits_en, logits_es), \
            "Different language IDs should produce different logits (Step 115)"

    def test_no_nan_in_forward(self, debug_model):
        """Forward pass should not produce NaN values (Step 113 stability)."""
        B, Src, Tgt = 2, 32, 16
        src = torch.randint(0, 1000, (B, Src))
        tgt = torch.randint(0, 1000, (B, Tgt))
        logits, alignments = debug_model(src, tgt)

        assert not torch.isnan(logits).any(), "NaN detected in logits!"
        for i, a in enumerate(alignments):
            assert not torch.isnan(a).any(), f"NaN in alignment layer {i}!"

    def test_weight_initialization_not_zero(self, debug_model):
        """Model weights should be non-zero after initialization (Step 113)."""
        for name, param in debug_model.named_parameters():
            if "weight" in name:
                assert param.abs().sum() > 0, f"Zero weights in: {name}"


# ---- Loss Function Tests (Steps 99, 100) ----

class TestTheologicalPenaltyLoss:
    def test_basic_loss_computation(self):
        B, T, V = 2, 10, 1000
        criterion = TheologicalPenaltyLoss(vocab_size=V)
        logits = torch.randn(B, T, V)
        targets = torch.randint(0, V, (B, T))
        result = criterion(logits, targets)

        assert "loss" in result
        assert result["loss"].item() > 0
        assert not torch.isnan(result["loss"]), "Loss should not be NaN"

    def test_keyword_penalty_amplification(self):
        """Loss should be higher for batches containing theological keywords."""
        B, T, V = 2, 8, 500
        # Token ID 42 is a theological keyword
        keyword_ids = {"sacred": [42]}
        criterion = TheologicalPenaltyLoss(
            vocab_size=V,
            theological_token_ids=keyword_ids,
            keyword_penalty_weight=5.0,
        )
        logits = torch.randn(B, T, V)

        # Targets without keyword
        targets_plain = torch.randint(10, 40, (B, T))
        # Targets with keyword
        targets_keyword = targets_plain.clone()
        targets_keyword[:, 0] = 42

        result_plain = criterion(logits, targets_plain)
        result_keyword = criterion(logits, targets_keyword)

        assert result_keyword["keyword_penalty"].item() > result_plain["keyword_penalty"].item(), \
            "Keyword penalty should be higher when theological keywords are in targets"

    def test_padding_tokens_ignored(self):
        """Loss should ignore padding positions (ignore_index=-100)."""
        B, T, V = 2, 10, 500
        criterion = TheologicalPenaltyLoss(vocab_size=V, ignore_index=-100)
        logits = torch.randn(B, T, V)

        # All-padding targets should yield near-zero loss
        targets_all_pad = torch.full((B, T), -100, dtype=torch.long)
        result = criterion(logits, targets_all_pad)

        assert result["ce_loss"].item() == pytest.approx(0.0, abs=1e-4), \
            "CE loss should be ~0 when all targets are padding"

    def test_formality_weight_modulates_loss(self):
        """Formal translation mode should amplify keyword penalty more."""
        B, T, V = 2, 8, 300
        keyword_ids = {"term": [10, 11, 12]}
        criterion = TheologicalPenaltyLoss(
            vocab_size=V,
            theological_token_ids=keyword_ids,
            keyword_penalty_weight=3.0,
        )
        logits = torch.randn(B, T, V)
        targets = torch.tensor([[10, 11, 12, 5, 6, 7, 8, 9]] * B)

        result_formal = criterion(logits, targets, formality_weight=0.0)   # formal
        result_dynamic = criterion(logits, targets, formality_weight=1.0)  # dynamic

        assert result_formal["loss"].item() >= result_dynamic["loss"].item(), \
            "Formal (literal) mode should impose equal or higher keyword penalty (Step 100)"


# ---- Dataset Tests (Step 89, 95) ----

class TestBiblicalParallelDataset:
    def _make_alignment(self, verse: int = 1) -> BiblicalVerseAlignment:
        return BiblicalVerseAlignment(
            book="GEN", chapter=1, verse=verse,
            source_lang="heb", target_lang="en",
            source_tokens=list(range(10, 30)),
            target_tokens=list(range(50, 65)),
        )

    def test_dataset_length(self):
        alignments = [self._make_alignment(i) for i in range(5)]
        ds = BiblicalParallelDataset(alignments=alignments)
        assert len(ds) == 5

    def test_item_tensor_types(self):
        alignments = [self._make_alignment()]
        ds = BiblicalParallelDataset(alignments=alignments)
        item = ds[0]
        assert item["src_tokens"].dtype == torch.long
        assert item["decoder_input"].dtype == torch.long
        assert item["labels"].dtype == torch.long

    def test_decoder_input_starts_with_bos(self):
        alignments = [self._make_alignment()]
        ds = BiblicalParallelDataset(alignments=alignments)
        item = ds[0]
        assert item["decoder_input"][0].item() == ds.BOS_ID, \
            "Decoder input should start with BOS token"

    def test_labels_end_with_eos(self):
        alignments = [self._make_alignment()]
        ds = BiblicalParallelDataset(alignments=alignments)
        item = ds[0]
        assert item["labels"][-1].item() == ds.EOS_ID, \
            "Labels should end with EOS token"

    def test_collate_fn_pads_correctly(self):
        """Collate function should pad sequences to max length in batch."""
        alignments = [
            BiblicalVerseAlignment(
                book="GEN", chapter=1, verse=i, source_lang="heb", target_lang="en",
                source_tokens=list(range(5 + i * 3)),   # Different source lengths
                target_tokens=list(range(50, 55 + i)),
            )
            for i in range(3)
        ]
        ds = BiblicalParallelDataset(alignments=alignments)
        batch = [ds[i] for i in range(3)]
        collated = BiblicalParallelDataset.collate_fn(batch)

        # All source tensors should have same length (padded to max)
        assert collated["src_tokens"].shape[0] == 3
        assert collated["src_tokens"].ndim == 2
        assert collated["decoder_input"].ndim == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
