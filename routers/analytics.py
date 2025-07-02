from fastapi import APIRouter, Query

try:
    from ..models.analytics import AnalyticsResponse, GeographicResponse
    from ..dependencies import CurrentActiveUser, SessionDep
    from ..services.analytics import AnalyticsService
except ImportError:
    from models.analytics import AnalyticsResponse, GeographicResponse
    from dependencies import CurrentActiveUser, SessionDep
    from services.analytics import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/", response_model=AnalyticsResponse)
async def get_user_analytics(
    current_user: CurrentActiveUser,
    session: SessionDep,
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
):
    """Get comprehensive analytics for the current user"""
    analytics_service = AnalyticsService(session)
    return analytics_service.get_analytics(current_user.id, days)


@router.get("/geographic", response_model=GeographicResponse)
async def get_geographic_analytics(
    current_user: CurrentActiveUser,
    session: SessionDep,
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
):
    """Get geographic analytics fro the current user"""
    analytics_service = AnalyticsService(session)
    return analytics_service.get_geographic_analytics(current_user.id, days)


@router.get("/test-geo")
async def test_geolocation(
    session: SessionDep,
    ip: str = Query(description="IP address to test"),
):
    """Test IP geolocation"""
    analytics_service = AnalyticsService(session)
    country = analytics_service._get_country_from_ip(ip)
    return {"ip": ip, "country": country}
