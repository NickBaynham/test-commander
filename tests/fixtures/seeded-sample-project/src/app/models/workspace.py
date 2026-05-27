"""Workspace model — a named container that owns assets."""


class Workspace:
    """A workspace owned by an account.

    Holds a list of assets and a per-account permission map.
    """

    def __init__(self, workspace_id: str, name: str, owner_account_id: str) -> None:
        self.id = workspace_id
        self.name = name
        self.owner_account_id = owner_account_id
        self.assets: list[str] = []

    def add_asset(self, asset_id: str) -> None:
        """Register an asset against this workspace."""
        self.assets.append(asset_id)
