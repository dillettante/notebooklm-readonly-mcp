# Client setup

The common server implements MCP; it does not call OpenAI or Anthropic APIs itself. Choose the local
or remote route below. These are client configuration recipes; vendor UI end-to-end tests are not
claimed. Menu labels and connector access vary by client version, account and workspace policy.

## Codex

After installing and logging in, add to your Codex `config.toml`. Replace `/absolute/path/to/checkout`
with your checkout path; use the full path to `uv` if your desktop app cannot find it.

```toml
[mcp_servers.notebooklm]
command = "uv"
args = ["run", "--frozen", "--no-editable", "--directory", "/absolute/path/to/checkout", "notebooklm-readonly-mcp"]
```

Alternatively register using `codex mcp add notebooklm -- uv run --frozen --no-editable --directory
/absolute/path/to/checkout notebooklm-readonly-mcp` (one terminal line).
Restart/reconnect the client. Ask it to list your NotebookLM notebooks and retrieve one source.
For remote deployment configure `url = "https://mcp.example.org/mcp"` and use the client's MCP OAuth login.

Official reference: https://developers.openai.com/codex/mcp

## Claude Code

Run as one line after local login:

```sh
claude mcp add --transport stdio --scope user notebooklm -- uv run --frozen --no-editable --directory /absolute/path/to/checkout notebooklm-readonly-mcp
```

Run `/mcp` to inspect the connection. A project-scoped `.mcp.json` example is in `examples/`.
To use the OAuth endpoint instead: `claude mcp add --transport http notebooklm https://mcp.example.org/mcp`,
then follow `/mcp` authentication. A remote server is configured as `type: http`, not stdio.

Official reference: https://code.claude.com/docs/en/mcp

## Claude Desktop

Use **Settings → Developer → Edit Config** for a local server (availability varies by desktop version).
Merge `examples/claude-desktop.json` into your existing `claude_desktop_config.json`; replace the checkout
path and use an absolute `uv` command path if necessary. On Windows escape JSON backslashes as `\\` or
use forward slashes. Restart Claude Desktop and inspect the available tools.

For a remote server use **Connectors**, as described under Claude web. Do not place a GitHub URL in
the remote server URL field.

## ChatGPT

1. Complete [remote deployment](remote.md) and confirm HTTPS/OAuth discovery and owner-only access.
2. In ChatGPT open Plugins/Apps (the current label varies), select **Add custom MCP server** / a custom
   app in developer mode. If unavailable, check your plan and workspace administrator's settings.
3. Enter `https://mcp.example.org/mcp` and choose **OAuth**.
4. Use the client ID and secret registered for ChatGPT at your identity provider, or its supported
   dynamic registration mechanism. Follow sign-in as an allowed owner subject.
5. Install/enable the resulting connector and try `list_notebooks`, then `source_fulltext`.

HTTP transport and metadata are tested at the protocol level. This repository does not include a
public ChatGPT app-directory listing or a hosted URL, and does not claim your account's UI was tested.

Official references:
- https://developers.openai.com/api/docs/guides/custom-mcp-server
- https://developers.openai.com/apps-sdk/build/auth

## Claude web

1. Complete [remote deployment](remote.md).
2. In Claude go to **Customize/Settings → Connectors → Add custom connector**.
3. Enter `https://mcp.example.org/mcp`. Choose sign-in with OAuth.
4. If your provider does not support Claude's published identity or automatic registration, select
   **Use your own OAuth client** and supply the credentials registered for Claude at your provider.
5. Authenticate as the allowed owner subject and enable the connector for a conversation.

An organization administrator may need to add or approve the connector. Mobile availability follows
the client's remote-connector support; a local desktop stdio configuration does not by itself add a web
or mobile connector.

Official reference:
https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp
