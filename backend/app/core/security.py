from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(...)
) -> User:

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    user = db.get(User, token)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return user