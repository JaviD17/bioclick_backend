from fastapi import APIRouter, HTTPException, status

from ..models.user import UserPublic, UserUpdate, UserPasswordChange
from ..models.link import LinkPublic
from ..dependencies import CurrentActiveUser
from ..services.user import UserService
from ..services.link import LinkService
from ..dependencies import SessionDep
from ..utils.security import verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserPublic)
async def get_current_user_profile(current_user: CurrentActiveUser):
    """Get current user's profile"""
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_current_user_profile(
    user_update: UserUpdate, current_user: CurrentActiveUser, session: SessionDep
):
    """Update current user's profile"""
    user_service = UserService(session)
    return user_service.update_user(current_user.id, user_update)


@router.post("/change-password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: CurrentActiveUser,
    session: SessionDep,
):
    """Change user password"""
    # Verify current password
    if not verify_password(
        password_data.current_password, current_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Hash new password
    new_hashed_password = get_password_hash(password_data.new_password)

    # Update user password using UserService
    user_service = UserService(session)
    user_service.update_password(current_user.id, new_hashed_password)

    return {"message": "Password changed successfuly"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    current_user: CurrentActiveUser, session: SessionDep
):
    """Delete current user's account"""
    user_service = UserService(session)
    user_service.delete_user(current_user.id)


@router.get("/me/links", response_model=list[LinkPublic])
async def get_current_user_links(current_user: CurrentActiveUser, session: SessionDep):
    """Get all links for current user"""
    link_service = LinkService(session)
    return link_service.get_user_links(current_user.id)
