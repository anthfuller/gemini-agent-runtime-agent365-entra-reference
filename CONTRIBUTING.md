# Contributing

Contributions that improve clarity, security, portability, and validation are welcome.

## Before opening a pull request

1. Create a focused branch.
2. Preserve the documented T1/T2 authentication sequence unless the change is explicitly presented as a separately validated design.
3. Do not add tenant IDs, project IDs, application IDs, object IDs, resource IDs, private URLs, credentials, tokens, customer data, screenshots, or raw troubleshooting logs.
4. Do not vendor Microsoft `Agent365-python` source.
5. Do not describe Sentinel, Purview, Agent 365 observability, Microsoft Graph operations, or other integrations as validated without reproducible evidence.
6. Run:

   ```bash
   python3 scripts/validate_repo.py
   ```

7. Explain any behavior change, security impact, and validation evidence in the pull request.

## Documentation

Use placeholders and synthetic examples. Link current authoritative vendor documentation when a procedure depends on a changing portal, SDK, or API. Avoid copying environment-specific instructions from private deployments.

## License

Unless explicitly stated otherwise, contributions submitted to this repository are licensed under Apache License 2.0.
