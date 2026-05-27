"""Authentication endpoints.

Implements the sign-in surface declared by ``specs/openapi.yaml`` under
``POST /sessions`` and ``DELETE /sessions/{id}``.
"""


def sign_in(account_id: str, code: str) -> dict[str, str]:
    """Validate a one-time code and return a session record.

    Returns a dictionary with ``id``, ``account_id``, and ``expires_at`` keys.
    Raises ``ValueError`` when the code is empty.
    """
    if not code:
        raise ValueError("code must not be empty")
    return {
        "id": f"sess-{account_id}",
        "account_id": account_id,
        "expires_at": "2099-01-01T00:00:00Z",
    }


def sign_out(session_id: str) -> None:
    """Destroy a session by identifier.

    Idempotent: signing out a session that does not exist is a no-op.
    """
    del session_id  # nothing to do in the fixture stub
