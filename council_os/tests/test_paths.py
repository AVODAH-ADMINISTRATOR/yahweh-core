import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from council_os.constraints import CharterViolation
from council_os.kernel import CouncilOSKernel
from council_os.paths import (
    CANONICAL_HOME,
    CANONICAL_REPO_ROOT,
    assert_home_canonical,
    is_forbidden_home,
    refuse_public_paths,
    resolve_home,
    resolve_repo_root,
)


def test_public_home_is_forbidden():
    assert is_forbidden_home("/public") is True
    assert is_forbidden_home("/public/yahweh-core") is True
    assert is_forbidden_home("/root") is False
    assert is_forbidden_home("/root/yahweh-core") is False
    assert is_forbidden_home("/home/runner") is False


def test_resolve_rejects_legacy_public_home():
    with pytest.raises(CharterViolation, match="/public"):
        resolve_home({"HOME": "/public"})
    with pytest.raises(CharterViolation, match="/public"):
        resolve_repo_root({"YAHWEH_CORE_HOME": "/public/yahweh-core"})
    with pytest.raises(CharterViolation, match="/public"):
        assert_home_canonical({"HOME": "/public", "YAHWEH_CORE_HOME": "/public/yahweh-core"})


def test_canonical_root_paths_accepted():
    snap = assert_home_canonical(
        {"HOME": CANONICAL_HOME, "YAHWEH_CORE_HOME": CANONICAL_REPO_ROOT}
    )
    assert snap["home"] == "/root"
    assert snap["repo_root"] == "/root/yahweh-core"
    assert snap["public_path_rejected"] is True
    assert snap["path_correction"] == "HOME=/root"
    assert resolve_home({"HOME": "/root"}) == "/root"
    assert resolve_repo_root({"HOME": "/root"}) == "/root/yahweh-core"


def test_refuse_public_paths_helper():
    refuse_public_paths(["/root/yahweh-core", "/var/lib"])
    with pytest.raises(CharterViolation):
        refuse_public_paths(["/tmp", "/public/yahweh-core"])


def test_kernel_compile_and_health_include_path_correction():
    kernel = CouncilOSKernel()
    report = kernel.compile()
    assert report["paths"]["canonical_home"] == "/root"
    assert report["paths"]["public_path_rejected"] is True
    health = kernel.health()
    assert health["paths"]["canonical_repo_root"] == "/root/yahweh-core"
    assert "/public" not in health["paths"]["home"]
