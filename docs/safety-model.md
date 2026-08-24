# Safety model

## Assets protected

- owner source tree and uncommitted work;
- Git history and remote branches;
- credentials and environment variables;
- production routes, crawl controls, indexing directives, and deployment configuration;
- business, legal, medical, pricing, location, and contact claims;
- release artifacts and their provenance.

## Adversaries and failure modes

The model assumes repository content, fetched pages, generated text, issues, dependency metadata, and command output may contain prompt injection. It also assumes the model can misunderstand architecture, choose the wrong file, overstate SEO outcomes, repeat a non-idempotent change, or stop after a partial write.

## Enforced controls

### Content is not authority

Instruction-like content is recorded as evidence. It never changes the workflow, permissions, allowed commands, risk level, or output destination.

### No implicit project execution

SEO Autopilot does not infer commands from `package.json`, Makefiles, README files, CI, or model suggestions. Optional validators require an exact argv array plus a matching SHA-256 in `.seo-autopilot.json`. Processes use `shell=False` and a sanitized environment.

### Mutation isolation

The owner working tree must be clean. A temporary worktree is created from exact `HEAD`. A dedicated local branch is used. Git hooks are disabled. No remote operation is implemented in the fix command.

### Risk floor

| Level | Engine behavior | Typical examples |
|---|---|---|
| A_AUTO_FIX | May apply after mechanical proof | Missing dimensions read from a supported local image header |
| B_REVIEW_REQUIRED | Evidence and proposal only | title, description, alt, lang, canonical, sitemap, internal links, JSON-LD |
| C_ADVISORY_ONLY | Report only | noindex, robots, redirects, URL or route changes, deletion, production/deployment |

The model cannot downgrade risk. A future adapter must add deterministic code and tests before expanding A-level scope.

### Budgets

Page count, changed files, diff lines, command timeout, and live-eval runtime are bounded. Exceeding a budget stops before further writes.

### Validation and idempotency

Built-in `git diff --check`, trusted project checks, source evidence revalidation, and a second audit must pass. Repeated A-level fixes are a failure.

### Rollback

Failure removes the isolated worktree and owned branch. Successful branches retain a state file and explicit rollback command. Rollback refuses to delete a branch that does not start with `seo-autopilot/`.

## Deliberately absent capabilities

Fix mode cannot push, merge, deploy, publish, edit remote resources, retrieve Search Console, purchase third-party data, or claim ranking/indexing outcomes. Those are separate owner-authorized workflows.

## Residual risks

- an owner-approved executable can still be malicious;
- a compromised interpreter, Git binary, host, or dependency source is outside the local trust boundary;
- static source cannot prove post-deployment rendering, indexing, traffic, ranking, or user experience;
- reports may contain repository excerpts and must be reviewed before sharing;
- GitHub branch protection, immutable releases, secret scanning, and private reporting settings require repository-level owner configuration in addition to tracked files.
