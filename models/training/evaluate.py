"""
Phase 4: Translation Quality Evaluation
Step 117: Compute and log BLEU, ROUGE, and COMET scores against validation datasets.
Step 105: Conduct initial validation passes checking for AI translation hallucinations.
Step 118: Quantize a branch of the model to 8-bit and 4-bit (GGUF/AWQ) for edge testing.

Metrics:
  - sacreBLEU (corpus-level BLEU, Step 11)
  - chrF (character n-gram F-score, robust for morphologically rich languages)
  - COMET (neural MT evaluation using reference + source, target COMET > 92.0)
  - ROUGE-L (for long-form text evaluation)
  - Hallucination detector: flags outputs with near-zero BLEU against any reference
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import torch

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Container for a full evaluation run's metrics."""
    bleu: float
    chrf: float
    comet: Optional[float]
    rouge_l: float
    hallucination_rate: float     # Step 105: % of outputs flagged as hallucinations
    theological_accuracy: float   # % of theological keywords correctly translated
    num_samples: int


class TranslationEvaluator:
    """
    Evaluates the YahwehTranslationEngine against standard MT metrics
    and custom theological accuracy checks.

    Metrics target (per 360-step roadmap):
      - COMET alignment score: > 92.0
      - Morphological parsing latency: < 150ms
    """

    # Minimum BLEU below which a translation is flagged as a hallucination
    HALLUCINATION_BLEU_THRESHOLD = 5.0

    # Target COMET score (Step 329 final benchmark)
    COMET_TARGET = 92.0

    def __init__(
        self,
        use_comet: bool = True,
        comet_model: str = "Unbabel/wmt22-comet-da",
        device: str = "cpu",
    ):
        self.device = device
        self.use_comet = use_comet
        self._load_metrics(use_comet, comet_model)

    def _load_metrics(self, use_comet: bool, comet_model: str):
        """Lazy-load evaluation libraries."""
        try:
            import sacrebleu
            self._sacrebleu = sacrebleu
        except ImportError:
            logger.warning("sacrebleu not installed. BLEU/chrF disabled.")
            self._sacrebleu = None

        try:
            from rouge_score import rouge_scorer
            self._rouge = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
        except ImportError:
            logger.warning("rouge_score not installed. ROUGE disabled.")
            self._rouge = None

        self._comet = None
        if use_comet:
            try:
                from comet import download_model, load_from_checkpoint
                model_path = download_model(comet_model)
                self._comet = load_from_checkpoint(model_path)
                logger.info(f"COMET model loaded: {comet_model}")
            except Exception as e:
                logger.warning(f"COMET not available: {e}. Skipping COMET evaluation.")

    @torch.no_grad()
    def generate_translations(
        self,
        model,
        src_tokens: torch.Tensor,          # (B, Src)
        tokenizer,
        max_tgt_len: int = 512,
        src_key_padding_mask: Optional[torch.Tensor] = None,
        lang_id: Optional[torch.Tensor] = None,
        beam_size: int = 4,
    ) -> List[str]:
        """
        Greedy/beam decoding to generate translations for evaluation.
        Uses the model's encoder + autoregressive decoder.
        """
        model.eval()
        B = src_tokens.size(0)
        device = src_tokens.device

        # Encode source
        encoder_output = model.encode(src_tokens, src_key_padding_mask)

        # Initialize decoder input with BOS token
        decoder_input = torch.full((B, 1), fill_value=1, dtype=torch.long, device=device)  # BOS=1
        finished = torch.zeros(B, dtype=torch.bool, device=device)
        generated = [[] for _ in range(B)]

        for step in range(max_tgt_len):
            decoder_output, _ = model.decode(
                decoder_input, encoder_output, lang_id,
                src_key_padding_mask=src_key_padding_mask,
            )
            # Greedy next token
            next_token_logits = decoder_output[:, -1, :]
            next_tokens = model.output_proj(next_token_logits).argmax(dim=-1)  # (B,)

            for i in range(B):
                if not finished[i]:
                    tok = next_tokens[i].item()
                    if tok == 2:  # EOS
                        finished[i] = True
                    else:
                        generated[i].append(tok)

            if finished.all():
                break

            decoder_input = torch.cat(
                [decoder_input, next_tokens.unsqueeze(1)], dim=1
            )

        # Decode token IDs to strings
        return [tokenizer.decode(ids, skip_special_tokens=True) for ids in generated]

    def compute_bleu(
        self, hypotheses: List[str], references: List[str]
    ) -> Tuple[float, float]:
        """Compute corpus BLEU and chrF scores."""
        if self._sacrebleu is None:
            return 0.0, 0.0
        bleu = self._sacrebleu.corpus_bleu(hypotheses, [references])
        chrf = self._sacrebleu.corpus_chrf(hypotheses, [references])
        return round(bleu.score, 2), round(chrf.score, 2)

    def compute_rouge_l(
        self, hypotheses: List[str], references: List[str]
    ) -> float:
        """Compute average ROUGE-L F1 score."""
        if self._rouge is None:
            return 0.0
        scores = [
            self._rouge.score(ref, hyp)["rougeL"].fmeasure
            for hyp, ref in zip(hypotheses, references)
        ]
        return round(sum(scores) / len(scores) * 100, 2) if scores else 0.0

    def compute_comet(
        self,
        hypotheses: List[str],
        references: List[str],
        sources: List[str],
    ) -> Optional[float]:
        """
        Compute COMET score (target: > 92.0 per Step 329 benchmarks).
        Requires source + reference + hypothesis triplets.
        """
        if self._comet is None:
            return None
        try:
            data = [
                {"src": s, "mt": h, "ref": r}
                for s, h, r in zip(sources, hypotheses, references)
            ]
            scores = self._comet.predict(data, batch_size=16, gpus=0)
            # COMET returns scores in [0, 1]; multiply by 100 for readability
            return round(scores.system_score * 100, 2)
        except Exception as e:
            logger.warning(f"COMET scoring failed: {e}")
            return None

    def detect_hallucinations(
        self, hypotheses: List[str], references: List[str]
    ) -> Tuple[float, List[int]]:
        """
        Step 105: Flag translations with near-zero BLEU as potential hallucinations.
        Returns (hallucination_rate, list of flagged indices).
        """
        if self._sacrebleu is None:
            return 0.0, []

        flagged = []
        for i, (hyp, ref) in enumerate(zip(hypotheses, references)):
            try:
                sent_bleu = self._sacrebleu.sentence_bleu(hyp, [ref])
                if sent_bleu.score < self.HALLUCINATION_BLEU_THRESHOLD:
                    flagged.append(i)
                    logger.warning(
                        f"Potential hallucination at index {i}: "
                        f"BLEU={sent_bleu.score:.1f} | output='{hyp[:80]}...'"
                    )
            except Exception:
                pass

        rate = len(flagged) / max(len(hypotheses), 1) * 100
        return round(rate, 2), flagged

    def evaluate(
        self,
        model,
        val_loader,
        tokenizer,
        source_texts: Optional[List[str]] = None,
    ) -> EvaluationResult:
        """
        Full evaluation run on the validation set.
        Returns an EvaluationResult with all MT quality metrics.
        """
        all_hypotheses = []
        all_references = []
        all_sources = source_texts or []

        for batch in val_loader:
            src_tokens = batch["src_tokens"]
            labels = batch["labels"]
            lang_ids = batch.get("lang_ids")
            src_mask = batch.get("src_key_padding_mask")

            hyps = self.generate_translations(
                model, src_tokens, tokenizer,
                lang_id=lang_ids,
                src_key_padding_mask=src_mask,
            )
            refs = [tokenizer.decode(
                [t for t in label.tolist() if t != -100],
                skip_special_tokens=True
            ) for label in labels]

            all_hypotheses.extend(hyps)
            all_references.extend(refs)

        bleu, chrf = self.compute_bleu(all_hypotheses, all_references)
        rouge_l = self.compute_rouge_l(all_hypotheses, all_references)
        comet = None
        if all_sources:
            comet = self.compute_comet(all_hypotheses, all_references, all_sources)
        hallucination_rate, _ = self.detect_hallucinations(all_hypotheses, all_references)

        result = EvaluationResult(
            bleu=bleu,
            chrf=chrf,
            comet=comet,
            rouge_l=rouge_l,
            hallucination_rate=hallucination_rate,
            theological_accuracy=0.0,  # TODO: Phase 7 TGS integration
            num_samples=len(all_hypotheses),
        )

        logger.info(
            f"\n{'='*50}\n"
            f"  Evaluation Results ({result.num_samples} samples)\n"
            f"  BLEU:         {result.bleu:.2f}\n"
            f"  chrF:         {result.chrf:.2f}\n"
            f"  ROUGE-L:      {result.rouge_l:.2f}\n"
            f"  COMET:        {result.comet if result.comet else 'N/A'} "
            f"(target: >{self.COMET_TARGET})\n"
            f"  Hallucination:{result.hallucination_rate:.1f}%\n"
            f"{'='*50}"
        )

        if comet is not None and comet < self.COMET_TARGET:
            logger.warning(
                f"COMET score {comet:.2f} is below target {self.COMET_TARGET}. "
                f"Continue training or adjust hyperparameters."
            )

        return result
