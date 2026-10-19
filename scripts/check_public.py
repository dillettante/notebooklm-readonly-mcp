"""Scan the Git publication set. Findings print rule/path only, never secret values."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {".env", "storage_state.json", "credentials.json", "config.local.json"}
RULES = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"),
    "google-key": re.compile(rb"AIza[0-9A-Za-z_-]{30,}"),
    "google-cookie": re.compile(rb'"name"\s*:\s*"(?:SID|SAPISID|__Secure-1PSID)"'),
    "storage-cookie-array": re.compile(rb'"cookies"\s*:\s*\[\s*\{'),
    "personal-home": re.compile(rb"/Users/(?!Shared/)[A-Za-z0-9._-]+/|C:\\\\Users\\\\[A-Za-z0-9._-]+"),
    "private-network": re.compile(rb"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d+\.\d+\b"),
    "email": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
}


def scan(paths):
    findings, unreadable = [], []
    for path in paths:
        rel = path.relative_to(ROOT).as_posix()
        if path.name in FORBIDDEN_NAMES or path.suffix in {".pem", ".key"}:
            findings.append({"file": rel, "rule": "forbidden-file"})
        try:
            data = path.read_bytes()
            data.decode("utf-8")
        except (OSError, UnicodeError):
            unreadable.append(rel)
            continue
        for name, pattern in RULES.items():
            if pattern.search(data):
                # Deliberately synthetic example domains in unit tests are not personal data.
                if name == "email" and all(
                    m.group().endswith((b"@example.org", b"@example.com")) for m in pattern.finditer(data)
                ):
                    continue
                findings.append({"file": rel, "rule": name})
    return {
        "files_scanned": len(paths),
        "unreadable_count": len(unreadable),
        "findings": findings,
        "verdict": "PASS" if not findings and not unreadable else "FAIL",
    }


def main():
    cp = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True)
    paths = [ROOT / p.decode() for p in cp.stdout.split(b"\0") if p]
    if not paths:
        raise SystemExit("No tracked files; stage the intended publication set before scanning.")
    report = scan(paths)
    print(json.dumps(report, indent=2))
    if report["verdict"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
