# Security Policy

## Supported version

Security fixes are applied to the current `main` branch. This reference implementation is provided without a production support commitment.

## Reporting a vulnerability

Use GitHub private vulnerability reporting when it is enabled for this repository. Do not place secrets, raw identity assertions, access tokens, authorization headers, tenant identifiers, customer information, or exploit details in a public issue.

If private reporting is unavailable, open a public issue containing only a request for a private reporting channel. Do not include vulnerability details in that issue.

## Deployment responsibility

This repository is a validated reference pattern, not a managed service or universal product-support statement. Customers are responsible for reviewing identity, application-role, API, cloud IAM, logging, and Conditional Access changes under their own security and change-management processes.

Use synthetic data and nonproduction environments first. Rotate any credential or token that may have been exposed.
