"""Email service for sending verification and notification emails."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from jose import jwt, JWTError

from src.core.config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# EMAIL VERIFICATION TOKEN
# ============================================================================

def create_email_verification_token(user_id: int) -> str:
    """Create a JWT token for email verification (expires in 24 hours)."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    to_encode = {
        "sub": str(user_id),
        "type": "email_verification",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_email_token(token: str) -> Optional[int]:
    """
    Verify email verification token and return user_id.
    Returns None if token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "email_verification":
            return None
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except JWTError:
        return None


# ============================================================================
# EMAIL SENDING
# ============================================================================

async def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Send an email using SMTP. Returns True if successful."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Skipping email send.")
        return False

    try:
        import aiosmtplib

        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
        message["To"] = to_email
        message["Subject"] = subject

        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            start_tls=True,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
        )

        logger.info(f"Email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False


async def send_verification_email(email: str, nama: str, token: str) -> bool:
    """Send email verification link to user."""
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); padding: 32px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .header p {{ color: #bfdbfe; margin: 8px 0 0; font-size: 14px; }}
            .body {{ padding: 32px; }}
            .body h2 {{ color: #1e293b; margin-top: 0; }}
            .body p {{ color: #475569; line-height: 1.6; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #1e40af, #3b82f6); color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 16px 0; }}
            .footer {{ padding: 24px 32px; background: #f8fafc; text-align: center; color: #94a3b8; font-size: 12px; }}
            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 4px; margin: 16px 0; }}
            .warning p {{ color: #92400e; margin: 0; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 IM-Balmon</h1>
                <p>Sistem Inventaris & Manajemen Perangkat</p>
            </div>
            <div class="body">
                <h2>Halo, {nama}!</h2>
                <p>Terima kasih telah mendaftar di sistem IM-Balmon. Silakan verifikasi alamat email Anda dengan mengklik tombol di bawah ini:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_url}" class="btn">✅ Verifikasi Email Saya</a>
                </div>

                <div class="warning">
                    <p>⏰ Link verifikasi ini berlaku selama <strong>24 jam</strong>. Setelah itu, Anda perlu meminta link baru.</p>
                </div>

                <p>Setelah email diverifikasi, akun Anda masih perlu di-approve oleh admin sebelum bisa digunakan untuk login.</p>
                
                <p style="font-size: 13px; color: #94a3b8;">Jika Anda tidak merasa mendaftar di IM-Balmon, abaikan email ini.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} IM-Balmon — Balai Monitor Spektrum Frekuensi Radio</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=email,
        subject="[IM-Balmon] Verifikasi Email Anda",
        html_content=html_content,
    )


async def send_account_created_notification(email: str, nama: str) -> bool:
    """Send notification to user when admin creates their account."""
    login_url = f"{settings.FRONTEND_URL}/login"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #059669, #10b981); padding: 32px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .header p {{ color: #a7f3d0; margin: 8px 0 0; font-size: 14px; }}
            .body {{ padding: 32px; }}
            .body h2 {{ color: #1e293b; margin-top: 0; }}
            .body p {{ color: #475569; line-height: 1.6; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #059669, #10b981); color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 16px 0; }}
            .footer {{ padding: 24px 32px; background: #f8fafc; text-align: center; color: #94a3b8; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 IM-Balmon</h1>
                <p>Akun Anda Telah Dibuat</p>
            </div>
            <div class="body">
                <h2>Halo, {nama}!</h2>
                <p>Admin telah membuat akun IM-Balmon untuk Anda. Anda dapat langsung login menggunakan email ini dan password yang telah diberikan oleh admin.</p>
                
                <div style="text-align: center;">
                    <a href="{login_url}" class="btn">🔑 Login Sekarang</a>
                </div>

                <p style="font-size: 13px; color: #94a3b8;">Disarankan untuk segera mengganti password Anda setelah login pertama kali.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} IM-Balmon — Balai Monitor Spektrum Frekuensi Radio</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=email,
        subject="[IM-Balmon] Akun Anda Telah Dibuat",
        html_content=html_content,
    )


async def send_password_reset_email(email: str, nama: str, token: str) -> bool:
    """Send password reset link to user."""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); overflow: hidden; }}
            .header {{ background: linear-gradient(135deg, #dc2626, #ef4444); padding: 32px; text-align: center; }}
            .header h1 {{ color: #ffffff; margin: 0; font-size: 24px; }}
            .header p {{ color: #fecaca; margin: 8px 0 0; font-size: 14px; }}
            .body {{ padding: 32px; }}
            .body h2 {{ color: #1e293b; margin-top: 0; }}
            .body p {{ color: #475569; line-height: 1.6; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #dc2626, #ef4444); color: #ffffff !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px; margin: 16px 0; }}
            .footer {{ padding: 24px 32px; background: #f8fafc; text-align: center; color: #94a3b8; font-size: 12px; }}
            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 4px; margin: 16px 0; }}
            .warning p {{ color: #92400e; margin: 0; font-size: 13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔑 IM-Balmon</h1>
                <p>Reset Password</p>
            </div>
            <div class="body">
                <h2>Halo, {nama}!</h2>
                <p>Kami menerima permintaan untuk mereset password akun Anda. Klik tombol di bawah ini untuk membuat password baru:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="btn">🔐 Reset Password Saya</a>
                </div>

                <div class="warning">
                    <p>⏰ Link reset ini berlaku selama <strong>1 jam</strong>. Setelah itu, Anda perlu meminta link baru.</p>
                </div>

                <p style="font-size: 13px; color: #94a3b8;">Jika Anda tidak meminta reset password, abaikan email ini. Password Anda tidak akan berubah.</p>
            </div>
            <div class="footer">
                <p>&copy; {datetime.now().year} IM-Balmon — Balai Monitor Spektrum Frekuensi Radio</p>
            </div>
        </div>
    </body>
    </html>
    """

    return await send_email(
        to_email=email,
        subject="[IM-Balmon] Reset Password Anda",
        html_content=html_content,
    )
