"""Account model — a registered user of the platform."""


class Account:
    """A registered platform account.

    Identified by an opaque account identifier. Carries a display name and a
    role of either ``member`` or ``admin``.
    """

    def __init__(self, account_id: str, display_name: str, role: str = "member") -> None:
        self.id = account_id
        self.display_name = display_name
        self.role = role

    def is_admin(self) -> bool:
        """Return True when the account holds the admin role."""
        return self.role == "admin"
