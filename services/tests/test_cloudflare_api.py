import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]
API_DIR = ROOT / "services" / "api"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from cloudflare_ai import CloudflareAIError, CloudflareWorkersAI, DEFAULT_MODEL, OFFICIAL_DOCS  # noqa: E402
from cloudflare_edge import (  # noqa: E402
    EDGE_HOP_VALUE,
    forbid_direct_origin,
    parse_edge_headers,
    payload_sha256,
    refuse_secret_action,
)
from council_os.constraints import CharterViolation  # noqa: E402

ACCOUNT_ID = "a" * 32
API_TOKEN = "test-token-not-for-live-use"


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_payload_sha256_is_stable():
    assert payload_sha256("ok") == payload_sha256(b"ok")
    assert len(payload_sha256("ok")) == 64


def test_strict_origin_forbids_direct_access():
    edge = parse_edge_headers({})
    assert forbid_direct_origin("/api/status", edge, mode="strict") is True
    assert forbid_direct_origin("/health", edge, mode="strict") is False
    via = parse_edge_headers({"CF-Ray": "abc123", "CF-Connecting-IP": "203.0.113.10"})
    assert via["via_edge"] is True
    assert via["has_connecting_ip"] is True
    assert via["ray"] == "abc123"
    assert "203.0.113.10" not in json.dumps(via)
    assert forbid_direct_origin("/api/status", via, mode="strict") is False
    hop = parse_edge_headers({"X-Avodah-Edge": EDGE_HOP_VALUE})
    assert forbid_direct_origin("/api/status", hop, mode="strict") is False


def test_workers_ai_posts_documented_translation_shape():
    session = MagicMock()
    session.post.return_value = FakeResponse({"result": {"translated_text": "bonjour"}})
    client = CloudflareWorkersAI(account_id=ACCOUNT_ID, api_token=API_TOKEN, session=session)
    output = client.translate("hello", "english", "french")
    assert output["result"]["translated_text"] == "bonjour"
    url, kwargs = session.post.call_args
    assert url[0] == f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{DEFAULT_MODEL}"
    assert kwargs["headers"]["Authorization"] == "Bearer " + API_TOKEN
    assert kwargs["json"] == {
        "text": "hello",
        "source_lang": "english",
        "target_lang": "french",
    }
    assert kwargs["timeout"] == 30
    snap = client.snapshot()
    dumped = json.dumps(snap)
    assert API_TOKEN not in dumped
    assert ACCOUNT_ID not in dumped
    assert snap["stores_secrets"] is False
    assert snap["configured"] is True
    assert snap["docs"] == OFFICIAL_DOCS
    assert API_TOKEN not in repr(client)


def test_workers_ai_refuses_unconfigured_and_unknown_model():
    client = CloudflareWorkersAI(account_id="", api_token="", session=MagicMock())
    with pytest.raises(CloudflareAIError, match="not configured"):
        client.translate("hello", "english", "french")
    ready = CloudflareWorkersAI(account_id=ACCOUNT_ID, api_token=API_TOKEN, session=MagicMock())
    with pytest.raises(CloudflareAIError, match="unsupported"):
        ready.run("@cf/unknown", {"text": "x"})
    with pytest.raises(CharterViolation, match="ZERO_TRUST_ISOLATION"):
        refuse_secret_action("store_api_token")


def test_api_cloudflare_and_translate_routes(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    import api as api_mod

    session = MagicMock()
    session.post.return_value = FakeResponse({"result": {"translated_text": "bonjour"}})
    api_mod.workers_ai = CloudflareWorkersAI(
        account_id=ACCOUNT_ID, api_token=API_TOKEN, session=session
    )
    client = TestClient(api_mod.app)

    catalog = client.get("/api/cloudflare")
    assert catalog.status_code == 200
    body = catalog.json()
    assert body["account"] == "cloudflare_enabled"
    assert body["stores_secrets"] is False
    assert body["tls"] == "1.3"
    dumped = json.dumps(body)
    assert API_TOKEN not in dumped
    assert "Authorization" not in dumped

    missing = client.post(
        "/api/translate",
        json={"text": "hello", "source_lang": "english", "target_lang": "french"},
    )
    # configured client should succeed
    assert missing.status_code == 200
    translated = missing.json()
    assert translated["model"] == DEFAULT_MODEL
    assert translated["result"]["result"]["translated_text"] == "bonjour"
    assert translated["payload_sha256"] == payload_sha256("hello")
    assert translated["stores_secrets"] is False

    status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json()["Cloudflare"]["stores_secrets"] is False
    assert client.get("/health").json()["origin_ip_exposed"] is False


def test_strict_origin_returns_403_without_edge(monkeypatch):
    pytest.importorskip("fastapi")
    monkeypatch.setenv("CLOUDFLARE_ORIGIN_MODE", "strict")
    from fastapi.testclient import TestClient
    import api as api_mod

    client = TestClient(api_mod.app)
    blocked = client.get("/api/status")
    assert blocked.status_code == 403
    assert blocked.json()["status"] == "Forbidden at origin — bounded"
    allowed = client.get("/api/status", headers={"CF-Ray": "edge-1"})
    assert allowed.status_code == 200
    assert client.get("/health").status_code == 200


def test_worker_bounds_unauthenticated_api():
    source = (ROOT / "plane" / "cloudflare" / "src" / "index.js").read_text(encoding="utf-8")
    assert "401 Unauthorized at edge — bounded" in source
    assert "X-Avodah-Edge" in source
    assert "ORIGIN_URL" in source
    wrangler = (ROOT / "plane" / "cloudflare" / "wrangler.toml").read_text(encoding="utf-8")
    assert 'main = "src/index.js"' in wrangler
    assert "[ai]" in wrangler
    assert 'binding = "AI"' in wrangler
    assert "API_TOKEN" not in wrangler
    assert "env.AI.run" in source
    assert "@cf/meta/m2m100-1.2b" in source


def test_official_workers_ai_docs_are_cited():
    assert OFFICIAL_DOCS["source"] == "https://github.com/cloudflare/cloudflare-docs"
    assert OFFICIAL_DOCS["rest_api"].endswith("/workers-ai/get-started/rest-api/")
    assert OFFICIAL_DOCS["model"].endswith("/workers-ai/models/m2m100-1.2b/")
    local_docs = (ROOT / "docs" / "cloudflare.md").read_text(encoding="utf-8")
    assert "workers-ai/get-started/rest-api/" in local_docs
    assert "env.AI.run()" in local_docs
    products = (ROOT / "council_os" / "cloudflare.py").read_text(encoding="utf-8")
    assert '"id": "workers_ai"' in products
