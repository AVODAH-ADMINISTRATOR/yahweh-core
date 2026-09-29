"""Unabridged Ethiopian Orthodox Tewahedo corpus catalog.

Identifiers and completeness only — no copyrighted scripture text.
Cross-translation is a measured proposal under HITL. The kernel does
not author divine scripture or replace relationship with God.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from council_os.constraints import CharterViolation
from council_os.domains import CHARTER_CITATIONS, KernelDomain, TRANSLATION_GPU_PURPOSE
from council_os.hitl import Proposal, ScholarSignoff
from council_os.kernel import CouncilOSKernel
from council_os.ledger import LifecycleLedger

CORPUS_CITATION = "docs/ethiopian_orthodox_corpus.md"

TRADITION = "ethiopian_orthodox_tewahedo"
LANGUAGES: Tuple[str, ...] = ("gez", "amh", "en")

# Traditional book identifiers (names only). Not scripture text.
NARROW_OT: Tuple[str, ...] = (
    "genesis",
    "exodus",
    "leviticus",
    "numbers",
    "deuteronomy",
    "joshua",
    "judges",
    "ruth",
    "1_samuel",
    "2_samuel",
    "1_kings",
    "2_kings",
    "1_chronicles",
    "2_chronicles",
    "ezra",
    "nehemiah",
    "esther",
    "job",
    "psalms",
    "proverbs",
    "ecclesiastes",
    "song_of_songs",
    "isaiah",
    "jeremiah",
    "lamentations",
    "ezekiel",
    "daniel",
    "hosea",
    "joel",
    "amos",
    "obadiah",
    "jonah",
    "micah",
    "nahum",
    "habakkuk",
    "zephaniah",
    "haggai",
    "zechariah",
    "malachi",
)

BROADER_OT: Tuple[str, ...] = (
    "jubilees",
    "enoch",
    "1_meqabyan",
    "2_meqabyan",
    "3_meqabyan",
    "joseph_ben_gurion",
    "tobit",
    "judith",
    "wisdom_of_solomon",
    "sirach",
)

NARROW_NT: Tuple[str, ...] = (
    "matthew",
    "mark",
    "luke",
    "john",
    "acts",
    "romans",
    "1_corinthians",
    "2_corinthians",
    "galatians",
    "ephesians",
    "philippians",
    "colossians",
    "1_thessalonians",
    "2_thessalonians",
    "1_timothy",
    "2_timothy",
    "titus",
    "philemon",
    "hebrews",
    "james",
    "1_peter",
    "2_peter",
    "1_john",
    "2_john",
    "3_john",
    "jude",
    "revelation",
)

BROADER_NT: Tuple[str, ...] = (
    "sinodos",
    "clement",
    "didascalia",
    "book_of_the_covenant",
    "ethiopic_clement",
)

UNABRIDGED_BOOKS: FrozenSet[str] = frozenset(
    NARROW_OT + BROADER_OT + NARROW_NT + BROADER_NT
)

CANON_BOOK_COUNT = 81

FORBIDDEN_ABRIDGEMENT = frozenset(
    {
        "drop_broader_canon",
        "abridge_enoch",
        "omit_meqabyan",
        "replace_with_66_only",
        "warp_translation",
        "omit_detail",
        "reduce_book_count",
    }
)


@dataclass(frozen=True)
class CorpusBook:
    book_id: str
    testament: str
    broader: bool

    def to_dict(self) -> Dict[str, str]:
        return {
            "book_id": self.book_id,
            "testament": self.testament,
            "broader": "true" if self.broader else "false",
        }


def _catalog() -> Tuple[CorpusBook, ...]:
    books: List[CorpusBook] = []
    for book_id in NARROW_OT:
        books.append(CorpusBook(book_id, "ot", False))
    for book_id in BROADER_OT:
        books.append(CorpusBook(book_id, "ot", True))
    for book_id in NARROW_NT:
        books.append(CorpusBook(book_id, "nt", False))
    for book_id in BROADER_NT:
        books.append(CorpusBook(book_id, "nt", True))
    return tuple(books)


CATALOG: Tuple[CorpusBook, ...] = _catalog()


class EthiopicCorpus:
    """Precision catalog and measured cross-translation proposals."""

    def __init__(self, kernel: CouncilOSKernel) -> None:
        self.kernel = kernel
        self.ledger: LifecycleLedger = kernel.ledger
        self._present: FrozenSet[str] = UNABRIDGED_BOOKS
        self.alignments: List[Dict[str, Any]] = []

    def snapshot(self) -> Dict[str, Any]:
        return {
            "tradition": TRADITION,
            "unabridged": True,
            "warped": False,
            "languages": list(LANGUAGES),
            "book_count": CANON_BOOK_COUNT,
            "complete": self.complete(),
            "kernel_authors_scripture": False,
            "kernel_is_the_word": False,
            "relationship_with_god": "facilitated_not_replaced",
            "citations": list(CHARTER_CITATIONS) + [CORPUS_CITATION],
            "octa_core": [domain.value for domain in KernelDomain],
            "android_hybrid": True,
            "host_decoupled": True,
        }

    def complete(self) -> bool:
        return self._present == UNABRIDGED_BOOKS and len(self._present) == CANON_BOOK_COUNT

    def assert_complete(self) -> None:
        if not self.complete() or len(UNABRIDGED_BOOKS) != CANON_BOOK_COUNT:
            raise CharterViolation("ethiopic corpus must remain unabridged")

    def refuse_warp(self, action: str) -> None:
        raise CharterViolation("ethiopic corpus must remain unabridged")

    def abridge(self, book_id: str) -> None:
        raise CharterViolation("ethiopic corpus must remain unabridged")

    def refuse_abridgement(self, action: str) -> None:
        if action in FORBIDDEN_ABRIDGEMENT or action:
            raise CharterViolation("ethiopic corpus must remain unabridged")

    def books(self) -> List[Dict[str, str]]:
        return [book.to_dict() for book in CATALOG]

    def analyze(self, book_id: str) -> Dict[str, Any]:
        if book_id not in UNABRIDGED_BOOKS:
            raise CharterViolation(f"unknown corpus book {book_id}")
        self.assert_complete()
        self.ledger.append(
            KernelDomain.TEXTUAL_CRITICISM,
            "ETHIOPIC_ANALYZE",
            {"book_id": book_id, "text_included": False},
        )
        return {
            "book_id": book_id,
            "method": "scientific_catalog",
            "confidence": 1.0,
            "scripture_text": None,
            "broader": book_id in BROADER_OT or book_id in BROADER_NT,
        }

    def propose_cross_translation(
        self,
        book_id: str,
        source_lang: str,
        target_lang: str,
        confidence: float,
    ) -> Proposal:
        if source_lang not in LANGUAGES or target_lang not in LANGUAGES:
            raise CharterViolation("unsupported corpus language")
        if book_id not in UNABRIDGED_BOOKS:
            raise CharterViolation(f"unknown corpus book {book_id}")
        self.assert_complete()
        proposal = self.kernel.propose(
            Proposal(
                domain=KernelDomain.LINGUISTIC_NLP,
                kind="translation",
                payload={
                    "book_id": book_id,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "tradition": TRADITION,
                    "scripture_text": None,
                },
                confidence=confidence,
            )
        )
        self.alignments.append(
            {
                "proposal_id": proposal.proposal_id,
                "book_id": book_id,
                "source_lang": source_lang,
                "target_lang": target_lang,
            }
        )
        return proposal

    def commit_translation(self, proposal_id: str, signoff: Optional[ScholarSignoff]) -> Proposal:
        return self.kernel.commit(proposal_id, signoff)

    def request_training_gpu(self) -> None:
        self.kernel.request_gpu(KernelDomain.LINGUISTIC_NLP, TRANSLATION_GPU_PURPOSE)

    def precision_map(self) -> Dict[str, str]:
        return {domain.value: f"core-{index + 1}" for index, domain in enumerate(KernelDomain)}
