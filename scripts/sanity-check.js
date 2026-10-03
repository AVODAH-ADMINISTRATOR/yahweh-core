#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");

function read(rel) {
  const full = path.join(root, rel);
  if (!fs.existsSync(full)) {
    throw new Error("missing " + rel);
  }
  return fs.readFileSync(full, "utf8");
}

const required = [
  "plane/cloudflare/wrangler.toml",
  "plane/cloudflare/src/index.js",
  "services/api/api.py",
  "services/api/cloudflare_ai.py",
  "docs/cloudflare.md",
  "package.json",
];

for (const rel of required) {
  read(rel);
}

const wrangler = read("plane/cloudflare/wrangler.toml");
if (!wrangler.includes('main = "src/index.js"')) {
  throw new Error("wrangler main is not src/index.js");
}
if (!wrangler.includes("[ai]") || !wrangler.includes('binding = "AI"')) {
  throw new Error("Workers AI binding is missing");
}
if (/API_TOKEN\s*=/.test(wrangler) || /CLOUDFLARE_API_TOKEN/.test(wrangler)) {
  throw new Error("wrangler must not store API tokens");
}

const worker = read("plane/cloudflare/src/index.js");
if (!worker.includes("401 Unauthorized at edge")) {
  throw new Error("Worker must return 401 for unauthenticated API routes");
}
if (!worker.includes("env.AI.run")) {
  throw new Error("Worker must call env.AI.run for translation");
}

const pkg = JSON.parse(read("package.json"));
if (!pkg.scripts || pkg.scripts.check !== "node scripts/sanity-check.js") {
  throw new Error("package.json check script drifted");
}

console.log("sanity check passed");
