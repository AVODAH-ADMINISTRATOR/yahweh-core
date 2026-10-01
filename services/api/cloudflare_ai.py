"""Cloudflare Workers AI client for origin translation.

Uses the documented v4 AI run URL. Account identifiers and API tokens
are read from process environment and are never written to the catalog,
ledger, or HTTP responses.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, Mapping, Optional

import requests

DEFAULT_MODEL = "@cf/meta/m2m100-1.2b"
ALLOWED_MODELS = frozenset({DEFAULT_MODEL})
API_BASE_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/"
ACCOUNT_ID_RE = re.compile(r"^[a-f0-9]{32}$", re.IGNORECASE)
REQUEST_TIMEOUT_SECONDS = 30


class CloudflareAIError(RuntimeError):
    """Raised when Workers AI cannot be called without leaking secrets."""


class CloudflareWorkersAI:
    """Thin client for Cloudflare Workers AI translation."""

    def __init__(
        self,
        account_id: Optional[str] = None,
        api_token: Optional[str] = None,
        session: Optional[requests.Session] = None,
        environ: Optional[Mapping[str, str]] = None,
    ) -> None:
        env = environ if environ is not None else os.environ
        self.account_id = (account_id if account_id is not None else env.get("CLOUDFLARE_ACCOUNT_ID", "")).strip()
        token = (api_token if api_token is not None else env.get("CLOUDFLARE_API_TOKEN", "")).strip()
        self._token = token
        self._session = session or requests.Session()

    def __repr__(self) -> str:
        return f"CloudflareWorkersAI(configured={self.configured}, stores_secrets=False)"

    @property
    def configured(self) -> bool:
        return bool(ACCOUNT_ID_RE.fullmatch(self.account_id) and self._token)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "provider": "cloudflare_workers_ai",
            "model": DEFAULT_MODEL,
            "configured": self.configured,
            "stores_secrets": False,
            "live_login": False,
            "account_id_present": bool(self.account_id),
            "token_present": bool(self._token),
        }

    def run(self, model: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if model not in ALLOWED_MODELS:
            raise CloudflareAIError("unsupported Workers AI model")
        if not self.configured:
            raise CloudflareAIError("Cloudflare Workers AI is not configured")
        url = API_BASE_URL.format(account_id=self.account_id) + model
        headers = {"Authorization": "Bearer " + self._token}
        try:
            response = self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.RequestException as exc:
            raise CloudflareAIError("Cloudflare Workers AI request failed") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise CloudflareAIError("Cloudflare Workers AI returned a non-JSON body") from exc
        if not isinstance(body, dict):
            raise CloudflareAIError("Cloudflare Workers AI returned an unexpected payload")
        if response.status_code >= 400:
            raise CloudflareAIError("Cloudflare Workers AI request failed")
        return body

    def translate(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        return self.run(
            DEFAULT_MODEL,
            {
                "text": text,
                "source_lang": source_lang,
                "target_lang": target_lang,
            },
        )
