"""Virtualized domain health service. Decoupled from host hardware identity."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from council_os.domains import parse_domain, spec_for
from council_os.forge import PRODUCT_TYPES, AutoDeveloperForge
from council_os.kernel import CouncilOSKernel

_KERNEL = CouncilOSKernel()
_KERNEL.compile()
_FORGE = AutoDeveloperForge(_KERNEL)
_FORGE.compile_workspace()
_DOMAIN = parse_domain(os.environ.get("COUNCIL_OS_DOMAIN", "governance"))


class DomainHealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _write_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/health"}:
            runtime = _KERNEL.mesh.get(_DOMAIN)
            payload = runtime.health()
            payload["kernel"] = {
                "compiled": _KERNEL.compiled,
                "personalized_will": False,
                "virtualized": True,
            }
            self._write_json(200, payload)
            return
        if self.path == "/citations":
            self._write_json(200, _KERNEL.domain_change_citations(_DOMAIN))
            return
        if self.path in {"/forge", "/forge/products"}:
            catalog = _FORGE.api_catalog()
            catalog["products"] = sorted(PRODUCT_TYPES)
            catalog["workspace"] = {
                "fluid": True,
                "host_decoupled": True,
                "compiled": _KERNEL.compiled,
            }
            self._write_json(200, catalog)
            return
        if self.path == "/compat":
            self._write_json(200, _FORGE.compat.snapshot())
            return
        if self.path == "/stewardship":
            self._write_json(200, _FORGE.steward.assignment())
            return
        if self.path == "/intel":
            self._write_json(
                200,
                {"briefs": [brief.to_dict() for brief in _FORGE.intel.briefs.values()]},
            )
            return
        self._write_json(404, {"error": "not found"})


def serve(port: int | None = None) -> None:
    spec = spec_for(_DOMAIN)
    bind_port = int(port or os.environ.get("COUNCIL_OS_PORT", spec.port))
    server = ThreadingHTTPServer(("0.0.0.0", bind_port), DomainHealthHandler)
    print(f"council-os domain={_DOMAIN.value} port={bind_port} virtualized=true")
    server.serve_forever()


if __name__ == "__main__":
    serve()
