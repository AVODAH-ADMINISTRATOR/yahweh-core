"""Append-only SHA-256 lifecycle ledger.

Sealed entries cannot be rewritten. Dual control may only append a
compensating record. AI workers cannot retain value amounts.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

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
        self._append_lock = threading.RLock()
        if self.storage_path is not None:
            with self._storage_lock():
                self._reload_from_storage()

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> List[LedgerEntry]:
        return list(self._entries)

    def head_hash(self) -> str:
        if not self._entries:
            return self.GENESIS_HASH
        return self._entries[-1].entry_hash

    @contextmanager
    def _storage_lock(self) -> Iterator[None]:
        if self.storage_path is None:
            yield
            return

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.storage_path.with_name(self.storage_path.name + ".lock")
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"\0")
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
                try:
                    yield
                finally:
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(descriptor, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def _reload_from_storage(self) -> None:
        if self.storage_path is None:
            return
        entries: List[LedgerEntry] = []
        if self.storage_path.exists():
            try:
                for line in self.storage_path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        entries.append(LedgerEntry(**json.loads(line)))
            except (OSError, TypeError, ValueError) as exc:
                raise CharterViolation("invalid JSONL ledger") from exc
        self._entries = entries
        if not self._verify_chain():
            raise CharterViolation("JSONL ledger integrity verification failed")

    def append(
        self,
        domain: KernelDomain,
        event: str,
        payload: Optional[Dict[str, Any]] = None,
        sealed: bool = False,
    ) -> LedgerEntry:
        if event.startswith("LEDGER_ENTRY_SEALED:"):
            raise CharterViolation("sealed ledger markers must be created with seal()")
        with self._append_lock, self._storage_lock():
            self._reload_from_storage()
            return self._append_entry(domain, event, payload, sealed)

    def _append_entry(
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
            encoded = (json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            descriptor = os.open(self.storage_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
            try:
                remaining = memoryview(encoded)
                while remaining:
                    written = os.write(descriptor, remaining)
                    remaining = remaining[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        self._entries.append(entry)
        return entry

    def _valid_seal_marker(self, index: int, target: LedgerEntry, marker: LedgerEntry) -> bool:
        expected_payload_hash = sha256_hex(json.dumps(
            {"sealed_index": index, "sealed_entry_id": target.entry_id},
            sort_keys=True,
            default=str,
        ))
        return (
            marker.index > index
            and marker.domain == target.domain
            and marker.event == f"LEDGER_ENTRY_SEALED:{index}"
            and marker.sealed
            and marker.payload_hash == expected_payload_hash
        )

    def seal(self, index: int) -> LedgerEntry:
        with self._append_lock, self._storage_lock():
            self._reload_from_storage()
            if index < 0 or index >= len(self._entries):
                raise CharterViolation("unknown ledger entry")
            if self._is_sealed(index):
                raise CharterViolation("ledger entry already sealed")
            target = self._entries[index]
            marker = self._append_entry(
                KernelDomain(target.domain),
                f"LEDGER_ENTRY_SEALED:{index}",
                {"sealed_index": index, "sealed_entry_id": target.entry_id},
                sealed=True,
            )
            if not self._valid_seal_marker(index, target, marker):
                raise CharterViolation("sealed ledger marker mismatch")
            return marker

    def _is_sealed(self, index: int) -> bool:
        if index < 0 or index >= len(self._entries):
            return False
        target = self._entries[index]
        return target.sealed or any(
            self._valid_seal_marker(index, target, entry)
            for entry in self._entries
        )

    def is_sealed(self, index: int) -> bool:
        with self._append_lock, self._storage_lock():
            self._reload_from_storage()
            return self._is_sealed(index)

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
        with self._append_lock, self._storage_lock():
            self._reload_from_storage()
            approval.validate()
            if not self._is_sealed(index):
                raise CharterViolation("compensation requires a sealed source entry")
            target = self._entries[index]
            return self._append_entry(
                domain,
                event,
                {
                    **(payload or {}),
                    "compensates": index,
                    "sealed_entry_id": target.entry_id,
                    "witness_a_hash": sha256_hex(approval.actor_a),
                    "witness_b_hash": sha256_hex(approval.actor_b),
                    "reason_hash": sha256_hex(approval.reason),
                },
            )

    def remember_value(self, _amount: Any) -> None:
        raise CharterViolation("NO_AI_VALUE_MEMORY")

    def flush_value_memory(self) -> None:
        self._value_memory = None

    def _verify_chain(self) -> bool:
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
            prev = entry.entry_hash

        for marker in self._entries:
            if not marker.event.startswith("LEDGER_ENTRY_SEALED:"):
                continue
            try:
                target_index = int(marker.event.partition(":")[2])
            except ValueError:
                return False
            if target_index < 0 or target_index >= len(self._entries):
                return False
            if not self._valid_seal_marker(target_index, self._entries[target_index], marker):
                return False
        return True

    def verify_chain(self) -> bool:
        with self._append_lock, self._storage_lock():
            self._reload_from_storage()
            return self._verify_chain()
