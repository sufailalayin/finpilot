import asyncio
import logging
import smtplib

import httpx
from email.message import EmailMessage

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailDeliveryError(RuntimeError):
    pass


async def _send_resend(
    *,
    to_email: str,
    subject: str,
    body: str,
) -> None:
    if not settings.resend_api_key or not settings.resend_from_email:
        raise EmailDeliveryError("Resend email delivery is not configured")

    sender = (
        f"{settings.resend_from_name} <{settings.resend_from_email}>"
        if settings.resend_from_name
        else settings.resend_from_email
    )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": sender,
                    "to": [to_email],
                    "subject": subject,
                    "text": body,
                },
            )
    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Unable to reach email provider") from exc

    if response.status_code < 200 or response.status_code >= 300:
        raise EmailDeliveryError("Email provider rejected the message")


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

    mode = settings.email_delivery_mode.lower()

    if mode == "log":
        logger.warning(
            "FINPILOT OTP delivery mode=log recipient=%s purpose=%s code=%s",
            to_email,
            purpose,
            code,
        )
        return

    if mode == "resend":
        await _send_resend(
            to_email=to_email,
            subject=subject,
            body=body,
        )
        return

    if mode != "smtp":
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



async def send_test_email(*, to_email: str) -> None:
    subject = "FinPilot email delivery test"
    body = (
        "FinPilot email delivery is configured correctly.\n\n"
        "This message was sent from the FinPilot Admin Console."
    )
    mode = settings.email_delivery_mode.lower()

    if mode == "resend":
        await _send_resend(
            to_email=to_email,
            subject=subject,
            body=body,
        )
        return

    if mode == "smtp":
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
                with smtplib.SMTP(
                    settings.smtp_host,
                    settings.smtp_port,
                    timeout=15,
                ) as client:
                    if settings.smtp_use_tls:
                        client.starttls()
                    if settings.smtp_username:
                        client.login(
                            settings.smtp_username,
                            settings.smtp_password,
                        )
                    client.send_message(message)
            except Exception as exc:
                raise EmailDeliveryError(
                    "Unable to send test email"
                ) from exc

        await asyncio.to_thread(_send)
        return

    raise EmailDeliveryError("Production email delivery is not configured")
