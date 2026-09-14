# Validation Matrix

## Purpose

This matrix defines the five outcomes demonstrated in the validated reference environment. It separates authentication, application-role authorization, and Conditional Access so each control can be observed at the correct enforcement point.

These are reference-environment results, not guaranteed outcomes for every tenant or third-party workload.

## Test-state warning

The role-based HTTP 403 test and the Conditional Access denial test use different policy states:

- To observe HTTP 403, the roleless identity must obtain a protected API token and reach the API. Conditional Access must not block that token exchange during this test.
- To observe the Conditional Access result, the deny identity is placed in the validated policy scope. T1 succeeds, T2 is blocked, and the API is not reached.

Do not interpret a Conditional Access block as an API HTTP 403. They occur at different boundaries.

## Matrix

| ID | Scenario | Required state | Execution boundary | Expected outcome |
|---|---|---|---|---|
| V-01 | Missing bearer token | Protected API deployed | Direct API request without `Authorization` | HTTP 401 |
| V-02 | Authenticated identity lacks `Investigation.Read` | Roleless child can obtain an API token; CA does not block T2 | Child resource exchange followed by API request | HTTP 403 |
| V-03 | Approved identity has `Investigation.Read` | Approved child has the application role | Approved agent invocation | HTTP 200 and `LAB-001` |
| V-04 | Conditional Access targets deny identity | Validated CA policy enabled for deny child | Denied agent invocation | T1 succeeds; T2 blocked; API not reached |
| V-05 | Approved identity outside CA scope | Approved child retains role and is excluded from the deny policy scope | Approved control invocation | T1 and T2 succeed; API remains allowed |

## Detailed procedures

### V-01 — Missing token

Request:

```bash
curl -i "${PROTECTED_API_BASE_URL}/investigations/LAB-001"
```

Record only the HTTP status and safe response body.

Expected:

```text
HTTP 401
{"detail":"Missing bearer token"}
```

### V-02 — Authenticated but unauthorized

Prerequisites:

- The selected child identity does not have `Investigation.Read`.
- Conditional Access does not block its T2 exchange during this test.
- The issued token audience is the protected API.

Invoke the roleless identity through the validated agent flow. Do not print or manually copy the access token.

Expected safe evidence:

```text
t1_success: true
resource_token_success: true
roles: []
api_http_status: 403
```

### V-03 — Approved application role

Invoke:

```bash
python -m src.invoke approved
```

Expected safe evidence:

```text
selected_mode: approved
t1_success: true
resource_token_success: true
roles: [Investigation.Read]
api_http_status: 200
api_response.investigationId: LAB-001
raw_token_exposed: false
```

### V-04 — Conditional Access blocks T2

Prerequisites:

- The validated Conditional Access policy targets the deny child identity.
- The Google-to-blueprint federated trust remains valid.

Invoke:

```bash
python -m src.invoke denied
```

Expected control sequence:

```text
T1 blueprint exchange: succeeds
T2 child resource exchange: blocked
Protected API: not reached
```

Capture the safe stage name, HTTP status from the token endpoint, sanitized error classification, and relevant Entra sign-in evidence. Do not store tokens or full diagnostic payloads containing tenant-specific identifiers.

### V-05 — Approved identity control test

With the deny policy still active, invoke:

```bash
python -m src.invoke approved
```

Expected:

```text
T1 blueprint exchange: succeeds
T2 child resource exchange: succeeds
Protected API: HTTP 200 and LAB-001
```

This test demonstrates the validated policy targeting, not a universal Conditional Access design.

## Evidence requirements

For each test, record:

- Test ID and UTC timestamp.
- Sanitized environment label.
- Selected validation mode.
- T1 success or failure.
- T2/resource-token success or failure.
- API reached: yes or no.
- API HTTP status when reached.
- Application roles returned in safe claim metadata.
- Sanitized Conditional Access result when applicable.

Never record:

- Google assertions.
- T1 tokens.
- Protected API access tokens.
- Authorization headers.
- Tenant, application, object, project, or runtime resource IDs in customer-facing evidence.

## Pass criteria

The reference pattern passes only when all five outcomes match the matrix and the approved control remains successful after the deny policy is enforced.
