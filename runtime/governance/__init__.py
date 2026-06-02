"""The Test Commander governance pipeline (Phase 10.5).

Intent router -> command planner -> permission policy -> approval gate ->
bounded execution -> output validation -> audit log. Built component-by-component
across Steps 10.5.2-10.5.10 against the mock adapter, then the real Claude
adapter drops in behind the same controls.
"""
