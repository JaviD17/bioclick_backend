from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from ..database import get_session
from ..services.email_scheduler import EmailScheduler

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/send-weekly-analytics")
async def trigger_weekly_analytics(session: Session = Depends(get_session)):
    """Manually trigger weekly analytics emails (for testing)"""
    try:
        result = EmailScheduler.send_weekly_analytics_emails(session)
        return {
            "message": "Weekly analytics emails triggered successfully",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send weekly analytics: {str(e)}",
        )


@router.get("/email-stats")
async def get_email_stats(days: int = 30, session: Session = Depends(get_session)):
    """Get email sending statistics"""
    try:
        stats = EmailScheduler.get_analytics_email_stats(session, days)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email stats: {str(e)}",
        )
