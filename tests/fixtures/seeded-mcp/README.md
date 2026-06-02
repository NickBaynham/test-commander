# seeded-mcp fixture

Sample MCP tool calls the Phase-11 MCP server and Runtime API are exercised
against. `tool-calls.yaml` lists, for each call: the tool name, its arguments,
the role of the caller, the expected permission level the request classifies to,
and whether it is an unsafe call the policy must refuse for a low-privilege role.

The fixture is universal (Decision D19): no product-specific vocabulary. It is
used by the MCP round-trip tests (11.3) and the permission-gate tests (11.4).
