"""File-upload endpoint.

Implements ``POST /workspaces/{id}/assets`` from ``specs/openapi.yaml``.
"""


# knowledge: undocumented-function
# The function below is intentionally missing a docstring to seed the
# undocumented-function gap for the /tc:learn-from-code extractor.
def upload_file(workspace_id: str, file_name: str, size_bytes: int) -> dict[str, object]:
    return {
        "id": f"asset-{file_name}",
        "workspace_id": workspace_id,
        "name": file_name,
        "size_bytes": size_bytes,
        "content_type": "application/octet-stream",
    }


def list_assets(workspace_id: str) -> list[dict[str, str]]:
    """Return the asset list for a workspace."""
    return [{"workspace_id": workspace_id, "id": "asset-sample", "name": "sample.bin"}]
