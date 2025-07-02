from datetime import datetime, timezone
from sqlmodel import Session, select
from fastapi import HTTPException, status

from ..models.user import User, UserUpdate


class UserService:
    def __init__(self, session: Session):
        self.session = session

    def get_user(self, user_id: int) -> User | None:
        """Get user by ID"""
        return self.session.get(User, user_id)

    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        """Update user profile"""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update only provided fields
        update_data = user_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update_password(self, user_id: int, new_hashed_password: str) -> None:
        """Update user's password"""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.hashed_password = new_hashed_password
        user.updated_at = datetime.now(timezone.utc)

        self.session.add(user)
        self.session.commit()

    def delete_user(self, user_id: int) -> None:
        """Delete user account"""
        user = self.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        self.session.delete(user)
        self.session.commit()
