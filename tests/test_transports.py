import sys
from pathlib import Path
from types import SimpleNamespace

import httpx
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from notebooklm_readonly_mcp.config import OAuthSettings, Settings
from notebooklm_readonly_mcp.server import create_server


async def test_stdio_initialization_tools_and_large_source():
    params = StdioServerParameters(
        command=sys.executable, args=[str(Path(__file__).with_name("fixture_server.py"))]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert len(tools.tools) == 5
            result = await session.call_tool("source_fulltext", {"notebook": "sample", "source_id": "sample"})
            assert not result.isError
            assert len(result.structuredContent["text"]) == 15000


async def test_signed_owner_can_initialize_and_retrieve_over_http(monkeypatch):
    import time

    class Stub:
        async def call(self, operation, **kwargs):
            return {"notebooks": [{"id": "sample-notebook", "title": "Sample"}]}

    oauth = OAuthSettings(
        issuer="https://identity.example.org/",
        jwks_url="https://identity.example.org/jwks",
        resource_url="https://mcp.example.org/mcp",
        subjects=frozenset({"owner"}),
    )
    server = create_server(
        Settings(allowed_notebooks=frozenset({"sample-notebook"})), oauth=oauth, backend=Stub()
    )
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        server._token_verifier.jwks,
        "get_signing_key_from_jwt",
        lambda token: SimpleNamespace(key=private.public_key()),
    )
    token = jwt.encode(
        {
            "sub": "owner",
            "iss": oauth.issuer,
            "aud": oauth.resource_url,
            "iat": int(time.time()) - 1,
            "exp": int(time.time()) + 120,
            "scope": oauth.scope,
        },
        private,
        algorithm="RS256",
    )
    app = server.streamable_http_app()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json, text/event-stream"}
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://mcp.example.org", headers=headers
        ) as client:
            init = await client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {},
                        "clientInfo": {"name": "protocol-test", "version": "1"},
                    },
                },
            )
            assert init.status_code == 200
            assert init.json()["result"]["capabilities"]["tools"] is not None
            call = await client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "list_notebooks", "arguments": {}},
                },
            )
            assert call.status_code == 200
            assert call.json()["result"]["structuredContent"]["notebooks"][0]["id"] == "sample-notebook"
