"""Append-only SHA-256 lifecycle ledger.

Sealed entries cannot be rewritten. Dual control may only append a
compensating record. AI workers cannot retain value amounts.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX platforms
    fcntl = None  # type: ignore[assignment]

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.stewardship_policy import check_action_policy, sanitize_text


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class LedgerEntry:
    index: int
    entry_id: str
    domain: str
    event: str
    payload_hash: str
    prev_hash: str
    entry_hash: str
    timestamp: str
    sealed: bool = False
    redacted: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DualControlApproval:
    actor_a: str
    actor_b: str
    reason: str

    def validate(self) -> None:
        try:
            self.actor_a = sanitize_text(self.actor_a, field="witness_a", max_length=256)
            self.actor_b = sanitize_text(self.actor_b, field="witness_b", max_length=256)
            self.reason = sanitize_text(self.reason, field="approval_reason")
            check_action_policy("dual_witness_approval", self.reason)
        except CharterViolation as exc:
            raise CharterViolation("NO_SEALED_LEDGER_OVERRIDE_WITHOUT_DUAL_CONTROL") from exc
        if self.actor_a == self.actor_b:
            raise CharterViolation("NO_SEALED_LEDGER_OVERRIDE_WITHOUT_DUAL_CONTROL")


PII_KEYS = frozenset({
    "password", "ssn", "secret", "passphrase", "token", "private_key",
    "api_key", "access_token", "refresh_token", "authorization",
})


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if str(key).lower() in PII_KEYS else _redact_value(nested)
            for key, nested in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_value(item) for item in value]
    return value


def redact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _redact_value(payload)


class LifecycleLedger:
    SEAL_PREFIX = "LEDGER_ENTRY_SEALED:"
    GENESIS_HASH = "0" * 64
    DOMAIN_CODES = {
        "identity": "IDN",
        "ledger": "LDG",
        "linguistic_nlp": "LNG",
        "textual_criticism": "TXT",
        "scout_edge": "EDG",
        "governance": "GOV",
        "treasury": "TRY",
        "sentinel": "SNT",
    }

    @staticmethod
    def numerology_digit(sequence: int, domain_code: str) -> int:
        letter_total = sum((ord(letter) - ord("A")) % 9 + 1 for letter in domain_code)
        return (sequence + letter_total - 1) % 9 + 1

    @classmethod
    def record_id(cls, index: int, domain: str, entry_hash: str) -> str:
        code = cls.DOMAIN_CODES.get(domain)
        if code is None:
            raise CharterViolation(f"unknown ledger domain {domain}")
        sequence = index + 1
        mnemonic_digit = cls.numerology_digit(sequence, code)
        return f"{sequence:06d}-{code}-{mnemonic_digit}-{sha256_hex(entry_hash)[:12]}"

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = Path(storage_path) if storage_path is not None else None
        self._entries: List[LedgerEntry] = []
        self._value_memory: Optional[str] = None
        self._lock = threading.RLock()
        self._load()

    def _load(self) -> None:
        if self.storage_path is None or not self.storage_path.exists():
            return
        entries: List[LedgerEntry] = []
        try:
            for line in self.storage_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entries.append(LedgerEntry(**json.loads(line)))
        except (OSError, TypeError, ValueError) as exc:
            raise CharterViolation("invalid JSONL ledger") from exc
        self._entries = entries
        if not self.verify_chain():
            raise CharterViolation("JSONL ledger integrity verification failed")

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> List[LedgerEntry]:
        return list(self._entries)

    def head_hash(self) -> str:
        if not self._entries:
            return self.GENESIS_HASH
        return self._entries[-1].entry_hash

    def append(
        self,
        domain: KernelDomain,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
        sealed: bool = False,
    ) -> LedgerEntry:
        if event.startswith(self.SEAL_PREFIX):
            raise CharterViolation("seal markers are written only by seal()")
        return self._append(domain, event, payload, sealed)

    def _append(
        self,
        domain: KernelDomain,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
        sealed: bool = False,
    ) -> LedgerEntry:
        with self._lock:
            if self.storage_path is None:
                return self._append_locked(domain, event, payload, sealed)
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path = self.storage_path.with_name(self.storage_path.name + ".lock")
            descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
            try:
                if fcntl is not None:
                    fcntl.flock(descriptor, fcntl.LOCK_EX)
                self._load()
                return self._append_locked(domain, event, payload, sealed)
            finally:
                os.close(descriptor)

    def _append_locked(
        self,
        domain: KernelDomain,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
        sealed: bool = False,
    ) -> LedgerEntry:
        safe = redact_payload(payload or {})
        payload_hash = sha256_hex(json.dumps(safe, sort_keys=True, default=str))
        prev_hash = self.head_hash()
        index = len(self._entries)
        timestamp = _utc_now()
        material = f"{index}:{domain.value}:{event}:{payload_hash}:{prev_hash}:{timestamp}:{sealed}"
        entry_hash = sha256_hex(material)
        entry = LedgerEntry(
            index=index,
            entry_id=self.record_id(index, domain.value, entry_hash),
            domain=domain.value,
            event=event,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=timestamp,
            sealed=sealed,
            redacted=True,
        )
        if self.storage_path is not None:
            encoded = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
            descriptor = os.open(self.storage_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
        self._entries.append(entry)
        return entry

    def seal(self, index: int) -> LedgerEntry:
        if index < 0 or index >= len(self._entries):
            raise CharterViolation("unknown ledger entry")
        if self.is_sealed(index):
            raise CharterViolation("ledger entry already sealed")
        target = self._entries[index]
        return self._append(
            KernelDomain(target.domain),
            f"{self.SEAL_PREFIX}{index}",
            {"sealed_index": index, "sealed_entry_id": target.entry_id},
            sealed=True,
        )

    def _valid_seal_marker(self, entry: LedgerEntry, entries: List[LedgerEntry]) -> Optional[int]:
        """Return the target index if entry is a well-formed seal marker, else None."""
        if not entry.event.startswith(self.SEAL_PREFIX) or not entry.sealed:
            return None
        raw = entry.event[len(self.SEAL_PREFIX):]
        if not raw.isascii() or not raw.isdigit() or str(int(raw)) != raw:
            return None
        target_index = int(raw)
        if target_index >= entry.index or target_index >= len(entries):
            return None
        target = entries[target_index]
        if target.domain != entry.domain:
            return None
        expected = {"sealed_index": target_index, "sealed_entry_id": target.entry_id}
        if entry.payload_hash != sha256_hex(json.dumps(expected, sort_keys=True, default=str)):
            return None
        return target_index

    def is_sealed(self, index: int) -> bool:
        if index < 0 or index >= len(self._entries):
            return False
        return self._entries[index].sealed or any(
            self._valid_seal_marker(entry, self._entries) == index
            for entry in self._entries[index + 1:]
        )

    def rewrite(self, _index: int, _payload: Dict[str, Any]) -> None:
        raise CharterViolation("NO_SEALED_LEDGER_OVERRIDE_WITHOUT_DUAL_CONTROL")

    def compensate_sealed(
        self,
        index: int,
        domain: KernelDomain,
        event: str,
        approval: DualControlApproval,
        payload: Optional[Dict[str, Any]] = None,
    ) -> LedgerEntry:
        approval.validate()
        if isinstance(index, bool) or not isinstance(index, int) or not self.is_sealed(index):
            raise CharterViolation("compensation requires a sealed source entry")
        return self.append(
            domain,
            event,
            {
                "compensates": index,
                "witness_a_hash": sha256_hex(approval.actor_a),
                "witness_b_hash": sha256_hex(approval.actor_b),
                "reason_hash": sha256_hex(approval.reason),
                **(payload or {}),
            },
        )

    def remember_value(self, _amount: Any) -> None:
        raise CharterViolation("NO_AI_VALUE_MEMORY")

    def flush_value_memory(self) -> None:
        self._value_memory = None

    def verify_chain(self) -> bool:
        prev = self.GENESIS_HASH
        for index, entry in enumerate(self._entries):
            if entry.index != index or entry.prev_hash != prev:
                return False
            material = (
                f"{entry.index}:{entry.domain}:{entry.event}:{entry.payload_hash}:"
                f"{entry.prev_hash}:{entry.timestamp}:{entry.sealed}"
            )
            expected_hash = sha256_hex(material)
            if entry.entry_hash != expected_hash:
                return False
            try:
                expected_id = self.record_id(entry.index, entry.domain, expected_hash)
            except CharterViolation:
                return False
            if entry.entry_id != expected_id:
                return False
            if entry.event.startswith(self.SEAL_PREFIX):
                if self._valid_seal_marker(entry, self._entries) is None:
                    return False
            prev = entry.entry_hash
        return True
