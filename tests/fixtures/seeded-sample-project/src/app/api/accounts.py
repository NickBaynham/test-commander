"""Account read endpoint.

Implements ``GET /accounts/{id}`` from ``specs/openapi.yaml``.
"""


def get_account(account_id: str) -> dict[str, object]:
    """Return the account record for the given identifier.

    The seeded fixture returns a static record; a real implementation would
    look the identifier up in a store.
    """
    return {
        "id": account_id,
        "display_name": "Sample Account",
        "role": "member",
    }
