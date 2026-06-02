# Output validation and secret safety

## Output validation

After execution, `governance.validation.validate(plan, result)` confirms the
diff matches the plan — fail-closed:

- every changed file is **within the planned write scope** (`plan.writes`);
- **no secret file** was touched (`.env`, `secret`, `credential`, `.pem`,
  `id_rsa`, `deploy`);
- the **expected outputs were produced** (`plan.expected_artifacts`).

Any violation makes `ValidationResult.ok` false and marks the run failed (admin
review). The pipeline attaches the verdict to its result; an out-of-scope write
or a secret-file touch fails the run even though the adapter "succeeded".

## Secret safety

- `redact(text)` masks secret-bearing assignments (anything whose key contains
  `KEY` / `TOKEN` / `SECRET` / `PASSWORD` / `CREDENTIAL`) so logs, artifacts, and
  prompts never carry secret values.
- `flags_env_var_print(text)` flags attempts to dump the environment
  (`printenv`, `os.environ`, `echo $VAR`, `env |`, `${VAR}`).

Provider keys stay server-side and are injected only into the runtime jobs that
need them; they never reach the frontend or the prompt.

## See also

- [Agent adapters](agent-adapters.md)
- [tc-governance skill](../SKILL.md)
