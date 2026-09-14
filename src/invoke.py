import asyncio
import os
import sys

import vertexai


PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]
RESOURCE_NAME = os.environ["GOOGLE_AGENT_RUNTIME_RESOURCE_NAME"]
INVOKE_USER_ID = os.getenv("INVOKE_USER_ID", "federation-validation")
VALID_MODES = {"approved", "denied"}

selected_mode = sys.argv[1].lower() if len(sys.argv) > 1 else "denied"
if selected_mode not in VALID_MODES:
    raise SystemExit(
        "Usage: python -m src.invoke [approved|denied]"
    )

client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
remote_agent = client.agent_engines.get(name=RESOURCE_NAME)


async def main() -> None:
    result = None
    async for event in remote_agent.async_stream_query(
        user_id=INVOKE_USER_ID,
        message=(
            "Validate Entra Agent ID federation using "
            f"selected_mode={selected_mode}."
        ),
    ):
        if not isinstance(event, dict):
            continue
        content = event.get("content") or {}
        for part in content.get("parts", []):
            function_response = part.get("function_response")
            if not function_response:
                continue
            if (
                function_response.get("name")
                == "validate_entra_agent_id_federation"
            ):
                result = function_response.get("response")

    if result is None:
        raise RuntimeError(
            "No federation validation result was returned."
        )

    print("selected_mode:", result.get("selected_mode"))
    print("t1_success:", result.get("t1_success"))
    print(
        "resource_token_success:", result.get("resource_token_success")
    )
    print("roles:", result.get("roles", []))
    print("api_http_status:", result.get("api_http_status"))
    print("api_response:", result.get("api_response"))
    print(
        "raw_token_exposed:", result.get("raw_token_exposed", False)
    )


asyncio.run(main())
