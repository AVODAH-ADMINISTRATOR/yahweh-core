import threading

from council_os.ledger import SerializedLedger


def test_concurrent_writes_serialize(tmp_path):
    ledger = SerializedLedger(tmp_path / "ledger.jsonl")

    def work(tid):
        for i in range(100):
            ledger.write({"thread": tid, "seq": i})

    threads = [threading.Thread(target=work, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    records = ledger.read_all()
    assert len(records) == 500
    assert all("thread" in r and "seq" in r for r in records)
