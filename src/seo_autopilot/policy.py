from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import RiskLevel


HIGH_RISK_FILENAMES = {
    "robots.txt",
    "sitemap.xml",
    "sitemap_index.xml",
    "nginx.conf",
    "vercel.json",
    "netlify.toml",
}

HIGH_RISK_TERMS = {
    "canonical",
    "hreflang",
    "noindex",
    "redirect",
    "route",
    "schema",
    "structured data",
    "delete page",
    "remove page",
    "deploy",
    "production",
}


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    title: str
    default_risk: RiskLevel
    severity: str
    source_url: str
    auto_fix_condition: str | None = None


@dataclass(frozen=True)
class PolicyPack:
    pack_id: str
    version: str
    last_verified: str
    rules: dict[str, PolicyRule]
    sources: tuple[str, ...]


def default_policy_path(source_root: Path) -> Path:
    return source_root / "policy-packs" / "google-search" / "2026-08" / "policies.json"


def load_policy_pack(path: Path) -> PolicyPack:
    if not path.is_file() or path.stat().st_size > 2_000_000:
        raise ValueError(f"policy pack is missing or invalid: {path}")
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("policy pack must use schema_version 1")
    raw_rules = payload.get("rules")
    if not isinstance(raw_rules, list):
        raise ValueError("policy pack rules must be an array")
    rules: dict[str, PolicyRule] = {}
    sources: list[str] = []
    for raw in raw_rules:
        if not isinstance(raw, dict):
            raise ValueError("each policy rule must be an object")
        rule_id = str(raw["id"])
        source_url = str(raw["source_url"])
        rule = PolicyRule(
            rule_id=rule_id,
            title=str(raw["title"]),
            default_risk=RiskLevel(str(raw["default_risk"])),
            severity=str(raw["severity"]),
            source_url=source_url,
            auto_fix_condition=str(raw["auto_fix_condition"]) if raw.get("auto_fix_condition") else None,
        )
        if rule_id in rules:
            raise ValueError(f"duplicate policy rule: {rule_id}")
        rules[rule_id] = rule
        if source_url not in sources:
            sources.append(source_url)
    return PolicyPack(
        pack_id=str(payload["pack_id"]),
        version=str(payload["version"]),
        last_verified=str(payload["last_verified"]),
        rules=rules,
        sources=tuple(sources),
    )


def classify_change(path: str, description: str, mechanically_proven: bool = False) -> RiskLevel:
    normalized_path = path.replace("\\", "/").lower()
    normalized_description = description.lower()
    filename = normalized_path.rsplit("/", 1)[-1]
    if filename in HIGH_RISK_FILENAMES:
        return RiskLevel.ADVISORY_ONLY
    if any(term in normalized_description or term in normalized_path for term in HIGH_RISK_TERMS):
        return RiskLevel.REVIEW_REQUIRED
    if mechanically_proven:
        return RiskLevel.AUTO_FIX
    return RiskLevel.REVIEW_REQUIRED
