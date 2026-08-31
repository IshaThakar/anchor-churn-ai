import os
import sys
from pathlib import Path

# Ensure root directory is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

try:
    from .config import Config
    from .api.routes import router as api_router
except ImportError:
    from backend.config import Config
    from backend.api.routes import router as api_router

app = FastAPI(
    title=Config.PROJECT_NAME,
    version=Config.VERSION,
    description="Enterprise-grade AI/ML platform for multi-dimensional behavioral telemetry ingestion, real-time churn propensity scoring, SHAP explainability, and omnichannel Next-Best-Action orchestration."
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount Frontend Static Files
frontend_dir = root_dir / "frontend"
if frontend_dir.exists():
    # Mount /static
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    # Serve index.html on root and /index.html
    @app.get("/")
    async def serve_root():
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        raise HTTPException(status_code=404, detail="index.html not found")

    @app.get("/index.html")
    async def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))

    # Fallback routes for direct asset requests
    @app.get("/style.css")
    async def serve_css():
        return FileResponse(str(frontend_dir / "style.css"))

    @app.get("/app.js")
    async def serve_js():
        return FileResponse(str(frontend_dir / "app.js"))


if __name__ == "__main__":
    import uvicorn
    print(f"[*] Starting Anchor Server on http://127.0.0.1:{Config.PORT}")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=Config.PORT, reload=True)
