from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user

router = APIRouter()


@router.post("/user", response_model=UserRead)
def create_user_endpoint(payload: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, payload.name, payload.phone)
