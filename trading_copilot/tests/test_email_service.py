"""Tests for email service."""

import os
import smtplib
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from trading_copilot.email_service import (
    DeliveryResult,
    EmailDeliveryError,
    EmailService,
    EmailServiceError,
    SMTPConfig,
    SMTPConnectionError,
)


@pytest.fixture
def smtp_config():
    """Create a test SMTP configuration."""
    return SMTPConfig(
        host="smtp.example.com",
        port=587,
        username="test_user",
        password_env="TEST_SMTP_PASSWORD",
        from_email="copilot@example.com",
        use_tls=True,
    )


@pytest.fixture
def email_service(smtp_config):
    """Create an email service instance."""
    return EmailService(smtp_config, retry_count=3, retry_delay=0.01)


@pytest.fixture
def mock_smtp_password():
    """Set up mock SMTP password environment variable."""
    with patch.dict(os.environ, {"TEST_SMTP_PASSWORD": "test_password"}):
        yield


class TestSMTPConfig:
    """Tests for SMTPConfig dataclass."""

    def test_config_creation(self):
        """Test creating SMTP config with all fields."""
        config = SMTPConfig(
            host="smtp.test.com",
            port=465,
            username="user",
            password_env="PASS_ENV",
            from_email="from@test.com",
            use_tls=False,
        )
        assert config.host == "smtp.test.com"
        assert config.port == 465
        assert config.username == "user"
        assert config.password_env == "PASS_ENV"
        assert config.from_email == "from@test.com"
        assert config.use_tls is False

    def test_config_default_tls(self):
        """Test that TLS is enabled by default."""
        config = SMTPConfig(
            host="smtp.test.com",
            port=587,
            username="user",
            password_env="PASS_ENV",
            from_email="from@test.com",
        )
        assert config.use_tls is True


class TestDeliveryResult:
    """Tests for DeliveryResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful delivery result."""
        result = DeliveryResult(
            success=True,
            message_id="<123@example.com>",
            error_message=None,
        )
        assert result.success is True
        assert result.message_id == "<123@example.com>"
        assert result.error_message is None

    def test_failed_result(self):
        """Test creating a failed delivery result."""
        result = DeliveryResult(
            success=False,
            message_id=None,
            error_message="Connection refused",
        )
        assert result.success is False
        assert result.message_id is None
        assert result.error_message == "Connection refused"


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    def test_init_with_config(self, smtp_config):
        """Test initializing email service with config."""
        service = EmailService(smtp_config)
        assert service._config == smtp_config
        assert service._retry_count == EmailService.DEFAULT_RETRY_COUNT
        assert service._retry_delay == EmailService.DEFAULT_RETRY_DELAY

    def test_init_with_custom_retry(self, smtp_config):
        """Test initializing with custom retry settings."""
        service = EmailService(smtp_config, retry_count=5, retry_delay=1.0)
        assert service._retry_count == 5
        assert service._retry_delay == 1.0


class TestEmailServicePassword:
    """Tests for password retrieval."""

    def test_get_password_success(self, email_service, mock_smtp_password):
        """Test getting password from environment."""
        password = email_service._get_password()
        assert password == "test_password"

    def test_get_password_missing(self, email_service):
        """Test error when password env var is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EmailServiceError) as exc_info:
                email_service._get_password()
            assert "TEST_SMTP_PASSWORD" in str(exc_info.value)


class TestEmailServiceConnection:
    """Tests for SMTP connection handling."""

    def test_create_connection_with_tls(self, email_service, mock_smtp_password):
        """Test creating connection with TLS."""
        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server):
            server = email_service._create_connection()
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("test_user", "test_password")
            assert server == mock_server

    def test_create_connection_without_tls(self, mock_smtp_password):
        """Test creating connection without TLS."""
        config = SMTPConfig(
            host="smtp.example.com",
            port=25,
            username="test_user",
            password_env="TEST_SMTP_PASSWORD",
            from_email="copilot@example.com",
            use_tls=False,
        )
        service = EmailService(config)
        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server):
            server = service._create_connection()
            mock_server.starttls.assert_not_called()
            mock_server.login.assert_called_once()

    def test_create_connection_auth_error(self, email_service, mock_smtp_password):
        """Test handling authentication error."""
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
        with patch("smtplib.SMTP", return_value=mock_server):
            with pytest.raises(SMTPConnectionError) as exc_info:
                email_service._create_connection()
            assert "authentication failed" in str(exc_info.value).lower()

    def test_create_connection_network_error(self, email_service, mock_smtp_password):
        """Test handling network error."""
        with patch("smtplib.SMTP", side_effect=OSError("Network unreachable")):
            with pytest.raises(SMTPConnectionError) as exc_info:
                email_service._create_connection()
            assert "Network error" in str(exc_info.value)


class TestEmailServiceSend:
    """Tests for email sending functionality."""

    def test_send_success(self, email_service, mock_smtp_password):
        """Test successful email send."""
        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server):
            result = email_service.send(
                to_email="recipient@example.com",
                subject="Test Report",
                html_content="<html><body>Test</body></html>",
            )
            assert result.success is True
            assert result.error_message is None
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()

    def test_send_includes_html_content(self, email_service, mock_smtp_password):
        """Test that HTML content is included in email."""
        mock_server = MagicMock()
        html_content = "<html><body><h1>Trading Report</h1></body></html>"
        with patch("smtplib.SMTP", return_value=mock_server):
            email_service.send(
                to_email="recipient@example.com",
                subject="Test Report",
                html_content=html_content,
            )
            # Check that sendmail was called with content containing HTML
            call_args = mock_server.sendmail.call_args
            message_content = call_args[0][2]  # Third argument is the message
            assert "Trading Report" in message_content

    def test_send_recipient_refused(self, email_service, mock_smtp_password):
        """Test handling recipient refused error (no retry)."""
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused(
            {"bad@example.com": (550, b"User unknown")}
        )
        with patch("smtplib.SMTP", return_value=mock_server):
            result = email_service.send(
                to_email="bad@example.com",
                subject="Test",
                html_content="<html></html>",
            )
            assert result.success is False
            assert "Recipient refused" in result.error_message
            # Should not retry for invalid recipient
            assert mock_server.sendmail.call_count == 1

    def test_send_retries_on_connection_error(self, smtp_config, mock_smtp_password):
        """Test that send retries on connection errors."""
        service = EmailService(smtp_config, retry_count=3, retry_delay=0.01)
        with patch("smtplib.SMTP", side_effect=OSError("Connection refused")):
            result = service.send(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<html></html>",
            )
            assert result.success is False
            assert "3 attempts" in result.error_message

    def test_send_retries_on_smtp_error(self, smtp_config, mock_smtp_password):
        """Test that send retries on SMTP errors."""
        service = EmailService(smtp_config, retry_count=2, retry_delay=0.01)
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = smtplib.SMTPServerDisconnected("Lost connection")
        with patch("smtplib.SMTP", return_value=mock_server):
            result = service.send(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<html></html>",
            )
            assert result.success is False
            assert mock_server.sendmail.call_count == 2

    def test_send_succeeds_after_retry(self, smtp_config, mock_smtp_password):
        """Test that send succeeds after initial failure."""
        service = EmailService(smtp_config, retry_count=3, retry_delay=0.01)
        mock_server = MagicMock()
        # Fail first two times, succeed on third
        mock_server.sendmail.side_effect = [
            smtplib.SMTPServerDisconnected("Lost connection"),
            smtplib.SMTPServerDisconnected("Lost connection"),
            None,  # Success
        ]
        with patch("smtplib.SMTP", return_value=mock_server):
            result = service.send(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<html></html>",
            )
            assert result.success is True
            assert mock_server.sendmail.call_count == 3


class TestEmailServiceBuildMessage:
    """Tests for message building."""

    def test_build_message_structure(self, email_service):
        """Test that message has correct structure."""
        message = email_service._build_message(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<html><body>Content</body></html>",
        )
        assert message["Subject"] == "Test Subject"
        assert message["To"] == "recipient@example.com"
        assert message["From"] == "copilot@example.com"
        # Should have both plain text and HTML parts
        assert message.is_multipart()

    def test_build_message_contains_html(self, email_service):
        """Test that message contains HTML content."""
        html = "<html><body><h1>Report</h1></body></html>"
        message = email_service._build_message(
            to_email="recipient@example.com",
            subject="Test",
            html_content=html,
        )
        # Get the HTML part
        payload = message.get_payload()
        html_part = payload[1]  # Second part is HTML
        assert "Report" in html_part.get_payload()


class TestEmailServiceAsync:
    """Tests for async send method."""

    @pytest.mark.asyncio
    async def test_send_async_success(self, email_service, mock_smtp_password):
        """Test async send wrapper."""
        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server):
            result = await email_service.send_async(
                to_email="recipient@example.com",
                subject="Test Report",
                html_content="<html><body>Test</body></html>",
            )
            assert result.success is True
