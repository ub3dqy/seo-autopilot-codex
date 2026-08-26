# Configuration

The deterministic engine works without project commands. Optional project validation and source scope are configured in `.seo-autopilot.json`.

## Trusted project checks

```json
{
  "schema_version": 1,
  "checks": [
    {
      "name": "project tests",
      "argv": ["npm", "test"],
      "sha256": "<digest>",
      "timeout_seconds": 300
    }
  ]
}
```

Calculate the digest from the exact argv array:

```bash
seo-autopilot command-hash -- npm test
```

Changing one argument invalidates trust. Commands run directly without a shell. Environment variables used for shell startup or runtime injection are removed. The executable itself remains an owner trust decision.

## Source-first audit scope

Optional scope additions and exclusions can share the same file:

```json
{
  "schema_version": 1,
  "scope": {
    "include_roots": ["website-src"],
    "exclude_directories": ["legacy-export"]
  },
  "checks": []
}
```

Scope paths are relative to the repository and may not contain `..`. Includes never override:

- hard browser-profile privacy exclusions;
- generated, archive, report, temporary, fixture, example, build, and dependency exclusions;
- symlink, junction, and reparse-point boundaries;
- the A-level `CURRENT_SOURCE` requirement.

The runtime records all effective exclusions in `run.json.audit_scope`. See [Audit scope and privacy boundary](audit-scope.md).

## Default budgets

- 500 static HTML pages;
- 10 changed files;
- 200 changed lines;
- 300 seconds per trusted command;
- 900 seconds for the manual live Codex canary;
- 250,000 directory entries for metadata-only scope discovery.

Use lower budgets for large or sensitive repositories. Budget expansion is an explicit owner decision and does not alter risk classification or privacy exclusions.
