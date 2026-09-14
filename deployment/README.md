# Deployment

| File | Purpose |
|---|---|
| `deploy.py` | Creates the Google Agent Runtime with a dedicated Agent Identity |
| `update.py` | Updates the existing runtime while preserving the validated packaging path |
| `requirements.txt` | Combined customer dependency set for the runtime scripts and protected API |
| `Procfile` | Starts the protected FastAPI application |

Run deployment commands from the repository root after loading a populated local `.env`. See [the customer deployment guide](../docs/deployment-guide.md).

These scripts do not provision Entra or Conditional Access objects. Use the current supported administrative experience and verify any automation contract against authoritative vendor documentation.
