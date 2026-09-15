# Repository Validation

Run the credential-free public-readiness checks from the repository root:

```bash
python3 scripts/validate_repo.py
```

The validator checks the approved manifest, Python syntax, placeholder configuration, sensitive-value patterns, customer validation outcomes, external SDK boundary, unsupported-integration disclaimers, and selected relative documentation links.

GitHub Actions runs the same validator for every pull request and push to `main`.

It does not contact Google Cloud, Microsoft Entra, Agent 365, or the protected API.
