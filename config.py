from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database URL
    database_url: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # App
    app_name: str = "BioTap"
    debug: bool = False

    # Email Settings
    resend_api_key: str
    from_email: str = "onboarding@resend.dev"
    frontend_url: str = "http://localhost:3000"

    # Email Feature Flags
    send_welcome_emails: bool = True
    send_analytics_emails: bool = True

    # Password Reset
    password_reset_expire_minutes: int = 30

    # CORS Origins (production-ready)
    cors_origins: str = (
        "http://localhost:3000,http://localhost:5173,https://yourdomain.com,https://www.yourdomain.com",
    )

    # Trusted hosts for production
    allowed_hosts: str = (
        "localhost,127.0.0.1,yourdomain.com,www.yourdomain.com,*.vercel.app"
    )

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Production environment detection
    environment: str = "development"

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Convert allowed hosts string to list"""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @property
    def is_production(self) -> bool:
        return self.environment == "production" or not self.debug


settings = Settings()
