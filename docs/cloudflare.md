---
title: Cloudflare edge
pcx_content_type: how-to
---

# Cloudflare edge

Connect the origin API to Cloudflare Workers, static assets, and Workers AI. Keep API tokens out of the kernel.

## Place the origin behind the Worker

You run `services/api/api.py` as the origin. `plane/cloudflare` is the public Worker.

Unauthenticated `/api/*` and `/ledger/*` requests receive `401` at the edge. Direct origin access in strict mode receives `403`. `/health` stays reachable for probes.

Set `CLOUDFLARE_ORIGIN_MODE=strict` on the origin when Cloudflare proxies production traffic.

The Worker serves [static assets](https://developers.cloudflare.com/workers/static-assets/) from `plane/cloudflare/dist` through the `ASSETS` binding.

## Create a Workers AI token

You need an Account ID and a token with Workers AI Read and Workers AI Edit. Create them from the Cloudflare dashboard as described in the [Workers AI REST API guide](https://developers.cloudflare.com/workers-ai/get-started/rest-api/).

Export the values in the origin environment. Do not commit them.

```sh
export CLOUDFLARE_ACCOUNT_ID=<YOUR_ACCOUNT_ID>
export CLOUDFLARE_API_TOKEN=<YOUR_API_TOKEN>
```

The origin reads those values from the environment. It attaches the token only to the outbound [Execute AI model](https://developers.cloudflare.com/api/resources/ai/methods/run/) request. Catalogs, ledger entries, and HTTP responses omit the token.

## Run translation

`POST /api/translate` runs [`@cf/meta/m2m100-1.2b`](https://developers.cloudflare.com/workers-ai/models/m2m100-1.2b/). That model is a many-to-many translation encoder-decoder.

The documented request body requires `text` and `target_lang`. `source_lang` defaults to `en`.

```json
{
  "text": "hello",
  "source_lang": "en",
  "target_lang": "fr"
}
```

The origin hashes the text with SHA-256 before it returns a result. If the token is missing, the route returns `503`.

On the Worker, bounded `POST /api/translate` calls `env.AI.run()` through the [Workers AI binding](https://developers.cloudflare.com/workers-ai/configuration/bindings/). The Wrangler file declares `ai.binding = "AI"` and does not store tokens.

:::note[Kernel catalog]
`python -m council_os cloudflare` records enabled products, including Workers AI. It does not log in to a live account and it does not store API tokens.
:::

## Inspect the edge contract

- `GET /health` — origin probe, allowed without Cloudflare headers
- `GET /api/cloudflare` — product catalog and Workers AI status, no secrets
- `GET /api/status` — includes the Cloudflare block
- `POST /api/translate` — Workers AI translation

Deploy the Worker with Wrangler from `plane/cloudflare`. `ORIGIN_URL` points at the origin. Keep API tokens out of `wrangler.toml`.

Official source: [cloudflare/cloudflare-docs](https://github.com/cloudflare/cloudflare-docs).
