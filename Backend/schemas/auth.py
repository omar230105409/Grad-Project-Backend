from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.errors import AppError
from app.models import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.services import security


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def register_user(db: Session, data: RegisterRequest) -> User:
    if get_user_by_email(db, data.email):
        raise AppError(409, "EMAIL_ALREADY_REGISTERED", "This email is already registered.")
    user = User(
        email=data.email,
        password_hash=security.hash_password(data.password),
        full_name=data.full_name,
        timezone=data.timezone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
    if not user or not security.verify_password(password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    return TokenResponse(
        access_token=security.create_access_token(user.id),
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )