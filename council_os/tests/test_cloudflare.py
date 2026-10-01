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
