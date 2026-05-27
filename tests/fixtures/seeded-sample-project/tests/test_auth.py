"""Tests for the sign-in surface."""

from app.api.auth import sign_in, sign_out


def test_sign_in_returns_session():
    session = sign_in("acc-123", "code-abc")
    assert session["account_id"] == "acc-123"
    assert session["id"].startswith("sess-")


def test_sign_out_is_idempotent():
    sign_out("sess-1")
    sign_out("sess-1")
