# Quality gate: <PASS | WARN | FAIL>

Evaluated against `tc-quality-report.gate.thresholds` (defaults apply where unset).

| criterion | measured | threshold | verdict |
| --- | --- | --- | --- |
| pass rate | <p/total> | >= <min-pass-rate> | <PASS/FAIL> |
| failed tests | <count> | <= <max-failed> | <PASS/FAIL> |
| flaky tests | <count> | <= <max-flaky> | <PASS/WARN> |
| open questions | <count> | <= <max-open-questions> | <PASS/WARN> |

Overall: **<PASS | WARN | FAIL>**

<!--
This is the shape /tc:quality-gate writes to quality-report/quality-gate.md. The
overall verdict is the worst per-criterion verdict (PASS < WARN < FAIL). Hard
criteria (pass rate, failed tests) breach to FAIL; soft criteria (flaky tests,
open questions) breach to WARN. The verdict is derived from the run record and
open questions (no clock), so a re-run over unchanged inputs is byte-identical.
-->
