"""
Tests for YOLO API utilities
"""
import pytest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.api.yolo import parse_classes


class TestParseClasses:
    """Test parse_classes utility function"""

    def test_parse_valid_classes(self):
        """Test parsing valid comma-separated class names"""
        result = parse_classes("person,car,dog")
        assert result == ["person", "car", "dog"]

    def test_parse_classes_with_spaces(self):
        """Test parsing classes with extra spaces"""
        result = parse_classes("person, car , dog")
        assert result == ["person", "car", "dog"]

    def test_parse_single_class(self):
        """Test parsing a single class"""
        result = parse_classes("person")
        assert result == ["person"]

    def test_parse_empty_string(self):
        """Test parsing empty string returns None"""
        result = parse_classes("")
        assert result is None

    def test_parse_none(self):
        """Test parsing None returns None"""
        result = parse_classes(None)
        assert result is None

    def test_parse_whitespace_only(self):
        """Test parsing whitespace-only string returns None or empty list"""
        result = parse_classes("   ")
        # The function returns empty list when all values are whitespace
        assert result == [] or result is None

    def test_parse_classes_with_empty_values(self):
        """Test parsing with empty values between commas"""
        result = parse_classes("person,,car,  ,dog")
        # Empty values should be filtered out
        assert result == ["person", "car", "dog"]

    def test_parse_classes_trailing_comma(self):
        """Test parsing with trailing comma"""
        result = parse_classes("person,car,dog,")
        assert result == ["person", "car", "dog"]

    def test_parse_classes_leading_comma(self):
        """Test parsing with leading comma"""
        result = parse_classes(",person,car,dog")
        assert result == ["person", "car", "dog"]

    def test_parse_classes_multiple_commas(self):
        """Test parsing with multiple consecutive commas"""
        result = parse_classes("person,,,car,,dog")
        assert result == ["person", "car", "dog"]

    def test_parse_classes_complex(self):
        """Test parsing complex input with various edge cases"""
        result = parse_classes(" , person , , car , dog , , ")
        assert result == ["person", "car", "dog"]
