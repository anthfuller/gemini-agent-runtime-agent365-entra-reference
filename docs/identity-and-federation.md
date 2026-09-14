# Identity and Federation

## Purpose

This guide explains the validated identity path between a Google Gemini Enterprise Agent Platform Agent Runtime and Microsoft Entra Agent ID. It describes the proven sequence without prescribing unverified SDK or Microsoft Graph provisioning calls.

## Identity objects

| Object | Purpose |
|---|---|
| Google Agent Runtime | Hosts the agent and receives a dedicated Google Agent Identity |
| Google Agent Identity assertion | Runtime-bound JWT-SVID presented to the Entra federated trust |
| Entra Agent ID blueprint | Defines the external federation relationship and accepts the Google assertion |
| Approved child Agent Identity | Receives `Investigation.Read` for the protected API |
| Deny child Agent Identity | Supports roleless and Conditional Access denial validation |
| Protected API service principal | Exposes `Investigation.Read` and represents the token audience |

## Validated T1/T2 sequence

### T1 — Blueprint exchange

1. The runtime requests its dedicated Google Agent Identity assertion from the Google metadata identity endpoint.
2. The requested audience is `api://AzureADTokenExchange`.
3. The runtime submits the assertion to the tenant-specific Microsoft identity-platform token endpoint.
4. The blueprint application ID is the client.
5. The selected child Agent Identity ID is supplied through `fmi_path`.
6. When the federated credential matches the live issuer, subject, and audience, Entra returns T1.

### T2 — Child resource exchange

1. The selected child Agent Identity becomes the client.
2. T1 is submitted as the client assertion.
3. The requested scope is the custom protected API's `.default` scope.
4. Entra evaluates token issuance, including applicable Conditional Access policy.
5. If allowed, Entra returns the protected API resource token.
6. The API validates the token and requires `Investigation.Read`.

T1 success does not imply T2 success, and T2 success does not imply API authorization. These are separate enforcement points.

## Create the Entra objects

Using the tenant's current supported Entra Agent ID administrative experience, create:

- one blueprint for the Google runtime family;
- one approved child Agent Identity; and
- one deny-test child Agent Identity.

Record application/client IDs and service-principal object IDs separately. The runtime configuration uses the application/client IDs. Administrative role assignment may require service-principal and app-role object IDs.

Do not embed provisioning calls copied from an old portal or API example. If Microsoft Graph automation is required, verify its current resource path, permissions, object types, and request body against Microsoft Learn before executing it.

## Configure the protected API role

Create a dedicated protected API application registration with an application role:

| Field | Reference value |
|---|---|
| Display name | `Investigation Reader` |
| Allowed member type | Applications |
| Value | `Investigation.Read` |
| Enabled | Yes |

Assign the role to the approved child Agent Identity only. Do not assign it to the blueprint, deny child, Google deployment operator, or Agent 365 connector.

## Capture live Google claims

Deploy the runtime with a dedicated Agent Identity before finalizing the federated identity credential. Invoke `diagnose_agent_identity` inside the runtime and retain only safe decoded metadata:

- issuer;
- subject;
- audience;
- issued-at and expiry times; and
- whether a certificate-bound claim is present.

Never record the raw assertion. Do not reuse the issuer or subject from another runtime, and do not substitute a service-account issuer or numeric service-account subject.

## Configure the federated identity credential

Add the federated identity credential to the blueprint using:

| Field | Required value |
|---|---|
| Issuer | Exact live Google `iss` |
| Subject type | Explicit subject identifier |
| Subject | Exact live Google SPIFFE `sub` |
| Audience | `api://AzureADTokenExchange` |
| Name | Tenant-unique descriptive name |

Preserve case and punctuation. If the runtime is deleted and recreated, capture its live identity claims again and review the credential before continuing.

## Configuration mapping

| Configuration | Value category |
|---|---|
| `ENTRA_TENANT_ID` | Target Entra tenant |
| `ENTRA_BLUEPRINT_APP_ID` | Blueprint application/client ID |
| `APPROVED_AGENT_ID` | Approved child application/client ID |
| `DENIED_AGENT_ID` | Deny child application/client ID |
| `PROTECTED_API_AUDIENCE` | Protected API Application ID URI |
| `PROTECTED_API_SCOPE` | Protected API `.default` scope |
| `GOOGLE_TOKEN_AUDIENCE` | `api://AzureADTokenExchange` |
| `ENTRA_TOKEN_SCOPE` | `api://AzureADTokenExchange/.default` |

All environment-specific values belong in runtime or deployment configuration, never in committed source.

## Boundaries

This identity flow does not prove:

- automatic Agent 365 Registry correlation;
- Microsoft Graph resource access;
- Sentinel or Purview integration;
- Agent 365 observability; or
- universal support for other agent runtimes or protected resources.
