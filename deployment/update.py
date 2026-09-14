import os

import vertexai
from vertexai.agent_engines import AdkApp

from src.agent import root_agent


PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
RESOURCE_NAME = os.environ["GOOGLE_AGENT_RUNTIME_RESOURCE_NAME"]
STAGING_BUCKET = os.environ["GOOGLE_AGENT_RUNTIME_STAGING_BUCKET"]

RUNTIME_REQUIREMENTS = [
    "google-cloud-aiplatform[agent_engines,adk]>=1.112",
    "google-adk[agent-identity]",
    "cloudpickle>=3.0",
    "pydantic>=2.6.4",
    "requests>=2.32",
]

REQUIRED_RUNTIME_ENV_VARS = (
    "ENTRA_TENANT_ID",
    "ENTRA_BLUEPRINT_APP_ID",
    "APPROVED_AGENT_ID",
    "DENIED_AGENT_ID",
    "PROTECTED_API_SCOPE",
    "PROTECTED_API_BASE_URL",
)
OPTIONAL_RUNTIME_ENV_VARS = (
    "GOOGLE_TOKEN_AUDIENCE",
    "ENTRA_TOKEN_SCOPE",
    "GOOGLE_ADK_AGENT_NAME",
    "GOOGLE_AGENT_MODEL",
    "INVESTIGATION_ID",
)

runtime_env_vars = {name: os.environ[name] for name in REQUIRED_RUNTIME_ENV_VARS}
runtime_env_vars.update(
    {
        name: os.environ[name]
        for name in OPTIONAL_RUNTIME_ENV_VARS
        if name in os.environ
    }
)

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
    http_options=dict(api_version="v1beta1"),
)
app = AdkApp(agent=root_agent)

updated_app = client.agent_engines.update(
    name=RESOURCE_NAME,
    agent=app,
    config={
        "staging_bucket": STAGING_BUCKET,
        "requirements": RUNTIME_REQUIREMENTS,
        "extra_packages": ["src"],
        "env_vars": runtime_env_vars,
    },
)

print("Agent update successful")
print("Resource:", updated_app.api_resource.name)
print("Effective identity:", updated_app.api_resource.spec.effective_identity)
