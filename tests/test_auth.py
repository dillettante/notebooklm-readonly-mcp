import time
from types import SimpleNamespace

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from notebooklm_readonly_mcp.auth import OAuthVerifier
from notebooklm_readonly_mcp.config import OAuthSettings, Settings
from notebooklm_readonly_mcp.server import create_server


@pytest.fixture
def oauth():
    return OAuthSettings(
        issuer="https://identity.example.org/",
        jwks_url="https://identity.example.org/jwks",
        resource_url="https://mcp.example.org/mcp",
        subjects=frozenset({"owner"}),
    )


@pytest.fixture
def verifier(oauth, monkeypatch):
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = OAuthVerifier(oauth)
    monkeypatch.setattr(
        verifier.jwks, "get_signing_key_from_jwt", lambda token: SimpleNamespace(key=private.public_key())
    )
    return verifier, private


def signed(private, **changes):
    claims = {
        "sub": "owner",
        "iss": "https://identity.example.org/",
        "aud": "https://mcp.example.org/mcp",
        "iat": int(time.time()) - 1,
        "exp": int(time.time()) + 300,
        "scope": "notebooklm:read",
    }
    claims.update(changes)
    return jwt.encode(claims, private, algorithm="RS256")


async def test_owner_token(verifier):
    verifier, private = verifier
    result = await verifier.verify_token(signed(private))
    assert result.subject == "owner"
    assert result.resource == "https://mcp.example.org/mcp"


@pytest.mark.parametrize(
    "changes",
    [
        {"sub": "other-person"},
        {"aud": "https://different.example.org/mcp"},
        {"iss": "https://different.example.org/"},
        {"exp": 1},
        {"scope": "other:scope"},
        {"scope": ["notebooklm:read"]},
    ],
)
async def test_wrong_tokens_rejected(verifier, changes):
    verifier, private = verifier
    assert await verifier.verify_token(signed(private, **changes)) is None


async def test_forged_signature(verifier):
    verifier, _ = verifier
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    assert await verifier.verify_token(signed(other)) is None


@pytest.mark.parametrize("missing", ["exp", "iat", "sub", "aud", "iss"])
async def test_missing_required_claim_rejected(verifier, missing):
    verifier, private = verifier
    claims = jwt.decode(signed(private), options={"verify_signature": False})
    claims.pop(missing)
    assert await verifier.verify_token(jwt.encode(claims, private, algorithm="RS256")) is None


async def test_unsigned_token_rejected(verifier):
    verifier, private = verifier
    claims = jwt.decode(signed(private), options={"verify_signature": False})
    assert await verifier.verify_token(jwt.encode(claims, key="", algorithm="none")) is None


def test_http_requires_notebook_allowlist(oauth):
    with pytest.raises(ValueError, match="nonempty allowed_notebooks"):
        create_server(Settings(), oauth=oauth)


def test_configuration_rejects_nonobject_json(tmp_path, monkeypatch):
    path = tmp_path / "config.local.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("NLM_MCP_CONFIG", str(path))
    with pytest.raises(ValueError, match="JSON object"):
        Settings.from_env()


async def test_http_requires_auth_and_publishes_resource_discovery(oauth):
    server = create_server(Settings(allowed_notebooks=frozenset({"sample-notebook"})), oauth=oauth)
    app = server.streamable_http_app()
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="https://mcp.example.org"
    ) as client:
        response = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert response.status_code == 401
        assert "resource_metadata=" in response.headers["www-authenticate"]
        metadata = await client.get("/.well-known/oauth-protected-resource/mcp")
        assert metadata.status_code == 200
        assert metadata.json()["resource"] == oauth.resource_url
        assert metadata.json()["authorization_servers"] == [oauth.issuer]


async def test_tools_annotate_chat_side_effect():
    tools = await create_server(Settings()).list_tools()
    assert len(tools) == 5
    by_name = {tool.name: tool for tool in tools}
    assert by_name["ask"].annotations.readOnlyHint is False
    assert by_name["ask"].annotations.idempotentHint is False
    assert by_name["source_fulltext"].annotations.readOnlyHint is True


def test_http_configuration_fails_closed(monkeypatch):
    for key in [
        "NLM_MCP_OAUTH_ISSUER",
        "NLM_MCP_OAUTH_JWKS_URL",
        "NLM_MCP_PUBLIC_URL",
        "NLM_MCP_OAUTH_SUBJECTS",
    ]:
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError):
        OAuthSettings.from_env()


def test_http_rejects_wildcard_subject(monkeypatch):
    for key, value in {
        "NLM_MCP_OAUTH_ISSUER": "https://identity.example.org/",
        "NLM_MCP_OAUTH_JWKS_URL": "https://identity.example.org/jwks",
        "NLM_MCP_PUBLIC_URL": "https://mcp.example.org/mcp",
        "NLM_MCP_OAUTH_SUBJECTS": "*",
    }.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(ValueError, match="wildcards"):
        OAuthSettings.from_env()
