"""Run credential-free public-readiness checks for this repository."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = (
    ".gitattributes",
    ".github/workflows/repository-quality.yml",
    ".gitignore",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "config/.env.example",
    "deployment/Procfile",
    "deployment/README.md",
    "deployment/deploy.py",
    "deployment/requirements.txt",
    "deployment/update.py",
    "docs/agent365-registry.md",
    "docs/architecture.md",
    "docs/build-history.md",
    "docs/conditional-access.md",
    "docs/demo-runbook.md",
    "docs/deployment-guide.md",
    "docs/entra/README.md",
    "docs/google/README.md",
    "docs/identity-and-federation.md",
    "docs/troubleshooting.md",
    "docs/validation-matrix.md",
    "infra/README.md",
    "scripts/README.md",
    "scripts/validate_repo.py",
    "src/README.md",
    "src/agent.py",
    "src/api.py",
    "src/invoke.py",
    "validation/200.md",
    "validation/401.md",
    "validation/403.md",
    "validation/conditional-access-block.md",
)

REQUIRED_ENV_KEYS = (
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_CLOUD_LOCATION",
    "GOOGLE_AGENT_RUNTIME_RESOURCE_NAME",
    "GOOGLE_AGENT_RUNTIME_STAGING_BUCKET",
    "GOOGLE_AGENT_DISPLAY_NAME",
    "GOOGLE_ADK_AGENT_NAME",
    "GOOGLE_AGENT_MODEL",
    "ENTRA_TENANT_ID",
    "ENTRA_BLUEPRINT_APP_ID",
    "APPROVED_AGENT_ID",
    "DENIED_AGENT_ID",
    "PROTECTED_API_APP_ID",
    "PROTECTED_API_AUDIENCE",
    "PROTECTED_API_SCOPE",
    "PROTECTED_API_BASE_URL",
)

EXPECTED_OUTCOMES = (
    ("No bearer token", "401"),
    ("without `Investigation.Read`", "403"),
    ("with `Investigation.Read`", "200"),
    ("T1 succeeds", "T2"),
    ("Approved identity", "allowed"),
)

ALLOWED_URL_HOSTS = {
    "apache.org",
    "docs.cloud.google.com",
    "github.com",
    "learn.microsoft.com",
    "login.microsoftonline.com",
    "metadata.google.internal",
    "sts.windows.net",
    "www.apache.org",
}

TEXT_NAMES = {".env.example", "Procfile"}
TEXT_SUFFIXES = {".json", ".md", ".mmd", ".py", ".txt", ".yaml", ".yml"}
FORBIDDEN_SUFFIXES = {".key", ".log", ".p12", ".pem", ".pfx", ".zip"}
FORBIDDEN_PATH_PARTS = {
    ".venv",
    "__pycache__",
    "private-evidence",
    "provenance",
    "raw-build-logs",
    "validated-source",
}

SENSITIVE_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(
        r"\b(?:gh[opsu]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"
    ),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "JWT": re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    "literal GUID": re.compile(
        r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
        r"[0-9a-f]{4}-[0-9a-f]{12}\b"
    ),
    "Google project number": re.compile(r"\bprojects/[0-9]{6,}(?:/|\b)"),
    "tenant domain": re.compile(r"(?i)\b[a-z0-9][a-z0-9-]*\.onmicrosoft\.com\b"),
    "email address": re.compile(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    "Windows user path": re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+"),
    "Unix user path": re.compile(r"(?:/home/|/Users/)[A-Za-z0-9._-]+"),
    "service-account private key": re.compile(
        r'(?i)"(?:private_key|private_key_id)"\s*:'
    ),
}

PRIVATE_SOURCE_MARKERS = (
    "gemini-agent-runtime-agent365-entra-agent-" + "id-reference",
    "validated-source-" + "checksums",
    "Google Agent Runtime(2)" + ".zip",
    "agent365-gemini-entra-federation-" + "export",
    "itpartners" + "12",
)


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def repository_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )


def text_files() -> list[Path]:
    return [
        path
        for path in repository_files()
        if path.name in TEXT_NAMES or path.suffix.lower() in TEXT_SUFFIXES
    ]


def check_manifest(errors: list[str]) -> None:
    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).is_file():
            fail(errors, f"Missing required public file: {relative_path}")

    for path in repository_files():
        relative = path.relative_to(ROOT)
        lowered_parts = {part.lower() for part in relative.parts}
        if lowered_parts & FORBIDDEN_PATH_PARTS:
            fail(errors, f"Forbidden private or local path: {relative}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            fail(errors, f"Forbidden file type: {relative}")


def check_python_syntax(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.py")):
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            fail(errors, f"Python syntax failed for {path.relative_to(ROOT)}: {exc}")


def check_json(errors: list[str]) -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            fail(errors, f"JSON validation failed for {path.relative_to(ROOT)}: {exc}")


def parse_env_template(errors: list[str]) -> dict[str, str]:
    path = ROOT / "config/.env.example"
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            fail(errors, f"Invalid config/.env.example line: {line_number}")
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check_environment_template(errors: list[str]) -> None:
    env_files = [
        path.relative_to(ROOT)
        for path in ROOT.rglob(".env*")
        if path.is_file() and ".git" not in path.parts
    ]
    if env_files != [Path("config/.env.example")]:
        fail(errors, f"Unexpected environment files: {env_files}")

    values = parse_env_template(errors)
    for key in REQUIRED_ENV_KEYS:
        value = values.get(key)
        if not value:
            fail(errors, f"Missing configuration placeholder: {key}")
        elif "YOUR_" not in value:
            fail(errors, f"Configuration value is not placeholderized: {key}")


def check_sensitive_content(errors: list[str]) -> None:
    for path in text_files():
        relative = path.relative_to(ROOT)
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeError as exc:
            fail(errors, f"Non-UTF-8 text file {relative}: {exc}")
            continue

        for label, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(content):
                fail(errors, f"Possible {label} in {relative}")

        lowered = content.lower()
        for marker in PRIVATE_SOURCE_MARKERS:
            if marker.lower() in lowered:
                fail(errors, f"Private-source marker '{marker}' in {relative}")

        bucket_scheme = "gs" + "://"
        bucket_pattern = re.compile(
            re.escape(bucket_scheme) + r"[^\s)>\]}\"'`]*"
        )
        for match in bucket_pattern.finditer(content):
            bucket_url = match.group(0)
            if bucket_url == bucket_scheme or "YOUR_" in bucket_url:
                continue
            fail(errors, f"Non-placeholder bucket URL in {relative}")

        for match in re.finditer(
            r"\breasoningEngines/[0-9A-Za-z_-]{6,}\b", content
        ):
            if "YOUR_" not in match.group(0):
                fail(errors, f"Non-placeholder runtime identifier in {relative}")

        for match in re.finditer(r"https?://[^\s)>\]}\"']+", content):
            url = match.group(0).rstrip(".,;:")
            host = (urlparse(url).hostname or "").lower()
            if host.startswith("your_"):
                continue
            if host not in ALLOWED_URL_HOSTS:
                fail(errors, f"Unapproved URL host '{host}' in {relative}")


def check_markdown_links(errors: list[str]) -> None:
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for path in sorted(ROOT.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(content):
            clean_target = target.split("#", 1)[0].strip()
            if not clean_target or clean_target.startswith(("http://", "https://")):
                continue
            destination = (path.parent / clean_target).resolve()
            try:
                destination.relative_to(ROOT)
            except ValueError:
                fail(errors, f"Markdown link escapes repository in {path.relative_to(ROOT)}")
                continue
            if not destination.exists():
                fail(
                    errors,
                    f"Broken relative link in {path.relative_to(ROOT)}: {clean_target}",
                )


def check_reference_contract(errors: list[str]) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/validation-matrix.md").read_text(encoding="utf-8")
    combined = readme + "\n" + matrix

    for left, right in EXPECTED_OUTCOMES:
        if left not in combined or right not in combined:
            fail(errors, f"Validated outcome is not explicit: {left} / {right}")

    required_boundaries = (
        "validated reference pattern",
        "Agent 365 Connected Platform / Registry",
        "Microsoft Entra Agent ID",
        "Agent365-python",
        "external",
        "vertexai.Client",
        "agentplatform.Client",
        "technical debt",
        "Microsoft Sentinel",
        "Microsoft Purview",
        "Agent 365 observability",
    )
    for phrase in required_boundaries:
        if phrase not in readme:
            fail(errors, f"Required public boundary is missing from README: {phrase}")

    for path in repository_files():
        lowered_parts = {part.lower() for part in path.relative_to(ROOT).parts}
        if "agent365-python" in lowered_parts or "microsoft-agents-a365" in lowered_parts:
            fail(errors, f"Microsoft SDK source appears vendored: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    check_manifest(errors)
    check_python_syntax(errors)
    check_json(errors)
    check_environment_template(errors)
    check_sensitive_content(errors)
    check_markdown_links(errors)
    check_reference_contract(errors)

    if errors:
        print("Public-readiness validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Public-readiness validation passed.")
    print(
        "Checks: manifest, Python syntax, JSON, environment placeholders, "
        "sensitive content, links, validated outcomes, and product boundaries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
