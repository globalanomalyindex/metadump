# metadump-skill

A Claude Code plugin/skill that turns a prompt into a **meta dump**: one large structured JSON file of retrieval metadata (tiered keywords, anti-keywords, descriptions, palettes, patterns, inspiration) that the model then queries like a search index throughout the build.

## Agent skills

### Issue tracker

Local markdown under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Development

- Tests: `python3 -m unittest discover -s tests` (finalize.py) and `node --test tests/workflow.test.mjs` (Workflow script control flow with mocked agents).
- Validate: `claude plugin validate .`
- `skills/metadump/scripts/finalize.py` is Python 3.9+ standard library only; keep it that way so it runs anywhere the skill is installed.
- Use the glossary's terms (`GLOSSARY.md`) in code, docs and skill text.
