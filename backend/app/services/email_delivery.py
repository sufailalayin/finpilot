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


def _otp_html(*, code: str, purpose: str) -> str:
    if purpose == "signup":
        heading = "Verify your email"
        action = "Complete your FinPilot signup"
    elif purpose == "admin_login":
        heading = "Administrator verification"
        action = "Use this code to complete your FinPilot Admin sign-in"
    else:
        heading = "Reset your password"
        action = "Use this code to reset your FinPilot password"
    return f"""<!doctype html>
<html>
  <body style="margin:0;background:#f4f7f6;font-family:Arial,sans-serif;color:#16231f">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 12px">
      <tr><td align="center">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:20px;overflow:hidden;border:1px solid #e4ece8">
          <tr><td style="background:#185A4A;padding:24px 28px;color:#fff;font-size:24px;font-weight:700">FinPilot</td></tr>
          <tr><td style="padding:32px 28px">
            <div style="font-size:24px;font-weight:700;margin-bottom:10px">{heading}</div>
            <div style="font-size:15px;line-height:1.6;color:#53645e;margin-bottom:24px">{action}.</div>
            <div style="font-size:36px;letter-spacing:8px;font-weight:800;text-align:center;padding:18px;border-radius:14px;background:#eef7f3;color:#185A4A">{code}</div>
            <div style="font-size:14px;line-height:1.6;color:#6b7b76;margin-top:24px">
              This code expires in {settings.otp_expiry_minutes} minutes. Never share this code with anyone.
            </div>
            <div style="font-size:13px;line-height:1.6;color:#88958f;margin-top:20px">
              If you did not request this, you can safely ignore this email.
            </div>
          </td></tr>
          <tr><td style="padding:18px 28px;background:#f8fbf9;color:#809089;font-size:12px">FinPilot by Hastron Ventures</td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>"""


async def _send_resend(
    *,
    to_email: str,
    subject: str,
    body: str,
    html: str | None = None,
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
                    **({"html": html} if html else {}),
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
    if purpose == "signup":
        subject = "Verify your FinPilot email"
        action = "verify your email address"
    elif purpose == "admin_login":
        subject = "FinPilot Admin verification code"
        action = "complete your administrator sign-in"
    else:
        subject = "Reset your FinPilot password"
        action = "reset your password"
    body = (
        f"Your FinPilot verification code is: {code}\n\n"
        f"Use this code to {action}. "
        f"It expires in {settings.otp_expiry_minutes} minutes.\n\n"
        "Never share this code with anyone. "
        "If you did not request this code, you can ignore this email."
    )
    html = _otp_html(code=code, purpose=purpose)

    mode = settings.email_delivery_mode.lower()

    if mode == "log":
        if settings.environment == "production":
            raise EmailDeliveryError(
                "OTP email delivery is not configured in production"
            )
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
            html=html,
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
    message.add_alternative(html, subtype="html")

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
