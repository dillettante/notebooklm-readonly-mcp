# OAuth-protected remote deployment

ChatGPT and Claude web need a remotely reachable HTTPS MCP endpoint. This package provides the
**OAuth resource server**; an external OAuth/OIDC identity provider handles authorization-code login,
PKCE, client registration, consent, token issuance and refresh. There is no built-in anonymous mode,
shared developer credential, Google-cookie upload endpoint or home-grown password login.

## One NotebookLM account per server instance

Run a dedicated server instance under your own OS user with your own NotebookLM profile. Only your
explicit allowed OAuth `sub` values may access it. OAuth signs the connector into this server; it does
**not** log into NotebookLM. Log into NotebookLM separately on the server and refresh that profile when
needed. Multiple independent users must deploy separate instances/profiles and separate OAuth audience
URLs. This project is not a multi-tenant hosted NotebookLM service.

## Prerequisites

- A persistent machine with the package installed and an already-authenticated NotebookLM profile.
- An HTTPS domain and reverse proxy to `127.0.0.1:8771`; TLS terminates at the proxy. No Docker is needed.
- An OAuth/OIDC provider supporting authorization code + PKCE and RS256 JWT **access tokens** with
  issuer/JWKS discovery and a configured API audience/resource. ID tokens are not access tokens.
- OAuth clients for ChatGPT and/or Claude. Register the callback URL shown by the client with the
  provider. Use explicit client ID/secret configuration if DCR/CIMD is unavailable. Do not guess callback
  URLs or enable arbitrary callback wildcards.

## Configure the identity provider

1. Create an API/resource whose identifier/audience is exactly `https://mcp.example.org/mcp`.
2. Define and grant the `notebooklm:read` scope to the owner client. It grants all five tools, including
   grounded Q&A with the documented chat-history side effect.
3. Configure access tokens to contain `iss`, `aud`, `sub`, `iat`, `exp`, and a space-separated `scope`.
   Only RS256 is accepted. Use a short access-token lifetime; client refresh is managed by your IdP.
4. Register each AI client, enable PKCE and configure its exact callbacks. The issuer's public
   `/.well-known/oauth-authorization-server` or OIDC discovery must advertise the endpoints the client
   needs. Providers differ in how they map RFC 8707 `resource` to audience; configure a default audience
   or the provider's resource mapping if necessary. A token with another audience is deliberately rejected.
5. Obtain the immutable `sub` of your owner account from a verified token/provider console. Add that
   exact value to the server allowlist. Tenant membership alone never grants access.

## Run

Set the following in your service manager's private environment (use `.env.example` as a variable
reference; the program does not auto-load `.env` files):

```sh
export NLM_MCP_PUBLIC_URL=https://mcp.example.org/mcp
export NLM_MCP_OAUTH_ISSUER=https://identity.example.org/
export NLM_MCP_OAUTH_JWKS_URL=https://identity.example.org/.well-known/jwks.json
export NLM_MCP_OAUTH_SUBJECTS='owner-subject-from-your-identity-provider'
export NLM_MCP_CONFIG=/absolute/private/path/config.local.json
uv run --frozen --no-editable notebooklm-readonly-mcp --transport streamable-http
```

These shell exports are for POSIX shells; in PowerShell set each with `$env:NAME = "value"`.
A nonempty `allowed_notebooks` list is mandatory in the local config; HTTP refuses to start without it. Do not reuse an example hostname or subject in production.
Install the service under an unprivileged user; keep its profile outside the checkout and outside web roots.
Prefer loopback binding and a reverse proxy on the same host. If deliberately binding a container/private
network address with `--host`, limit inbound traffic to your proxy and do not expose the backend port.

Example [Caddy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy) configuration:

```caddyfile
mcp.example.org {
    reverse_proxy 127.0.0.1:8771
}
```

Forward `/mcp` and `/.well-known/oauth-protected-resource/mcp` unchanged and preserve the public Host
header. The server permits only the configured public authority and local hosts for DNS rebinding
protection. Do not log Authorization headers, cookies, source text or full request bodies at the proxy.

## Verify before adding a cloud client

```sh
curl -i -X POST https://mcp.example.org/mcp
curl https://mcp.example.org/.well-known/oauth-protected-resource/mcp
```

The first request must return `401` and `WWW-Authenticate` pointing to resource metadata; the second
returns the exact resource/audience, issuer URL and `notebooklm:read` scope. Follow the issuer metadata
from there. Verify a wrong subject, wrong audience, expired token and missing scope are all rejected.
Use an MCP client with a legitimate owner access token to test initialization, tools and retrieval.
The issuer/JWKS and HTTPS server must be reachable from the cloud client, not only on your LAN/VPN.

Protocol tests exercise metadata, unauthorized rejection and a signed owner token over HTTP. Setting
up a real provider/domain and signing in through your ChatGPT/Claude account remain deployment tasks.

## Revocation and recovery

Remove an OAuth subject and restart this MCP service to block it. Disconnect the connector at the AI
client and revoke grants at the identity provider. Signed access tokens remain valid until expiry
unless blocked by the local allowlist; this server does not implement token introspection. Log in again
on the server when the Google session expires. Never publish or share its `storage_state.json`.
