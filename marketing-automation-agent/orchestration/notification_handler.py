"""Email and Slack notification handler."""

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Sends success and error notifications via email and/or Slack."""

    def __init__(
        self,
        notification_email: Optional[str] = None,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_username: Optional[str] = None,
        smtp_password: Optional[str] = None,
        slack_webhook_url: Optional[str] = None,
        sender_name: str = "Marketing Automation Agent",
    ):
        self.notification_email = notification_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.slack_webhook_url = slack_webhook_url
        self.sender_name = sender_name

    def send_success_summary(self, posts: List[Dict]):
        """Notify that the daily run completed successfully."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"✓ Marketing Agent Success — {date_str}"
        topics = "\n".join(f"  • {p.get('topic_title', 'Unknown')}" for p in posts)
        body = (
            f"Marketing automation completed successfully!\n\n"
            f"Posts published: {len(posts)}\n"
            f"Topics:\n{topics}\n\n"
            f"Check LinkedIn to review published posts."
        )
        self._send(subject, body, color="#36a64f")

    def send_error_alert(self, error_message: str):
        """Notify about a workflow failure."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"✗ Marketing Agent Error — {date_str}"
        body = (
            f"Marketing automation encountered an error:\n\n"
            f"{error_message}\n\n"
            f"Check logs at: data/logs/{datetime.now().strftime('%Y%m%d')}.log"
        )
        self._send(subject, body, color="#ff0000")

    def send_preview_summary(self, posts: List[Dict]):
        """Notify that a preview run completed (no LinkedIn posting)."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"ℹ Marketing Agent Preview — {date_str}"
        topics = "\n".join(f"  • {p.get('topic_title', 'Unknown')}" for p in posts)
        body = (
            f"Preview run completed (posts were NOT published to LinkedIn).\n\n"
            f"Generated posts: {len(posts)}\n"
            f"Topics:\n{topics}\n"
        )
        self._send(subject, body, color="#439fe0")

    def _send(self, subject: str, body: str, color: str = "#36a64f"):
        """Send via email and/or Slack."""
        if self.notification_email and self.smtp_username and self.smtp_password:
            self._send_email(subject, body)
        if self.slack_webhook_url:
            self._send_slack(subject, body, color)

    def _send_email(self, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{self.sender_name} <{self.smtp_username}>"
            msg["To"] = self.notification_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.smtp_username, self.notification_email, msg.as_string())

            logger.info(f"Email notification sent to {self.notification_email}")
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def _send_slack(self, subject: str, body: str, color: str):
        try:
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": subject,
                        "text": body,
                        "footer": self.sender_name,
                        "ts": int(datetime.now().timestamp()),
                    }
                ]
            }
            resp = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Slack notification sent")
            else:
                logger.error(f"Slack notification failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
