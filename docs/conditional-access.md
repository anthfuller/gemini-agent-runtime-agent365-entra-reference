# Conditional Access

## Validated control

The validated Conditional Access policy targeted the deny child Agent Identity and the protected API resource:

1. The Google assertion satisfied the blueprint federated trust.
2. T1 succeeded.
3. Conditional Access blocked T2 for the deny child.
4. No protected API resource token was returned.
5. The protected API was not reached.
6. The approved child remained outside the deny-policy scope and continued to receive HTTP 200 with `LAB-001`.

This result is specific to the validated tenant and policy configuration.

## Safe implementation sequence

Use the tenant's current supported Agent ID or workload-identity Conditional Access experience. Portal labels, licensing, policy capabilities, and API contracts can change.

1. Complete the 401, 403, and approved 200 validation scenarios first.
2. Identify the deny child Agent Identity unambiguously.
3. Target only the intended child identity and protected API resource.
4. Exclude emergency and administrative recovery paths according to organizational policy.
5. Start the policy in report-only mode.
6. Invoke the deny child and correlate the intended policy in the same UTC sign-in window.
7. Confirm the approved child is outside the policy scope.
8. Obtain change approval.
9. Enable the block grant control.
10. Repeat the deny and approved validation scenarios.

Do not embed unverified Microsoft Graph calls in automation. Verify the current Graph resource types, permissions, and request schema before provisioning policies programmatically.

## Distinguish the denial points

| Result | Meaning |
|---|---|
| T1 fails | The external assertion or blueprint federation step failed |
| T1 succeeds and T2 is blocked | Conditional Access or another token-issuance control stopped the child exchange |
| T2 succeeds and API returns 403 | Authentication succeeded; the API denied the missing `Investigation.Read` role |
| T2 succeeds and API returns 200 | Token issuance and API role authorization succeeded |

An API HTTP 403 is not evidence of a Conditional Access block. The validated CA outcome prevents the API call.

## Evidence

Record only:

- selected child mode;
- T1 success;
- T2 blocked or allowed;
- whether the API was reached;
- sanitized Conditional Access result and UTC correlation time; and
- the approved control result.

Never capture raw assertions, T1 tokens, resource tokens, authorization headers, tenant identifiers, application identifiers, or internal URLs.

See [Conditional Access block validation](../validation/conditional-access-block.md).
