from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session
from datetime import datetime
from ..database import engine
from ..services.email_scheduler import EmailScheduler
import atexit


def create_scheduler():
    """Create and configure the background scheduler"""
    scheduler = BackgroundScheduler()

    # Add weekly analytics email job (every Monday at 9 AM)
    scheduler.add_job(
        func=send_weekly_analytics_job,
        trigger=CronTrigger(day_of_week="mon", hour=9, minute=0),
        id="weekly_analytics_emails",
        name="Send Weekly Analytics Emails",
        replace_existing=True,
    )

    # Add a test job that runs every hour (remove in production)
    scheduler.add_job(
        func=test_scheduler_job,
        trigger=CronTrigger(minute=0),  # Every hour at minute 0
        id="test_scheduler",
        name="Test Scheduler Health",
        replace_existing=True,
    )

    return scheduler


def send_weekly_analytics_job():
    """Job function to send weekly analytics emails"""
    try:
        with Session(engine) as session:
            result = EmailScheduler.send_weekly_analytics_emails(session)
            print(f"📊 Weekly analytics job result: {result}")
    except Exception as e:
        print(f"❌ Weekly analytics job failed: {e}")


def test_scheduler_job():
    """Test job to verify scheduler is working"""
    print(f"⏰ Scheduler health check at {datetime.now()}")


# Global scheduler instance
scheduler = None


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    if scheduler is None:
        scheduler = create_scheduler()
        scheduler.start()
        print("🚀 Background scheduler started")

        # Shut down the scheduler when exiting the app
        atexit.register(lambda: scheduler.shutdown())


def stop_scheduler():
    """Stop the background scheduler"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        print("🛑 Background scheduler stopped")
