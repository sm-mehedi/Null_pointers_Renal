from sqlalchemy.orm import Session

from app.models.user import User
from app.utils.validators import validate_phone


def create_user(db: Session, name: str, phone: str) -> User:
    user = User(name=name.strip(), phone=validate_phone(phone))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
