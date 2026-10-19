#!/bin/sh
set -eu
cd "$(dirname "$0")"
uv sync --frozen --no-editable
printf '%s\n' 'Installed. Next: uv run --frozen --no-editable playwright install chromium' 'Then: uv run --frozen --no-editable notebooklm login'
