from datetime import datetime, timedelta, timezone
from typing import Dict
from sqlmodel import Session, select, func, and_
import user_agents
import geoip2.database
import geoip2.errors

try:

    from ..models.analytics import (
        ClickEvent,
        ClickEventCreate,
        DailyStats,
        LinkStats,
        DeviceStats,
        CountryStats,
        CityStats,
        GeographicResponse,
        AnalyticsResponse,
    )
    from ..models.link import Link
except ImportError:
    from models.analytics import (
        ClickEvent,
        ClickEventCreate,
        DailyStats,
        LinkStats,
        DeviceStats,
        CountryStats,
        CityStats,
        GeographicResponse,
        AnalyticsResponse,
    )
    from models.link import Link


class AnalyticsService:
    def __init__(self, session: Session):
        self.session = session

    def track_click(
        self,
        link_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
        referer: str | None = None,
    ) -> ClickEvent:
        """Track a click event with metadata"""

        # Parse user agent for device/browser info
        device_type = "unknown"
        browser = "unknown"

        if user_agent:
            ua = user_agents.parse(user_agent)
            if ua.is_mobile:
                device_type = "mobile"
            elif ua.is_tablet:
                device_type = "tablet"
            elif ua.is_pc:
                device_type = "desktop"

            browser = ua.browser.family if ua.browser.family else "unknown"

        # Get country code from IP (you'll need to add GeoIP2 database)
        country = self._get_country_from_ip(ip_address) if ip_address else None

        # Create click event
        click_data = ClickEventCreate(
            link_id=link_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
            country=country,
            device_type=device_type,
            browser=browser,
        )

        click_event = ClickEvent(**click_data.model_dump())
        self.session.add(click_event)
        self.session.commit()
        self.session.refresh(click_event)

        return click_event

    def get_geographic_analytics(
        self, user_id: int, days: int = 30
    ) -> GeographicResponse:
        """Get comprehensive geographic analytics"""

        # Date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # get user's links
        user_links = self.session.exec(
            select(Link).where(Link.user_id == user_id)
        ).all()

        link_ids = [link.id for link in user_links]

        if not link_ids:
            return GeographicResponse(
                total_countries=0,
                top_countries=[],
                city_breakdown=[],
                geographic_trends=[],
            )

        # Get country statistics
        top_countries = self._get_country_stats(link_ids, start_date)

        city_breakdown = self._get_city_stats(link_ids, start_date)

        # Geographic trends over time
        geographic_trends = self._get_geographic_trends(link_ids, start_date, end_date)

        return GeographicResponse(
            total_countries=len(top_countries),
            top_countries=top_countries,
            city_breakdown=city_breakdown,
            geographic_trends=geographic_trends,
        )

    def get_analytics(self, user_id: int, days: int = 30) -> AnalyticsResponse:
        """Get comprehensive analytics for a user"""

        # Date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get user's links
        user_links = self.session.exec(
            select(Link).where(Link.user_id == user_id)
        ).all()

        link_ids = [link.id for link in user_links]

        if not link_ids:
            return AnalyticsResponse(
                total_clicks=0,
                unique_visitors=0,
                daily_stats=[],
                top_links=[],
                device_stats=[],
                growth_percentage=0.0,
            )

        # Total clicks in period
        total_clicks = self.session.exec(
            select(func.count(ClickEvent.id)).where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                )
            )
        ).one()

        # Unique visitors (unique IP addresses)
        unique_visitors = self.session.exec(
            select(func.count(func.distinct(ClickEvent.ip_address))).where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                    ClickEvent.ip_address.is_not(None),
                )
            )
        ).one()

        # Daily statistics
        daily_stats = self._get_daily_stats(link_ids, start_date, end_date)

        # Top Links
        top_links = self._get_top_links(user_links, start_date)

        # Device statistics
        device_stats = self._get_device_stats(link_ids, start_date)

        # Growth calculation (compare to previous period)
        growth_percentage = self._calculate_growth(link_ids, start_date, days)

        return AnalyticsResponse(
            total_clicks=total_clicks,
            unique_visitors=unique_visitors,
            daily_stats=daily_stats,
            top_links=top_links,
            device_stats=device_stats,
            growth_percentage=growth_percentage,
        )

    def _get_daily_stats(
        self, link_ids: list[int], start_date: datetime, end_date: datetime
    ) -> list[DailyStats]:
        """Get daily click statistics"""

        # SQL to group clicks by date
        stmt = (
            select(
                func.date(ClickEvent.clicked_at).label("date"),
                func.count(ClickEvent.id).label("clicks"),
            )
            .where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                    ClickEvent.clicked_at <= end_date,
                )
            )
            .group_by(func.date(ClickEvent.clicked_at))
            .order_by("date")
        )

        results = self.session.exec(stmt).all()

        return [DailyStats(date=str(row.date), clicks=row.clicks) for row in results]

    def _get_top_links(
        self, links: list[Link], start_date: datetime
    ) -> list[LinkStats]:
        """Get top performing links"""

        link_performance = []
        total_clicks = 0

        for link in links:
            # Count clicks for this link in the period
            clicks = self.session.exec(
                select(func.count(ClickEvent.id)).where(
                    and_(
                        ClickEvent.link_id == link.id,
                        ClickEvent.clicked_at >= start_date,
                    )
                )
            ).one()

            total_clicks += clicks
            link_performance.append((link, clicks))

        # Sort by clicks and calculate percentages
        link_performance.sort(key=lambda x: x[1], reverse=True)

        top_links = []
        for link, clicks in link_performance[:5]:  # Top 5
            percentage = (clicks / total_clicks * 100) if total_clicks > 0 else 0
            top_links.append(
                LinkStats(
                    link_id=link.id,
                    title=link.title,
                    clicks=clicks,
                    percentage=round(percentage, 1),
                )
            )

        return top_links

    def _get_device_stats(
        self, link_ids: list[int], start_date: datetime
    ) -> list[DeviceStats]:
        """Get device type statistics"""
        stmt = (
            select(ClickEvent.device_type, func.count(ClickEvent.id).label("count"))
            .where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                    ClickEvent.device_type.is_not(None),
                )
            )
            .group_by(ClickEvent.device_type)
        )

        results = self.session.exec(stmt).all()
        total = sum(row.count for row in results)

        if total == 0:
            return []

        return [
            DeviceStats(
                device_type=row.device_type,
                count=row.count,
                percentage=round(row.count / total * 100, 1),
            )
            for row in results
        ]

    def _calculate_growth(
        self, link_ids: list[int], start_date: datetime, days: int
    ) -> float:
        """Calculate growth percentage compared to previous period"""

        # Previous period
        previous_end = start_date
        previous_start = previous_end - timedelta(days=days)

        # Current period clicks
        current_clicks = self.session.exec(
            select(func.count(ClickEvent.id)).where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                )
            )
        ).one()

        # Previous period clicks
        previous_clicks = self.session.exec(
            select(func.count(ClickEvent.id)).where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= previous_start,
                    ClickEvent.clicked_at < previous_end,
                )
            )
        ).one()

        if previous_clicks == 0:
            return 100.0 if current_clicks > 0 else 0.0

        growth = ((current_clicks - previous_clicks) / previous_clicks) * 100
        return round(growth, 1)

    def _get_country_from_ip(self, ip_address: str) -> str | None:
        """Get country code from IP address using GeoIP2"""
        try:
            with geoip2.database.Reader("./GeoLite2-Country.mmdb") as reader:
                response = reader.country(ip_address)
                return response.country.iso_code
        except (geoip2.errors.AddressNotFoundError, FileNotFoundError, OSError):
            return None

    def _get_country_stats(
        self, link_ids: list[int], start_date: datetime
    ) -> list[CountryStats]:
        """Get country-level statistics"""

        # Get country click counts
        stmt = (
            select(
                ClickEvent.country,
                func.count(ClickEvent.id).label("clicks"),
                func.count(func.distinct(ClickEvent.ip_address)).label(
                    "unique_visitors"
                ),
            )
            .where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                    ClickEvent.country.is_not(None),
                )
            )
            .group_by(ClickEvent.country)
            .order_by(func.count(ClickEvent.id).desc())
        )

        results = self.session.exec(stmt).all()
        total_clicks = sum(row.clicks for row in results)

        # Map country codes to names
        country_names = self._get_country_names()

        country_stats = []
        for row in results:
            percentage = (row.clicks / total_clicks * 100) if total_clicks > 0 else 0
            country_stats.append(
                CountryStats(
                    country_code=row.country,
                    country_name=country_names.get(row.country, row.country),
                    clicks=row.clicks,
                    percentage=round(percentage, 1),
                    unique_visitors=row.unique_visitors,
                )
            )

        return country_stats[:10]  # Top 10 countries

    def _get_city_stats(
        self, link_ids: list[int], start_date: datetime
    ) -> list[CityStats]:
        """Get city-level statistics (placeholder for future enhancement)"""
        # You could enhance this by adding city tracking to your ClickEvent model
        # For now, return empty list
        return []

    def _get_geographic_trends(
        self, link_ids: list[int], start_date: datetime, end_date: datetime
    ) -> list[DailyStats]:
        """Get geographic trends over time"""

        # Daily geographic clicks (only from countries)
        stmt = (
            select(
                func.date(ClickEvent.clicked_at).label("date"),
                func.count(ClickEvent.id).label("clicks"),
            )
            .where(
                and_(
                    ClickEvent.link_id.in_(link_ids),
                    ClickEvent.clicked_at >= start_date,
                    ClickEvent.clicked_at <= end_date,
                    ClickEvent.country.is_not(None),
                )
            )
            .group_by(func.date(ClickEvent.clicked_at))
            .order_by("date")
        )

        results = self.session.exec(stmt).all()
        return [DailyStats(date=str(row.date), clicks=row.clicks) for row in results]

    def _get_country_names(self) -> Dict[str, str]:
        """Map ISO country codes to country names"""
        return {
            "US": "United States",
            "GB": "United Kingdom",
            "CA": "Canada",
            "AU": "Australia",
            "DE": "Germany",
            "FR": "France",
            "IT": "Italy",
            "ES": "Spain",
            "NL": "Netherlands",
            "BR": "Brazil",
            "JP": "Japan",
            "CN": "China",
            "IN": "India",
            "MX": "Mexico",
            "AR": "Argentina",
            "CL": "Chile",
            "CO": "Colombia",
            "PE": "Peru",
            "RU": "Russia",
            "UA": "Ukraine",
            "PL": "Poland",
            "SE": "Sweden",
            "NO": "Norway",
            "DK": "Denmark",
            "FI": "Finland",
            "CH": "Switzerland",
            "AT": "Austria",
            "BE": "Belgium",
            "PT": "Portugal",
            "IE": "Ireland",
            "NZ": "New Zealand",
            "ZA": "South Africa",
            "EG": "Egypt",
            "NG": "Nigeria",
            "KE": "Kenya",
            "MA": "Morocco",
            "TH": "Thailand",
            "VN": "Vietnam",
            "SG": "Singapore",
            "MY": "Malaysia",
            "ID": "Indonesia",
            "PH": "Philippines",
            "KR": "South Korea",
            "TR": "Turkey",
            "SA": "Saudi Arabia",
            "AE": "UAE",
            "IL": "Israel",
            "QA": "Qatar",
            # Add more as needed
        }
