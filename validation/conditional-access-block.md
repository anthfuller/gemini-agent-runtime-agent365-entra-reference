# Conditional Access Block

## Purpose

Confirm that the targeted deny child is blocked during the T2 resource-token exchange while the approved control remains allowed.

## Preconditions

- The 401, roleless 403, and approved 200 scenarios have passed.
- The intended policy matched the deny child in report-only mode.
- The approved child is outside the deny-policy scope.
- The block policy was enabled through the target environment's approved change process.

## Deny request

```bash
python -m src.invoke denied
```

## Expected deny result

| Field | Expected value |
|---|---|
| T1 | Succeeds |
| T2 | Blocked |
| API reached | No |
| Control | Conditional Access |

## Approved control

```bash
python -m src.invoke approved
```

Expected: T1 and T2 succeed; the protected API returns HTTP 200 and `LAB-001`.

## Interpretation

The validated policy acted at token issuance. It did not produce an API HTTP 403 because the deny request never reached the API.

Retain only sanitized policy results and UTC correlation times. Do not store tokens, tenant identifiers, application identifiers, internal URLs, or raw sign-in records.
