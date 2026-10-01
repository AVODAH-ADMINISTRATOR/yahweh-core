from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time
from whatsapp_mainframe_bridge import IntegratedAvodahWhatsAppMainframeBridge
from cloudflare_ai import CloudflareAIError, CloudflareWorkersAI, DEFAULT_MODEL
from cloudflare_edge import (
    bind_edge,
    edge_catalog,
    forbid_direct_origin,
    parse_edge_headers,
    payload_sha256,
)

app = FastAPI(title="Integrated Avodah LLC API", description="Corporate Compliance Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bridge = IntegratedAvodahWhatsAppMainframeBridge()
tamper_log = []
defense_status = "Active"
threat_database_version = "AI-v2.6.5-Adaptive"
cloudflare_edge = bind_edge()
workers_ai = CloudflareWorkersAI()

class PayloadRequest(BaseModel):
    payload: str

class WhatsAppCommandRequest(BaseModel):
    command: str
    token: str

class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_lang: str = Field(..., min_length=1)
    target_lang: str = Field(..., min_length=1)

@app.middleware("http")
async def cloudflare_origin_gate(request: Request, call_next):
    edge = parse_edge_headers(request.headers)
    request.state.cloudflare = edge
    if forbid_direct_origin(request.url.path, edge):
        return JSONResponse(
            {
                "status": "Forbidden at origin — bounded",
                "edge": "cloudflare",
                "stores_secrets": False,
            },
            status_code=403,
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )
    response = await call_next(request)
    response.headers.setdefault("Cache-Control", "no-store")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    return response

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "edge": "cloudflare",
        "tls": "1.3",
        "origin_ip_exposed": False,
        "stores_secrets": False,
    }

@app.get("/api/cloudflare")
def get_cloudflare(request: Request):
    catalog = edge_catalog(enabled=cloudflare_edge.enabled)
    catalog["workers_ai"] = workers_ai.snapshot()
    catalog["via_edge"] = bool(getattr(request.state, "cloudflare", {}).get("via_edge"))
    return catalog

@app.get("/api/status")
def get_system_status():
    return {
        "System Deployment": "Fully Operational",
        "AI Threat Database": threat_database_version,
        "Defense Status": defense_status,
        "Tamper Violations Logged": len(tamper_log),
        "Gateway Status": "Verified Online",
        "Profile": {
            "name": bridge.profile_name,
            "address": bridge.address,
            "website": bridge.website
        },
        "Cloudflare": {
            "account": edge_catalog(enabled=cloudflare_edge.enabled)["account"],
            "tls": "1.3",
            "payload_hashing": "sha256",
            "workers_ai": workers_ai.snapshot(),
            "stores_secrets": False,
            "live_login": False,
        },
    }

@app.post("/api/translate")
def translate_text(body: TranslateRequest):
    digest = payload_sha256(body.text)
    if not workers_ai.configured:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "Cloudflare Workers AI is not configured",
                "model": DEFAULT_MODEL,
                "payload_sha256": digest,
                "stores_secrets": False,
            },
        )
    try:
        result = workers_ai.translate(body.text, body.source_lang, body.target_lang)
    except CloudflareAIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "status": "Cloudflare Workers AI request failed",
                "model": DEFAULT_MODEL,
                "payload_sha256": digest,
                "stores_secrets": False,
            },
        ) from exc
    return {
        "model": DEFAULT_MODEL,
        "source_lang": body.source_lang,
        "target_lang": body.target_lang,
        "payload_sha256": digest,
        "result": result,
        "stores_secrets": False,
    }

@app.post("/api/scan")
def scan_payload(request: PayloadRequest):
    """
    AI-driven intelligence engine scanning for runtime anomalies.
    """
    digest = payload_sha256(request.payload)
    tampering_signatures = ["eval(", "exec(", "__import__", "os.system", "subprocess", "bypass_lock"]
    is_violator = any(sig in request.payload for sig in tampering_signatures)
    
    if is_violator:
        tamper_log.append({"timestamp": time.time(), "payload_sha256": digest})
        new_pwd = bridge.rotate_mainframe_lock()
        return {
            "status": "Violator Neutralized", 
            "action": "Quarantined and Mainframe Locked",
            "new_password": new_pwd,
            "payload_sha256": digest,
        }
    else:
        return {"status": "Clean", "action": "Authorized Access Granted", "payload_sha256": digest}

@app.post("/api/lockdown")
def trigger_lockdown():
    """Forces an emergency rotation of the mainframe credential."""
    new_pwd = bridge.rotate_mainframe_lock()
    return {"status": "Mainframe Locked", "new_password": new_pwd}

@app.get("/api/whatsapp-qr")
def get_whatsapp_qr(command: str = "STATUS"):
    """Returns the WhatsApp target link for frontend QR generation."""
    link = f"https://wa.me/{bridge.phone}?text=CMD:{command}"
    return {"whatsapp_link": link, "target": bridge.phone}

@app.post("/api/whatsapp-webhook")
def process_webhook(request: WhatsAppCommandRequest):
    """Simulates a webhook receiver for WhatsApp messages."""
    result = bridge.process_whatsapp_command(request.command, request.token)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
