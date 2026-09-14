# Microsoft Entra Agent ID

The Entra portion of the reference contains:

- one Agent ID blueprint;
- a federated identity credential built from the live Google runtime claims;
- approved and deny child Agent Identities;
- the `Investigation.Read` protected API application role; and
- narrowly scoped Conditional Access validation.

Start with [Identity and federation](../identity-and-federation.md), then follow [Conditional Access](../conditional-access.md) only after the 401, 403, and 200 controls pass.

Agent 365 Connected Platform / Registry discovery remains a separate plane. See [Agent 365 Registry discovery boundary](../agent365-registry.md).
