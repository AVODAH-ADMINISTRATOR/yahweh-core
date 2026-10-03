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


SEAL_EVENT_PREFIX = "LEDGER_ENTRY_SEALED:"
_SEAL_EVENT_RE = re.compile(r"^LEDGER_ENTRY_SEALED:(\d+)$")
_ENTRY_ID_RE = re.compile(r"^\d{6}-[A-Z]{3}-[1-9]-[0-9a-f]{12}$")


def parse_seal_target(event: str) -> Optional[int]:
    """Return the sealed target index for a well-formed seal marker, else None."""
    if not isinstance(event, str):
        return None
    match = _SEAL_EVENT_RE.fullmatch(event)
    if match is None:
        return None
    return int(match.group(1), 10)


def validate_entry_id(entry_id: str) -> str:
    if not isinstance(entry_id, str) or _ENTRY_ID_RE.fullmatch(entry_id) is None:
        raise CharterViolation("invalid ledger entry identifier")
    return entry_id


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
        self._write_lock = threading.RLock()
        if self.storage_path is not None and self.storage_path.exists():
            try:
                for line in self.storage_path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        raw = json.loads(line)
                        entry = LedgerEntry(**raw)
                        validate_entry_id(entry.entry_id)
                        seal_target = parse_seal_target(entry.event)
                        if seal_target is not None and seal_target >= entry.index:
                            raise CharterViolation("invalid sealed ledger marker")
                        self._entries.append(entry)
            except CharterViolation:
                raise
            except (OSError, TypeError, ValueError) as exc:
                raise CharterViolation("invalid JSONL ledger") from exc
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
        with self._write_lock:
            if not isinstance(event, str) or not event.strip():
                raise CharterViolation("ledger event is required")
            seal_target = parse_seal_target(event)
            if event.startswith(SEAL_EVENT_PREFIX) and seal_target is None:
                raise CharterViolation("invalid sealed ledger marker")
            if seal_target is not None:
                if seal_target < 0 or seal_target >= len(self._entries):
                    raise CharterViolation("sealed marker target out of range")
                target = self._entries[seal_target]
                if payload is None:
                    raise CharterViolation("sealed marker requires target identifier")
                sealed_index = payload.get("sealed_index")
                sealed_entry_id = payload.get("sealed_entry_id")
                if sealed_index != seal_target:
                    raise CharterViolation("sealed marker target mismatch")
                validate_entry_id(str(sealed_entry_id) if sealed_entry_id is not None else "")
                if sealed_entry_id != target.entry_id:
                    raise CharterViolation("sealed marker target identifier mismatch")
                sealed = True

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
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                encoded = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
                descriptor = os.open(self.storage_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
                    handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
            self._entries.append(entry)
            return entry

    def seal(self, index: int) -> LedgerEntry:
        with self._write_lock:
            if not isinstance(index, int) or isinstance(index, bool):
                raise CharterViolation("unknown ledger entry")
            if index < 0 or index >= len(self._entries):
                raise CharterViolation("unknown ledger entry")
            if self.is_sealed(index):
                raise CharterViolation("ledger entry already sealed")
            target = self._entries[index]
            validate_entry_id(target.entry_id)
            return self.append(
                KernelDomain(target.domain),
                f"{SEAL_EVENT_PREFIX}{index}",
                {"sealed_index": index, "sealed_entry_id": target.entry_id},
                sealed=True,
            )

    def is_sealed(self, index: int) -> bool:
        if not isinstance(index, int) or isinstance(index, bool):
            return False
        if index < 0 or index >= len(self._entries):
            return False
        if self._entries[index].sealed:
            return True
        for entry in self._entries:
            target = parse_seal_target(entry.event)
            if target is None:
                continue
            if target == index and entry.index > index:
                return True
        return False

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
        with self._write_lock:
            approval.validate()
            if not isinstance(index, int) or isinstance(index, bool):
                raise CharterViolation("compensation requires a sealed source entry")
            if not self.is_sealed(index):
                raise CharterViolation("compensation requires a sealed source entry")
            target = self._entries[index]
            validate_entry_id(target.entry_id)
            return self.append(
                domain,
                event,
                {
                    "compensates": index,
                    "compensates_entry_id": target.entry_id,
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
            try:
                validate_entry_id(entry.entry_id)
            except CharterViolation:
                return False
            seal_target = parse_seal_target(entry.event)
            if entry.event.startswith(SEAL_EVENT_PREFIX) and seal_target is None:
                return False
            if seal_target is not None:
                if seal_target < 0 or seal_target >= entry.index or not entry.sealed:
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
            prev = entry.entry_hash
        return True
