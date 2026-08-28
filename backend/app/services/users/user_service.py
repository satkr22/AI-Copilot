from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister, UserLogin


class UserService:

    def __init__(self, db: Session):
        self.db = db

    def register(self, data: UserRegister) -> User:

        existing = (
            self.db.query(User)
            .filter(User.email == data.email)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )

        user = User(
            name=data.name,
            email=data.email,
            created_at=datetime.now(timezone.utc)
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def login(self, data: UserLogin) -> User:

        user = (
            self.db.query(User)
            .filter(User.email == data.email)
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        return user

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)