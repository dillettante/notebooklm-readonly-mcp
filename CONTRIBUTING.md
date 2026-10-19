# Contributing

Use Python 3.11+, clone the repo, then `uv sync --frozen --no-editable --group dev --reinstall-package notebooklm-readonly-mcp`. Run pytest, ruff, and
`python scripts/check_public.py` before submitting changes. Use synthetic fixtures only; never record
real notebooks, account information, browser state or OAuth credentials in tests or Git history.

Preserve full indexed text, real citation mappings, explicit errors and notebook allowlists. Do not
add write/delete/share tools without a separate design discussion. Any tool with a chat-history or
other side effect must advertise it honestly in MCP annotations. Add regression coverage for auth
and data-boundary changes. Note actual client UI validation separately from protocol tests.
