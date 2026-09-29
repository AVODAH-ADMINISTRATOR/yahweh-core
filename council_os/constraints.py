"""Immutable Council OS charter constraints.

These rules are bound at compile/build time. Runtime, operators, and AI
workers cannot waive, reinterpret, or outgrow them. Personalized will is
out of scope.
"""

from __future__ import annotations

from typing import FrozenSet

CONSTRAINT_LOCK_VERSION = "1.0.0"

IMMUTABLE_CONSTRAINTS: FrozenSet[str] = frozenset(
    {
        "NO_PERSONALIZED_WILL",
        "NO_CHARTER_WAIVER",
        "NO_CHARTER_REINTERPRETATION",
        "NO_SELF_MODIFYING_PRODUCTION",
        "NO_HIDDEN_REWARD_LOOPS",
        "NO_MISSION_REWRITE_ENDPOINT",
        "NO_AI_COMMIT_AUTHORITATIVE_TEXT",
        "NO_AI_COMMIT_FUNDS",
        "NO_AI_COMMIT_POLICY",
        "NO_SEALED_LEDGER_OVERRIDE_WITHOUT_DUAL_CONTROL",
        "NO_AI_VALUE_MEMORY",
        "HITL_REQUIRED_FOR_AUTHORITATIVE_COMMIT",
        "ZERO_TRUST_ISOLATION",
        "KILL_SWITCH_REQUIRED",
        "HOST_HARDWARE_DECOUPLED",
    }
)

FORBIDDEN_BIND_PATHS = frozenset(
    {
        "/api/v1/set_mission",
        "/api/v1/waive_charter",
        "/api/v1/enable_personalized_will",
        "/api/v1/manual_fiat_override",
        "/api/v1/treasury_bypass_consensus",
        "/api/v1/force_unlock_chrono_capsule",
    }
)


class CharterViolation(Exception):
    """Raised when an action would violate the immutable charter."""


class CharterLock:
    def __init__(self) -> None:
        self._constraints = frozenset(IMMUTABLE_CONSTRAINTS)
        self._version = CONSTRAINT_LOCK_VERSION

    @property
    def constraints(self) -> FrozenSet[str]:
        return self._constraints

    @property
    def version(self) -> str:
        return self._version

    def assert_intact(self, expected: FrozenSet[str] | None = None) -> None:
        expected = expected if expected is not None else IMMUTABLE_CONSTRAINTS
        if self._constraints != expected:
            raise CharterViolation("charter constraints were altered")
        if self._version != CONSTRAINT_LOCK_VERSION:
            raise CharterViolation("charter lock version drift")

    def contains(self, name: str) -> bool:
        return name in self._constraints

    def waive(self, _name: str) -> None:
        raise CharterViolation("NO_CHARTER_WAIVER")

    def reinterpret(self, _name: str) -> None:
        raise CharterViolation("NO_CHARTER_REINTERPRETATION")

    def enable_personalized_will(self) -> None:
        raise CharterViolation("NO_PERSONALIZED_WILL")

    def set_own_mission(self, _mission: str) -> None:
        raise CharterViolation("NO_MISSION_REWRITE_ENDPOINT")

    def outgrow(self) -> None:
        raise CharterViolation("NO_CHARTER_WAIVER")

    def bind_endpoint(self, path: str) -> None:
        if path in FORBIDDEN_BIND_PATHS:
            raise CharterViolation("NO_MISSION_REWRITE_ENDPOINT")
