#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def git_files(root: Path) -> list[Path]:
    completed = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    return [root / item.decode("utf-8", errors="surrogateescape") for item in completed.stdout.split(b"\x00") if item]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def created_time(root: Path) -> str:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch is None:
        completed = subprocess.run(
            ["git", "log", "-1", "--format=%ct"], cwd=root, capture_output=True, text=True, check=False
        )
        epoch = completed.stdout.strip() if completed.returncode == 0 and completed.stdout.strip() else "0"
    return datetime.fromtimestamp(int(epoch), timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a deterministic SPDX 2.3 source SBOM.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    files = [path for path in git_files(root) if path.is_file()]
    file_entries = []
    verification = hashlib.sha1()
    for index, path in enumerate(sorted(files, key=lambda item: item.relative_to(root).as_posix()), 1):
        relative = path.relative_to(root).as_posix()
        digest = sha256(path)
        verification.update(digest.encode("ascii"))
        file_entries.append(
            {
                "SPDXID": f"SPDXRef-File-{index}",
                "fileName": f"./{relative}",
                "checksums": [{"algorithm": "SHA256", "checksumValue": digest}],
                "licenseConcluded": "NOASSERTION",
                "licenseInfoInFiles": ["NOASSERTION"],
                "copyrightText": "NOASSERTION",
            }
        )
    package_verification = verification.hexdigest()
    namespace_digest = hashlib.sha256(f"{version}:{package_verification}".encode("utf-8")).hexdigest()
    document = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"seo-autopilot-codex-{version}",
        "documentNamespace": f"https://github.com/ub3dqy/seo-autopilot-codex/spdx/{version}/{namespace_digest}",
        "creationInfo": {
            "created": created_time(root),
            "creators": ["Tool: scripts/generate_sbom.py"],
            "licenseListVersion": "3.25",
        },
        "packages": [
            {
                "name": "seo-autopilot-codex",
                "SPDXID": "SPDXRef-Package",
                "versionInfo": version,
                "downloadLocation": "https://github.com/ub3dqy/seo-autopilot-codex",
                "filesAnalyzed": True,
                "packageVerificationCode": {"packageVerificationCodeValue": package_verification},
                "licenseConcluded": "LicenseRef-Proprietary",
                "licenseDeclared": "LicenseRef-Proprietary",
                "copyrightText": "Copyright 2026 ub3dqy",
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": f"pkg:github/ub3dqy/seo-autopilot-codex@{version}",
                    }
                ],
            }
        ],
        "files": file_entries,
        "relationships": [
            {"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": "SPDXRef-Package"},
            *[
                {"spdxElementId": "SPDXRef-Package", "relationshipType": "CONTAINS", "relatedSpdxElement": entry["SPDXID"]}
                for entry in file_entries
            ],
        ],
        "hasExtractedLicensingInfos": [
            {
                "licenseId": "LicenseRef-Proprietary",
                "extractedText": "See LICENSE.md in the source repository.",
                "name": "SEO Autopilot proprietary source-available notice",
            }
        ],
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
