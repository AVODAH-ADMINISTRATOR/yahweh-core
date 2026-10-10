from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path

from council_os.domains import KernelDomain
from council_os.ledger import SerializedLedger


def _append_in_process(path: str, worker: int, count: int) -> int:
    ledger = SerializedLedger(path)
    for sequence in range(count):
        ledger.append(KernelDomain.LEDGER, f"PROCESS_{worker}_{sequence}")
    return count


def test_ledger_serializes_500_concurrent_thread_writes(tmp_path: Path):
    path = tmp_path / "threaded-ledger.jsonl"
    ledger = SerializedLedger(path)

    with ThreadPoolExecutor(max_workers=5) as workers:
        list(workers.map(
            lambda sequence: ledger.append(KernelDomain.LEDGER, f"THREAD_{sequence}"),
            range(500),
        ))

    restored = SerializedLedger(path)
    assert len(restored) == 500
    assert restored.verify_chain()


def test_ledger_serializes_writers_across_processes(tmp_path: Path):
    path = str(tmp_path / "process-ledger.jsonl")

    with ProcessPoolExecutor(max_workers=5) as workers:
        assert sum(workers.map(
            _append_in_process,
            [path] * 5,
            range(5),
            [10] * 5,
        )) == 50

    ledger = SerializedLedger(path)
    assert len(ledger) == 50
    assert ledger.verify_chain()
