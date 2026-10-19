"""OAuth resource server: delegate interactive login and token issuance to an external IdP."""

import asyncio

import jwt
from mcp.server.auth.provider import AccessToken

from .config import OAuthSettings


class OAuthVerifier:
    def __init__(self, settings: OAuthSettings):
        self.settings = settings
        self.jwks = jwt.PyJWKClient(settings.jwks_url, timeout=10, cache_jwk_set=True, lifespan=300)

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            key = await asyncio.to_thread(self.jwks.get_signing_key_from_jwt, token)
            claims = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                audience=self.settings.resource_url,
                issuer=self.settings.issuer,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
            scope = claims.get("scope", "")
            if not isinstance(scope, str):
                return None
            scopes = scope.split()
            if claims["sub"] not in self.settings.subjects or self.settings.scope not in scopes:
                return None
            return AccessToken(
                token=token,
                client_id=claims.get("azp") or claims.get("client_id") or claims["sub"],
                scopes=scopes,
                expires_at=claims["exp"],
                resource=self.settings.resource_url,
                subject=claims["sub"],
            )
        except (jwt.PyJWTError, ValueError, TypeError, KeyError, OSError):
            return None
