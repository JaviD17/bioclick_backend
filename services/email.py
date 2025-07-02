import resend
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from ..config import settings
from ..models.email import EmailLog, EmailType

resend.api_key = settings.resend_api_key


class EmailService:
    @staticmethod
    def send_email(
        to: str,
        subject: str,
        html_content: str,
        from_email: str = settings.from_email,
        session: Session | None = None,
        user_id: int | None = None,
        email_type: EmailType | None = None,
    ) -> Dict[str, Any]:
        """Send an email using Resend with optional logging"""
        try:
            response = resend.Emails.send(
                {"from": from_email, "to": to, "subject": subject, "html": html_content}
            )

            # Log the email if session provided
            if session and user_id and email_type:
                email_log = EmailLog(
                    user_id=user_id,
                    email_type=email_type,
                    recipient_email=to,
                    subject=subject,
                    success=True,
                )
                session.add(email_log)
                session.commit()

            return {"success": True, "data": response}
        except Exception as e:
            # Log the error if session provided
            if session and user_id and email_type:
                email_log = EmailLog(
                    user_id=user_id,
                    email_type=email_type,
                    recipient_email=to,
                    subject=subject,
                    success=False,
                    error_message=str(e),
                )
                session.add(email_log)
                session.commit()

            return {"success": False, "error": str(e)}

    @staticmethod
    def send_welcome_email(
        user_email: str,
        username: str,
        session: Session | None = None,
        user_id: int | None = None,
    ) -> Dict[str, Any]:
        """Send welcome email to new users"""
        # Feature flag check
        if not settings.send_welcome_emails:
            return {"success": True, "message": "Welcome emails disabled"}

        subject = f"Welcome to {settings.app_name}! 🎉"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; }}
                .content {{ padding: 40px; }}
                .welcome-text {{ font-size: 18px; color: #374151; margin-bottom: 30px; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .features {{ background-color: #f8fafc; padding: 30px; border-radius: 8px; margin: 30px 0; }}
                .feature {{ margin-bottom: 15px; }}
                .footer {{ text-align: center; padding: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to {settings.app_name}!</h1>
                </div>
                <div class="content">
                    <p class="welcome-text">Hi <strong>{username}</strong>,</p>
                    
                    <p>🎉 <strong>Your account has been created successfully!</strong> You're now part of thousands of creators building their online presence with our platform.</p>
                    
                    <div class="features">
                        <h3>What you can do now:</h3>
                        <div class="feature">✨ <strong>Create unlimited links</strong> to showcase your content</div>
                        <div class="feature">📊 <strong>Track analytics</strong> to see how your links perform</div>
                        <div class="feature">🎨 <strong>Customize your page</strong> with themes and icons</div>
                        <div class="feature">⚡ <strong>Real-time updates</strong> with our optimistic UI</div>
                    </div>
                    
                    <p>Ready to get started? Access your dashboard and create your first link!</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.frontend_url}/dashboard" class="cta-button">
                            Go to Dashboard →
                        </a>
                    </div>
                    
                    <p>If you have any questions, just reply to this email. We're here to help!</p>
                    
                    <p>Best regards,<br>The {settings.app_name} Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {user_email}</p>
                    <p>© 2025 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(
            user_email,
            subject,
            html_content,
            session=session,
            user_id=user_id,
            email_type=EmailType.WELCOME,
        )

    @staticmethod
    def send_password_reset_email(
        user_email: str,
        username: str,
        reset_token: str,
        session: Session | None = None,
        user_id: int | None = None,
    ) -> Dict[str, Any]:
        """Send password reset email"""
        subject = f"Reset your {settings.app_name} password 🔐"
        reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); padding: 40px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; }}
                .content {{ padding: 40px; }}
                .reset-text {{ font-size: 18px; color: #374151; margin-bottom: 30px; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; }}
                .warning {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 20px; margin: 30px 0; }}
                .footer {{ text-align: center; padding: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <p class="reset-text">Hi <strong>{username}</strong>,</p>
                    
                    <p>We received a request to reset your password for your {settings.app_name} account.</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" class="cta-button">
                            Reset Your Password
                        </a>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Important:</strong>
                        <ul>
                            <li>This link will expire in 30 minutes</li>
                            <li>If you didn't request this reset, you can safely ignore this email</li>
                            <li>Never share this link with anyone</li>
                        </ul>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #f3f4f6; padding: 10px; border-radius: 4px; font-family: monospace;">{reset_link}</p>
                    
                    <p>Best regards,<br>The {settings.app_name} Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {user_email}</p>
                    <p>© 2025 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return EmailService.send_email(
            user_email,
            subject,
            html_content,
            session=session,
            user_id=user_id,
            email_type=EmailType.PASSWORD_RESET,
        )

    @staticmethod
    def send_analytics_summary(
        user_email: str,
        username: str,
        analytics_data: Dict[str, Any],
        session: Session | None = None,
        user_id: int | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> Dict[str, Any]:
        """Send weekly analytics summary"""
        # Feature flag check
        if not settings.send_analytics_emails:
            return {"success": True, "message": "Analytics emails disabled"}

        subject = f"📊 Your weekly {settings.app_name} analytics summary"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
                .header {{ background: linear-gradient(135deg, #059669 0%, #047857 100%); padding: 40px; text-align: center; }}
                .header h1 {{ color: white; margin: 0; font-size: 28px; }}
                .content {{ padding: 40px; }}
                .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0; }}
                .stat-card {{ background-color: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }}
                .stat-number {{ font-size: 32px; font-weight: bold; color: #059669; }}
                .stat-label {{ color: #6b7280; font-size: 14px; margin-top: 5px; }}
                .top-links {{ background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 30px 0; }}
                .link-item {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #e5e7eb; }}
                .footer {{ text-align: center; padding: 30px; color: #6b7280; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Weekly Analytics Summary</h1>
                </div>
                <div class="content">
                    <p>Hi <strong>{username}</strong>,</p>
                    
                    <p>Here's how your links performed this week:</p>
                    
                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="stat-number">{analytics_data.get('total_clicks', 0)}</div>
                            <div class="stat-label">Total Clicks</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{analytics_data.get('unique_visitors', 0)}</div>
                            <div class="stat-label">Unique Visitors</div>
                        </div>
                    </div>
                    
                    <div class="top-links">
                        <h3>🔥 Top Performing Links:</h3>
                        {' '.join([f'<div class="link-item"><span>{link["title"]}</span><span> </span><span>{link["clicks"]} clicks</span></div>' for link in analytics_data.get('top_links', [])[:3]])}
                    </div>
                    
                    <p>🚀 <strong>Growth:</strong> Your clicks are {analytics_data.get('growth_percentage', 0):.1f}% compared to last week!</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.frontend_url}/dashboard/analytics" style="display: inline-block; background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold;">
                            View Full Analytics →
                        </a>
                    </div>
                    
                    <p>Keep up the great work!</p>
                    
                    <p>Best regards,<br>The {settings.app_name} Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent to {user_email}</p>
                    <p>© 2025 {settings.app_name}. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        result = EmailService.send_email(
            user_email,
            subject,
            html_content,
            session=session,
            user_id=user_id,
            email_type=EmailType.ANALYTICS_SUMMARY,
        )

        # Add analytics-specifc logging
        if session and user_id and result.get("success"):
            statement = (
                select(EmailLog)
                .where(
                    EmailLog.user_id == user_id,
                    EmailLog.email_type == EmailType.ANALYTICS_SUMMARY,
                )
                .order_by(EmailLog.sent_at.desc())
            )

            email_log = session.exec(statement).first()

            if email_log:
                email_log.analytics_period_start = period_start
                email_log.analytics_period_end = period_end
                session.commit()

        return result
