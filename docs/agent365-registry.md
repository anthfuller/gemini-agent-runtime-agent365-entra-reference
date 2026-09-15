# Agent 365 Registry Discovery Boundary

## Purpose

Agent 365 Connected Platform / Registry discovery and Entra Agent ID federation are related governance concerns but separate technical planes.

| Capability | Agent 365 Connected Platform / Registry | Microsoft Entra Agent ID |
|---|---|---|
| Inventory and discovery | Yes | Not the validated purpose |
| Registration and management context | Yes | Identity objects may be governed separately |
| Accept Google workload assertion | No | Blueprint federated credential |
| Select child Agent Identity | No | Blueprint and `fmi_path` |
| Issue protected API token | No | Microsoft identity platform |
| Application-role authorization | No | Child service principal and protected API |
| Conditional Access | No | Entra policy evaluation |

## Validated observation

In the controlled environment, a manual Connected Platform synchronization discovered the new Google runtime after it surfaced as a Reasoning Engine resource. That discovery did not create the Entra blueprint, child Agent Identities, federated credential, or protected API authorization.

The discovered record could remain `Unmanaged` while the separate Entra federation and governance path worked.

## Correlation limitation

No documented, validated method was established for retroactively associating the discovered Google record with the separately created Entra blueprint and child Agent Identity.

Do not:

- infer an Agent 365 registration identifier from a Google resource path;
- patch a registration using an unverified identifier;
- treat an `Unmanaged` record as proof that Entra federation failed; or
- claim Registry discovery performs authentication or token issuance.

## Microsoft Agent365-python

Microsoft [`Agent365-python`](https://github.com/microsoft/Agent365-python) is an external SDK and reference. Its source is not included here, and the validated T1/T2 federation flow does not import it.

SDK-based registration, tooling, and observability must be designed and validated independently against the current upstream repository and Microsoft documentation.

## Implementation decision

Implementers may configure Registry discovery as a separate workstream after the identity path is understood. Use distinct acceptance criteria and evidence for:

1. Agent discovery and inventory.
2. Entra Agent ID authentication and governance.
3. Any future SDK-based integration.
