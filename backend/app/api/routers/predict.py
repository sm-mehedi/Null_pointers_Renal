import base64
import io
from datetime import datetime, timezone
from textwrap import wrap

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image, ImageDraw

from app.core.config import settings
from app.services.inference import model_service
from app.utils.validators import validate_upload

router = APIRouter()


@router.post("/predict")
async def predict_endpoint(
    name: str = Form(..., min_length=2, max_length=120),
    phone: str = Form(..., min_length=7, max_length=32),
    file: UploadFile = File(...),
):
    image_bytes = await validate_upload(file, settings.max_upload_mb)

    try:
        result = model_service.predict(image_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Prediction could not be completed.") from exc

    return {
        "name": name,
        "phone": phone,
        "prediction": result.prediction,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
        "timestamp": datetime.now(timezone.utc),
        "model_name": result.model_name,
        "original_image": result.original_image,
        "heatmap_image": result.heatmap_image,
        "explanation": "The highlighted regions indicate the areas that contributed most to the AI model's prediction.",
    }


def _decode_data_url(data_url: str) -> Image.Image:
    try:
        _, encoded = data_url.split(",", 1)
        return Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Report image data could not be decoded.") from exc


def _draw_wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width: int, line_height: int) -> int:
    x, y = xy
    for line in wrap(text, width=width):
        draw.text((x, y), line, fill=(31, 41, 55))
        y += line_height
    return y


@router.post("/report-pdf")
async def report_pdf(payload: dict):
    original = _decode_data_url(payload.get("original_image", ""))
    heatmap = _decode_data_url(payload.get("heatmap_image", ""))

    page = Image.new("RGB", (1240, 1754), "white")
    draw = ImageDraw.Draw(page)
    y = 70
    draw.text((70, y), "Kidney Disease Detection Report", fill=(15, 23, 42))
    y += 50
    draw.text((70, y), f"Name: {payload.get('name', 'N/A')}", fill=(31, 41, 55))
    y += 30
    draw.text((70, y), f"Phone: {payload.get('phone', 'N/A')}", fill=(31, 41, 55))
    y += 30
    draw.text((70, y), f"Time: {payload.get('timestamp', 'N/A')}", fill=(31, 41, 55))
    y += 50
    draw.text((70, y), f"Prediction: {payload.get('prediction', 'N/A')}", fill=(37, 99, 235))
    y += 34
    draw.text((70, y), f"Confidence: {float(payload.get('confidence', 0)):.2f}%", fill=(20, 184, 166))
    y += 48

    probabilities = payload.get("probabilities") or {}
    draw.text((70, y), "Class Probabilities", fill=(15, 23, 42))
    y += 32
    for label, value in probabilities.items():
        draw.text((90, y), f"{label}: {float(value):.2f}%", fill=(31, 41, 55))
        y += 26

    y += 24
    y = _draw_wrapped(draw, payload.get("description", ""), (70, y), 125, 26)
    y += 30
    y = _draw_wrapped(draw, payload.get("explanation", ""), (70, y), 125, 26)
    y += 32
    y = _draw_wrapped(
        draw,
        "Disclaimer: This AI result is for research and decision support only. Consult a qualified physician for medical diagnosis and treatment.",
        (70, y),
        125,
        26,
    )

    original.thumbnail((500, 500))
    heatmap.thumbnail((500, 500))
    image_y = 1080
    page.paste(original, (70, image_y))
    page.paste(heatmap, (670, image_y))
    draw.text((70, image_y + 520), "Original CT Scan", fill=(31, 41, 55))
    draw.text((670, image_y + 520), "Grad-CAM Heatmap", fill=(31, 41, 55))

    output = io.BytesIO()
    page.save(output, format="PDF", resolution=120.0)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=kidney-ai-report.pdf"},
    )
