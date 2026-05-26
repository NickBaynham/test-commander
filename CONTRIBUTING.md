# Contributing to Test Commander

Thanks for the interest. Test Commander is built incrementally, in small verifiable steps, with documentation written as we go. Contributions follow the same discipline.

## Before you start

- Read [planning/plan.md](planning/plan.md). Every change should map to a current phase or be raised as an open question.
- Confirm your environment is set up: run `./bootstrap.sh` then `make install`. If either fails, that's the contribution we want first.

## Workflow

1. **Pick a phase or step.** Work the open To Do for the current phase. Don't jump ahead — Phase N depends on Phase N-1's artifacts.
2. **Small, incremental commits.** Each commit should leave the repo in a working state. `make verify` should pass before you push.
3. **Tests with the code.** Every feature or skill change ships with a test or fixture. No "I'll add the test later."
4. **Documentation as you go.** User-facing changes update `docs/user-guide/`. New commands update `docs/command-reference.md`. Every phase entry updates `CHANGELOG.md`.
5. **Open a pull request.** Reference the plan step (e.g. "Phase 0, Step 0.4"). Include the `make verify` output or a screenshot of the relevant manual review.

## Code style

- Python: PDM for dependency management. Target `>=3.12`. No virtualenvs inside containers unless multiple Python apps conflict.
- Shell: POSIX `sh` where possible. No PowerShell. Windows users run under WSL2 or Git Bash.
- Markdown: standard technical writing. No emojis anywhere — code, logs, UI, docs.
- Skills: every TC skill lives under `plugins/test-commander/skills/<skill-name>/` with a `SKILL.md` and frontmatter (`name`, `description`).

## Reviewing your own work

Before pushing:

- `make lint` clean.
- `make test` clean.
- `make verify` clean (includes skill verification).
- Manual review against the step's Definition of Done in `planning/plan.md`.

## Root-cause discipline

When you fix a bug, reproduce it with a failing test first, then fix it, then update docs so the same failure mode can't recur silently. Don't paper over a symptom.

## License

By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
