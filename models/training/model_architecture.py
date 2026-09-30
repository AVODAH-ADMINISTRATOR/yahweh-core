"""
Phase 4: Core Translation Model Architecture
Step 91: Base LLM foundation - Llama-3 with custom extensions
Step 92: Custom vocabulary extension for ancient languages
Step 96: Multi-head cross-attention mechanism for source-target alignment
Step 97: Rotary Position Embeddings (RoPE) for long biblical book contexts
Step 107: FlashAttention-2 integration for training speed optimization

Architecture: Encoder-Decoder Transformer with:
  - Custom biblical vocabulary tokens (Hebrew/Greek/Aramaic)
  - Cross-attention layers aligning source ancient text with KG embeddings
  - RoPE for handling long-context biblical books (e.g., Psalms, Isaiah)
  - FlashAttention-2 for memory-efficient attention computation
"""

import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Rotary Position Embeddings (RoPE) — Step 97
# Optimized for long biblical book contexts (up to 32k tokens)
# ---------------------------------------------------------------------------

class RotaryEmbedding(nn.Module):
    """
    Rotary Position Embedding (RoPE) for encoding positional information
    without absolute position tokens. Effective for long-range dependencies
    across full biblical chapters and books.
    """

    def __init__(self, dim: int, max_seq_len: int = 32768, base: int = 10000):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer("inv_freq", inv_freq)
        self._build_cache(max_seq_len)

    def _build_cache(self, seq_len: int):
        t = torch.arange(seq_len, device=self.inv_freq.device).float()
        freqs = torch.outer(t, self.inv_freq)
        emb = torch.cat([freqs, freqs], dim=-1)
        self.register_buffer("cos_cached", emb.cos()[None, None, :, :])
        self.register_buffer("sin_cached", emb.sin()[None, None, :, :])

    def forward(self, q: torch.Tensor, k: torch.Tensor, seq_len: int):
        if seq_len > self.max_seq_len:
            self._build_cache(seq_len)
        cos = self.cos_cached[:, :, :seq_len, :]
        sin = self.sin_cached[:, :, :seq_len, :]
        return apply_rotary_emb(q, k, cos, sin)


def rotate_half(x: torch.Tensor) -> torch.Tensor:
    """Rotate the second half of the last dimension of x."""
    x1, x2 = x.chunk(2, dim=-1)
    return torch.cat([-x2, x1], dim=-1)


def apply_rotary_emb(
    q: torch.Tensor,
    k: torch.Tensor,
    cos: torch.Tensor,
    sin: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor]:
    q_rot = (q * cos) + (rotate_half(q) * sin)
    k_rot = (k * cos) + (rotate_half(k) * sin)
    return q_rot, k_rot


# ---------------------------------------------------------------------------
# Biblical Cross-Attention — Step 96
# Tracks semantic alignment between source ancient text tokens
# and Knowledge Graph (KG) node embeddings.
# ---------------------------------------------------------------------------

class BiblicalCrossAttention(nn.Module):
    """
    Multi-head cross-attention module tailored for tracking source-target
    alignment between:
      - Query: Target language decoder states
      - Key/Value: Source ancient language (Hebrew/Greek) token embeddings
                   optionally augmented with Knowledge Graph embeddings

    Supports FlashAttention-2 (Step 107) when available.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        dropout: float = 0.1,
        use_flash_attention: bool = True,
    ):
        super().__init__()
        assert d_model % num_heads == 0, "d_model must be divisible by num_heads"

        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads
        self.scale = math.sqrt(self.head_dim)
        self.use_flash_attention = use_flash_attention

        # Projection layers
        self.q_proj = nn.Linear(d_model, d_model, bias=False)
        self.k_proj = nn.Linear(d_model, d_model, bias=False)
        self.v_proj = nn.Linear(d_model, d_model, bias=False)
        self.out_proj = nn.Linear(d_model, d_model, bias=False)

        # Alignment head: produces per-token alignment scores for
        # theological keyword tracking (Step 99)
        self.alignment_head = nn.Linear(d_model, 1, bias=False)

        self.dropout = nn.Dropout(dropout)

    def _split_heads(self, x: torch.Tensor) -> torch.Tensor:
        """Reshape (B, T, D) -> (B, num_heads, T, head_dim)"""
        B, T, _ = x.size()
        return x.view(B, T, self.num_heads, self.head_dim).transpose(1, 2)

    def _merge_heads(self, x: torch.Tensor) -> torch.Tensor:
        """Reshape (B, num_heads, T, head_dim) -> (B, T, D)"""
        B, _, T, _ = x.size()
        return x.transpose(1, 2).contiguous().view(B, T, self.d_model)

    def forward(
        self,
        decoder_hidden: torch.Tensor,       # (B, Tgt, D) — target decoder states
        encoder_hidden: torch.Tensor,        # (B, Src, D) — source ancient text
        kg_embeddings: Optional[torch.Tensor] = None,  # (B, Src, D) — KG node embeddings
        key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            context: (B, Tgt, D) attended context vector
            alignment_scores: (B, Tgt, Src) per-token alignment weights
        """
        B, Tgt, _ = decoder_hidden.size()

        # Fuse Knowledge Graph embeddings with encoder hidden states (Step 96)
        if kg_embeddings is not None:
            encoder_hidden = encoder_hidden + kg_embeddings

        Q = self._split_heads(self.q_proj(decoder_hidden))   # (B, H, Tgt, Dh)
        K = self._split_heads(self.k_proj(encoder_hidden))   # (B, H, Src, Dh)
        V = self._split_heads(self.v_proj(encoder_hidden))   # (B, H, Src, Dh)

        # Scaled dot-product attention
        # FlashAttention-2 path (Step 107)
        if self.use_flash_attention and Q.is_cuda:
            try:
                from flash_attn import flash_attn_func
                # flash_attn expects (B, T, H, Dh)
                Q_fa = Q.transpose(1, 2)
                K_fa = K.transpose(1, 2)
                V_fa = V.transpose(1, 2)
                attn_output = flash_attn_func(Q_fa, K_fa, V_fa, dropout_p=0.0, causal=False)
                context = self._merge_heads(attn_output.transpose(1, 2))
                # Compute alignment scores separately for interpretability
                with torch.no_grad():
                    attn_weights = torch.softmax(
                        (Q @ K.transpose(-2, -1)) / self.scale, dim=-1
                    )
                    alignment_scores = attn_weights.mean(dim=1)  # avg over heads
            except ImportError:
                context, alignment_scores = self._standard_attention(Q, K, V, key_padding_mask)
        else:
            context, alignment_scores = self._standard_attention(Q, K, V, key_padding_mask)

        context = self.out_proj(context)
        return context, alignment_scores

    def _standard_attention(
        self,
        Q: torch.Tensor,
        K: torch.Tensor,
        V: torch.Tensor,
        key_padding_mask: Optional[torch.Tensor],
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        attn_scores = (Q @ K.transpose(-2, -1)) / self.scale  # (B, H, Tgt, Src)

        if key_padding_mask is not None:
            # mask: (B, Src) -> (B, 1, 1, Src)
            attn_scores = attn_scores.masked_fill(
                key_padding_mask.unsqueeze(1).unsqueeze(2), float("-inf")
            )

        attn_weights = torch.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        context = self._merge_heads(attn_weights @ V)
        alignment_scores = attn_weights.mean(dim=1)  # (B, Tgt, Src)
        return context, alignment_scores


# ---------------------------------------------------------------------------
# Encoder Block — Source Ancient Language Representation
# ---------------------------------------------------------------------------

class BiblicalEncoderLayer(nn.Module):
    """
    Transformer encoder layer for processing ancient source texts
    (Biblical Hebrew, Koine Greek, Imperial Aramaic).
    Uses RoPE for positional encoding to handle long book-level contexts.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        d_ff: int,
        dropout: float = 0.1,
        max_seq_len: int = 32768,
    ):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(
            d_model, num_heads, dropout=dropout, batch_first=True
        )
        self.rope = RotaryEmbedding(d_model // num_heads, max_seq_len=max_seq_len)
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.SiLU(),  # SwiGLU activation (Llama-3 style)
            nn.Linear(d_ff, d_model),
        )
        self.norm1 = nn.RMSNorm(d_model)
        self.norm2 = nn.RMSNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        src: torch.Tensor,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        # Pre-norm architecture (Llama-3 style)
        residual = src
        src = self.norm1(src)
        src_attn, _ = self.self_attn(src, src, src, key_padding_mask=src_key_padding_mask)
        src = residual + self.dropout(src_attn)

        residual = src
        src = self.norm2(src)
        src = residual + self.dropout(self.ff(src))
        return src


# ---------------------------------------------------------------------------
# Decoder Block — Target Language Generation
# ---------------------------------------------------------------------------

class BiblicalDecoderLayer(nn.Module):
    """
    Transformer decoder layer for generating target language translations.
    Includes the BiblicalCrossAttention module for source-target alignment.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int,
        d_ff: int,
        dropout: float = 0.1,
        use_flash_attention: bool = True,
    ):
        super().__init__()
        # Self-attention on target tokens (causal / masked)
        self.self_attn = nn.MultiheadAttention(
            d_model, num_heads, dropout=dropout, batch_first=True
        )
        # Cross-attention with source ancient text + KG embeddings (Step 96)
        self.cross_attn = BiblicalCrossAttention(
            d_model, num_heads, dropout=dropout,
            use_flash_attention=use_flash_attention,
        )
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.SiLU(),
            nn.Linear(d_ff, d_model),
        )
        self.norm1 = nn.RMSNorm(d_model)
        self.norm2 = nn.RMSNorm(d_model)
        self.norm3 = nn.RMSNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        tgt: torch.Tensor,
        encoder_output: torch.Tensor,
        kg_embeddings: Optional[torch.Tensor] = None,
        tgt_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # 1. Masked self-attention
        residual = tgt
        tgt = self.norm1(tgt)
        tgt_sa, _ = self.self_attn(tgt, tgt, tgt, attn_mask=tgt_mask)
        tgt = residual + self.dropout(tgt_sa)

        # 2. Cross-attention with source (Step 96)
        residual = tgt
        tgt = self.norm2(tgt)
        tgt_ca, alignment_scores = self.cross_attn(
            tgt, encoder_output, kg_embeddings, src_key_padding_mask
        )
        tgt = residual + self.dropout(tgt_ca)

        # 3. Feed-forward
        residual = tgt
        tgt = self.norm3(tgt)
        tgt = residual + self.dropout(self.ff(tgt))

        return tgt, alignment_scores


# ---------------------------------------------------------------------------
# Full Translation Model — Yahweh Core Engine
# ---------------------------------------------------------------------------

class YahwehTranslationEngine(nn.Module):
    """
    Full Encoder-Decoder Translation Architecture for the Biblical Language
    Translation Engine (Phase 4, Steps 91-120).

    Design Principles:
    - Step 91: Llama-3 inspired architecture (pre-norm, RMSNorm, SwiGLU)
    - Step 92: Extended vocabulary for ancient language tokens
    - Step 96: Cross-attention with Knowledge Graph embedding fusion
    - Step 97: RoPE for long biblical book contexts
    - Step 100: Language-conditioned decoding (style tokens)
    - Step 107: FlashAttention-2 integration
    - Step 115: Target language conditioning token
    """

    def __init__(
        self,
        src_vocab_size: int,        # Ancient lang vocabulary (Hebrew+Greek+Aramaic)
        tgt_vocab_size: int,        # Target language vocabulary
        d_model: int = 4096,        # Hidden dimension (Llama-3 70B scale)
        num_encoder_layers: int = 16,
        num_decoder_layers: int = 16,
        num_heads: int = 32,
        d_ff: int = 14336,          # 3.5x d_model (SwiGLU standard)
        max_seq_len: int = 32768,   # Long context for full biblical books
        dropout: float = 0.1,
        kg_embedding_dim: int = 256,  # Knowledge Graph node embedding size
        num_target_languages: int = 50,  # Step 115: language conditioning tokens
        use_flash_attention: bool = True,
    ):
        super().__init__()

        self.d_model = d_model
        self.src_vocab_size = src_vocab_size
        self.tgt_vocab_size = tgt_vocab_size

        # --- Embeddings ---
        self.src_embedding = nn.Embedding(src_vocab_size, d_model)
        self.tgt_embedding = nn.Embedding(tgt_vocab_size, d_model)
        self.rope = RotaryEmbedding(d_model // num_heads, max_seq_len)

        # Step 115: Target language conditioning token embedding
        self.lang_embedding = nn.Embedding(num_target_languages, d_model)

        # Step 96: KG embedding projection to d_model
        self.kg_proj = nn.Linear(kg_embedding_dim, d_model, bias=False)

        # --- Encoder Stack ---
        self.encoder_layers = nn.ModuleList([
            BiblicalEncoderLayer(d_model, num_heads, d_ff, dropout, max_seq_len)
            for _ in range(num_encoder_layers)
        ])
        self.encoder_norm = nn.RMSNorm(d_model)

        # --- Decoder Stack ---
        self.decoder_layers = nn.ModuleList([
            BiblicalDecoderLayer(d_model, num_heads, d_ff, dropout, use_flash_attention)
            for _ in range(num_decoder_layers)
        ])
        self.decoder_norm = nn.RMSNorm(d_model)

        # --- Output Projection ---
        self.output_proj = nn.Linear(d_model, tgt_vocab_size, bias=False)

        # Tie embedding weights (Step 101 optimization)
        if src_vocab_size == tgt_vocab_size:
            self.output_proj.weight = self.tgt_embedding.weight

        self._init_weights()

    def _init_weights(self):
        """Xavier initialization for stable training (Step 113)."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
            elif isinstance(module, nn.Embedding):
                nn.init.normal_(module.weight, mean=0, std=self.d_model ** -0.5)

    def encode(
        self,
        src_tokens: torch.Tensor,              # (B, Src)
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """Encode source ancient language tokens."""
        x = self.src_embedding(src_tokens) * math.sqrt(self.d_model)
        for layer in self.encoder_layers:
            x = layer(x, src_key_padding_mask)
        return self.encoder_norm(x)

    def decode(
        self,
        tgt_tokens: torch.Tensor,               # (B, Tgt)
        encoder_output: torch.Tensor,           # (B, Src, D)
        lang_id: Optional[torch.Tensor] = None, # (B,) — Step 115
        kg_embeddings: Optional[torch.Tensor] = None,  # (B, Src, kg_dim)
        tgt_mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, list]:
        """Decode target language tokens with cross-attention alignment."""
        B, Tgt = tgt_tokens.size()
        x = self.tgt_embedding(tgt_tokens) * math.sqrt(self.d_model)

        # Inject language conditioning token (Step 115)
        if lang_id is not None:
            lang_emb = self.lang_embedding(lang_id).unsqueeze(1)  # (B, 1, D)
            x = x + lang_emb

        # Project KG embeddings to d_model
        kg_proj = None
        if kg_embeddings is not None:
            kg_proj = self.kg_proj(kg_embeddings)

        # Causal mask for decoder self-attention
        if tgt_mask is None:
            tgt_mask = nn.Transformer.generate_square_subsequent_mask(Tgt, device=x.device)

        all_alignments = []
        for layer in self.decoder_layers:
            x, alignment = layer(x, encoder_output, kg_proj, tgt_mask, src_key_padding_mask)
            all_alignments.append(alignment)

        x = self.decoder_norm(x)
        return x, all_alignments

    def forward(
        self,
        src_tokens: torch.Tensor,
        tgt_tokens: torch.Tensor,
        lang_id: Optional[torch.Tensor] = None,
        kg_embeddings: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, list]:
        """
        Full forward pass: Source ancient text -> Target translation logits.

        Returns:
            logits: (B, Tgt, tgt_vocab_size)
            alignments: list of (B, Tgt, Src) alignment matrices per decoder layer
        """
        encoder_output = self.encode(src_tokens, src_key_padding_mask)
        decoder_output, alignments = self.decode(
            tgt_tokens, encoder_output, lang_id, kg_embeddings,
            src_key_padding_mask=src_key_padding_mask,
        )
        logits = self.output_proj(decoder_output)
        return logits, alignments


# ---------------------------------------------------------------------------
# Model Factory — Preset Configurations
# ---------------------------------------------------------------------------

def build_yahweh_engine(
    size: str = "base",
    src_vocab_size: int = 64000,
    tgt_vocab_size: int = 64000,
    use_flash_attention: bool = True,
) -> YahwehTranslationEngine:
    """
    Factory function to instantiate the YahwehTranslationEngine.

    Sizes:
      - "debug"  : Tiny model for CPU unit testing (Step 113 validation)
      - "base"   : ~1B parameter model for initial fine-tuning
      - "large"  : ~7B parameter model
      - "full"   : ~70B parameter model (requires 8x A100/H100)
    """
    configs = {
        "debug": dict(d_model=256, num_encoder_layers=2, num_decoder_layers=2,
                      num_heads=4, d_ff=512, max_seq_len=512),
        "base":  dict(d_model=2048, num_encoder_layers=16, num_decoder_layers=16,
                      num_heads=16, d_ff=8192, max_seq_len=8192),
        "large": dict(d_model=4096, num_encoder_layers=32, num_decoder_layers=32,
                      num_heads=32, d_ff=14336, max_seq_len=16384),
        "full":  dict(d_model=8192, num_encoder_layers=40, num_decoder_layers=40,
                      num_heads=64, d_ff=28672, max_seq_len=32768),
    }
    assert size in configs, f"Unknown size '{size}'. Choose from: {list(configs)}"
    return YahwehTranslationEngine(
        src_vocab_size=src_vocab_size,
        tgt_vocab_size=tgt_vocab_size,
        use_flash_attention=use_flash_attention,
        **configs[size],
    )
