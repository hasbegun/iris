"""
Shared validation models and utilities
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """
    Result of validation operation

    Attributes:
        is_valid: Whether validation passed
        error_message: Optional error message if validation failed
    """
    is_valid: bool
    error_message: Optional[str] = None

    @classmethod
    def success(cls) -> 'ValidationResult':
        """Create successful validation result"""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, message: str) -> 'ValidationResult':
        """Create failed validation result with error message"""
        return cls(is_valid=False, error_message=message)

    def __bool__(self) -> bool:
        """Allow using validation result in boolean context"""
        return self.is_valid
