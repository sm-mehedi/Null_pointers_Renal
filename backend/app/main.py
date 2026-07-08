from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routers import predict, sample_images
from app.core.config import settings
from app.services.inference import model_service

app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/api", tags=["prediction"])
app.include_router(sample_images.router, prefix="/api", tags=["sample-images"])

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_CANDIDATES = [
    (BASE_DIR.parent / "frontend").resolve(),
    Path("/frontend"),
]
FRONTEND_DIR = next((path for path in FRONTEND_CANDIDATES if path.exists()), FRONTEND_CANDIDATES[0])

if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    app.mount("/sample-images", StaticFiles(directory=FRONTEND_DIR / "sample-images"), name="sample-images-static")


@app.on_event("startup")
def startup_event():
    model_service.load()


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_service.is_loaded}


@app.get("/")
def index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": settings.app_name}
