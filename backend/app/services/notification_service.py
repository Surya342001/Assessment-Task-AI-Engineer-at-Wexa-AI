
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import structlog

from app.config import settings

logger = structlog.get_logger(__name__)


class NotificationService:
    async def send_invitation_email(
        self,
        to_email: str,
        org_name: str,
        invite_link: str,
    ) -> None:
        subject = f"You're invited to join {org_name} on Analytics Platform"
        body = f"""
        <html><body>
        <h2>You've been invited to {org_name}</h2>
        <p>Click the link below to accept your invitation:</p>
        <a href="{invite_link}">Accept Invitation</a>
        <p>This link expires in 7 days.</p>
        </body></html>
        """
        await self._send_email(to_email=to_email, subject=subject, html_body=body)

    async def send_alert_notification(
        self,
        channels: list[dict[str, Any]],
        alert_name: str,
        triggered_value: float,
        threshold: float,
        message: str,
    ) -> list[dict[str, Any]]:
        sent = []
        for channel in channels:
            channel_type = channel.get("type")
            try:
                if channel_type == "email":
                    email = channel.get("config", {}).get("email")
                    if email:
                        await self._send_alert_email(email, alert_name, message)
                        sent.append({"type": "email", "target": email, "status": "sent"})
                elif channel_type == "webhook":
                    url = channel.get("config", {}).get("url")
                    if url:
                        await self._send_webhook(url, alert_name, triggered_value, message)
                        sent.append({"type": "webhook", "target": url, "status": "sent"})
                elif channel_type == "in_app":
                    sent.append({"type": "in_app", "status": "queued"})
            except Exception as e:
                logger.error("notification_failed", channel_type=channel_type, error=str(e))
                sent.append({"type": channel_type, "status": "failed", "error": str(e)})
        return sent

    async def _send_alert_email(
        self, to_email: str, alert_name: str, message: str
    ) -> None:
        subject = f"[Alert Triggered] {alert_name}"
        body = f"<h3>Alert: {alert_name}</h3><p>{message}</p>"
        await self._send_email(to_email=to_email, subject=subject, html_body=body)

    async def _send_webhook(
        self, url: str, alert_name: str, triggered_value: float, message: str
    ) -> None:
        import httpx
        payload = {
            "text": f"*Alert Triggered*: {alert_name}\n{message}",
            "alert_name": alert_name,
            "triggered_value": triggered_value,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

    async def _send_email(
        self, to_email: str, subject: str, html_body: str
    ) -> None:
        if not settings.SMTP_USER:
            logger.warning("smtp_not_configured", to=to_email, subject=subject)
            return

        try:
            import aiosmtplib

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
            message["To"] = to_email
            message.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )
            logger.info("email_sent", to=to_email, subject=subject)
        except Exception as e:
            logger.error("email_send_failed", to=to_email, error=str(e))
            raise
