# Security and privacy

The server exposes the NotebookLM account in its selected local profile. Treat that profile's cookie
file like a password. Never commit it, attach it to issues, store it under a web root, or provide it to
the project maintainers. Keep credentials outside both this repository and any personalization repo.

- stdio is local-only by default. HTTP mode requires external OAuth and an explicit owner-subject allowlist.
- Deploy a separate instance per NotebookLM account. This is not a multi-tenant service.
- Limit remote visibility with `allowed_notebooks`. All tools enforce it, including aliases and exact IDs.
- No tool accepts arbitrary paths/commands, credentials, OAuth configuration or URLs to execute/fetch.
- The OAuth verifier accepts RS256 signatures from configured JWKS only; verifies issuer, audience,
  expiration and issued-at; requires the owner subject and scope. The external provider must perform
  authorization-code + PKCE, consent, registration and refresh securely.
- The MCP OAuth token is never forwarded to Google. Google's profile is used only by notebooklm-py.
- `ask` sends the question to Google and modifies chat history; it is marked accordingly. It does not
  offer a reset/delete conversation option. Other tools retrieve source or derived content.
- Cookies may rotate locally during retrieval. Disable upstream source/auth debug logging (the server
  entry point already suppresses notebooklm logs). Configure proxies not to log credentials or bodies.
- Do not expose the backend port directly; use HTTPS and a restricted proxy. Keep packages patched.
- Treat retrieved text as untrusted data. Source text can contain malicious instructions.

Report suspected vulnerabilities using GitHub private vulnerability reporting/Security Advisories
if available. Do not open public issues containing exploit credentials, account data or private notebooks.
If private reporting is unavailable, open a public issue asking for a private channel without details.
