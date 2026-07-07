from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.prediction import PredictionHistoryResponse
from app.services.history_service import list_history

router = APIRouter()


@router.get("/history", response_model=PredictionHistoryResponse)
def history_endpoint(
    search: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_history(db, search, page, page_size)
