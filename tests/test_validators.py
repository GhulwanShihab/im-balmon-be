# tests/test_validators.py
"""Unit tests for password and input validators."""

import pytest
from src.utils.validators import (
    validate_email,
    validate_password_strength,
    _has_sequential_chars,
    _has_repeated_chars,
    _calculate_strength_score,
    sanitize_filename,
)


class TestValidateEmail:
    """Test cases for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user123@example.co.id",
            "test_user@subdomain.example.org",
        ]
        for email in valid_emails:
            assert validate_email(email) is True, f"Email {email} should be valid"

    def test_invalid_email(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid",
            "invalid@",
            "@example.com",
            "user@.com",
            "user@example",
            "",
            "user name@example.com",  # space not allowed
        ]
        for email in invalid_emails:
            assert validate_email(email) is False, f"Email {email} should be invalid"


class TestValidatePasswordStrength:
    """Test cases for password strength validation."""

    def test_strong_password(self):
        """Test that a strong password passes validation."""
        result = validate_password_strength("SecurePass123!")
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["strength_score"] >= 50

    def test_password_too_short(self):
        """Test that short passwords fail validation."""
        result = validate_password_strength("Short1!")
        assert result["valid"] is False
        assert any("12 characters" in error for error in result["errors"])

    def test_password_minimum_length(self):
        """Test password with minimum acceptable length."""
        result = validate_password_strength("12345678")  # 8 chars - minimum
        assert result["valid"] is True

    def test_empty_password(self):
        """Test empty password fails validation."""
        result = validate_password_strength("")
        assert result["valid"] is False

    def test_password_strength_score(self):
        """Test password strength scoring."""
        # Weak password
        weak_result = validate_password_strength("12345678")
        assert weak_result["strength_score"] < 50

        # Strong password with all character types
        strong_result = validate_password_strength("SecurePass123!@#")
        assert strong_result["strength_score"] >= 75


class TestSequentialChars:
    """Test cases for sequential character detection."""

    def test_sequential_numbers(self):
        """Test detection of sequential numbers."""
        assert _has_sequential_chars("abc123def") is True
        assert _has_sequential_chars("test456test") is True

    def test_sequential_letters(self):
        """Test detection of sequential letters."""
        assert _has_sequential_chars("passwordabc") is True
        assert _has_sequential_chars("testxyz") is True

    def test_qwerty_pattern(self):
        """Test detection of QWERTY keyboard patterns."""
        assert _has_sequential_chars("passqweword") is True

    def test_no_sequential_chars(self):
        """Test password without sequential characters."""
        assert _has_sequential_chars("p@ssw0rd!") is False


class TestRepeatedChars:
    """Test cases for repeated character detection."""

    def test_repeated_chars(self):
        """Test detection of repeated characters."""
        assert _has_repeated_chars("passssword") is True
        assert _has_repeated_chars("aaa111") is True

    def test_no_repeated_chars(self):
        """Test password without repeated characters."""
        assert _has_repeated_chars("password") is False
        assert _has_repeated_chars("aabb11") is False  # Only 2 consecutive


class TestCalculateStrengthScore:
    """Test cases for password strength scoring."""

    def test_weak_password_score(self):
        """Test weak password gets low score."""
        score = _calculate_strength_score("abc")
        assert score < 25

    def test_medium_password_score(self):
        """Test medium password gets medium score."""
        score = _calculate_strength_score("Password1")
        assert 25 <= score < 75

    def test_strong_password_score(self):
        """Test strong password gets high score."""
        score = _calculate_strength_score("SecurePassword123!@#")
        assert score >= 75

    def test_max_score_cap(self):
        """Test that score never exceeds 100."""
        score = _calculate_strength_score("VeryLongSecureP@ssw0rd123!@#$%^&*()_+")
        assert score <= 100


class TestSanitizeFilename:
    """Test cases for filename sanitization."""

    def test_remove_dangerous_chars(self):
        """Test removal of dangerous characters."""
        result = sanitize_filename("file<>:\"/\\|?*.txt")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result
        assert '"' not in result
        assert "/" not in result
        assert "\\" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_normal_filename(self):
        """Test that normal filenames are preserved."""
        result = sanitize_filename("normal_file.pdf")
        assert result == "normal_file.pdf"

    def test_max_length(self):
        """Test filename length limiting."""
        long_name = "a" * 100 + ".pdf"
        result = sanitize_filename(long_name, max_length=50)
        assert len(result) <= 50

    def test_preserve_extension(self):
        """Test that file extension is preserved."""
        result = sanitize_filename("a" * 60 + ".jpg", max_length=20)
        assert result.endswith(".jpg")
