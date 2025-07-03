from sqlmodel import Session, select
from fastapi import HTTPException, status
from datetime import datetime, timezone

try:
    from ..models.link import Link, LinkCreate, LinkUpdate
except ImportError:
    from models.link import Link, LinkCreate, LinkUpdate


class LinkService:
    def __init__(self, session: Session):
        self.session = session

    def get_link(self, link_id: int) -> Link:
        """Get link by ID"""
        link = self.session.get(Link, link_id)
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Link not found"
            )
        return link

    def get_user_links(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[Link]:
        """Get all links for a user with pagination"""
        statement = (
            select(Link)
            .where(Link.user_id == user_id)
            .order_by(Link.display_order, Link.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def create_link(self, link_create: LinkCreate, user_id: int) -> Link:
        """Create new link"""
        link_data = link_create.model_dump()
        link_data["user_id"] = user_id

        new_link = Link(**link_data)
        self.session.add(new_link)
        self.session.commit()
        self.session.refresh(new_link)
        return new_link

    def update_link(self, link_id: int, link_update: LinkUpdate) -> Link:
        """Update a link"""
        link = self.get_link(link_id)

        # Update only provided fields
        update_data = link_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(link, key, value)

        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def delete_link(self, link_id: int) -> None:
        """Delete a link"""
        link = self.get_link(link_id)
        self.session.delete(link)
        self.session.commit()

    def increment_click_count(self, link_id: int) -> Link:
        """Increment click count for a link"""
        link = self.get_link(link_id)

        if not link.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Link is not active"
            )

        link.click_count += 1
        link.updated_at = datetime.now(timezone.utc)

        self.session.add(link)
        self.session.commit()
        self.session.refresh(link)
        return link

    def get_public_user_links(self, username: str) -> list[Link]:
        """Get active links for a user (public view)"""
        try:
            from ..models.user import User
        except ImportError:
            from models.user import User

        statement = select(User).where(User.username == username)
        user = self.session.exec(statement).first()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        statement = (
            select(Link)
            .where(Link.user_id == user.id, Link.is_active == True)
            .order_by(Link.display_order, Link.created_at.desc())
        )
        return list(self.session.exec(statement).all())
