# Visual documentation methodology

How Test Commander turns committed workspace artifacts into diagrams and
infographics, and the two disciplines that keep those visuals trustworthy.

## Generate-and-cite, never invent

Every visual is rendered **only** from committed workspace artifacts — the
traceability maps, the requirements inventory, the risk register, the quality
report, the system model, the user-journey index, the automation plan. A
generator never fabricates a node, edge, or metric that is not present in a
source.

Every generated file ends with a `> Sources:` footer listing the workspace path
of each artifact it drew from. The "sources cited" check is mechanical, not a
reviewer's discipline: the test suite asserts the footer exists and names the
artifacts the generator read.

When a required source is missing or still a template stub, the generator
**refuses** (exit 2) with a message that points at the command that produces it
(for example, `/tc:diagram-flow` directs the user at `/tc:learn-from-docs` when
`product-knowledge/user-journeys.md` is absent). A diagram is never drawn from
an empty or placeholder source.

## Mermaid text is the source of truth

The `/tc:diagram-*` commands and `/tc:generate-infographic` emit deterministic,
byte-stable Mermaid/Markdown only — no binaries. The same workspace state
produces byte-identical output on every run (nodes and edges are sorted; no
timestamps leak into the diagram body). This makes visuals diffable and
reviewable in a pull request.

Rendering to SVG/PNG is a separate step owned by `/tc:render-visuals`, the only
command that shells out (to the Mermaid CLI). It is refused under pytest, so the
suite asserts the Mermaid *source*, never a rendered binary.

## The Claude judgment layer

The helpers extract and lay out exactly what the sources contain. Interpretation
— which journeys matter most, how to caption a risk cluster, what story an
infographic should tell — is the human-or-Claude layer on top. The helper
guarantees fidelity and determinism; Claude adds the narrative when presenting
the visual to a user. The helper never editorializes inside the diagram.

## Output layout

Mermaid sources land under `<workspace>/visuals/mermaid/<name>.md`; rendered
output under `visuals/svg/` and `visuals/png/`; infographics under
`visuals/infographic/`. Nothing outside `visuals/` is ever written.

## See also

- [Diagram standards](diagram-standards.md) - the per-kind Mermaid conventions.
- [tc-visualize skill](../SKILL.md)
