# Repository guidance

This package exposes five NotebookLM retrieval/Q&A tools. `src/notebooklm_readonly_mcp` contains
configuration, the SDK adapter, JWT verification, transport/tool construction and the entry point.
No personal settings or credentials belong here. Use synthetic fixtures and preserve explicit errors.

Commands: `uv sync --frozen --no-editable --group dev --reinstall-package notebooklm-readonly-mcp`, `uv run --frozen --no-editable pytest`, `uv run --frozen --no-editable ruff check .`,
`uv run --frozen --no-editable python scripts/check_public.py`, `uv build`.

HTTP requires OAuth and an explicit subject allowlist. Do not bypass those boundaries to make a test
pass. Update docs/validation.md with actual tested scope, not assumed vendor UI compatibility.
