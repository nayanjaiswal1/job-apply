from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from job_agent.errors import TransientError
from job_agent.ports.email import EmailPort, RawEmail

log = structlog.get_logger()

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587
_IMAP_HOST = "imap.gmail.com"
_IMAP_PORT = 993


class EmailTool:
    """EmailPort: Gmail OAuth2 SMTP send + IMAP poll over TLS."""

    def __init__(self) -> None:
        self._address = os.environ.get("GMAIL_ADDRESS", "")
        self._refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN", "")
        self._client_id = os.environ.get("GMAIL_CLIENT_ID", "")
        self._client_secret = os.environ.get("GMAIL_CLIENT_SECRET", "")

    def _access_token(self) -> str:
        import urllib.parse
        import urllib.request
        data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": self._refresh_token,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            import json
            return str(json.loads(resp.read())["access_token"])

    async def send(self, to: str, subject: str, body_html: str, body_text: str) -> None:
        token = self._access_token()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self._address
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))
        try:
            with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.docmd("AUTH", f"XOAUTH2 {_xoauth2_string(self._address, token)}")
                smtp.sendmail(self._address, to, msg.as_string())
            log.info("email_sent", to=to, subject=subject)
        except smtplib.SMTPException as exc:
            raise TransientError(f"SMTP error: {exc}") from exc

    async def poll_inbox(self, since_hours: int = 1) -> list[RawEmail]:
        import base64
        import email as email_lib
        import imaplib2  # type: ignore[import]

        token = self._access_token()
        auth_string = _xoauth2_string(self._address, token)
        emails: list[RawEmail] = []
        try:
            imap = imaplib2.IMAP4_SSL(_IMAP_HOST, _IMAP_PORT)
            imap.authenticate("XOAUTH2", lambda _: auth_string.encode())
            imap.select("INBOX")
            since = datetime.now(timezone.utc).strftime("%d-%b-%Y")
            _, ids = imap.search(None, f'(SINCE "{since}")')
            for mid in (ids[0] or b"").split():
                _, data = imap.fetch(mid, "(RFC822)")
                raw = data[0][1] if data and data[0] else b""
                msg = email_lib.message_from_bytes(raw)
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="replace")
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="replace")
                emails.append(RawEmail(
                    message_id=str(msg.get("Message-ID", "")),
                    subject=str(msg.get("Subject", "")),
                    sender=str(msg.get("From", "")),
                    body_text=body,
                    received_at=datetime.now(timezone.utc),
                ))
            imap.logout()
        except Exception as exc:
            raise TransientError(f"IMAP error: {exc}") from exc
        return emails


def _xoauth2_string(email: str, token: str) -> str:
    import base64
    raw = f"user={email}\x01auth=Bearer {token}\x01\x01"
    return base64.b64encode(raw.encode()).decode()


def _check() -> None:
    _: EmailPort = EmailTool.__new__(EmailTool)  # type: ignore[type-abstract]


_check()
