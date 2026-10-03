"""Append-only SHA-256 lifecycle ledger.

Sealed entries cannot be rewritten. Dual control may only append a
compensating record. AI workers cannot retain value amounts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading

try:
    import fcntl
except ImportError:
    fcntl = None
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from council_os.constraints import CharterViolation
from council_os.domains import KernelDomain
from council_os.stewardship_policy import check_action_policy, sanitize_text


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _lock_file(descriptor: int) -> None:
    if fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return
    import msvcrt

    os.lseek(descriptor, 0, os.SEEK_SET)
    msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)


def _unlock_file(descriptor: int) -> None:
    if fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return
    import msvcrt

    os.lseek(descriptor, 0, os.SEEK_SET)
    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)


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
        if self.storage_path is not None and self.storage_path.exists():
            self._entries = self._read_entries()
            if not self.verify_chain():
                raise CharterViolation("JSONL ledger integrity verification failed")

    def _read_entries(self) -> List[LedgerEntry]:
        try:
            entries = []
            for line in self.storage_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    entries.append(LedgerEntry(**json.loads(line)))
            return entries
        except (OSError, TypeError, ValueError) as exc:
            raise CharterViolation("invalid JSONL ledger") from exc

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
        with self._lock:
            descriptor = None
            try:
                if self.storage_path is not None:
                    self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                    descriptor = os.open(self.storage_path, os.O_RDWR | os.O_CREAT, 0o600)
                    _lock_file(descriptor)
                    self._entries = self._read_entries() if os.fstat(descriptor).st_size else []
                    if not self.verify_chain():
                        raise CharterViolation("JSONL ledger integrity verification failed")

                safe = redact_payload(payload or {})
                payload_hash = sha256_hex(json.dumps(safe, sort_keys=True, default=str))
                index = len(self._entries)
                seal_marker = re.fullmatch(r"LEDGER_ENTRY_SEALED:(0|[1-9][0-9]*)", event)
                if event.startswith("LEDGER_ENTRY_SEALED"):
                    if seal_marker is None or not sealed:
                        raise CharterViolation("invalid ledger seal record")
                    target_index = int(seal_marker.group(1))
                    if target_index >= index or self.is_sealed(target_index):
                        raise CharterViolation("invalid ledger seal target")
                    target = self._entries[target_index]
                    expected_payload_hash = sha256_hex(json.dumps(
                        {"sealed_index": target_index, "sealed_entry_id": target.entry_id},
                        sort_keys=True,
                        default=str,
                    ))
                    if domain.value != target.domain or payload_hash != expected_payload_hash:
                        raise CharterViolation("invalid ledger seal target")
                prev_hash = self.head_hash()
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
                if descriptor is not None:
                    encoded = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
                    os.lseek(descriptor, 0, os.SEEK_END)
                    written = 0
                    while written < len(encoded):
                        written += os.write(descriptor, encoded[written:])
                    os.fsync(descriptor)
                self._entries.append(entry)
                return entry
            finally:
                if descriptor is not None:
                    _unlock_file(descriptor)
                    os.close(descriptor)

    def seal(self, index: int) -> LedgerEntry:
        if index < 0 or index >= len(self._entries):
            raise CharterViolation("unknown ledger entry")
        if self.is_sealed(index):
            raise CharterViolation("ledger entry already sealed")
        target = self._entries[index]
        return self.append(
            KernelDomain(target.domain),
            f"LEDGER_ENTRY_SEALED:{index}",
            {"sealed_index": index, "sealed_entry_id": target.entry_id},
            sealed=True,
        )

    def is_sealed(self, index: int) -> bool:
        if index < 0 or index >= len(self._entries):
            return False
        return self._entries[index].sealed or any(
            entry.event == f"LEDGER_ENTRY_SEALED:{index}" for entry in self._entries
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
        if not self.is_sealed(index):
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
        sealed_targets = set()
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
            seal_marker = re.fullmatch(r"LEDGER_ENTRY_SEALED:(0|[1-9][0-9]*)", entry.event)
            if entry.event.startswith("LEDGER_ENTRY_SEALED"):
                if seal_marker is None or not entry.sealed:
                    return False
                target_index = int(seal_marker.group(1))
                if target_index >= index or target_index in sealed_targets:
                    return False
                target = self._entries[target_index]
                if target.sealed:
                    return False
                expected_payload_hash = sha256_hex(json.dumps(
                    {"sealed_index": target_index, "sealed_entry_id": target.entry_id},
                    sort_keys=True,
                    default=str,
                ))
                if entry.domain != target.domain or entry.payload_hash != expected_payload_hash:
                    return False
                sealed_targets.add(target_index)
            prev = entry.entry_hash
        return True
