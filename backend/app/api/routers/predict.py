from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.prediction import Prediction
from app.services.inference import model_service
from app.services.user_service import create_user
from app.utils.validators import validate_upload

router = APIRouter()


@router.post("/predict")
async def predict_endpoint(
    name: str = Form(..., min_length=2, max_length=120),
    phone: str = Form(..., min_length=7, max_length=32),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    image_bytes = await validate_upload(file, settings.max_upload_mb)

    try:
        result = model_service.predict(image_bytes)
        user = create_user(db, name, phone)
        record = Prediction(user_id=user.id, prediction=result.prediction, confidence=result.confidence)
        db.add(record)
        db.commit()
        db.refresh(record)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Prediction could not be completed.") from exc

    return {
        "prediction": result.prediction,
        "confidence": result.confidence,
        "probabilities": result.probabilities,
        "timestamp": record.timestamp,
        "model_name": result.model_name,
        "original_image": result.original_image,
        "heatmap_image": result.heatmap_image,
        "explanation": "The highlighted regions indicate the areas that contributed most to the AI model's prediction.",
    }
