from datetime import datetime

from pydantic import BaseModel


class PredictionHistoryItem(BaseModel):
    id: int
    name: str
    phone: str
    prediction: str
    confidence: float
    timestamp: datetime


class PredictionHistoryResponse(BaseModel):
    items: list[PredictionHistoryItem]
    total: int
    page: int
    page_size: int
