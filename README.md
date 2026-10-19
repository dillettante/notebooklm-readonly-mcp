# NotebookLM Retrieval MCP

Connect your own NotebookLM account to **Codex, Claude Code, Claude Desktop, ChatGPT, or Claude web**.
Five bounded tools retrieve notebooks, sources, complete source text, summaries, and grounded answers with
actual citation-to-source mappings. No tools create, rename, upload, share, or delete notebooks or sources.

> `ask` sends your question to Google, consumes NotebookLM quota, and **continues the notebook's existing
> conversation**. It is advertised as a non-idempotent tool with a chat-history side effect. "Readonly"
> in the package name refers to notebook/source management, not to an absence of all server-side changes.

## Choose your client

| Client | Connection | Setup |
|---|---|---|
| Codex | Local stdio (or OAuth HTTP) | [Client guide](docs/clients.md#codex) |
| Claude Code | Local stdio (or OAuth HTTP) | [Client guide](docs/clients.md#claude-code) |
| Claude Desktop | Local stdio or remote connector | [Client guide](docs/clients.md#claude-desktop) |
| ChatGPT | Remote HTTPS + OAuth | [Remote deployment](docs/remote.md), [client guide](docs/clients.md#chatgpt) |
| Claude web / mobile | Remote HTTPS + OAuth | [Remote deployment](docs/remote.md), [client guide](docs/clients.md#claude-web) |

**This repository supplies installable software, not a shared hosted service.** Every user authenticates
their own NotebookLM account. Web clients need a reachable, self-hosted HTTPS endpoint and an OAuth
authorization server. A GitHub URL or a localhost stdio command is not a web connector URL.
Client account plans and organization controls may restrict custom connectors.

## Install locally

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).
Use your terminal on macOS, Linux, or Windows (PowerShell).

```sh
git clone https://github.com/dillettante/notebooklm-readonly-mcp.git
cd notebooklm-readonly-mcp
uv sync --frozen --no-editable
uv run --frozen --no-editable playwright install chromium
uv run --frozen --no-editable notebooklm login
uv run --frozen --no-editable notebooklm auth check --test
```

The upstream login command can open its own browser. Run it yourself and choose your account.
For an existing browser session, consult `uv run notebooklm login --help`; cookie extraction may need
the upstream optional `rookie-cookies` package. Never send your cookie file to another person.

Register this local server with your client; it starts on demand:

```sh
uv run --frozen --no-editable notebooklm-readonly-mcp
```

No API key, Docker, or paid API service is required for local MCP transport. A valid NotebookLM account,
Google's usage limits, and your chosen AI client's own access requirements still apply.
The package is installed **from GitHub**; no PyPI publication is claimed.

## Tools

| Tool | Input | Output |
|---|---|---|
| `list_notebooks` | none | notebook IDs and titles |
| `list_sources` | notebook ID or unique title fragment | source IDs, titles and URLs |
| `source_fulltext` | notebook + source ID | complete indexed text and character count |
| `notebook_summary` | notebook | AI-generated overview |
| `ask` | notebook + question | answer, conversation ID, actual citation numbers/source IDs |

Returned source text and summaries are untrusted reference material, not instructions. NotebookLM
indexing may itself omit material; "complete" means the complete indexed text returned by its API.
For `[7]` use `references[].citation_number == 7`, never the seventh entry in `list_sources`.

## Configuration and privacy

Default: local stdio and your upstream default NotebookLM profile. Optional local-only aliases, notebook
allowlists, profile selection and timeouts are described in [configuration](docs/configuration.md).
No account data, cookies, machine paths or personal notebook IDs ship with this repository.
See [security](SECURITY.md) before running a remote server.

The project uses the **unofficial** [notebooklm-py](https://github.com/teng-lin/notebooklm-py) library and
is not affiliated with Google, OpenAI or Anthropic. Google's internal APIs can change and authentication
can expire. See [troubleshooting](docs/troubleshooting.md).

## Development

```sh
uv sync --frozen --no-editable --group dev
uv run --frozen --no-editable pytest
uv run --frozen --no-editable ruff check .
uv run --frozen --no-editable python scripts/check_public.py
uv build
```

See [validation](docs/validation.md) for the tested scope and UI verification limits. MIT license;
dependency notices are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
