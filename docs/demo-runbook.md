# Client Demo Runbook

## Objective

Demonstrate the difference between missing authentication, authenticated-but-unauthorized access, approved application-role access, and Conditional Access blocking of a selected child Agent Identity.

The demo proves the validated reference pattern only. It does not prove universal third-party-agent support or any untested Agent 365, Microsoft Graph, Sentinel, Purview, or observability integration.

## Roles

| Role | Responsibility |
|---|---|
| Facilitator | Runs the approved and denied scenarios and explains boundaries |
| Entra administrator | Confirms role assignments and the prevalidated Conditional Access state |
| Google Cloud operator | Confirms the deployed Agent Runtime resource and runtime identity |
| Observer | Records only the safe evidence fields |

## Pre-demo checklist

- Use a nonproduction tenant, project, API, and synthetic investigation record.
- Confirm the repository commit used for the demo.
- Confirm the populated environment configuration is not in source control.
- Confirm the approved and denied child identities are unambiguous.
- Confirm the approved child has `Investigation.Read`.
- Confirm how the roleless HTTP 403 state will be demonstrated before the CA deny state is enforced.
- Confirm the deny Conditional Access policy has already been validated in the environment.
- Confirm the approved child remains outside the deny policy scope.
- Disable terminal or HTTP logging that could expose tokens.
- Prepare a sanitized evidence worksheet using the test IDs in `validation-matrix.md`.

## Demo order

### 1. Explain the two planes

Show the architecture diagram and state:

- Agent 365 Connected Platform / Registry handles separate registration, management, and discovery concerns.
- Entra Agent ID supplies the federation, child identity, role, token issuance, and Conditional Access controls demonstrated here.
- The custom API performs final token and role enforcement.

### 2. Missing-token control — V-01

Run:

```bash
curl -i "${PROTECTED_API_BASE_URL}/investigations/LAB-001"
```

Expected: HTTP 401 with `Missing bearer token`.

Explain that the API rejects unauthenticated access before evaluating application roles.

### 3. Roleless authenticated control — V-02

Use the prevalidated state in which the roleless child can obtain a protected API token and is not blocked by Conditional Access.

Invoke the roleless scenario without displaying its token.

Expected:

```text
T1 succeeds
T2 succeeds
roles is empty or does not contain Investigation.Read
API returns HTTP 403
```

Explain that authentication succeeded and the API enforced authorization.

### 4. Approved identity — V-03

Run:

```bash
python -m src.invoke approved
```

Expected:

```text
selected_mode: approved
t1_success: true
resource_token_success: true
roles includes Investigation.Read
api_http_status: 200
investigationId: LAB-001
raw_token_exposed: false
```

Explain that the child identity received the application role and the API enforced it.

### 5. Conditional Access deny — V-04

Confirm the prevalidated Conditional Access policy is enforcing the deny child identity. Do not redesign or edit the policy during the customer demonstration.

Run:

```bash
python -m src.invoke denied
```

Expected:

```text
T1 succeeds
T2 is blocked
API is not reached
```

Explain that this is a token-issuance control, not an HTTP 403 returned by the protected API.

### 6. Approved control after CA enforcement — V-05

Run:

```bash
python -m src.invoke approved
```

Expected: T1 and T2 succeed, followed by HTTP 200 and `LAB-001`.

Explain that the approved identity remains allowed because it is outside the validated deny-policy scope.

## Safe evidence to display

- Selected mode.
- T1 and resource-token success flags.
- Token audience category, issuer category, version, signing algorithm, and key ID when appropriately sanitized.
- Application roles.
- API HTTP status and synthetic response.
- `raw_token_exposed: false`.
- Sanitized Conditional Access result.

Do not display raw Google assertions, T1 tokens, resource tokens, authorization headers, tenant IDs, application IDs, project IDs, runtime resource IDs, or unsanitized URLs.

## Recovery plan

If a step fails:

1. Stop at the failing stage.
2. Preserve the approved control if possible.
3. Use `troubleshooting.md` to classify the failure.
4. Do not change identity, role, scope, or policy settings live without the responsible administrator's approval.
5. Resume only after the expected state is restored.

## Close

Conclude with three points:

1. The reference demonstrates workload federation from the validated Google Agent Runtime to Entra Agent ID.
2. Child Agent Identities support distinct authorization and Conditional Access outcomes in the validated environment.
3. Agent 365 discovery and future integrations require separate implementation and validation.
