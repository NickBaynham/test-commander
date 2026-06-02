"""Step 10.5.8 - output validation + secret safety.

After execution, the runtime verifies files changed are within the planned
scope, no secret files were touched, and expected outputs were produced. Secret
safety: redact secret values, flag env-var-printing attempts.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))

from agent_adapters.base import ExecutionResult  # noqa: E402
from governance import planner, validation  # noqa: E402


def test_validation_ok_when_changes_match_plan():
    plan = planner.plan("/tc:automate")
    result = ExecutionResult(status="succeeded", files_changed=list(plan.expected_artifacts))
    v = validation.validate(plan, result)
    assert v.ok is True
    assert v.violations == []


def test_out_of_scope_write_fails_the_run():
    plan = planner.plan("/tc:automate")  # scope: tests/, traceability/automation-map.md
    result = ExecutionResult(
        status="succeeded",
        files_changed=[*plan.expected_artifacts, "src/app/accounts.py"],
    )
    v = validation.validate(plan, result)
    assert v.ok is False
    assert any("src/app/accounts.py" in msg for msg in v.violations)


def test_secret_file_touch_fails_the_run():
    plan = planner.plan("/tc:automate")
    result = ExecutionResult(status="succeeded", files_changed=[".env"])
    v = validation.validate(plan, result)
    assert v.ok is False
    assert any("secret" in msg.lower() for msg in v.violations)


def test_missing_expected_output_fails_the_run():
    plan = planner.plan("/tc:automate")
    result = ExecutionResult(status="succeeded", files_changed=[])  # produced nothing
    v = validation.validate(plan, result)
    assert v.ok is False


def test_redact_masks_secret_values():
    text = "API_KEY=sk-supersecret123 and token=abcd1234efgh"
    red = validation.redact(text)
    assert "sk-supersecret123" not in red
    assert "abcd1234efgh" not in red
    assert "REDACTED" in red


def test_flags_env_var_print_attempts():
    assert validation.flags_env_var_print("printenv") is True
    assert validation.flags_env_var_print("echo $OPENAI_API_KEY") is True
    assert validation.flags_env_var_print("print(os.environ)") is True
    assert validation.flags_env_var_print("review the requirements") is False
