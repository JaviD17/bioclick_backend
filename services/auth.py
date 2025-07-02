from datetime import timedelta, datetime, timezone
import secrets
from sqlmodel import Session, select
from fastapi import HTTPException, status

from ..models.user import User, UserCreate
from ..models.auth import (
    Token,
    UserLogin,
    UserRegister,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetToken,
)
from ..utils.security import verify_password, get_password_hash, create_access_token
from ..config import settings
from .email import EmailService


class AuthService:
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_username(self, username: str) -> User | None:
        """Get user by username"""
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()

    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email"""
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()

    def authenticate_user(self, username: str, password: str) -> User | None:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_user(self, user_register: UserRegister) -> User:
        """Create a new user"""
        # Check if username already exists
        if self.get_user_by_username(user_register.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # Check if email already exists
        if self.get_user_by_email(user_register.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create user with hashed password
        user_create = UserCreate(
            username=user_register.username,
            email=user_register.email,
            full_name=user_register.full_name,
            password=user_register.password,
        )

        user_data = user_create.model_dump()
        user_data["hashed_password"] = get_password_hash(user_register.password)

        new_user = User(**user_data)
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)

        # Send welcome email
        try:
            EmailService.send_welcome_email(new_user.email, new_user.username)
        except Exception as e:
            # Log error but don't fail user creation
            print(f"Failed to send welcome email: {e}")

        return new_user

    def login_user(self, user_login: UserLogin) -> Token:
        """ "Login user and return access token"""
        user = self.authenticate_user(user_login.username, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token)

    def request_password_reset(self, reset_request: PasswordResetRequest) -> dict:
        """Generate password reset token and send email"""
        user = self.get_user_by_email(reset_request.email)
        if not user:
            # Don't reveal if email exists for security
            return {"message": "If the email exists, a reset link has been sent"}

        # Generate secure token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.password_reset_expire_minutes
        )

        # Save token to database
        db_token = PasswordResetToken(
            user_id=user.id, token=reset_token, expires_at=expires_at
        )
        self.session.add(db_token)
        self.session.commit()

        # Send reset email
        try:
            EmailService.send_password_reset_email(
                user.email, user.username, reset_token
            )
        except Exception as e:
            print(f"Failed to send password reset email: {e}")

        return {"message": "If the email exists, a reset link has been sent"}

    def reset_password(self, reset_confirm: PasswordResetConfirm) -> dict:
        """Reset password using token"""
        # Find valid token
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token == reset_confirm.token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc),
        )
        db_token = self.session.exec(statement).first()

        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )

        # Get user
        user = self.session.get(User, db_token.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update password
        user.hashed_password = get_password_hash(reset_confirm.new_password)
        user.updated_at = datetime.now(timezone.utc)

        # Mark token as used
        db_token.is_used = True

        self.session.commit()

        return {"message": "Password reset successfully"}
