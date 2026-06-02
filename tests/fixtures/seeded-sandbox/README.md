# seeded-sandbox fixture

Sample sandbox configuration and target list the Phase-12 provider abstraction
and safety guards are exercised against. `config.yaml` is a representative
`/tc:sandbox-init` output (provider, environment label, target, allow-list,
private-range block, approval requirements). `targets.yaml` lists candidate
targets, each flagged `unsafe` when the safety guards must refuse it (a private
network range, or a host not on the allow-list).

The fixture is universal (Decision D19): no product-specific vocabulary. It is
used by the provider tests (12.2), the command tests (12.3), and the
safety-guard tests (12.4).
