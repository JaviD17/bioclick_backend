from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

try:
    from ..models.link import LinkCreate, LinkUpdate, LinkPublic
    from ..dependencies import CurrentActiveUser, SessionDep
    from ..services.link import LinkService
    from ..services.analytics import AnalyticsService
    from ..utils.helpers import get_client_ip
except ImportError:
    from models.link import LinkCreate, LinkUpdate, LinkPublic
    from dependencies import CurrentActiveUser, SessionDep
    from services.link import LinkService
    from services.analytics import AnalyticsService
    from utils.helpers import get_client_ip


router = APIRouter(prefix="/links", tags=["links"])
limiter = Limiter(key_func=get_remote_address)


# Protected endpoints (authenticated users)
@router.post("/", response_model=LinkPublic, status_code=status.HTTP_201_CREATED)
async def create_link(
    link_create: LinkCreate, current_user: CurrentActiveUser, session: SessionDep
):
    """Create a new link"""
    link_service = LinkService(session)
    return link_service.create_link(link_create, current_user.id)


@router.get("/", response_model=list[LinkPublic])
async def get_user_links(
    current_user: CurrentActiveUser,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """Get all links for current user with pagination"""
    link_service = LinkService(session)
    return link_service.get_user_links(current_user.id, skip=skip, limit=limit)


@router.get("/{link_id}", response_model=LinkPublic)
async def get_link(link_id: int, current_user: CurrentActiveUser, session: SessionDep):
    """Get a specific link"""
    link_service = LinkService(session)
    link = link_service.get_link(link_id)

    # Check if user owns this link
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this link",
        )
    return link


@router.patch("/{link_id}", response_model=LinkPublic)
async def update_link(
    link_id: int,
    link_update: LinkUpdate,
    current_user: CurrentActiveUser,
    session: SessionDep,
):
    """Update a specific link"""
    link_service = LinkService(session)

    # Check if user owns this link
    link = link_service.get_link(link_id)
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this link",
        )

    return link_service.update_link(link_id, link_update)


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: int, current_user: CurrentActiveUser, session: SessionDep
):
    """Delete a specific link"""
    link_service = LinkService(session)

    # Check if user owns this link
    link = link_service.get_link(link_id)
    if link.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this link",
        )
    link_service.delete_link(link_id)


# Public endpoints with rate limiting
@router.post("/{link_id}/click", response_model=LinkPublic)
@limiter.limit("100/minute")  # Limit clicks to 100 per minute
async def track_click(request: Request, link_id: int, session: SessionDep):
    """Track a click on a link (public endpoint) with rate limiting"""
    link_service = LinkService(session)
    return link_service.increment_click_count(link_id)


@router.get("/{link_id}/redirect")
@limiter.limit("100/minute")  # Limit redirects to 100 per minute
async def click_and_redirect(request: Request, link_id: int, session: SessionDep):
    """Track click and redirect to the actual URL (public endpoint) with rate limiting"""
    link_service = LinkService(session)
    analytics_service = AnalyticsService(session)

    # Get the link
    link = link_service.get_link(link_id)

    if not link.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Link is not active"
        )

    # Extract request metadata
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    # Track the click with metadata
    analytics_service.track_click(
        link_id=link_id, ip_address=ip_address, user_agent=user_agent, referer=referer
    )

    # Also increment the simple click counter
    link_service.increment_click_count(link_id)

    return RedirectResponse(url=str(link.url), status_code=status.HTTP_302_FOUND)


@router.get("/public/{username}", response_model=list[LinkPublic])
@limiter.limit("30/minute")  # Limit public user profile to 30 requests per minute
async def get_public_user_profile(request: Request, username: str, session: SessionDep):
    """Get public view of user's active links (public endpoint) with rate limiting"""
    link_service = LinkService(session)
    return link_service.get_public_user_links(username)
