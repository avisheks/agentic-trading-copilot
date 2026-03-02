"""Email service for Trading Copilot report delivery."""

import logging
import os
import smtplib
import time
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """SMTP server configuration."""
    host: str
    port: int
    username: str
    password_env: str  # Environment variable name for password
    from_email: str
    use_tls: bool = True


@dataclass
class DeliveryResult:
    """Result of email delivery attempt."""
    success: bool
    message_id: str | None
    error_message: str | None


class EmailServiceError(Exception):
    """Base exception for email service errors."""
    pass


class SMTPConnectionError(EmailServiceError):
    """Raised when SMTP connection fails."""
    pass


class EmailDeliveryError(EmailServiceError):
    """Raised when email delivery fails."""
    pass


class EmailService:
    """Sends HTML reports via email using SMTP."""

    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 2.0  # seconds

    def __init__(
        self,
        config: SMTPConfig,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """
        Initialize email service with SMTP configuration.

        Args:
            config: SMTP server configuration
            retry_count: Number of retry attempts on failure
            retry_delay: Delay between retries in seconds
        """
        self._config = config
        self._retry_count = retry_count
        self._retry_delay = retry_delay

    def _get_password(self) -> str:
        """Get SMTP password from environment variable."""
        password = os.environ.get(self._config.password_env)
        if not password:
            raise EmailServiceError(
                f"SMTP password not found in environment variable: {self._config.password_env}"
            )
        return password

    def _create_connection(self) -> smtplib.SMTP:
        """
        Create and authenticate SMTP connection.

        Returns:
            Authenticated SMTP connection

        Raises:
            SMTPConnectionError: If connection or authentication fails
        """
        try:
            if self._config.use_tls:
                server = smtplib.SMTP(self._config.host, self._config.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self._config.host, self._config.port)

            password = self._get_password()
            server.login(self._config.username, password)
            return server

        except smtplib.SMTPAuthenticationError as e:
            raise SMTPConnectionError(f"SMTP authentication failed: {e}")
        except smtplib.SMTPConnectError as e:
            raise SMTPConnectionError(f"Failed to connect to SMTP server: {e}")
        except smtplib.SMTPException as e:
            raise SMTPConnectionError(f"SMTP error during connection: {e}")
        except OSError as e:
            raise SMTPConnectionError(f"Network error connecting to SMTP server: {e}")

    def _build_message(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> MIMEMultipart:
        """Build MIME message for HTML email."""
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self._config.from_email
        message["To"] = to_email

        # Create plain text fallback
        plain_text = "This email requires an HTML-capable email client to view."
        text_part = MIMEText(plain_text, "plain")
        html_part = MIMEText(html_content, "html")

        message.attach(text_part)
        message.attach(html_part)

        return message

    def send(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> DeliveryResult:
        """
        Send HTML email with retry logic.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML report content

        Returns:
            DeliveryResult with status and message ID
        """
        message = self._build_message(to_email, subject, html_content)
        last_error: Optional[Exception] = None

        for attempt in range(self._retry_count):
            try:
                server = self._create_connection()
                try:
                    server.sendmail(
                        self._config.from_email,
                        [to_email],
                        message.as_string(),
                    )
                    # Extract message ID if available
                    message_id = message.get("Message-ID")
                    logger.info(f"Email sent successfully to {to_email}")
                    return DeliveryResult(
                        success=True,
                        message_id=message_id,
                        error_message=None,
                    )
                finally:
                    server.quit()

            except SMTPConnectionError as e:
                last_error = e
                logger.warning(
                    f"SMTP connection error (attempt {attempt + 1}/{self._retry_count}): {e}"
                )
            except smtplib.SMTPRecipientsRefused as e:
                # Don't retry if recipient is invalid
                logger.error(f"Recipient refused: {to_email}")
                return DeliveryResult(
                    success=False,
                    message_id=None,
                    error_message=f"Recipient refused: {e}",
                )
            except smtplib.SMTPException as e:
                last_error = e
                logger.warning(
                    f"SMTP error (attempt {attempt + 1}/{self._retry_count}): {e}"
                )
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Unexpected error (attempt {attempt + 1}/{self._retry_count}): {e}"
                )

            # Wait before retry (except on last attempt)
            if attempt < self._retry_count - 1:
                time.sleep(self._retry_delay)

        # All retries exhausted
        error_msg = f"Failed to send email after {self._retry_count} attempts: {last_error}"
        logger.error(error_msg)
        return DeliveryResult(
            success=False,
            message_id=None,
            error_message=error_msg,
        )

    async def send_async(
        self,
        to_email: str,
        subject: str,
        html_content: str,
    ) -> DeliveryResult:
        """
        Async wrapper for send method.

        Note: Uses synchronous SMTP under the hood. For true async,
        consider using aiosmtplib in production.
        """
        return self.send(to_email, subject, html_content)
