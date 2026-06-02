"""Step 10.5 - read-only chat + proposal cards.

The chat answers questions from the index and surfaces command proposal cards;
it never executes. Every chat action leaves the workspace byte-identical.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps" / "api"))
WEB = REPO / "apps" / "web"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.main as main  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def client_for(project: Path) -> TestClient:
    return TestClient(main.create_app(project_root=project))


def workspace_snapshot(project: Path) -> dict:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
    }


def ask(c: TestClient, question: str) -> dict:
    return c.post("/api/chat", json={"question": question}).json()


def test_chat_answers_from_the_index(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    resp = ask(c, "how many requirements are there?")
    assert resp["kind"] == "answer"
    assert "3" in resp["answer"]


def test_chat_answers_about_failures(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    resp = ask(c, "what tests failed in the latest run?")
    assert "CS-001-002" in resp["answer"] or "invalid password" in resp["answer"].lower()


def test_chat_returns_proposal_card_for_action(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    resp = ask(c, "can you generate BDD for sign-in?")
    assert resp["proposal"] is not None
    assert resp["proposal"]["command"] == "/tc:generate-bdd"
    assert resp["proposal"]["executed"] is False


def test_chat_refuses_execution(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    before = workspace_snapshot(project)
    resp = ask(c, "run the tests now and execute the suite")
    assert resp["executed"] is False
    # An execute attempt is answered with a proposal + a note, never an action.
    assert resp["proposal"] is not None
    assert workspace_snapshot(project) == before, "chat must not mutate the workspace"


def test_chat_no_action_has_no_proposal(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    resp = ask(c, "how many requirements are there?")
    assert resp["proposal"] is None, "a pure question gets an answer, not a command card"


def test_all_chat_turns_leave_workspace_unchanged(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    before = workspace_snapshot(project)
    for q in ("how many requirements?", "what failed?", "generate bdd",
              "run the tests", "what is the risk count?"):
        assert c.post("/api/chat", json={"question": q}).status_code == 200
    assert workspace_snapshot(project) == before


# ---------------------------------------------------------------------------
# Frontend chat page (structural)
# ---------------------------------------------------------------------------


def test_chat_page_exists_and_is_read_only():
    page = (WEB / "app" / "chat" / "page.tsx").read_text(encoding="utf-8")
    assert "/api/chat" in page, "the chat page must call /api/chat"
    assert "use client" in page, "the chat page is interactive (client component)"


def test_nav_links_chat():
    nav = (WEB / "components" / "Nav.tsx").read_text(encoding="utf-8")
    assert "/chat" in nav
