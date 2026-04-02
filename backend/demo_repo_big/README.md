# BigDemo Monolith (stress test)

Internal dashboard + auth stack. Lots of legacy modules; most are irrelevant to any single bugfix.

## Areas

- `src/auth/` — login, tokens, session
- `src/api/` — HTTP handlers
- `src/dashboard/` — widgets (usage charts)
- `src/legacy/` — deprecated batch jobs

If you only need to fix **login / 401**, you should not load the entire tree into the LLM.
