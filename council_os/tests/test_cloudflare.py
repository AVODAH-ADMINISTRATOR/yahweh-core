import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.cloudflare import (
    EDGE_STATUS,
    ORIGIN_STATUS,
    PAGES_ASSETS,
    WORKER_MAIN,
    WRANGLER_CONFIG,
    AGENTS_STARTER,
    AGENTS_STARTER_WRANGLER,
    AGENTS_STARTER_MAIN,
    WEB_TOOLS,
)
from council_os.constraints import CharterViolation
from council_os.forge import AutoDeveloperForge
from council_os.kernel import CouncilOSKernel

ROOT = Path(__file__).resolve().parents[2]


def test_wrangler_binds_worker_assets_without_secrets():
    wrangler = (ROOT / WRANGLER_CONFIG).read_text()
    lowered = wrangler.lower()
    assert 'main = "src/index.js"' in wrangler
    assert 'directory = "./dist"' in wrangler
    assert 'binding = "ASSETS"' in wrangler
    assert "api_token" not in lowered
    assert "account_id" not in lowered
    assert "api_key" not in lowered


def test_worker_enforces_401_edge_and_403_origin():
    worker = (ROOT / WORKER_MAIN).read_text()
    assert "status: 401" in worker
    assert "status: 403" in worker
    assert 'path.startsWith("/api/")' in worker
    assert 'path === "/origin"' in worker
    assert "ASSETS" in worker


def test_pages_redirects_do_not_proxy_origin():
    dist_redirects = (ROOT / PAGES_ASSETS / "_redirects").read_text()
    docs_redirects = (ROOT / "docs" / "_redirects").read_text()
    for text in (dist_redirects, docs_redirects):
        assert "origin.yahweh-core.internal" not in text
        assert "/* /index.html 200" in text


def test_cloudflare_snapshot_points_at_in_tree_edge_files():
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    edge = forge.compile_workspace()["cloudflare"]
    assert (ROOT / edge["wrangler_config"]).is_file()
    assert (ROOT / edge["worker_main"]).is_file()
    assert (ROOT / edge["pages_assets"]).is_dir()
    assert edge["edge_status"] == EDGE_STATUS
    assert edge["origin_status"] == ORIGIN_STATUS
    with pytest.raises(CharterViolation, match="ZERO_TRUST_ISOLATION"):
        forge.cloudflare.refuse("expose_origin_ip")


def test_agents_starter_has_no_cloudflare_secrets():
    wrangler = (ROOT / AGENTS_STARTER_WRANGLER).read_text().lower()
    package = (ROOT / AGENTS_STARTER / "package.json").read_text()
    assert (ROOT / AGENTS_STARTER_MAIN).is_file()
    assert "agents-starter" in (ROOT / AGENTS_STARTER_WRANGLER).read_text()
    assert '"dev": "vite dev"' in package
    assert "api_token" not in wrangler
    assert "account_id" not in wrangler
    assert "cloudflare_api_token" not in wrangler


def test_web_tools_keeps_keys_in_environment():
    source = (ROOT / WEB_TOOLS).read_text()
    assert 'os.getenv("FIRECRAWL_API_KEY")' in source
    assert 'os.getenv("NOUS_API_KEY")' in source
    assert "sk-" not in source
    kernel = CouncilOSKernel()
    forge = AutoDeveloperForge(kernel)
    edge = forge.compile_workspace()["cloudflare"]
    assert edge["agents_starter"] == AGENTS_STARTER
    assert edge["web_tools"] == WEB_TOOLS
    assert edge["stores_secrets"] is False
    assert edge["live_login"] is False
    with pytest.raises(CharterViolation, match="ZERO_TRUST_ISOLATION"):
        forge.cloudflare.refuse("live_account_login")
