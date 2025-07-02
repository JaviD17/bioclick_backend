from sqlmodel import Field, SQLModel
from pydantic import EmailStr
from datetime import datetime, timezone


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(SQLModel):
    username: str | None = None


class UserLogin(SQLModel):
    username: str
    password: str


class UserRegister(SQLModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None


class PasswordResetRequest(SQLModel):
    email: EmailStr


class PasswordResetConfirm(SQLModel):
    token: str
    new_password: str


class PasswordResetToken(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    token: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    is_used: bool = Field(default=False)
