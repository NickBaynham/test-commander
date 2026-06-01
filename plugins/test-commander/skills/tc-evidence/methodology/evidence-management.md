# Evidence management methodology

How the `tc-evidence` indexer routes the artifacts a run produces into the
workspace evidence tree, indexes them with provenance, and enforces the
commit-versus-ignore policy. `tc-evidence` has no `/tc:*` command - this
methodology is its authoritative behavior spec.

## The policy

| Artifact type | Extensions | Evidence subdir | Git policy |
| --- | --- | --- | --- |
| Screenshot | `.png` `.jpg` `.jpeg` `.gif` | `evidence/screenshots/` | committed |
| Video | `.webm` `.mp4` | `evidence/videos/` | git-ignored by default (git-lfs opt-in) |
| Trace | `.zip` | `evidence/traces/` | git-ignored by default (git-lfs opt-in) |
| Log | `.txt` `.log` | `evidence/logs/` | committed |
| Report | `.json` `.html` | `evidence/logs/` | committed |

The split follows the Phase 7 open-question resolutions: screenshots are small
and review-critical, so they are committed (Q5); videos and traces can be large,
so they are git-ignored by default with a documented git-lfs opt-in (Q5);
JSON/HTML reports are committed and referenced from the quality report. The
policy is enforced by the indexer, not by an author's discipline.

## The `.gitignore`

The indexer writes `evidence/.gitignore` so the large classes are ignored while
their directory placeholders (`README.md`) stay committed:

```gitignore
videos/*
!videos/README.md
traces/*
!traces/README.md
```

To version videos or traces, enable [git-lfs](https://git-lfs.com), track the
relevant patterns (`git lfs track "evidence/videos/**"`), and delete the
matching lines from `evidence/.gitignore`. The indexer never deletes artifacts -
"git-ignored" is about what git tracks, not what exists on disk.

## Routing and the index

`index_run_evidence(project_root, run_id)`:

1. Reads `runs/<RUN-ID>/results.json` (the machine-readable per-run record
   `/tc:run` writes) for the named run's artifact attachments.
2. **Routes** each artifact: classifies it by extension, resolves its source
   (absolute as Playwright emits it, or relative to `source_root`), and copies
   it into `evidence/<subdir>/`. A source that cannot be found is still indexed
   - the run record is the source of truth, not the filesystem.
3. **Rebuilds** `evidence/evidence-index.md` over **every** run record under
   `runs/`, so the index is the complete, deterministic picture. Each row
   carries the artifact's logical path, type, git policy, run id, and scenario
   provenance (requirement, candidate, scenario).
4. **Writes** `evidence/.gitignore`.

Because the index is rebuilt from the records (not from a mutable accumulator),
re-running over unchanged records produces byte-identical output - the same
determinism contract every Test Commander helper holds.

## How it is invoked

`/tc:run` calls `index_run_evidence` automatically after writing its per-run
record, suppressible with `--no-index` (the defer-not-defend wiring pattern:
`/tc:generate-bdd` auto-runs `/tc:review-bdd`, `/tc:automate` auto-runs
`/tc:review-automation`, and `/tc:run` auto-runs the evidence indexer). The web
console (Phase 10) will call the same entry point. There is no standalone
`/tc:*` command; a thin CLI (`index_evidence.py --run-id <RUN-ID>`) exists for
manual / debugging use.

## The Claude judgment layer

The indexer is mechanical: classify, route, index. Claude adds the judgment the
mechanics cannot:

- deciding when a large trace is worth the git-lfs cost (a one-off flake vs. a
  recurring production-critical failure);
- spotting an evidence gap - a `failed` result with no screenshot attached -
  and flagging it for the run to be repeated with tracing on;
- curating which evidence belongs in the quality report's evidence summary
  versus what stays in the index for the record.
