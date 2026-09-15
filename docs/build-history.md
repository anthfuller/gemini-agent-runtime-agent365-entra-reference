# Curated Build History

This history summarizes the evidence supplied with the validated lab. It is not
a verbatim transcript. Raw build logs, screenshots, tokens, tenant identifiers,
application identifiers, project identifiers, resource paths, and service URLs
are intentionally excluded.

## Evidence handling

- The source archive was inspected read-only.
- Only final or still-relevant conclusions are retained here.
- Earlier findings that were later disproved are marked as superseded.
- A successful lab outcome is not generalized into product-wide support.
- Raw Google assertions, Entra tokens, and authorization headers were not
  included in the reference repository.

## Milestones

| Milestone | Curated outcome | Status |
|---|---|---|
| Baseline | Existing Agent 365 Connected Platform synchronization discovered Google-hosted agents. | Validated in the lab |
| Agent Runtime canary | A Gemini Enterprise Agent Platform Agent Runtime deployment was created in the selected Google region. Its underlying resource was exposed as a Reasoning Engine. | Validated in the lab |
| Agent 365 discovery | A manual Connected Platform synchronization increased the discovered inventory and displayed the new runtime agent in Agent 365 Registry. | Validated in the lab |
| Dedicated Google identity | The programmatic runtime deployment used `identity_type=AGENT_IDENTITY` and received a dedicated Google Agent Identity. | Validated in the lab |
| Runtime packaging | Supplying the repository `src` directory as an extra package resolved the remote import failure while preserving the existing runtime resource and identity. | Validated in the lab |
| Live identity claims | The runtime retrieved a Google identity assertion internally and disclosed only safe decoded metadata. The issuer was the Agent Identity workload-pool issuer and the subject was the runtime's SPIFFE identity. | Validated in the lab |
| Entra FIC | The Entra Agent Identity blueprint FIC was configured from the exact live Google `iss`, `sub`, and requested `aud` values. | Validated in the lab |
| Blueprint exchange (T1) | Entra accepted the Google assertion and issued the blueprint token for the selected child identity path. | HTTP 200 validated |
| Child resource exchange (T2) | A child Agent Identity obtained a token for the custom protected API. | Validated in the lab |
| Application authorization | The protected API exposed `Investigation.Read`; the role was assigned to the approved child and omitted from the deny child. | Validated in the lab |
| Protected API controls | No token returned HTTP 401; an authenticated roleless identity returned HTTP 403; the approved identity returned HTTP 200 and `LAB-001`. | Validated in the lab |
| Conditional Access | A deny-child-specific policy matched in report-only mode, then blocked the deny child's T2 request when enabled. T1 succeeded and the API was not reached. | Validated in the lab |
| Approved control | The approved child, outside the deny policy scope, continued to receive T2 and HTTP 200 with `LAB-001`. | Validated in the lab |

## Superseded findings

### Service-account issuer and numeric subject

An early FIC used the Google service-account issuer and a numeric subject. That
configuration was based on a shared service-account identity pattern. It does
not match the dedicated Agent Identity used by the final runtime deployment.

The final reference requires operators to retrieve safe claims from the live,
dedicated Agent Runtime identity and configure the FIC with the exact observed
issuer and SPIFFE subject. Do not copy issuer or subject values from another
runtime.

### Conditional Access initially reported as not validated

An intermediate investigation did not observe the expected Conditional Access
evaluation and left the policy in report-only mode. Later evidence superseded
that conclusion:

1. The API-specific policy matched the deny child in report-only mode.
2. The same policy was enabled with a block grant control.
3. The deny child's T1 exchange succeeded.
4. Its T2 resource-token request was blocked.
5. The protected API was not reached.
6. The approved child remained allowed.

### Connected Platform record correlation

The lab investigated whether an existing Google record synchronized through
Agent 365 Connected Platforms could be retroactively associated with the
separately created Entra blueprint and child Agent Identity. No documented,
validated correlation method was established. The synchronized record could
remain `Unmanaged` while the separate Entra federation and governance path
worked.

Do not infer an internal Agent 365 registration ID from a Google resource path,
and do not PATCH a registration until a supported API and verified target ID
have been established independently.

## Implementation decisions retained

- Preserve the two-exchange T1/T2 flow from the validated implementation.
- Keep the approved/denied child selector in runtime environment variables.
- Keep the protected API audience separate from Microsoft Graph.
- Validate the access-token issuer actually produced by the tenant and token
  version used by this reference.
- Keep raw credentials out of model responses and logs.
- Retain `vertexai.Client` in the baseline. The migration to
  `agentplatform.Client` is tracked technical debt and must be validated as a
  separate change.
- Keep Microsoft `Agent365-python` external. This reference neither vendors it
  nor claims that it participates in the validated federation path.

## Explicitly outside the validated evidence

The supplied evidence does not validate:

- universal support for every third-party agent framework or resource;
- retroactive merging of Connected Platform inventory with Entra Agent ID;
- Agent 365 observability or telemetry ingestion;
- Microsoft Sentinel integration;
- Microsoft Purview integration;
- production resilience, scale, disaster recovery, or compliance posture;
- a migration from `vertexai.Client` to `agentplatform.Client`;
- arbitrary Microsoft Graph operations as part of the final protected-API
  reference pattern.

Any extension in this list needs its own architecture review and evidence.

## External reference snapshot

The Microsoft [`Agent365-python`](https://github.com/microsoft/Agent365-python)
repository was reviewed as an external product reference at commit
`06e9d597ed06a2dd89df52d284e99439129b3e6f` (2026-09-08). Its documented SDK
areas include observability, notifications, runtime utilities, and tooling. No
Microsoft SDK source is copied into this repository, and the validated Python
implementation does not import an Agent 365 package.

Current platform procedures should always be checked against the vendor's
official documentation before deployment.
