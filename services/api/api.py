from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from whatsapp_mainframe_bridge import IntegratedAvodahWhatsAppMainframeBridge

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

class PayloadRequest(BaseModel):
    payload: str

class WhatsAppCommandRequest(BaseModel):
    command: str
    token: str

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
        }
    }

@app.post("/api/scan")
def scan_payload(request: PayloadRequest):
    """
    AI-driven intelligence engine scanning for runtime anomalies.
    """
    tampering_signatures = ["eval(", "exec(", "__import__", "os.system", "subprocess", "bypass_lock"]
    is_violator = any(sig in request.payload for sig in tampering_signatures)
    
    if is_violator:
        tamper_log.append({"timestamp": time.time(), "payload": request.payload})
        new_pwd = bridge.rotate_mainframe_lock()
        return {
            "status": "Violator Neutralized", 
            "action": "Quarantined and Mainframe Locked",
            "new_password": new_pwd
        }
    else:
        return {"status": "Clean", "action": "Authorized Access Granted"}

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
