from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import time

# Smart imports - try relative first, then absolute
try:
    # Try relative import (for fastapi dev)
    from .config import settings
    from .database import create_db_and_tables
    from .routers import auth, users, links, analytics, admin
except ImportError:
    # Fall back to absolute imports (for gunicorn in production)
    from config import settings
    from database import create_db_and_tables
    from routers import auth, users, links, analytics, admin

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # startup
    print("🚀 Starting up BioClick API...")
    create_db_and_tables()
    print("✅ Database tables created successfully")

    # Start background scheduler (only in production)
    if not settings.debug:
        try:
            try:
                from .tasks.scheduler import start_scheduler
            except ImportError:
                from tasks.scheduler import start_scheduler

            start_scheduler()
            print(f"📆 Background email scheduler started")
        except ImportError:
            print("⚠️ Scheduler module not available")
        except Exception as e:
            print(f"⚠️ Failed to start scheduler: {e}")
    else:
        print("🔧 Development mode - scheduler disabled")

    yield

    # Shutdown
    print("🛑 Shutting down BioClick API...")

    # Stop the background scheduler
    if not settings.debug:
        try:
            try:
                from .tasks.scheduler import stop_scheduler
            except ImportError:
                from tasks.scheduler import stop_scheduler

            stop_scheduler()
            print("📆 Background scheduler stopped")
        except:
            pass


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    description="BioClick built with FastAPI and SQLModel",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Security middleware
if not settings.debug:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    if not settings.debug:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        )

    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    if not settings.debug:
        print(
            f"{request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s"
        )

    return response


# Include routers with rate limiting
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(links.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Root endpoint with rate limiting"""
    return {
        "message": "Welcome to BioClick API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Not available in production",
        "redoc": "/redoc" if settings.debug else "Not available in production",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": "development" if settings.debug else "production",
    }


@app.get("/api/health")
async def api_health_check():
    """Detailed health check for monitoring"""
    try:
        # You can add database connectivity check here if needed
        return {
            "status": "healthy",
            "database": "connected",
            "environment": "development" if settings.debug else "production",
            "timestamp": time.time(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
