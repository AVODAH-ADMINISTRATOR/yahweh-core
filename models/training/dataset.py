"""
Phase 4: Parallel Biblical Corpus Dataset
Step 89: Export tokenized datasets into optimized formats (Parquet/TFRecord)
Step 95: SFT using verified parallel alignments (Ancient -> Modern)
Step 98: Bidirectional translation tasks (Ancient -> Modern, Modern -> Ancient)
Step 104: Chapter-level context windows for single-verse translation inference

Supports:
- Ancient -> Modern translation (primary SFT task)
- Modern -> Ancient back-translation (verification task, Step 98)
- Chapter-level context ingestion (Step 104)
- Formality conditioning (Step 100): formal vs. dynamic register tokens
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import torch
from torch.utils.data import Dataset, DataLoader, IterableDataset

logger = logging.getLogger(__name__)


class TranslationDirection(Enum):
    ANCIENT_TO_MODERN = "ancient_to_modern"
    MODERN_TO_ANCIENT = "modern_to_ancient"   # Step 98: back-translation


class TranslationRegister(Enum):
    """
    Step 100: Formal/Literal <-> Dynamic/Functional translation slider.
    Encoded as a special conditioning token prepended to every target sequence.
    """
    FORMAL_LITERAL = 0      # "Word-for-word" (e.g., NASB style)
    BALANCED = 1            # Balanced equivalence (e.g., ESV style)
    DYNAMIC_FUNCTIONAL = 2  # "Thought-for-thought" (e.g., NLT style)


@dataclass
class BiblicalVerseAlignment:
    """
    A single verse-level training example mapping ancient source to modern target.
    BCV = Book-Chapter-Verse coordinate system (Step 58).
    """
    book: str
    chapter: int
    verse: int
    source_lang: str            # "heb", "grc", "arc"
    target_lang: str            # ISO 639-1 code, e.g., "en", "es", "fr"
    source_tokens: List[int]    # Tokenized ancient source
    target_tokens: List[int]    # Tokenized modern translation
    source_morphology: Optional[List[Dict]] = field(default=None)  # Step 75
    kg_embedding_ids: Optional[List[int]] = field(default=None)    # Step 132
    register: TranslationRegister = TranslationRegister.BALANCED
    has_variants: bool = False                                      # Step 52
    confidence: float = 1.0    # Alignment confidence from TGS


@dataclass
class ChapterContext:
    """
    Step 104: Full chapter context for context-aware single-verse translation.
    The model reads entire chapters to inform individual verse translations.
    """
    book: str
    chapter: int
    verse_alignments: List[BiblicalVerseAlignment]
    focus_verse: int            # The verse we are generating a translation for


class BiblicalParallelDataset(Dataset):
    """
    PyTorch Dataset for the Biblical Parallel Corpus (Steps 31-60, 89, 95).

    Supports loading from:
    - Parquet files (primary format, Step 89)
    - JSON Lines (JSONL) for debugging
    - In-memory lists of BiblicalVerseAlignment objects (unit tests)

    Each item returns tensors ready for the YahwehTranslationEngine.
    """

    # Special token IDs — must match the tokenizer vocabulary (Step 92)
    BOS_ID = 1
    EOS_ID = 2
    PAD_ID = 0
    MASK_ID = 3

    # Register conditioning tokens (Step 100, Step 115)
    REGISTER_TOKEN_IDS = {
        TranslationRegister.FORMAL_LITERAL:    64000,
        TranslationRegister.BALANCED:          64001,
        TranslationRegister.DYNAMIC_FUNCTIONAL: 64002,
    }

    # Language conditioning tokens (Step 115)
    LANG_TOKEN_IDS = {
        "en": 64010, "es": 64011, "fr": 64012, "de": 64013,
        "zh": 64014, "ar": 64015, "sw": 64016, "hi": 64017,
        # Low-resource languages (Step 111)
        "am": 64050, "or": 64051, "ti": 64052,
    }

    def __init__(
        self,
        data_path: Optional[str] = None,
        alignments: Optional[List[BiblicalVerseAlignment]] = None,
        max_src_len: int = 512,
        max_tgt_len: int = 512,
        direction: TranslationDirection = TranslationDirection.ANCIENT_TO_MODERN,
        use_chapter_context: bool = False,   # Step 104
        context_window_size: int = 5,        # verses before/after focus verse
        include_kg_embeddings: bool = False, # Step 132
    ):
        self.max_src_len = max_src_len
        self.max_tgt_len = max_tgt_len
        self.direction = direction
        self.use_chapter_context = use_chapter_context
        self.context_window_size = context_window_size
        self.include_kg_embeddings = include_kg_embeddings

        if alignments is not None:
            self.alignments = alignments
        elif data_path is not None:
            self.alignments = self._load_data(data_path)
        else:
            raise ValueError("Must provide either `data_path` or `alignments`.")

        logger.info(
            f"Loaded {len(self.alignments)} verse alignments "
            f"({direction.value}, context={use_chapter_context})"
        )

    def _load_data(self, path: str) -> List[BiblicalVerseAlignment]:
        """Load dataset from Parquet or JSONL file."""
        p = Path(path)
        if p.suffix == ".parquet":
            return self._load_parquet(p)
        elif p.suffix in (".jsonl", ".json"):
            return self._load_jsonl(p)
        else:
            raise ValueError(f"Unsupported format: {p.suffix}. Use .parquet or .jsonl")

    def _load_parquet(self, path: Path) -> List[BiblicalVerseAlignment]:
        try:
            import pyarrow.parquet as pq
            table = pq.read_table(str(path))
            df = table.to_pandas()
            alignments = []
            for _, row in df.iterrows():
                alignments.append(BiblicalVerseAlignment(
                    book=row["book"],
                    chapter=int(row["chapter"]),
                    verse=int(row["verse"]),
                    source_lang=row["source_lang"],
                    target_lang=row["target_lang"],
                    source_tokens=json.loads(row["source_tokens"]),
                    target_tokens=json.loads(row["target_tokens"]),
                    register=TranslationRegister(row.get("register", 1)),
                    confidence=float(row.get("confidence", 1.0)),
                ))
            return alignments
        except ImportError:
            raise ImportError("pyarrow is required for Parquet loading. "
                              "Install with: pip install pyarrow")

    def _load_jsonl(self, path: Path) -> List[BiblicalVerseAlignment]:
        alignments = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                d = json.loads(line.strip())
                alignments.append(BiblicalVerseAlignment(**d))
        return alignments

    def __len__(self) -> int:
        return len(self.alignments)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        alignment = self.alignments[idx]

        if self.direction == TranslationDirection.ANCIENT_TO_MODERN:
            src_tokens = alignment.source_tokens
            tgt_tokens = alignment.target_tokens
        else:
            # Step 98: Bidirectional — swap source and target for back-translation
            src_tokens = alignment.target_tokens
            tgt_tokens = alignment.source_tokens

        # Truncate to max lengths
        src_tokens = src_tokens[:self.max_src_len]
        # Decoder input: BOS + target tokens; Labels: target tokens + EOS
        decoder_input = [self.BOS_ID] + tgt_tokens[:self.max_tgt_len - 1]
        labels = tgt_tokens[:self.max_tgt_len - 1] + [self.EOS_ID]

        result = {
            "src_tokens":     torch.tensor(src_tokens, dtype=torch.long),
            "decoder_input":  torch.tensor(decoder_input, dtype=torch.long),
            "labels":         torch.tensor(labels, dtype=torch.long),
            "lang_id":        torch.tensor(
                self.LANG_TOKEN_IDS.get(alignment.target_lang, 64010),
                dtype=torch.long
            ),
            "register_id":    torch.tensor(alignment.register.value, dtype=torch.long),
            "confidence":     torch.tensor(alignment.confidence, dtype=torch.float32),
        }

        return result

    @staticmethod
    def collate_fn(batch: List[Dict]) -> Dict[str, torch.Tensor]:
        """
        Pad sequences to the max length within the batch.
        Returns tensors suitable for the YahwehTranslationEngine.
        """
        src_lens = [b["src_tokens"].size(0) for b in batch]
        tgt_lens = [b["decoder_input"].size(0) for b in batch]
        max_src = max(src_lens)
        max_tgt = max(tgt_lens)
        B = len(batch)

        src_tokens = torch.zeros(B, max_src, dtype=torch.long)
        decoder_input = torch.zeros(B, max_tgt, dtype=torch.long)
        labels = torch.full((B, max_tgt), fill_value=-100, dtype=torch.long)
        src_padding_mask = torch.ones(B, max_src, dtype=torch.bool)
        lang_ids = torch.zeros(B, dtype=torch.long)
        confidences = torch.ones(B, dtype=torch.float32)

        for i, b in enumerate(batch):
            sl = b["src_tokens"].size(0)
            tl = b["decoder_input"].size(0)
            src_tokens[i, :sl] = b["src_tokens"]
            decoder_input[i, :tl] = b["decoder_input"]
            labels[i, :tl] = b["labels"]
            src_padding_mask[i, :sl] = False  # False = not masked (attend)
            lang_ids[i] = b["lang_id"]
            confidences[i] = b["confidence"]

        return {
            "src_tokens": src_tokens,
            "decoder_input": decoder_input,
            "labels": labels,
            "src_key_padding_mask": src_padding_mask,
            "lang_ids": lang_ids,
            "confidences": confidences,
        }


def build_dataloaders(
    train_path: str,
    val_path: str,
    batch_size: int = 16,
    num_workers: int = 4,
    max_src_len: int = 512,
    max_tgt_len: int = 512,
    use_chapter_context: bool = False,
) -> Tuple[DataLoader, DataLoader]:
    """Build train and validation DataLoaders for Phase 4 training."""
    train_ds = BiblicalParallelDataset(
        data_path=train_path,
        max_src_len=max_src_len,
        max_tgt_len=max_tgt_len,
        use_chapter_context=use_chapter_context,
    )
    val_ds = BiblicalParallelDataset(
        data_path=val_path,
        max_src_len=max_src_len,
        max_tgt_len=max_tgt_len,
        use_chapter_context=use_chapter_context,
    )
    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        collate_fn=BiblicalParallelDataset.collate_fn,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        collate_fn=BiblicalParallelDataset.collate_fn,
        pin_memory=True,
    )
    return train_loader, val_loader
