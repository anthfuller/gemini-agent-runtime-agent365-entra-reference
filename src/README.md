# Source

| File | Purpose |
|---|---|
| `agent.py` | Google ADK agent and validated T1/T2 federation tool |
| `invoke.py` | Safe approved/denied runtime invocation client |
| `api.py` | Minimal FastAPI service enforcing the Entra token and `Investigation.Read` |

These files are sanitized, behavior-preserving derivatives of the validated implementation. Environment-specific identifiers are supplied through configuration.

The code deliberately retains `vertexai.Client` where it was used in the validated baseline. Its migration is tracked separately.
