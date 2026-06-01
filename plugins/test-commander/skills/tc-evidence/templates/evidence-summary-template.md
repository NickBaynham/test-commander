# Evidence index

_Managed by the tc-evidence indexer (`/tc:run`). Screenshots, logs, and reports are committed; videos and traces are git-ignored by default (enable git-lfs to version them - see the tc-run evidence-management methodology)._

| artifact | type | policy | run | requirement | candidate | scenario |
| --- | --- | --- | --- | --- | --- | --- |
| evidence/screenshots/<id>.png | screenshot | committed | RUN-NNNNNNNN-NNNNNN | REQ-NNN | CS-NNN-NNN | <scenario title> |
| evidence/traces/<id>.zip | trace | git-ignored | RUN-NNNNNNNN-NNNNNN | REQ-NNN | CS-NNN-NNN | <scenario title> |
| evidence/videos/<id>.webm | video | git-ignored | RUN-NNNNNNNN-NNNNNN | REQ-NNN | CS-NNN-NNN | <scenario title> |

<!--
This is the shape index_run_evidence writes to evidence/evidence-index.md. Rows
are sorted by the artifact's logical path then run id, and the index is rebuilt
from every runs/<RUN-ID>/results.json record, so a re-run over unchanged records
is byte-identical. The companion evidence/.gitignore ignores videos/ and traces/
while keeping their README placeholders committed.
-->
