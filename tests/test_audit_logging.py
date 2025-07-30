"""Tests for audit logging functionality."""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

from app import log_user_guess, setup_audit_logger


def test_setup_audit_logger():
    """Test that audit logger is set up correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict("os.environ", {"LOGS_DIR": tmpdir}):
            logger = setup_audit_logger()

            assert logger.name == "audit"
            assert logger.level == logging.INFO
            assert len(logger.handlers) > 0

            # Check that log file is created
            log_file = Path(tmpdir) / "audit.log"
            assert log_file.exists()


def test_log_user_guess():
    """Test that user guesses are logged correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "audit.log"

        # Create a custom logger for testing
        test_logger = logging.getLogger("test_audit")
        test_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        # Mock the audit logger
        with patch("app.audit_logger", test_logger):
            # Test logging a guess
            log_user_guess("zyskowicz", "192.168.1.1")

            # Read the log file
            log_content = log_file.read_text()

            # Verify log entry
            assert "192.168.1.1" in log_content
            assert "zyskowicz" in log_content
            assert "guess_submitted" in log_content

            # Parse the JSON part
            log_lines = log_content.strip().split("\n")
            assert len(log_lines) == 1

            # Extract JSON from log line (after timestamp)
            log_parts = log_lines[0].split(" - ", 1)
            assert len(log_parts) == 2

            json_data = json.loads(log_parts[1])
            assert json_data["client_ip"] == "192.168.1.1"
            assert json_data["guess"] == "zyskowicz"
            assert json_data["action"] == "guess_submitted"
            assert "timestamp" in json_data


def test_log_user_guess_with_unknown_ip():
    """Test logging with unknown IP address."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "audit.log"

        # Create a custom logger for testing
        test_logger = logging.getLogger("test_audit_unknown")
        test_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        # Mock the audit logger
        with patch("app.audit_logger", test_logger):
            # Test logging a guess with unknown IP
            log_user_guess("testname", "unknown")

            # Read the log file
            log_content = log_file.read_text()

            # Verify log entry
            assert "unknown" in log_content
            assert "testname" in log_content


def test_log_multiple_guesses():
    """Test that multiple guesses are logged correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "audit.log"

        # Create a custom logger for testing
        test_logger = logging.getLogger("test_audit_multiple")
        test_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        # Mock the audit logger
        with patch("app.audit_logger", test_logger):
            # Test logging multiple guesses
            log_user_guess("zyskowicz", "192.168.1.1")
            log_user_guess("testing", "192.168.1.2")
            log_user_guess("surname", "10.0.0.1")

            # Read the log file
            log_content = log_file.read_text()
            log_lines = log_content.strip().split("\n")

            # Should have 3 log entries
            assert len(log_lines) == 3

            # Check each entry
            assert "zyskowicz" in log_lines[0]
            assert "192.168.1.1" in log_lines[0]

            assert "testing" in log_lines[1]
            assert "192.168.1.2" in log_lines[1]

            assert "surname" in log_lines[2]
            assert "10.0.0.1" in log_lines[2]
