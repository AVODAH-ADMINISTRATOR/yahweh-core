/**
 * AVODAH-OS-8-CORE — 360° Edge Router — b08a2817 — Selam OS
 * Static: dist/* cached
 * Proxy: /api/* /ledger/* /health -> ORIGIN_URL (server.cjs:3000)
 * Auth: Edge 401 check (token presence + 120s TTL), Node 403 + WORM enforcement
 * NIST: validity reliability safety security accountability transparency
 */
export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url);
    const path = url.pathname;

    // 1. Security headers — NIST
    const secHeaders = {
      "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "Content-Security-Policy": "default-src 'self'; script-src 'self'; connect-src 'self' https:; img-src 'self' data:; style-src 'self' 'unsafe-inline'",
      "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
      "X-Radiance": env.RADIANCE || "1790814470",
      "X-OS-ID": "b08a2817",
      "X-Perception": "360-omnipotence-bounded"
    };

    // 2. Static routing — served via [assets] — let platform handle
    if (!path.startsWith('/api/') &&!path.startsWith('/ledger/') && path!== '/health' &&!path.startsWith('/tokens')) {
      // Cache behavior: static immutable 1y for hashed assets, no-cache for index.html
      return env.ASSETS.fetch(req).then(r => {
        const res = new Response(r.body, r);
        Object.entries(secHeaders).forEach(([k,v])=>res.headers.set(k,v));
        if (path === '/' || path.endsWith('index.html')) {
          res.headers.set("Cache-Control", "no-cache, no-store, must-revalidate");
        } else {
          res.headers.set("Cache-Control", "public, max-age=31536000, immutable");
        }
        return res;
      });
    }

    // 3. Edge auth — 401 enforcement — token presence + 120s TTL mint check
    if (path.startsWith('/api/') || path.startsWith('/ledger/')) {
      const auth = req.headers.get('Authorization');
      if (!auth ||!auth.startsWith('Bearer ')) {
        return new Response(JSON.stringify({error:"401 missing token", id:"b08a2817"}), {status:401, headers:{...secHeaders, "Content-Type":"application/json"}});
      }
      // Light TTL check — full verification delegated to Node WORM
      try {
        const token = auth.slice(7);
        const payload = JSON.parse(atob(token.split('.')[1] || ''));
        const age = Date.now()/1000 - (payload.iat || 0);
        if (age > 120) {
          return new Response(JSON.stringify({error:"401 TTL expired 120s", age, id:"b08a2817"}), {status:401, headers:{...secHeaders, "Content-Type":"application/json"}});
        }
      } catch {}
    }

    // 4. Reverse-proxy to Node engine — server.cjs:3000 — bounded origin
    const originUrl = (env.ORIGIN_URL || "http://localhost:3000") + path + url.search;
    const proxyReq = new Request(originUrl, {
      method: req.method,
      headers: req.headers,
      body: req.method!== 'GET' && req.method!== 'HEAD'? req.body : null
    });
    proxyReq.headers.set("X-Forwarded-By", "Cloudflare-360-b08a2817");
    proxyReq.headers.set("X-Forwarded-For", req.headers.get('CF-Connecting-IP') || '');

    try {
      const originRes = await fetch(proxyReq);
      const res = new Response(originRes.body, originRes);
      Object.entries(secHeaders).forEach(([k,v])=>res.headers.set(k,v));
      res.headers.set("Cache-Control", "no-store"); // API never cached — WORM integrity
      return res;
    } catch (e) {
      return new Response(JSON.stringify({error:"Origin unreachable", detail:e.message, id:"b08a2817"}), {status:502, headers:{...secHeaders, "Content-Type":"application/json"}});
    }
  }
}
