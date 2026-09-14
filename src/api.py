import os
from typing import Any

import jwt
import requests
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient


TENANT_ID = os.environ["ENTRA_TENANT_ID"]
API_AUDIENCE = os.environ["PROTECTED_API_AUDIENCE"]
REQUIRED_ROLE = os.getenv(
    "PROTECTED_API_REQUIRED_ROLE", "Investigation.Read"
)

ISSUER = f"https://sts.windows.net/{TENANT_ID}/"
OIDC_CONFIG_URL = (
    f"https://login.microsoftonline.com/{TENANT_ID}/"
    ".well-known/openid-configuration"
)

app = FastAPI()
bearer = HTTPBearer(auto_error=False)


def get_jwks_uri() -> str:
    response = requests.get(OIDC_CONFIG_URL, timeout=10)
    response.raise_for_status()
    return str(response.json()["jwks_uri"])


JWKS_CLIENT = PyJWKClient(get_jwks_uri())


def validate_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials
    try:
        signing_key = JWKS_CLIENT.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=API_AUDIENCE,
            issuer=ISSUER,
        )
    except Exception:
        raise HTTPException(
            status_code=401, detail="Invalid bearer token"
        ) from None

    roles = claims.get("roles", [])
    if REQUIRED_ROLE not in roles:
        raise HTTPException(
            status_code=403,
            detail="Required application role is missing",
        )
    return claims


@app.get("/investigations/LAB-001")
def get_investigation(
    _: dict[str, Any] = Depends(validate_token),
) -> dict[str, str]:
    return {
        "investigationId": "LAB-001",
        "title": "Synthetic account investigation",
        "severity": "Medium",
        "status": "Open",
        "subject": "synthetic-user-001",
        "summary": "Customer-neutral synthetic investigation record.",
    }
