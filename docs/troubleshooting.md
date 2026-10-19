# Troubleshooting

- **Authentication expired / UPSTREAM_ERROR:** run `uv run --frozen --no-editable notebooklm auth check --test` locally with
  the same profile/storage settings as the server, then `uv run --frozen --no-editable notebooklm login`. Do not post the raw
  error HTML, debug log, cookies or storage state in an issue. Errors are not converted to empty lists.
- **Wrong account:** choose a named NotebookLM profile, log in to that profile and set `NLM_MCP_PROFILE`.
  A local stdio client inherits environment variables from the app; restarting may be necessary.
- **Command not found in a desktop app:** set the full path to `uv` in its MCP config. Use an absolute
  checkout directory. On Windows use a valid JSON-escaped path and restart the desktop client.
- **Notebook title matches multiple notebooks:** run `list_notebooks` and pass the exact allowed ID.
- **Source appears truncated:** this server returns the full indexed source. Your AI client may have
  its own response/context display limits. Compare `char_count`; the upstream index may also omit text.
- **HTTP won't start:** a nonempty notebook allowlist and all four OAuth settings are mandatory and the public URL must be HTTPS `/mcp`.
- **401 after sign-in:** check issuer, RS256, exact audience, expiry, owner `sub`, and `notebooklm:read`
  scope in your provider's private diagnostics. A Google login cookie is not an MCP OAuth access token.
- **Cloud client cannot connect:** localhost/private VPN URLs are unreachable to cloud clients. Follow
  [remote.md](remote.md) and check the client's account/workspace permissions and OAuth registration.
- **Google changes its API:** upstream may need a release. This project pins the version tested for
  reproducible installs. Open an issue with package versions and sanitized symptoms; avoid raw traces.
