# Validation scope

Release candidate 0.1.0, checked 2026-10-19.

## Executed locally

- Python 3.12 on macOS: 32 pytest cases passed.
- stdio: actual MCP initialization, tool discovery, large-text retrieval through a subprocess client.
- Streamable HTTP: initialization and tool call using a signed RS256 owner access token; protected
  resource metadata; unauthenticated rejection; wrong subject/audience/issuer/signature/expiry/scope rejection.
- Notebook allowlists apply to all five operations; aliases cannot bypass them.
- An upstream failure is an error, not an empty notebook list. Exception messages do not echo upstream
  tokens/account details. Real empty lists remain valid results.
- Fulltext fixture preserves 10,000 Unicode characters; stdio fixture preserves 15,000 characters.
- Real-account smoke test: all five tools succeeded, including 9,916 characters of indexed source text
  and a grounded answer returning six citation/source references. This smoke test preceded the final
  configuration/strict-list/error-guidance changes. A subsequent live check returned Google session
  expiry (AuthError); the local OS credential store was locked, so automatic cookie refresh did not
  succeed. Final-release protocol/unit/CI tests use synthetic data. No fresh live-login success or
  continuously healthy Google session is claimed. No source text or profile is committed.
- Ruff checks, wheel/source distribution build, and publication-set privacy scan are release checks.

## Boundaries

ChatGPT, Claude web, Claude Desktop and Claude Code configuration guides follow their documented MCP
interfaces. Their individual product UIs and a real external OAuth issuer/domain were not exercised in
this local release check. They may require account-plan features or organization administrator approval.
OAuth token issuance/refresh, PKCE and registration belong to the external identity provider. The local
HTTP tests verify the resource server with synthetic signed access tokens, not a complete provider flow.

CI is configured for Linux, macOS and Windows on Python 3.11 and 3.12. A configured matrix is not evidence
that those jobs have passed; consult the GitHub Actions result for the exact release commit.

The MCP SDK may emit a pydantic-settings `lifespan` annotation warning with newer dependency versions.
Initialization, all tool calls and the HTTP tests still succeed in the checked environment. This warning
does not indicate an authentication bypass or a successful external client connection.
