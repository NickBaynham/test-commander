# Anomaly record template

A single anomaly entry in the recorded-session JSON carries this structure:

```json
{
  "timestamp": "2026-05-28T10:00:12.815Z",
  "event_type": "anomaly",
  "page_url": "/dashboard",
  "anomaly": {
    "category": "slow-response",
    "severity": "medium",
    "page_url": "/dashboard",
    "reproduction": "GET /workspaces returned in 3812ms; acceptable threshold for dashboard load is 1000ms.",
    "screenshot_id": "S-002"
  },
  "_knowledge": "knowledge: slow-response"
}
```

## Required fields

| Field | Notes |
| --- | --- |
| `timestamp` | ISO-8601 UTC. Used to detect adjacent screenshots for the missing-evidence review check. |
| `event_type` | Must be the literal string `"anomaly"`. |
| `anomaly.category` | One of the universal core: `slow-response`, `console-error`, `broken-link`, `missing-evidence`, `auth-mismatch`, `unexpected-state`. |
| `anomaly.severity` | One of the universal core: `low`, `medium`, `high`, `critical`. |
| `anomaly.reproduction` | A short string describing how to reproduce the anomaly. Surfaces in the exploration note's Anomalies table. |
| `anomaly.screenshot_id` | The ID of a captured screenshot, OR `null` if no screenshot is associated. The missing-evidence review check fires when this is `null` AND no `screenshot` event exists within ±3s of `timestamp`. |
| `_knowledge` | Optional. Carries the literal phrase `knowledge: <category>` so the scaffold test's uniform marker regex finds it (per the Phase 3 Step 3.1 marker-uniformity lesson). |

## Optional fields

| Field | Notes |
| --- | --- |
| `anomaly.page_url` | The page the anomaly occurred on. If omitted, falls back to the outer `page_url`. |

## See also

- [Session-based-test-management methodology](../methodology/session-based-test-management.md) - the universal anomaly categories + their detection rules.
- [Seeded recorded session](../../../../../tests/fixtures/seeded-exploration-session/recorded-session.json) - 6 anomaly entries, one per universal category.
