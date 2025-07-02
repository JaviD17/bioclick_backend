from sqlmodel import Field, SQLModel
from datetime import datetime, timezone


class ClickEventBase(SQLModel):
    """Base model for click tracking"""

    ip_address: str | None = Field(default=None, max_length=45)  # Support IPv6
    user_agent: str | None = Field(default=None, max_length=500)
    referer: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=2)  # ISO country code
    device_type: str | None = Field(
        default=None, max_length=20
    )  # mobile, desktop, tablet
    browser: str | None = Field(default=None, max_length=50)


class ClickEvent(ClickEventBase, table=True):
    """Database model for click events"""

    id: int | None = Field(default=None, primary_key=True)
    link_id: int = Field(foreign_key="link.id")
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClickEventCreate(ClickEventBase):
    """Model for creating click events"""

    link_id: int


class DailyStats(SQLModel):
    """Daily aggregated statistics"""

    date: str
    clicks: int


class LinkStats(SQLModel):
    """Link performance statistics"""

    link_id: int
    title: str
    clicks: int
    percentage: float


class DeviceStats(SQLModel):
    """Device type statistics"""

    device_type: str
    count: int
    percentage: float


class CountryStats(SQLModel):
    """Country-Level analytics"""

    country_code: str
    country_name: str
    clicks: int
    percentage: float
    unique_visitors: int


class CityStats(SQLModel):
    """City-level analytics"""

    city: str
    country_code: str
    country_name: str
    clicks: int
    percentage: float


class GeographicResponse(SQLModel):
    """Geographic analytics response"""

    total_countries: int
    top_countries: list[CountryStats]
    city_breakdown: list[CityStats]
    geographic_trends: list[DailyStats]


class AnalyticsResponse(SQLModel):
    """Complete analytics response"""

    total_clicks: int
    unique_visitors: int
    daily_stats: list[DailyStats]
    top_links: list[LinkStats]
    device_stats: list[DeviceStats]
    growth_percentage: float
