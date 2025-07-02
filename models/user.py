from sqlmodel import Field, SQLModel
from datetime import datetime, timezone
from pydantic import EmailStr


class UserBase(SQLModel):
    username: str = Field(index=True, min_length=3, max_length=50)
    email: EmailStr = Field(index=True)
    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=100)


class UserUpdate(SQLModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class UserPasswordChange(SQLModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=100)


class UserPublic(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None
