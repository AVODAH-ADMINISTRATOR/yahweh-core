from fastapi import FastAPI
from api.routes import router as api_router

app = FastAPI(
    title="Textual Criticism Service",
    description="Computes variant scoring and manages Apparatus Criticus.",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "textual-criticism"}
