from datetime import datetime, timedelta, timezone
from sqlmodel import Session, select
from typing import Dict, Any

try:
    from ..models.user import User
    from ..models.email import EmailLog, EmailType
    from ..services.analytics import AnalyticsService
    from ..services.email import EmailService
except ImportError:
    from models.user import User
    from models.email import EmailLog, EmailType
    from services.analytics import AnalyticsService
    from services.email import EmailService


class EmailScheduler:
    @staticmethod
    def send_weekly_analytics_emails(session: Session):
        """Send weekly analytics emails to all active users"""
        print(f"🚀 Starting weekly analytics email job at {datetime.now(timezone.utc)}")

        # Calculate the period (last 7 days)
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        # Get all active users
        statement = select(User).where(User.is_active == True)
        users = session.exec(statement).all()

        analytics_service = AnalyticsService(session)
        sent_count = 0
        error_count = 0

        for user in users:
            try:
                # Check if we already sent analytics for this period
                existing_log = session.exec(
                    select(EmailLog).where(
                        EmailLog.user_id == user.id,
                        EmailLog.email_type == EmailType.ANALYTICS_SUMMARY,
                        EmailLog.analytics_period_start >= start_date,
                        EmailLog.success == True,
                    )
                ).first()

                if existing_log:
                    print(f"📧 Skipping {user.email} - already sent for this period")
                    continue

                # Get user's analytics for the past week
                analytics_response = analytics_service.get_analytics(user.id, days=7)

                # Convert the response object to a dictionar
                analytics_data = analytics_response.model_dump()

                # Only send if user has some activity
                if analytics_data.get("total_clicks", 0) > 0:
                    result = EmailService.send_analytics_summary(
                        user.email,
                        user.username,
                        analytics_data,
                        session=session,
                        user_id=user.id,
                        period_start=start_date,
                        period_end=end_date,
                    )

                    if result.get("success"):
                        print(f"✅ Sent weekly analytics to {user.email}")
                        sent_count += 1
                    else:
                        print(
                            f"❌ Failed to send to {user.email}: {result.get('error', 'Unknown error')}"
                        )
                        error_count += 1
                else:
                    print(f"📊 Skipping {user.email} - no activity this week")

            except Exception as e:
                print(f"❌ Failed to send analytics email to {user.email}: {e}")
                error_count += 1
        print(
            f"📊 Weekly analytics job completed: {sent_count} sent, {error_count} errors"
        )
        return {"sent": sent_count, "errors": error_count}

    @staticmethod
    def get_analytics_email_stats(session: Session, days: int = 30) -> Dict[str, Any]:
        """Get statistics about analytics email sending"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        statement = select(EmailLog).where(
            EmailLog.email_type == EmailType.ANALYTICS_SUMMARY,
            EmailLog.sent_at >= cutoff_date,
        )

        logs = session.exec(statement).all()

        total_sent = len([log for log in logs if log.success])
        total_failed = len([log for log in logs if not log.success])

        return {
            "total_sent": total_sent,
            "total_failed": total_failed,
            "success_rate": (
                (total_sent / (total_sent + total_failed)) * 100
                if (total_sent + total_failed) > 0
                else 0
            ),
            "last_sent": max(
                [log.sent_at for log in logs if log.success], default=None
            ),
        }
