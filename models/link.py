from sqlmodel import Field, SQLModel
from datetime import datetime, timezone
from pydantic import HttpUrl, field_validator


class LinkBase(SQLModel):
    title: str = Field(index=True, max_length=100)
    url: str = Field(max_length=2000)

    # Using this because -> SQLModel does not know how to store url: HttpUrl = Field(max_length=2000) in the database
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format"""
        # This will raise validation if invalid URL
        HttpUrl(v)
        return v

    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)
    display_order: int = Field(default=0)
    icon: str | None = Field(default=None, max_length=50)


class Link(LinkBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    click_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)

    # Foreign key to user
    user_id: int = Field(foreign_key="user.id")


class LinkCreate(LinkBase):
    pass  # user_id will be set from authenticated user


class LinkUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=100)
    url: str | None = Field(default=None, max_length=2000)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None
    display_order: int | None = None
    icon: str | None = Field(default=None, max_length=50)
    updated_at: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate URL format if provided"""
        if v is not None:  # Only validate if URL is provided
            HttpUrl(v)  # This will raise a ValidationError if invalid
        return v


class LinkPublic(LinkBase):
    id: int
    click_count: int
    created_at: datetime
    updated_at: datetime | None
    user_id: int
