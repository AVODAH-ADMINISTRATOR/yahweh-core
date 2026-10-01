---
title: Cloudflare edge
pcx_content_type: how-to
---

# Cloudflare edge

Connect the origin API to Cloudflare without storing tokens in the kernel.

## Place the origin behind the Worker

You run `services/api/api.py` as the origin. The Worker in `plane/cloudflare` is the public edge.

Unauthenticated `/api/*` and `/ledger/*` requests receive `401` at the edge. Direct origin access in strict mode receives `403`. `/health` stays reachable for probes.

Set `CLOUDFLARE_ORIGIN_MODE=strict` on the origin when Cloudflare proxies production traffic.

## Configure Workers AI translation

`POST /api/translate` calls Cloudflare Workers AI model `@cf/meta/m2m100-1.2b` through the v4 AI run URL.

Export these values in the origin environment. Do not commit them.

```sh
export CLOUDFLARE_ACCOUNT_ID=<YOUR_ACCOUNT_ID>
export CLOUDFLARE_API_TOKEN=<YOUR_API_TOKEN>
```

The origin reads the account identifier and token from the environment. It attaches the token to the outbound Workers AI request only. Catalogs, ledger entries, and HTTP responses omit the token.

Example request body:

```json
{
  "text": "hello",
  "source_lang": "english",
  "target_lang": "french"
}
```

The origin hashes the text with SHA-256 before it returns a result. If the token is missing, the route returns `503`.

:::note[Kernel catalog]
`python -m council_os cloudflare` records enabled products. It does not log in to a live account and it does not store API tokens.
:::

## Inspect the edge contract

- `GET /health` — origin probe, allowed without Cloudflare headers
- `GET /api/cloudflare` — product catalog and Workers AI status, no secrets
- `GET /api/status` — includes the Cloudflare block
- `POST /api/translate` — Workers AI translation

Deploy the Worker with Wrangler from `plane/cloudflare`. `ORIGIN_URL` points at the origin. Keep API tokens out of `wrangler.toml`.
