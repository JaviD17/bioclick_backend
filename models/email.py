from sqlmodel import Field, SQLModel
from datetime import datetime, timezone
from enum import Enum


class EmailType(str, Enum):
    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    ANALYTICS_SUMMARY = "analytics_summary"


class EmailLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    email_type: EmailType
    recipient_email: str = Field(index=True)
    subject: str
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = Field(default=True)
    error_message: str | None = Field(default=None)

    # For analytics emails specifically
    analytics_period_start: datetime | None = Field(default=None)
    analytics_period_end: datetime | None = Field(default=None)
