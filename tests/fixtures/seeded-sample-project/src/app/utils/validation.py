"""Validation utilities."""


def is_non_empty_string(value: object) -> bool:
    """Return True when value is a non-empty string."""
    return isinstance(value, str) and bool(value)


def is_positive_int(value: object) -> bool:
    """Return True when value is a positive integer."""
    return isinstance(value, int) and value > 0
