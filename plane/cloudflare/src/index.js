export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const path = url.pathname;
    const bounded = { "Cache-Control": "no-store", "X-OS-ID": "b08a2817" };

    if (path.startsWith("/api/") || path.startsWith("/ledger/")) {
      return new Response("401 Unauthorized at edge — bounded", {
        status: 401,
        headers: bounded,
      });
    }

    if (path === "/origin" || path.startsWith("/origin/")) {
      return new Response("403 Forbidden at origin — isolated", {
        status: 403,
        headers: bounded,
      });
    }

    if (path === "/health") {
      return Response.json(
        {
          status: "edge_bounded",
          origin_exposed: false,
          live_login: false,
          stores_secrets: false,
          tls: "1.3",
        },
        { headers: bounded }
      );
    }

    if (path === "/cloudflare") {
      return Response.json(
        {
          account: "cloudflare_enabled",
          edge_status: 401,
          origin_status: 403,
          origin_exposed: false,
          live_login: false,
          stores_secrets: false,
          tls: "1.3",
        },
        { headers: bounded }
      );
    }

    if (env && env.ASSETS) {
      return env.ASSETS.fetch(req);
    }
    return new Response("edge bounded", { status: 200, headers: bounded });
  },
};
