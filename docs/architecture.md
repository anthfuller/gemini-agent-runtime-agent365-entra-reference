# Architecture

## Reference status

This repository documents a validated reference pattern connecting Google Gemini Enterprise Agent Platform Agent Runtime to Microsoft Entra Agent ID and a custom protected API.

The pattern was validated in one controlled environment. It is not a universal support statement for every third-party agent runtime, tenant configuration, Conditional Access policy, or protected resource.

## Validated architecture

The implementation uses two autonomous token exchanges:

1. The agent running in Google Agent Runtime requests its Google Agent Identity JWT-SVID from the Google metadata service. The requested audience is `api://AzureADTokenExchange`.
2. The runtime submits that Google assertion to the Microsoft identity platform token endpoint. The Agent Identity blueprint application is the client, and `fmi_path` identifies the selected child Agent Identity. A successful response is the blueprint T1 token.
3. The runtime submits the T1 token in a second client-credentials exchange. The selected child Agent Identity is the client, and the requested scope belongs to the custom protected API.
4. Microsoft Entra evaluates the second exchange, including Conditional Access policies that target the child Agent Identity.
5. When the second exchange succeeds, the agent calls the protected API with the resource token.
6. The API validates the token signature, issuer, audience, and `Investigation.Read` application role before returning the synthetic `LAB-001` record.

The README provides the compact architecture flow. The remainder of this document defines the detailed trust boundaries and token sequence.

## Components and responsibilities

| Component | Responsibility | Trust boundary |
|---|---|---|
| Google Agent Runtime | Hosts the Google ADK agent and executes the federation tool | Google Cloud |
| Google metadata identity endpoint | Issues the runtime-bound Google Agent Identity assertion | Google Cloud identity |
| Entra Agent Identity blueprint | Establishes the federated trust and receives the Google assertion | Microsoft Entra tenant |
| Child Agent Identity | Represents the selected autonomous agent identity and receives resource permissions | Microsoft Entra tenant |
| Conditional Access | Evaluates policy at the child identity resource-token exchange | Microsoft Entra policy plane |
| Protected API | Validates the Entra token and enforces the application role | Customer application boundary |
| Agent 365 Connected Platform / Registry | Provides a separate registration, management, and discovery plane | Microsoft 365 / Agent 365 |

## Identity selection

The validation agent supports two explicit modes:

- `approved` selects the child Agent Identity identified by `APPROVED_AGENT_ID`.
- `denied` selects the child Agent Identity identified by `DENIED_AGENT_ID`.

The selected child identity is passed as `fmi_path` during the first exchange and as `client_id` during the second exchange. The IDs are runtime configuration and must never be hard-coded in the public implementation.

The mode names are validation labels, not authorization controls. Effective authorization is determined by Entra token issuance, Conditional Access, resource permission assignment, and the API's application-role enforcement.

## Authentication and authorization boundaries

| Control | Question answered | Enforcement point |
|---|---|---|
| Google Agent Identity assertion | Is the workload presenting its runtime identity? | Google metadata service and Entra federated trust |
| Blueprint T1 exchange | Does the external assertion satisfy the blueprint federation configuration? | Microsoft identity platform token endpoint |
| Child resource-token exchange | Can the selected child identity obtain a token for the protected API? | Microsoft identity platform token endpoint |
| Conditional Access | Is token issuance allowed for this child identity under the targeted policy? | Second token exchange in the validated scenario |
| Token signature, issuer, and audience | Was the token issued by the expected tenant for this API? | Protected API |
| `Investigation.Read` application role | Is the authenticated identity authorized for the investigation operation? | Protected API |

Authentication alone does not grant access. An authenticated child identity without the required application role reaches the API but receives HTTP 403.

## Conditional Access decision point

The validated denial scenario targets the denied child Agent Identity:

1. The Google assertion satisfies the federated trust, so T1 succeeds.
2. Conditional Access blocks the second exchange for the selected child identity.
3. No protected API resource token is returned.
4. The API is not reached.

The approved child identity remains outside the targeted policy scope in the validated reference environment and continues to receive a resource token and call the API.

This outcome is specific to the validated policy configuration. Exact customer policy behavior must be verified in the target tenant before deployment guidance is finalized.

## Protected API contract

The reference API exposes:

```text
GET /investigations/LAB-001
```

The API enforces:

- A bearer token must be present.
- The token must have a valid RS256 signature.
- The issuer must match the configured Entra tenant.
- The audience must match the configured protected API audience.
- The `roles` claim must contain `Investigation.Read`.

The synthetic response contains no customer investigation data.

## Validated outcomes

| Scenario | Validated outcome |
|---|---|
| No token | HTTP 401 |
| Authenticated identity without `Investigation.Read` | HTTP 403 |
| Approved identity with `Investigation.Read` | HTTP 200 and `LAB-001` |
| Denied identity targeted by Conditional Access | T1 succeeds, T2 is blocked, and the API is not reached |
| Approved identity outside Conditional Access scope | Access remains allowed |

## Token-handling constraints

The implementation uses raw assertions and access tokens only inside the token-exchange and API-call functions. Normal tool results expose selected claims and status metadata, not raw tokens.

Customer deployments must not add token logging, exception payload dumping, HTTP debug logging that records authorization headers, or persistence of assertions and access tokens.

## Configuration boundary

Environment-specific values are supplied through environment variables, including:

- Google project, region, runtime resource, staging bucket, and display names.
- Entra tenant, blueprint application, and approved/denied child Agent Identity IDs.
- Protected API audience, scope, base URL, and required role.

`config/.env.example` contains placeholders only. Populated `.env` files are excluded from source control.

## SDK status

The sanitized derivative intentionally preserves the validated `vertexai.Client` implementation and its `agent_engines` create, update, get, and query behavior.

Migration to `agentplatform.Client` is tracked as technical debt. It must be implemented and validated separately rather than being presented as part of the proven baseline.

## Explicitly unvalidated

This architecture does not establish validation for:

- Microsoft Graph resource access.
- Microsoft Sentinel integration.
- Agent 365 observability.
- Microsoft Purview integration.
- Agent 365 Registry onboarding automation.
- Every Google or third-party agent runtime.
- Every protected API or Conditional Access design.
