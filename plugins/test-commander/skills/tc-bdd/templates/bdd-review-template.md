# BDD review verdict

The review writes its verdict into the per-feature summary
`bdd/summaries/<area>.md` (the `- Review verdict:` line) and routes each finding
to `requirements/open-questions.md`. This template documents both shapes.

## Summary verdict line

```
- Review verdict: pass
```

or, when findings exist:

```
- Review verdict: <N> finding(s) - categories: <cat>, <cat>
```

## Gap-signal line (in requirements/open-questions.md)

```
- [tc-bdd/bdd-review-<area>] [bdd-review] <category>: scenario '<name>' <message>.
```

Where `<category>` is one of `ambiguous-step`, `missing-tag`, `untraceable`,
`ui-coupled-step`, `missing-examples`, `conjunction-overload`. Signals are
deduplicated by `(source-id, question)`.
