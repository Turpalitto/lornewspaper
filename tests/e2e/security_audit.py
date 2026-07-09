#!/usr/bin/env python3
"""Security audit — dependency scan, header check, Docker scan."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parent.parent.parent


def check_frontend_deps() -> list[dict]:
    issues = []
    r = subprocess.run(["npm", "audit", "--json"], capture_output=True, text=True, cwd=ROOT / "web", timeout=60)
    if r.stdout:
        try:
            for pkg, v in json.loads(r.stdout).get("vulnerabilities", {}).items():
                if v.get("severity") in ("high", "critical"):
                    issues.append({"type": "dep", "package": pkg, "severity": v["severity"], "via": v.get("via", [])})
        except json.JSONDecodeError:
            pass
    return issues


def check_secrets() -> list[dict]:
    issues = []
    patterns = [
        (r'(?i)(api[_-]?key|secret|password|token)\s*=\s*["\'](?!\*|change-me)', "Possible hardcoded secret"),
        (r'-----BEGIN (RSA |EC )?PRIVATE KEY-----', "Embedded private key"),
    ]
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", ".next", ".mypy_cache", ".pytest_cache", ".ruff_cache")]
        for f in files:
            if not f.endswith((".py", ".ts", ".tsx", ".yml", ".yaml", ".toml", ".json")) or f == "package-lock.json":
                continue
            path = Path(root) / f
            try:
                text = path.read_text(errors="ignore")
                for pat, desc in patterns:
                    for m in re.finditer(pat, text):
                        issues.append({"file": str(path.relative_to(ROOT)), "line": text[:m.start()].count("\n") + 1, "desc": desc})
            except Exception:
                pass
    return issues


def check_headers_config() -> list[dict]:
    issues = []
    expected = [
        ("X-Content-Type-Options", "nosniff"), ("X-Frame-Options", "DENY"),
        ("Strict-Transport-Security", "max-age=63072000"),
        ("X-XSS-Protection", "0"), ("Referrer-Policy", "strict-origin"),
    ]
    for fpath in [ROOT / "api" / "security.py", ROOT / "web" / "next.config.ts"]:
        if not fpath.exists():
            issues.append({"file": str(fpath), "desc": "Security headers file missing"})
            continue
        text = fpath.read_text()
        for hdr, val in expected:
            if hdr not in text:
                issues.append({"file": str(fpath.relative_to(ROOT)), "desc": f"Missing header: {hdr}"})
    return issues


def check_cors_config() -> list[dict]:
    issues = []
    cfg = ROOT / "api" / "app.py"
    if cfg.exists():
        text = cfg.read_text()
        if 'allow_origins=settings.cors_origins' in text:
            issues.append({"file": "api/app.py", "desc": "CORS origins from config — verify in production"})
    return issues


def check_dockerfile() -> list[dict]:
    issues = []
    for df in [ROOT / "Dockerfile", ROOT / "web" / "Dockerfile"]:
        if not df.exists():
            issues.append({"file": str(df), "desc": "Dockerfile missing"})
            continue
        text = df.read_text()
        if "USER root" in text or "USER app" not in text:
            issues.append({"file": df.relative_to(ROOT).as_posix(), "desc": "Runs as root — security risk"})
        if "HEALTHCHECK" not in text:
            issues.append({"file": df.relative_to(ROOT).as_posix(), "desc": "Missing HEALTHCHECK"})
    return issues


def run_all() -> dict[str, Any]:
    results = {"timestamp": datetime.now(UTC).isoformat(), "findings": []}
    for name, fn in [
        ("frontend_dependencies", check_frontend_deps),
        ("secret_leakage", check_secrets),
        ("security_headers", check_headers_config),
        ("cors_config", check_cors_config),
        ("dockerfile_audit", check_dockerfile),
    ]:
        findings = fn()
        results["findings"].extend({"category": name, **f} for f in findings)
    results["total_findings"] = len(results["findings"])
    results["high"] = sum(1 for f in results["findings"] if f.get("severity") == "high")
    return results


if __name__ == "__main__":
    results = run_all()
    print(json.dumps(results, indent=2))
    Path(ROOT / "security_audit_results.json").write_text(json.dumps(results, indent=2))
    sys.exit(min(results["high"], 1))
