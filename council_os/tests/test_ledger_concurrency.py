import threading

from council_os.ledger import SerializedLedger


def test_concurrent_writes_no_corruption(tmp_path):
    ledger = SerializedLedger(str(tmp_path / "ledger.jsonl"))

    def work(t):
        for i in range(100):
            ledger.write({"thread": t, "seq": i, "data": f"record_{t}_{i}"})

    threads = [threading.Thread(target=work, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    records = ledger.read_all()
    assert len(records) == 500 == ledger.count()
    for r in records:
        assert r["data"] == f"record_{r['thread']}_{r['seq']}"


def test_atomic_large_write(tmp_path):
    ledger = SerializedLedger(str(tmp_path / "sub" / "l.jsonl"))
    big = {"data": "x" * 10000}
    ledger.write(big)
    assert ledger.read_all() == [big]
