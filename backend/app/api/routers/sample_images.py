import io
import zipfile
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

CATEGORIES = {
    "normal": "Normal",
    "stone": "Kidney Stone",
    "tumor": "Kidney Tumor",
    "cyst": "Kidney Cyst",
}

DESCRIPTIONS = {
    "normal": "Reference CT scans without visible kidney disease indicators. Add normal sample images to this folder when available.",
    "stone": "Kidney stone sample CT scans for testing the upload flow and comparing model confidence on stone-like findings.",
    "tumor": "Kidney tumor sample CT scans for testing tumor-class predictions and Grad-CAM highlighted regions.",
    "cyst": "Kidney cyst sample CT scans for testing cyst-class predictions and explaining model attention with heatmaps.",
}

ARCHIVE_FILES = {
    "stone": "Stone.zip",
    "tumor": "Tumor.zip",
    "cyst": "Cyst.zip",
}


def sample_root() -> Path:
    candidates = [
        Path(__file__).resolve().parents[4] / "frontend" / "sample-images",
        Path.cwd().parent / "frontend" / "sample-images",
        Path("/frontend/sample-images"),
    ]
    return next((path for path in candidates if path.exists()), candidates[0])


def static_sample_url(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    return "/sample-images/" + quote(relative)


@router.get("/sample-images")
def list_sample_images():
    root = sample_root()
    data = []
    for key, label in CATEGORIES.items():
        folder = root / key
        files = []
        if folder.exists():
            for path in sorted(folder.rglob("*")):
                if path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    url = static_sample_url(path, root)
                    files.append(
                        {
                            "name": path.name,
                            "url": url,
                            "download_url": url,
                        }
                    )
        archive_name = ARCHIVE_FILES.get(key)
        archive_path = root / "archives" / archive_name if archive_name else None
        data.append(
            {
                "category": key,
                "label": label,
                "description": DESCRIPTIONS[key],
                "preview": files[0]["url"] if files else None,
                "files": files,
                "count": len(files),
                "archive_url": static_sample_url(archive_path, root) if archive_path and archive_path.exists() else None,
            }
        )
    return {"categories": data}


@router.get("/sample-images/download-all")
def download_all_samples():
    root = sample_root()
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
        for key in CATEGORIES:
            folder = root / key
            if folder.exists():
                for path in folder.rglob("*"):
                    if path.is_file():
                        archive.write(path, path.relative_to(root))
            else:
                archive.writestr(f"{key}/.keep", "")
    memory.seek(0)
    return StreamingResponse(
        memory,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=kidney-sample-images.zip"},
    )
