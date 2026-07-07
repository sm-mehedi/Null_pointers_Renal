from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.user import User


def list_history(db: Session, search: str | None, page: int, page_size: int):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    base = select(Prediction, User).join(User, Prediction.user_id == User.id)
    count_query = select(func.count(Prediction.id)).join(User, Prediction.user_id == User.id)

    if search:
        term = f"%{search.strip()}%"
        condition = or_(User.name.ilike(term), User.phone.ilike(term))
        base = base.where(condition)
        count_query = count_query.where(condition)

    total = db.scalar(count_query) or 0
    rows = db.execute(
        base.order_by(Prediction.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        {
            "id": prediction.id,
            "name": user.name,
            "phone": user.phone,
            "prediction": prediction.prediction,
            "confidence": prediction.confidence,
            "timestamp": prediction.timestamp,
        }
        for prediction, user in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
