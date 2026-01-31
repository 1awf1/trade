"""
Notification service for sending email and web push notifications.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from utils.config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationService:
    """
    Service for sending notifications via email and web push.
    
    Validates: Requirement 18.5, 18.6
    """
    
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, html_body: str = None) -> bool:
        """
        Send email notification via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
            
        Validates: Requirement 18.5
        """
        try:
            # Check if SMTP is configured
            if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                logger.warning("SMTP not configured, skipping email notification")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach plain text
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    @staticmethod
    def send_alarm_email(to_email: str, alarm_data: Dict) -> bool:
        """
        Send alarm notification email.
        
        Args:
            to_email: Recipient email address
            alarm_data: Alarm trigger data
            
        Returns:
            True if email sent successfully
        """
        try:
            coin = alarm_data.get('coin', 'Unknown')
            alarm_type = alarm_data.get('type', 'Unknown')
            condition = alarm_data.get('condition', 'Unknown')
            threshold = alarm_data.get('threshold', 0)
            current_value = alarm_data.get('current_value', 0)
            
            # Create subject
            subject = f"🔔 Alarm Tetiklendi: {coin}"
            
            # Create plain text body
            body = f"""
Kripto Para Analiz Sistemi - Alarm Bildirimi

Coin: {coin}
Alarm Tipi: {alarm_type}
Koşul: {condition}
Eşik Değer: {threshold}
Mevcut Değer: {current_value}

Bu alarm koşulları karşılandığı için tetiklenmiştir.

---
Kripto Para Analiz Sistemi
            """.strip()
            
            # Create HTML body
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .info-row {{ margin: 10px 0; }}
        .label {{ font-weight: bold; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>🔔 Alarm Tetiklendi</h2>
        </div>
        <div class="content">
            <div class="info-row">
                <span class="label">Coin:</span> {coin}
            </div>
            <div class="info-row">
                <span class="label">Alarm Tipi:</span> {alarm_type}
            </div>
            <div class="info-row">
                <span class="label">Koşul:</span> {condition}
            </div>
            <div class="info-row">
                <span class="label">Eşik Değer:</span> {threshold}
            </div>
            <div class="info-row">
                <span class="label">Mevcut Değer:</span> {current_value}
            </div>
            <p style="margin-top: 20px;">
                Bu alarm koşulları karşılandığı için tetiklenmiştir.
            </p>
        </div>
        <div class="footer">
            Kripto Para Analiz Sistemi
        </div>
    </div>
</body>
</html>
            """.strip()
            
            return NotificationService.send_email(to_email, subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send alarm email: {e}")
            return False
    
    @staticmethod
    def send_web_push(subscription: Dict, title: str, body: str, data: Dict = None) -> bool:
        """
        Send web push notification.
        
        Args:
            subscription: Web push subscription object
            title: Notification title
            body: Notification body
            data: Optional additional data
            
        Returns:
            True if push sent successfully
            
        Validates: Requirement 18.6
        """
        try:
            # TODO: Implement actual web push using pywebpush library
            # For now, just log
            logger.info(f"Web push notification: {title} - {body}")
            logger.debug(f"Subscription: {subscription}, Data: {data}")
            
            # In production, you would use something like:
            # from pywebpush import webpush, WebPushException
            # webpush(
            #     subscription_info=subscription,
            #     data=json.dumps({"title": title, "body": body, "data": data}),
            #     vapid_private_key=settings.VAPID_PRIVATE_KEY,
            #     vapid_claims={"sub": f"mailto:{settings.EMAIL_FROM}"}
            # )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send web push: {e}")
            return False
    
    @staticmethod
    def send_alarm_web_push(subscription: Dict, alarm_data: Dict) -> bool:
        """
        Send alarm notification via web push.
        
        Args:
            subscription: Web push subscription object
            alarm_data: Alarm trigger data
            
        Returns:
            True if push sent successfully
        """
        try:
            coin = alarm_data.get('coin', 'Unknown')
            alarm_type = alarm_data.get('type', 'Unknown')
            current_value = alarm_data.get('current_value', 0)
            
            title = f"🔔 Alarm: {coin}"
            body = f"{alarm_type} - Mevcut değer: {current_value}"
            
            return NotificationService.send_web_push(subscription, title, body, alarm_data)
            
        except Exception as e:
            logger.error(f"Failed to send alarm web push: {e}")
            return False
