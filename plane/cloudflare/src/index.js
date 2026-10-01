export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const path = url.pathname;
    const boundedHeaders = {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    };

    if (path === "/health") {
      return proxyToOrigin(req, env, path, url.search);
    }

    if (path.startsWith("/api/") || path.startsWith("/ledger/")) {
      const bounded =
        req.headers.get("CF-Access-Jwt-Assertion") ||
        req.headers.get("Authorization");
      if (!bounded) {
        return new Response("401 Unauthorized at edge — bounded", {
          status: 401,
          headers: boundedHeaders,
        });
      }
      if (path === "/api/translate" && req.method === "POST" && env.AI) {
        return translateAtEdge(req, env, boundedHeaders);
      }
      return proxyToOrigin(req, env, path, url.search);
    }

    if (env.ASSETS) {
      return env.ASSETS.fetch(req);
    }
    return new Response("Not found", { status: 404, headers: boundedHeaders });
  },
};

async function translateAtEdge(req, env, boundedHeaders) {
  let body;
  try {
    body = await req.json();
  } catch (err) {
    return Response.json(
      { status: "invalid JSON body", stores_secrets: false },
      { status: 400, headers: boundedHeaders }
    );
  }
  const text = body && body.text;
  const target = body && body.target_lang;
  const source = (body && body.source_lang) || "en";
  if (!text || !target) {
    return Response.json(
      { status: "text and target_lang are required", stores_secrets: false },
      { status: 400, headers: boundedHeaders }
    );
  }
  const result = await env.AI.run("@cf/meta/m2m100-1.2b", {
    text,
    source_lang: source,
    target_lang: target,
  });
  return Response.json(
    {
      model: "@cf/meta/m2m100-1.2b",
      source_lang: source,
      target_lang: target,
      result,
      stores_secrets: false,
    },
    { headers: boundedHeaders }
  );
}

async function proxyToOrigin(req, env, path, search) {
  const origin = env.ORIGIN_URL;
  if (!origin) {
    if (path === "/health") {
      return Response.json(
        {
          status: "healthy",
          edge: "cloudflare",
          origin_ip_exposed: false,
          stores_secrets: false,
        },
        { headers: { "Cache-Control": "no-store" } }
      );
    }
    return new Response("401 Unauthorized at edge — bounded", {
      status: 401,
      headers: { "Cache-Control": "no-store" },
    });
  }

  const target = new URL(path + (search || ""), origin);
  const headers = new Headers(req.headers);
  headers.set("X-Avodah-Edge", "cloudflare");
  headers.delete("host");

  const init = {
    method: req.method,
    headers,
  };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = req.body;
  }

  const resp = await fetch(target, init);
  const out = new Headers(resp.headers);
  out.set("Cache-Control", "no-store");
  out.delete("server");
  return new Response(resp.body, { status: resp.status, headers: out });
}
