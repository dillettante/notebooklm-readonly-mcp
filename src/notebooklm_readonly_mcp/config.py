"""Local configuration. No credentials are accepted through MCP tool arguments."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


def https_url(value: str, name: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{name} must be an HTTPS URL without credentials, query or fragment")
    return value


@dataclass(frozen=True)
class Settings:
    profile: str | None = None
    storage: str | None = None
    aliases: dict[str, str] = field(default_factory=dict)
    allowed_notebooks: frozenset[str] = frozenset()
    timeout: int = 120

    @classmethod
    def from_env(cls) -> "Settings":
        data = {}
        if filename := os.environ.get("NLM_MCP_CONFIG"):
            data = json.loads(Path(filename).expanduser().read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Configuration must be a JSON object")
        aliases = data.get("aliases", {})
        allowed = data.get("allowed_notebooks", [])
        if not isinstance(aliases, dict) or any(
            not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
            for k, v in aliases.items()
        ):
            raise ValueError("aliases must map nonempty names to notebook IDs")
        if not isinstance(allowed, list) or any(not isinstance(v, str) or not v for v in allowed):
            raise ValueError("allowed_notebooks must be a list of notebook IDs")
        timeout = int(os.environ.get("NLM_MCP_TIMEOUT", "120"))
        if not 1 <= timeout <= 600:
            raise ValueError("NLM_MCP_TIMEOUT must be between 1 and 600 seconds")
        return cls(
            profile=os.environ.get("NLM_MCP_PROFILE") or None,
            storage=os.path.expanduser(os.environ["NLM_MCP_STORAGE"])
            if os.environ.get("NLM_MCP_STORAGE")
            else None,
            aliases={k.strip().casefold(): v for k, v in aliases.items()},
            allowed_notebooks=frozenset(allowed),
            timeout=timeout,
        )


@dataclass(frozen=True)
class OAuthSettings:
    issuer: str
    jwks_url: str
    resource_url: str
    subjects: frozenset[str]
    scope: str = "notebooklm:read"

    @classmethod
    def from_env(cls) -> "OAuthSettings":
        values = {
            key: os.environ.get(key, "")
            for key in (
                "NLM_MCP_OAUTH_ISSUER",
                "NLM_MCP_OAUTH_JWKS_URL",
                "NLM_MCP_PUBLIC_URL",
                "NLM_MCP_OAUTH_SUBJECTS",
            )
        }
        if not all(values.values()):
            raise ValueError(
                "HTTP mode requires OAuth issuer, JWKS URL, public /mcp URL and allowed subjects"
            )
        resource = https_url(values["NLM_MCP_PUBLIC_URL"], "NLM_MCP_PUBLIC_URL")
        if urlsplit(resource).path != "/mcp":
            raise ValueError("NLM_MCP_PUBLIC_URL must end in /mcp with no additional path prefix")
        subjects = frozenset(s.strip() for s in values["NLM_MCP_OAUTH_SUBJECTS"].split(",") if s.strip())
        if not subjects or "*" in subjects:
            raise ValueError("At least one explicit OAuth subject is required; wildcards are forbidden")
        return cls(
            issuer=https_url(values["NLM_MCP_OAUTH_ISSUER"], "NLM_MCP_OAUTH_ISSUER"),
            jwks_url=https_url(values["NLM_MCP_OAUTH_JWKS_URL"], "NLM_MCP_OAUTH_JWKS_URL"),
            resource_url=resource,
            subjects=subjects,
        )
