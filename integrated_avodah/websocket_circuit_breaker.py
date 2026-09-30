"""
Integrated Avodah LLC - Phase 3, Step 27 (Python implementation)
WebSocket auto-reconnect with exponential backoff, jitter, circuit breaker, and
persistent file-backed resync queue.

This implementation is intentionally dependency-free and simulates connection
attempts so it can run in constrained environments. Replace the simulated
connect/send logic with a real websocket client (e.g., `websockets` or
`aiohttp`) in production.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List


class WebSocketCircuitBreakerEngineModule:
    def __init__(
        self,
        entity_name: str = "Integrated Avodah LLC",
        monitored_ports: List[int] = None,
        failure_threshold: int = 3,
        cool_down_seconds: int = 30,
        max_backoff_delay_ms: int = 10000,
        queue_filename: str | None = None,
    ) -> None:
        self.entity_name = entity_name
        self.monitored_ports = monitored_ports or [8080, 8081, 8082, 8083, 8084]

        # Circuit breaker parameters
        self.failure_threshold = failure_threshold
        self.cool_down_seconds = cool_down_seconds
        self.max_backoff_delay_ms = max_backoff_delay_ms

        # Per-port state
        self.failure_counts: Dict[int, int] = {p: 0 for p in self.monitored_ports}
        self.last_failure_ts: Dict[int, float] = {p: 0.0 for p in self.monitored_ports}
        self.circuit_state: Dict[int, str] = {p: "CLOSED" for p in self.monitored_ports}

        # Persistent re-sync queue (file-backed). JSON lines format.
        if queue_filename:
            self.queue_path = Path(queue_filename)
        else:
            self.queue_path = Path(__file__).with_name("ws_resync_queue.jsonl")

        # Ensure queue file exists
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_path.exists():
            self.queue_path.write_text("")

    # ------------------------- Persistent Queue -------------------------
    def enqueue_message(self, message: Dict[str, Any]) -> None:
        """Append a message to the persistent queue as a JSON line."""
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "message": message,
        }
        with self.queue_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")

    def _load_queue(self) -> List[Dict[str, Any]]:
        """Load all queued entries from disk."""
        if not self.queue_path.exists():
            return []
        entries: List[Dict[str, Any]] = []
        with self.queue_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except Exception:
                    # Skip malformed lines
                    continue
        return entries

    def _clear_queue(self) -> None:
        """Clear the queue file after successful flush."""
        self.queue_path.write_text("")

    # ------------------------- Circuit Breaker -------------------------
    def _update_circuit_state(self, port: int) -> None:
        failures = self.failure_counts.get(port, 0)
        now_ts = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else float("%.3f" % datetime.datetime.utcnow().timestamp())

        if failures >= self.failure_threshold:
            self.circuit_state[port] = "OPEN"
            self.last_failure_ts[port] = now_ts
        elif failures > 0:
            self.circuit_state[port] = "HALF-OPEN"
        else:
            self.circuit_state[port] = "CLOSED"

    def _circuit_allows_attempt(self, port: int) -> bool:
        state = self.circuit_state.get(port, "CLOSED")
        if state == "OPEN":
            elapsed = asyncio.get_event_loop().time() - self.last_failure_ts.get(port, 0)
            # If cool-down passed, allow a half-open trial
            if elapsed >= self.cool_down_seconds:
                self.circuit_state[port] = "HALF-OPEN"
                return True
            return False
        return True

    # ------------------------- Backoff Strategy -------------------------
    def _compute_backoff_seconds(self, attempt: int) -> float:
        """Exponential backoff with full jitter. attempt starts at 0."""
        base_ms = min(self.max_backoff_delay_ms, (2 ** attempt) * 100)
        # Full jitter: random between 0 and base_ms
        jitter_ms = random.uniform(0, base_ms)
        return jitter_ms / 1000.0

    # ------------------------- Simulated WebSocket Actions -------------------------
    async def _simulate_connect(self, port: int) -> bool:
        """
        Simulated connection logic. In a real implementation replace this
        with an actual websocket connection attempt and handshake.

        For demo/testing this randomly fails based on failure_counts to allow
        exercising the backoff + circuit breaker.
        """
        # Introduce tiny delay to simulate network
        await asyncio.sleep(0.05)

        # Very simple heuristic: if recorded failures are high, more likely to fail
        failures = self.failure_counts.get(port, 0)
        prob_fail = min(0.9, 0.2 + 0.2 * failures)
        success = random.random() > prob_fail
        return success

    async def _simulate_send(self, port: int, payload: Dict[str, Any]) -> bool:
        """Simulated message send. Returns True on success."""
        await asyncio.sleep(0.02)
        # Small chance of transient failure
        success = random.random() > 0.05
        return success

    # ------------------------- Public Runner -------------------------
    async def run_one_port(self, port: int, max_attempts: int = 6) -> Dict[str, Any]:
        """Attempt to connect and flush the queue for a single port using
        exponential backoff, jitter, and circuit breaker logic.

        Returns a manifest-like dict for the attempt.
        """
        attempt = 0
        attempt_ts = datetime.datetime.utcnow().isoformat()

        # If circuit open and cool-down not elapsed, skip attempts
        self._update_circuit_state(port)
        if not self._circuit_allows_attempt(port):
            return {
                "port": port,
                "status": "SKIPPED_CIRCUIT_OPEN",
                "circuitState": self.circuit_state.get(port),
                "timestamp": attempt_ts,
            }

        while attempt < max_attempts:
            backoff = self._compute_backoff_seconds(attempt)
            if attempt > 0:
                # Wait before retrying
                await asyncio.sleep(backoff)

            success = await self._simulate_connect(port)
            if success:
                # Reset failure count and mark healthy
                self.failure_counts[port] = 0
                self._update_circuit_state(port)

                # Flush persistent queue
                queued = self._load_queue()
                sent = 0
                failed = 0
                for entry in queued:
                    ok = await self._simulate_send(port, entry["message"])
                    if ok:
                        sent += 1
                    else:
                        failed += 1

                if sent > 0 and failed == 0:
                    # All flushed successfully
                    self._clear_queue()

                return {
                    "port": port,
                    "status": "CONNECTED_AND_FLUSHED",
                    "sentCount": sent,
                    "failedCount": failed,
                    "circuitState": self.circuit_state.get(port),
                    "attempts": attempt + 1,
                    "timestamp": attempt_ts,
                }
            else:
                # Mark failure and possibly trip circuit
                self.failure_counts[port] = self.failure_counts.get(port, 0) + 1
                self.last_failure_ts[port] = asyncio.get_event_loop().time()
                self._update_circuit_state(port)

                if self.failure_counts[port] >= self.failure_threshold:
                    # Circuit trips to OPEN
                    return {
                        "port": port,
                        "status": "FAILED_CIRCUIT_TRIPPED",
                        "circuitState": self.circuit_state.get(port),
                        "attempts": attempt + 1,
                        "timestamp": attempt_ts,
                    }

            attempt += 1

        # Exhausted attempts
        return {
            "port": port,
            "status": "FAILED_EXHAUSTED_ATTEMPTS",
            "circuitState": self.circuit_state.get(port),
            "attempts": attempt,
            "timestamp": attempt_ts,
        }

    # ------------------------- Manifests & Helpers -------------------------
    def export_circuit_breaker_manifest(self) -> Dict[str, Any]:
        sample_port = self.monitored_ports[0]
        sample_eval = {
            "port": sample_port,
            "failureThreshold": self.failure_threshold,
            "coolDownSeconds": self.cool_down_seconds,
            "maxBackoffMs": self.max_backoff_delay_ms,
            "queueFile": str(self.queue_path),
        }
        manifest = {
            "entity": self.entity_name,
            "monitoredCluster": self.monitored_ports,
            "circuitBreakerRules": sample_eval,
            "complianceStatus": "Phase 3, Step 27 WebSocket Re-Sync & Circuit Breaker Engine Initialized",
        }
        return manifest


# ------------------------- Demo / Quick Verification -------------------------
if __name__ == "__main__":
    async def demo():
        module = WebSocketCircuitBreakerEngineModule(
            monitored_ports=[8082],
            failure_threshold=2,
            cool_down_seconds=5,
            max_backoff_delay_ms=2000,
        )

        # Enqueue a few messages while offline
        for i in range(3):
            module.enqueue_message({"type": "resync", "seq": i + 1, "payload": {"foo": "bar"}})

        print("[PHASE 3, STEP 27 DEMO] Queue path:", module.queue_path)
        print("Initial manifest:")
        print(json.dumps(module.export_circuit_breaker_manifest(), indent=2))

        # Run connection attempts to flush queue
        print("Running connection runner for port 8082 (demo). This will simulate connect/send with backoff.")
        result = await module.run_one_port(8082)
        print("Run result:", json.dumps(result, indent=2))

        # Show remaining queue length
        q = module._load_queue()
        print(f"Remaining queued messages: {len(q)}")

    asyncio.run(demo())
