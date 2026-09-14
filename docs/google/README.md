# Google Agent Runtime

The validated Google component is a Gemini Enterprise Agent Platform Agent Runtime deployed with a dedicated Agent Identity.

The runtime:

- hosts the Google ADK agent;
- obtains its identity assertion from the Google metadata identity endpoint;
- requests `api://AzureADTokenExchange` as the assertion audience;
- performs the Entra T1/T2 exchanges inside the runtime; and
- returns only safe validation metadata.

Use [the deployment guide](../deployment-guide.md) for the end-to-end sequence and [identity and federation](../identity-and-federation.md) for the trust mapping.

The baseline retains `vertexai.Client` to preserve validated behavior. Migration to `agentplatform.Client` is unvalidated technical debt and belongs in a separate change.
