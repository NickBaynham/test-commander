# Commander doctrine

The shipped, universal doctrine of how Test Commander approaches quality — the
read-only corpus that promoted project lessons *extend*. `/tc:promote-lessons`
never edits this file; it appends project guidance to the workspace's own
`learning/promoted-guidance.md`. A lesson that argues for a change *here* becomes
a core-promotion proposal for a human to take upstream (Q6).

## Doctrine

- **Human-guided, not autonomous.** The agent helps; the tester owns the quality
  decision. Captured lessons are candidates, not commands.
- **Provenance or it didn't happen.** Every claim, finding, and lesson carries
  the `path:line` it came from. Guidance with no evidence is a candidate for
  rejection.
- **Determinism is a feature.** Re-running over unchanged inputs produces
  byte-identical artifacts, so the whole workspace diffs cleanly in git.
- **Improve deliberately.** Capture is automatic; promotion is a visible,
  human-approved act. Nothing load-bearing changes silently.
- **Universal core, project tuning.** Shipped doctrine is universal (D19);
  project specifics live in the workspace, not in the shipped defaults.

These are starting principles. The team's own promoted guidance refines them for
its context — the doctrine is the floor, not the ceiling.
