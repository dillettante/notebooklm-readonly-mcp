# Configuration

Credentials stay in the upstream NotebookLM profile, outside this repository. The MCP tools never
accept credentials, profile paths, arbitrary shell commands or URLs to fetch as tool arguments.

| Environment variable | Default / purpose |
|---|---|
| `NLM_MCP_PROFILE` | Upstream default profile if omitted |
| `NLM_MCP_STORAGE` | Optional absolute path to your upstream storage state |
| `NLM_MCP_CONFIG` | Optional local JSON aliases and notebook allowlist |
| `NLM_MCP_TIMEOUT` | Overall call timeout, 120 seconds; allowed range 1–600 |

Use `examples/config.example.json` as a starting point. Copy it to `config.local.json` (gitignored),
replace the example notebook IDs, then set `NLM_MCP_CONFIG` to its absolute path in your client's env.
An empty `allowed_notebooks` list exposes all notebooks accessible by that account. A nonempty list
is enforced for all five tools. Aliases cannot bypass it. HTTP mode requires a nonempty list and refuses to start without it.

Upstream `NOTEBOOKLM_*` variables also affect notebooklm-py. In particular, do not inject
`NOTEBOOKLM_AUTH_JSON` from untrusted sources. Prefer profile files managed by `notebooklm login`.
Use the matching profile when logging in (`notebooklm --profile PROFILE login`).

HTTP mode always requires the OAuth environment variables in [remote.md](remote.md). It cannot be
turned into an anonymous network service with a flag. Local stdio inherits trust from its host client.
