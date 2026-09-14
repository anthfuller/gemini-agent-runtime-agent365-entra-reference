# Customer Deployment Guide

This guide reproduces the validated reference pattern with sanitized values.
It is not a support statement for every third-party agent, tenant, resource, or
policy design.

## Prerequisites

- A nonproduction Google Cloud project with access to Gemini Enterprise Agent Platform Agent Runtime and Agent Identity.
- A Microsoft Entra tenant with the required Agent ID and Conditional Access capabilities and licensing.
- Permissions to create the protected API application, application role, blueprint, child Agent Identities, federated identity credential, and narrowly scoped policy.
- An HTTPS service capable of hosting the synthetic FastAPI protected API.
- Python and Google Cloud tooling appropriate to the validated dependency set.
- Approved change and evidence-handling procedures for the target environment.

Portal labels, SDKs, product availability, and Microsoft Graph contracts can change. Verify current administrative steps against authoritative Google and Microsoft documentation instead of treating this repository as a frozen API contract.

## Deployment order

The order matters because the API URL is injected into Agent Runtime, while the
FIC issuer and subject are learned only after the runtime has a dedicated Agent
Identity.

1. Prepare the local configuration.
2. Create the protected API registration and `Investigation.Read` app role.
3. Create the Entra Agent ID blueprint and two child Agent Identities.
4. Assign `Investigation.Read` to the approved child only.
5. Deploy the protected API and record its HTTPS URL.
6. Deploy Google Agent Runtime with `AGENT_IDENTITY`.
7. Retrieve safe live Google identity claims from inside the runtime.
8. Add the FIC to the blueprint using those exact claims.
9. Validate 401, 403, and 200 before enabling Conditional Access.
10. Validate the deny-child Conditional Access policy and repeat the approved
    control test.
11. Optionally configure Agent 365 Connected Platform discovery as a separate
    workstream.

## 1. Prepare the repository

```bash
git clone https://github.com/anthfuller/gemini-agent-runtime-agent365-entra-reference.git
cd gemini-agent-runtime-agent365-entra-reference
python -m venv .venv
source .venv/bin/activate
python -m pip install -r deployment/requirements.txt
cp config/.env.example .env
```

Populate `.env` locally. Do not commit it.

```bash
set -a
source .env
set +a
```

Keep these fixed unless a separately validated design changes them:

```text
GOOGLE_TOKEN_AUDIENCE=api://AzureADTokenExchange
ENTRA_TOKEN_SCOPE=api://AzureADTokenExchange/.default
PROTECTED_API_REQUIRED_ROLE=Investigation.Read
INVESTIGATION_ID=LAB-001
```

## 2. Create the protected API application

In the target Entra tenant, create an application registration dedicated to
the reference API.

1. Record its application/client ID and service-principal object ID separately.
2. Set the Application ID URI to the tenant-approved value represented here as
   `api://<PROTECTED_API_APP_ID>`.
3. Define an application role with:

   | Field | Reference value |
   |---|---|
   | Display name | `Investigation Reader` |
   | Allowed member type | Applications |
   | Value | `Investigation.Read` |
   | Description | Read the synthetic investigation endpoint |
   | Enabled | Yes |

4. Record the app-role ID for the administrative assignment step.
5. Populate `PROTECTED_API_APP_ID`, `PROTECTED_API_AUDIENCE`, and
   `PROTECTED_API_SCOPE` in the local deployment environment.

Do not use Microsoft Graph as the resource for this customer pattern. The
validated final resource is the custom protected API.

## 3. Create the Entra Agent ID objects

Use the current Entra Agent ID administrative experience to create:

- one blueprint for the Google runtime family;
- one approved child Agent Identity; and
- one deny-test child Agent Identity.

Record the blueprint application/client ID and each child application/client
ID. Use clear nonproduction display names so the two children cannot be
confused during role and Conditional Access changes.

The initial blueprint can exist without its Google FIC. The exact FIC claims
will be added after the Google runtime exists.

## 4. Assign least-privilege API authorization

Assign the protected API's `Investigation.Read` application role to the
approved child Agent Identity service principal. Do not assign it to:

- the blueprint;
- the deny child;
- the Google deployment operator; or
- the Agent 365 Connected Platform connector.

Use the current supported portal or administrative interface in the tenant.
If an API is required, verify its current Microsoft Graph contract and required
permissions from Microsoft Learn before executing it. This repository does not
guess or embed the provisioning request.

After assignment, populate:

```text
ENTRA_BLUEPRINT_APP_ID=<blueprint application/client ID>
APPROVED_AGENT_ID=<approved child application/client ID>
DENIED_AGENT_ID=<deny child application/client ID>
```

## 5. Deploy the protected API

Install the API dependencies in its deployment environment:

```bash
python -m pip install -r deployment/requirements.txt
```

The API needs:

```text
ENTRA_TENANT_ID=<tenant ID>
PROTECTED_API_AUDIENCE=api://<protected API application/client ID>
PROTECTED_API_REQUIRED_ROLE=Investigation.Read
```

Deploy `src/api.py` to an HTTPS service. The validated lab used
Cloud Run and `deployment/Procfile`. It allowed unauthenticated Cloud Run
transport intentionally because the application performs Microsoft Entra
bearer-token validation. If organizational policy requires an additional
gateway, validate that it forwards the `Authorization` header without weakening
either layer.

Record the service origin, without the investigation path, as
`PROTECTED_API_BASE_URL`.

Run the first control:

```bash
curl -i "${PROTECTED_API_BASE_URL}/investigations/LAB-001"
```

Expected: HTTP 401 with a missing-bearer-token response.

The baseline validator expects the Entra v1 issuer format observed in the lab.
Confirm the token version and issuer in the target tenant using safe decoded
metadata. Do not weaken issuer validation to make an unexpected token pass.

## 6. Deploy Google Agent Runtime

Authenticate the Google Cloud CLI, select the project, and create the staging
bucket required by the validated SDK path. Confirm all `.env` values required
by `deployment/deploy.py` are present, then run from the repository root:

```bash
python -m deployment.deploy
```

The script deploys the ADK application with:

- `identity_type=AGENT_IDENTITY`;
- a staging bucket;
- runtime environment variables;
- runtime dependencies; and
- `src` as an extra package.

Record the returned runtime resource name and effective identity in the
controlled worksheet. Populate `GOOGLE_AGENT_RUNTIME_RESOURCE_NAME` for later
updates and invocation.

This baseline deliberately retains `vertexai.Client`. Treat the warning to
migrate to `agentplatform.Client` as technical debt; do not combine that
migration with initial reproduction of the validated flow.

## 7. Capture the live Google FIC claims

Invoke the deployed agent's `diagnose_agent_identity` tool from the Agent
Runtime test surface. The tool retrieves the assertion inside the runtime and
returns only:

- `issuer`;
- `subject`;
- `audience`;
- issued-at and expiry values; and
- whether a certificate-bound claim is present.

Never display or persist the raw assertion. Confirm that:

```text
audience = api://AzureADTokenExchange
subject = the SPIFFE identity of this exact runtime resource
issuer = the Agent Identity workload-pool issuer observed live
```

Do not substitute the Google service-account issuer or a numeric
service-account subject. Those values belong to a superseded experiment.

## 8. Add the federated identity credential

On the Entra Agent ID blueprint, create a FIC with:

| Field | Value |
|---|---|
| Issuer | Exact live Google `iss` value |
| Subject type | Explicit subject identifier |
| Subject | Exact live Google SPIFFE `sub` value |
| Audience | `api://AzureADTokenExchange` |
| Name | A tenant-unique, descriptive name |

Preserve exact case and punctuation. The issuer and subject are runtime
specific. If the runtime is deleted and recreated, obtain new live claims and
review the FIC because the runtime resource ID, identity, and permissions can
change.

## 9. Validate federation and authorization

Keep Conditional Access from blocking the deny child's T2 exchange during the
HTTP 403 test.

Denied child:

```bash
python -m src.invoke denied
```

Expected: T1 and T2 succeed, the safe role list omits
`Investigation.Read`, and the API returns HTTP 403.

Approved child:

```bash
python -m src.invoke approved
```

Expected: T1 and T2 succeed, the safe role list contains
`Investigation.Read`, and the API returns HTTP 200 with `LAB-001`.

Use [the validation matrix](validation-matrix.md) for evidence requirements.

## 10. Configure and validate Conditional Access

Create a narrowly scoped policy for the deny child Agent Identity and the
protected API resource. Follow the tenant's current supported Agent ID or
workload-identity policy experience; UI names and API shapes may change.

1. Start in report-only mode.
2. Invoke the deny child and confirm the intended policy matches in the same UTC
   sign-in window.
3. Confirm the approved child is outside the policy scope.
4. Obtain change approval and enable the block control.
5. Invoke the deny child again.
6. Verify T1 succeeds, T2 is blocked, and the API is not reached.
7. Invoke the approved child and verify HTTP 200 plus `LAB-001`.

Do not call a protected API HTTP 403 a Conditional Access result. HTTP 403 is
the API's missing-role decision; the validated Conditional Access block stops
T2 before the API call.

## 11. Optional Agent 365 discovery

Agent 365 Connected Platform synchronization is a separate inventory path. In
the lab, the Google connector discovered the new runtime because it surfaced as
a Reasoning Engine resource. That did not create or correlate the Entra Agent
ID objects.

If discovery is required, configure it as a separate change using current
Microsoft documentation, least-privilege Google connector credentials, and its
own validation record. An `Unmanaged` Connected Platform record does not by
itself mean the Entra federation failed.

Do not install or vendor `Agent365-python` merely to reproduce the validated
federation path. Use it only for a separately designed Agent 365 SDK capability.

## 12. Update an existing runtime

After a reviewed code or configuration change:

```bash
python -m deployment.update
```

Confirm the runtime resource and effective Agent Identity were preserved.
Repeat at least the approved control and any scenario affected by the change.
If the runtime identity changed, stop and revalidate the FIC before continuing.

## Completion criteria

Deployment is complete only when all five rows in
[`validation-matrix.md`](validation-matrix.md) pass and no raw token or
environment-specific identifier is present in customer-facing evidence.
