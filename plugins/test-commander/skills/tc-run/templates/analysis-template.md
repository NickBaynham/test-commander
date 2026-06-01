# Test analysis <RUN-ID>

- Triaged: <N> non-passed result(s) (<category: count, ...>)

| requirement | candidate | scenario | result | classification |
| --- | --- | --- | --- | --- |
| REQ-NNN | CS-NNN-NNN | <scenario title> | failed | product-defect |
| REQ-NNN | CS-NNN-NNN | <scenario title> | failed | test-defect |
| REQ-NNN | CS-NNN-NNN | <scenario title> | failed | environment |
| REQ-NNN | CS-NNN-NNN | <scenario title> | flaky | flaky |

<!--
This is the shape /tc:analyze-results writes to runs/<RUN-ID>/analysis.md. Only
non-passed results appear; rows are sorted by requirement, candidate, scenario,
so a re-run over an unchanged run record is byte-identical. A clean (all-passed)
run records "_No failures or flaky tests in this run._" instead of the table.
Each non-passed result also routes a deduplicated [test-analysis] signal to
requirements/open-questions.md.
-->
