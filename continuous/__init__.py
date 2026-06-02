"""Test Commander continuous quality agent mode (Phase 13).

Watches application changes, maps them to impacted features, finds coverage
gaps, and proposes new tests - running the watch -> analyze -> propose -> PR loop
through the same Phase-10.5 pipeline. The configured autonomy mode (0-4) is a
ceiling on what auto-approves; nothing above it executes without explicit human
approval.
"""
