"""
Tests for ValidationResult model
"""
import pytest
from app.models.validation import ValidationResult


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_success_creation(self):
        """Test creating a success validation result"""
        result = ValidationResult.success()
        assert result.is_valid is True
        assert result.error_message is None
        assert bool(result) is True

    def test_failure_creation(self):
        """Test creating a failure validation result"""
        error_msg = "Invalid image format"
        result = ValidationResult.failure(error_msg)
        assert result.is_valid is False
        assert result.error_message == error_msg
        assert bool(result) is False

    def test_direct_creation_valid(self):
        """Test direct creation of valid result"""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.error_message is None
        assert bool(result) is True

    def test_direct_creation_invalid(self):
        """Test direct creation of invalid result"""
        error_msg = "File too large"
        result = ValidationResult(is_valid=False, error_message=error_msg)
        assert result.is_valid is False
        assert result.error_message == error_msg
        assert bool(result) is False

    def test_bool_conversion(self):
        """Test boolean conversion works correctly"""
        valid_result = ValidationResult.success()
        invalid_result = ValidationResult.failure("error")

        assert bool(valid_result) is True
        assert bool(invalid_result) is False

        # Test in conditionals
        if valid_result:
            passed_valid = True
        else:
            passed_valid = False

        if invalid_result:
            passed_invalid = False
        else:
            passed_invalid = True

        assert passed_valid is True
        assert passed_invalid is True
