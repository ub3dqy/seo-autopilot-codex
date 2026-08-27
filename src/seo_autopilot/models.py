from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    AUTO_FIX = "A_AUTO_FIX"
    REVIEW_REQUIRED = "B_REVIEW_REQUIRED"
    ADVISORY_ONLY = "C_ADVISORY_ONLY"


class RunStatus(str, Enum):
    READY = "READY"
    READY_WITH_LIMITATIONS = "READY_WITH_LIMITATIONS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    BLOCKED = "BLOCKED"
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_RUN = "NOT_RUN"


class Phase(str, Enum):
    INITIALIZED = "INITIALIZED"
    DISCOVERY_COMPLETE = "DISCOVERY_COMPLETE"
    EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
    PLAN_COMPLETE = "PLAN_COMPLETE"
    PATCH_APPLIED = "PATCH_APPLIED"
    VALIDATION_COMPLETE = "VALIDATION_COMPLETE"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


class EvidenceClass(str, Enum):
    DETERMINISTIC_STATIC = "DETERMINISTIC_STATIC"
    FRAMEWORK_SOURCE = "FRAMEWORK_SOURCE"
    LIVE_BROWSER = "LIVE_BROWSER"
    EXTERNAL_DATA = "EXTERNAL_DATA"
    OWNER_FACT = "OWNER_FACT"
    SCOPE_CONTROL = "SCOPE_CONTROL"


class ScopeExclusionStatus(str, Enum):
    EXCLUDED_BY_SCOPE = "EXCLUDED_BY_SCOPE"
    EXCLUDED_SENSITIVE = "EXCLUDED_SENSITIVE"


@dataclass(frozen=True)
class Evidence:
    source: str
    location: str
    excerpt: str = ""
    sha256: str | None = None


@dataclass(frozen=True)
class ScopeExclusion:
    path: str
    status: ScopeExclusionStatus
    reason: str
    detection_markers: list[str] = field(default_factory=list)
    files_not_read: bool = True
    entries_not_read: int | None = None


@dataclass
class AuditScope:
    mode: str
    git_repository: bool
    source_roots: list[str] = field(default_factory=list)
    tracked_candidates: int = 0
    untracked_source_candidates: int = 0
    candidate_files: int = 0
    static_html_files_scanned: int = 0
    framework_files_scanned: int = 0
    excluded_generated_directories: list[ScopeExclusion] = field(default_factory=list)
    excluded_non_production_directories: list[ScopeExclusion] = field(default_factory=list)
    excluded_site_verification_files: list[ScopeExclusion] = field(default_factory=list)
    excluded_sensitive_directories: list[ScopeExclusion] = field(default_factory=list)
    metadata_entries_examined: int = 0
    metadata_scan_truncated: bool = False


@dataclass
class Finding:
    finding_id: str
    rule_id: str
    severity: str
    title: str
    message: str
    path: str
    line: int | None
    risk: RiskLevel
    confidence: float
    evidence: list[Evidence] = field(default_factory=list)
    evidence_class: EvidenceClass = EvidenceClass.DETERMINISTIC_STATIC
    auto_fix_available: bool = False
    status: str = "OPEN"


@dataclass(frozen=True)
class SafeFix:
    finding_id: str
    path: str
    line: int
    offset: int
    original: str
    replacement: str
    description: str
    risk: RiskLevel = RiskLevel.AUTO_FIX


@dataclass
class Change:
    path: str
    description: str
    risk: RiskLevel
    before_sha256: str
    after_sha256: str
    lines_changed: int
    finding_ids: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    name: str
    status: RunStatus
    command: list[str] = field(default_factory=list)
    returncode: int | None = None
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class DoctorResult:
    status: RunStatus
    repository_root: str | None
    stack: str
    git_available: bool
    codex_available: bool
    clean_worktree: bool | None
    limitations: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)


@dataclass
class RunReport:
    schema_version: int
    run_id: str
    product_version: str
    policy_pack_version: str
    status: RunStatus
    phase: Phase
    repository_root: str
    repository_commit: str | None
    detected_stack: str
    started_at: str
    finished_at: str | None = None
    mode: str = "audit"
    findings: list[Finding] = field(default_factory=list)
    planned_fixes: list[SafeFix] = field(default_factory=list)
    changes: list[Change] = field(default_factory=list)
    checks: list[CheckResult] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    residual_risks: list[str] = field(default_factory=list)
    branch: str | None = None
    rollback: list[str] = field(default_factory=list)
    budgets: dict[str, int] = field(default_factory=dict)
    external_sources: list[str] = field(default_factory=list)
    audit_scope: AuditScope | None = None

    def to_dict(self) -> dict[str, Any]:
        return _enum_values(asdict(self))


def _enum_values(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {key: _enum_values(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_enum_values(item) for item in value]
    if isinstance(value, tuple):
        return [_enum_values(item) for item in value]
    return value
