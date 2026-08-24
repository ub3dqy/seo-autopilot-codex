# Configuration

The deterministic engine works without project commands. Optional project validation is configured in `.seo-autopilot.json`.

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

Default budgets:

- 500 static HTML pages;
- 10 changed files;
- 200 changed lines;
- 300 seconds per trusted command;
- 900 seconds for the manual live Codex canary.

Use lower budgets for large or sensitive repositories. Budget expansion is an explicit owner decision and does not alter risk classification.
