import base64
import json
import os

import requests
from google.adk.agents import Agent


TENANT_ID = os.environ["ENTRA_TENANT_ID"]
BLUEPRINT_APP_ID = os.environ["ENTRA_BLUEPRINT_APP_ID"]
PROTECTED_API_SCOPE = os.environ["PROTECTED_API_SCOPE"]
PROTECTED_API_BASE_URL = os.environ["PROTECTED_API_BASE_URL"].rstrip("/")

GOOGLE_TOKEN_AUDIENCE = os.getenv(
    "GOOGLE_TOKEN_AUDIENCE", "api://AzureADTokenExchange"
)
ENTRA_TOKEN_SCOPE = os.getenv(
    "ENTRA_TOKEN_SCOPE", "api://AzureADTokenExchange/.default"
)
INVESTIGATION_ID = os.getenv("INVESTIGATION_ID", "LAB-001")

METADATA_IDENTITY_URL = (
    "http://metadata.google.internal/computeMetadata/v1/"
    "instance/service-accounts/default/identity"
)
CLIENT_ASSERTION_TYPE = (
    "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
)


def _decode_jwt_payload(token: str) -> dict:
    """Decode a JWT payload for safe diagnostics without validating it."""
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))


def _get_google_agent_identity_token() -> str:
    """Obtain the Google Agent Identity JWT-SVID without printing it."""
    response = requests.get(
        METADATA_IDENTITY_URL,
        headers={"Metadata-Flavor": "Google"},
        params={"audience": GOOGLE_TOKEN_AUDIENCE, "format": "full"},
        timeout=10,
    )
    response.raise_for_status()
    return response.text.strip()


def diagnose_agent_identity() -> dict:
    """Return safe Google Agent Identity claims, never the raw JWT."""
    claims = _decode_jwt_payload(_get_google_agent_identity_token())
    return {
        "success": True,
        "issuer": claims.get("iss"),
        "subject": claims.get("sub"),
        "audience": claims.get("aud"),
        "issued_at": claims.get("iat"),
        "expires_at": claims.get("exp"),
        "certificate_bound": "cnf" in claims,
    }


def _resolve_child_agent_id(selected_mode: str = "denied") -> str:
    if selected_mode not in {"approved", "denied"}:
        raise ValueError("selected_mode must be approved or denied")
    env_name = (
        "APPROVED_AGENT_ID"
        if selected_mode == "approved"
        else "DENIED_AGENT_ID"
    )
    child_agent_id = os.getenv(env_name)
    if not child_agent_id:
        raise RuntimeError(
            f"Required runtime environment variable {env_name} is missing"
        )
    return child_agent_id


def validate_entra_agent_id_federation(
    selected_mode: str = "denied",
) -> dict:
    """Perform blueprint T1 and child Agent Identity resource exchanges."""
    try:
        child_agent_id = _resolve_child_agent_id(selected_mode)
        google_assertion = _get_google_agent_identity_token()
        token_url = (
            "https://login.microsoftonline.com/"
            f"{TENANT_ID}/oauth2/v2.0/token"
        )

        t1_response = requests.post(
            token_url,
            data={
                "client_id": BLUEPRINT_APP_ID,
                "scope": ENTRA_TOKEN_SCOPE,
                "grant_type": "client_credentials",
                "client_assertion_type": CLIENT_ASSERTION_TYPE,
                "client_assertion": google_assertion,
                "fmi_path": child_agent_id,
            },
            timeout=20,
        )
        if t1_response.status_code != 200:
            error_body = t1_response.json()
            return {
                "success": False,
                "stage": "t1_blueprint_exchange",
                "http_status": t1_response.status_code,
                "error": error_body.get("error"),
                "error_description": error_body.get("error_description"),
            }

        t1_body = t1_response.json()
        t1_token = t1_body.get("access_token")
        if not t1_token:
            return {
                "success": False,
                "stage": "t1_blueprint_exchange",
                "error": "No T1 access token returned.",
            }

        resource_response = requests.post(
            token_url,
            data={
                "client_id": child_agent_id,
                "scope": PROTECTED_API_SCOPE,
                "grant_type": "client_credentials",
                "client_assertion_type": CLIENT_ASSERTION_TYPE,
                "client_assertion": t1_token,
            },
            timeout=20,
        )
        if resource_response.status_code != 200:
            error_body = resource_response.json()
            return {
                "success": False,
                "stage": "child_agent_resource_exchange",
                "t1_success": True,
                "http_status": resource_response.status_code,
                "error": error_body.get("error"),
                "error_description": error_body.get("error_description"),
            }

        resource_body = resource_response.json()
        resource_token = resource_body.get("access_token")
        if not resource_token:
            return {
                "success": False,
                "stage": "child_agent_resource_exchange",
                "t1_success": True,
                "error": "No protected API access token returned.",
            }

        resource_claims = _decode_jwt_payload(resource_token)
        header_segment = resource_token.split(".")[0]
        header_padding = "=" * (-len(header_segment) % 4)
        resource_header = json.loads(
            base64.urlsafe_b64decode(
                header_segment + header_padding
            ).decode("utf-8")
        )

        api_response = requests.get(
            f"{PROTECTED_API_BASE_URL}/investigations/{INVESTIGATION_ID}",
            headers={"Authorization": f"Bearer {resource_token}"},
            timeout=30,
        )
        try:
            api_body = api_response.json()
        except ValueError:
            api_body = {"detail": "Non-JSON response"}

        return {
            "success": True,
            "selected_mode": selected_mode,
            "stage": "child_agent_resource_exchange",
            "t1_success": True,
            "resource_token_success": True,
            "http_status": resource_response.status_code,
            "token_type": resource_body.get("token_type"),
            "expires_in": resource_body.get("expires_in"),
            "resource_audience": resource_claims.get("aud"),
            "resource_issuer": resource_claims.get("iss"),
            "resource_token_version": resource_claims.get("ver"),
            "resource_kid": resource_header.get("kid"),
            "resource_alg": resource_header.get("alg"),
            "resource_subject": resource_claims.get("sub"),
            "resource_appid": (
                resource_claims.get("appid") or resource_claims.get("azp")
            ),
            "roles": resource_claims.get("roles", []),
            "api_http_status": api_response.status_code,
            "api_response": api_body,
            "raw_token_exposed": False,
        }
    except Exception as exc:
        return {
            "success": False,
            "stage": "entra_agent_id_federation",
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }


root_agent = Agent(
    name=os.getenv(
        "GOOGLE_ADK_AGENT_NAME", "Gemini_Entra_Agent_ID_Reference"
    ),
    model=os.getenv("GOOGLE_AGENT_MODEL", "gemini-2.5-flash"),
    description=(
        "Validates Google Agent Runtime to Microsoft Entra "
        "Agent ID federation."
    ),
    instruction="""
You are a federation validation agent.

Your purpose is to validate identity federation between
Google Agent Runtime and Microsoft Entra Agent ID.

When asked to inspect Google identity claims, use
diagnose_agent_identity.

When asked to test, validate, or perform Entra Agent ID
federation, use validate_entra_agent_id_federation.

Never expose:
- Google ID tokens
- Microsoft access tokens
- JWT assertions
- credentials
- private keys
- secrets

Return only safe validation results and token metadata.
""",
    tools=[diagnose_agent_identity, validate_entra_agent_id_federation],
)
