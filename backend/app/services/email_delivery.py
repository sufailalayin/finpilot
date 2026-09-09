import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


async def send_otp_email(
    *,
    to_email: str,
    code: str,
    purpose: str,
) -> None:
    subject = (
        "Verify your FinPilot email"
        if purpose == "signup"
        else "Reset your FinPilot password"
    )
    action = (
        "verify your email address"
        if purpose == "signup"
        else "reset your password"
    )
    body = (
        f"Your FinPilot verification code is: {code}\n\n"
        f"Use this code to {action}. "
        f"It expires in {settings.otp_expiry_minutes} minutes.\n\n"
        "If you did not request this code, you can ignore this email."
    )

    if settings.email_delivery_mode.lower() == "log":
        logger.warning(
            "FINPILOT OTP delivery mode=log recipient=%s purpose=%s code=%s",
            to_email,
            purpose,
            code,
        )
        return

    if settings.email_delivery_mode.lower() != "smtp":
        raise EmailDeliveryError("Unsupported email delivery mode")

    if not settings.smtp_host or not settings.smtp_from_email:
        raise EmailDeliveryError("SMTP email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = (
        f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        if settings.smtp_from_name
        else settings.smtp_from_email
    )
    message["To"] = to_email
    message.set_content(body)

    def _send() -> None:
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
                if settings.smtp_use_tls:
                    client.starttls()
                if settings.smtp_username:
                    client.login(settings.smtp_username, settings.smtp_password)
                client.send_message(message)
        except Exception as exc:
            raise EmailDeliveryError("Unable to send verification email") from exc

    await asyncio.to_thread(_send)
