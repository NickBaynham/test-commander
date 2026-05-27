"""Tests for the validation utilities.

Note: ``app.api.files.upload_file`` is intentionally not covered here to seed
the untested-function gap signal.
"""

# knowledge: untested-function
# app.api.files.upload_file has no test coverage.

from app.utils.validation import is_non_empty_string, is_positive_int


def test_non_empty_string_accepts_string():
    assert is_non_empty_string("abc")


def test_non_empty_string_rejects_empty():
    assert not is_non_empty_string("")


def test_positive_int_accepts_positive():
    assert is_positive_int(7)


def test_positive_int_rejects_zero():
    assert not is_positive_int(0)
