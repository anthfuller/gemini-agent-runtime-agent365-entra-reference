# Troubleshooting

## Start with the failing stage

Troubleshoot the flow in order. A later boundary cannot succeed when an earlier boundary failed.

| Stage | Safe result indicator | Primary area to inspect |
|---|---|---|
| Configuration load | Missing environment variable exception | Runtime configuration |
| Google identity | Metadata request exception | Agent Runtime identity and metadata access |
| Blueprint exchange | `stage: t1_blueprint_exchange` | Federated identity credential and blueprint configuration |
| Child resource exchange | `stage: child_agent_resource_exchange` with `t1_success: true` | Child identity, API scope, permissions, or Conditional Access |
| Protected API authentication | API HTTP 401 | Token signature, issuer, audience, or bearer header |
| Protected API authorization | API HTTP 403 | `Investigation.Read` application role |
| Successful request | API HTTP 200 and `LAB-001` | Expected result |

## Configuration failures

Symptoms:

- A required environment variable is missing.
- A project, runtime resource, bucket, scope, or URL placeholder was not replaced.
- The agent fails before making a metadata or token request.

Checks:

1. Copy `config/.env.example` to a local, ignored `.env` file or configure the equivalent deployment environment variables.
2. Confirm no value still begins with `YOUR_` or contains a placeholder segment.
3. Confirm the protected API scope ends in `/.default` and belongs to the protected API.
4. Confirm the protected API base URL does not include the investigation path.
5. Never commit the populated configuration.

## Google metadata identity failure

Symptoms:

- Timeout or HTTP failure contacting the metadata identity endpoint.
- No Google assertion is returned.

Checks:

1. Confirm the code is running inside the intended Agent Runtime rather than an ordinary local Python process.
2. Confirm the deployment uses Google Agent Identity.
3. Confirm the metadata request includes the `Metadata-Flavor: Google` header.
4. Confirm the requested audience is `api://AzureADTokenExchange` unless the validated design has deliberately changed.
5. Record only safe exception type and stage information.

## T1 blueprint exchange failure

Symptoms:

- `stage` is `t1_blueprint_exchange`.
- The Google assertion was obtained, but no T1 access token was returned.

Checks:

1. Confirm the Entra tenant and blueprint application identifiers refer to the intended tenant.
2. Confirm the federated identity credential belongs to the blueprint.
3. Compare issuer, subject, and audience configuration with safe decoded Google claim metadata.
4. Confirm the selected child identity is passed through `fmi_path`.
5. Verify the token request uses the blueprint client ID and `api://AzureADTokenExchange/.default`.

Do not change issuer, subject, audience, or token-request fields based on an assumed SDK or Graph behavior. Compare them with the validated build record and authoritative platform documentation.

## T2 child resource exchange failure

Symptoms:

- `stage` is `child_agent_resource_exchange`.
- `t1_success` is true.
- No protected API resource token is returned.

Checks:

1. Confirm the selected child Agent Identity ID is correct for the requested mode.
2. Confirm the second request uses that child identity as `client_id`.
3. Confirm the protected API scope is correct.
4. Confirm required API permissions and consent are present.
5. Review the Entra sign-in result for the child identity.
6. Determine whether Conditional Access intentionally blocked the exchange.

This token targets the custom protected API. Do not troubleshoot it as a Microsoft Graph token unless the implementation has separately been changed and validated to request Microsoft Graph.

## Conditional Access result

The validated denial pattern is:

```text
T1 succeeds -> T2 blocked -> API not reached
```

If T1 fails, troubleshoot the federated identity credential before Conditional Access. If T2 succeeds and the API returns HTTP 403, troubleshoot the application role rather than labeling the result a Conditional Access denial.

Confirm policy behavior using Entra evidence from the same UTC test window. Sanitize all tenant and identity identifiers before preserving customer-facing evidence.

## Protected API HTTP 401

Possible causes:

- Missing bearer token.
- Invalid signature.
- Unexpected issuer.
- Unexpected audience.
- Expired or malformed token.

Checks:

1. Distinguish the expected missing-token test from an invalid-token failure.
2. Confirm the API audience exactly matches the resource token `aud` claim.
3. Confirm the configured tenant matches the token issuer expected by the validated API.
4. Confirm the API can retrieve the tenant OpenID configuration and signing keys.
5. Do not log the bearer token while diagnosing.

## Protected API HTTP 403

HTTP 403 means the token passed authentication but lacks the required application role.

Checks:

1. Inspect only the safe `roles` result.
2. Confirm `Investigation.Read` is defined on the protected API application.
3. Confirm the role is assigned to the intended child Agent Identity.
4. Obtain a new token after changing a role assignment.

## No function response returned

Symptoms:

- Invocation completes without the expected federation tool response.
- `invoke_agent.py` raises `No federation validation result was returned.`

Checks:

1. Confirm the deployed agent includes `validate_entra_agent_id_federation` as a tool.
2. Confirm the invocation message contains the selected mode.
3. Inspect safe event structure without printing token-bearing request data.
4. Confirm the deployed source and local invocation script are from compatible commits.

## Deployment or update packaging failure

Checks:

1. Run deployment commands from the repository root.
2. Confirm the `src` directory exists because it is supplied as an extra package.
3. Confirm Agent Runtime dependencies are available from `deployment/requirements.txt`.
4. Confirm the staging bucket begins with `gs://`.
5. Confirm all required runtime environment variables are present before importing the agent module.

The repository deliberately retains `vertexai.Client`. Do not resolve a packaging issue by migrating to `agentplatform.Client` inside the validated baseline branch.

## Escalation evidence

Provide only:

- UTC timestamp.
- Failing stage.
- HTTP status.
- Sanitized error code and description.
- Safe token metadata such as issuer category, audience category, expiry, algorithm, and roles.
- Relevant sanitized Conditional Access result.
- Repository commit SHA.

Never provide raw assertions, access tokens, authorization headers, secrets, or unsanitized environment identifiers.
