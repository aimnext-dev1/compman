# GitHub Pages Homepage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a responsive hybrid landing-and-guide homepage for compman through GitHub Pages.

**Architecture:** Keep the site as dependency-free semantic HTML and CSS under `docs/site/`. Deploy that directory with GitHub's official Pages artifact workflow and protect its required structure with lightweight repository tests.

**Tech Stack:** HTML5, CSS, GitHub Actions, pytest

## Global Constraints

- No JavaScript, site generator, package manager, external font, analytics, cookie, or third-party asset.
- Public URL is `https://allbegray.github.io/compman/`.
- GitHub Actions permissions are limited to `contents: read`, `pages: write`, and `id-token: write`.
- Site must remain usable on mobile and desktop, with accessible contrast and focus states.

---

### Task 1: Create the hybrid project homepage

**Files:**
- Create: `docs/site/index.html`
- Create: `docs/site/styles.css`
- Modify: `tests/test_repository_urls.py`
- Create: `LICENSE`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: static homepage entry point and stylesheet
- Consumes: current CLI commands, repository URL, README, CHANGELOG, and LICENSE links

- [ ] **Step 1: Write failing site structure tests**

Assert that the HTML declares viewport and description metadata, references only the local stylesheet, contains the required section IDs, uses `init --scaffold`, documents S3 and HTTP deployment, and links to the official repository. Assert that CSS contains responsive media rules and visible `:focus-visible` styling. Assert that `LICENSE` contains the approved MIT text and copyright holder and that package metadata declares MIT.

- [ ] **Step 2: Run the focused test and verify failure**

```bash
uv run pytest tests/test_repository_urls.py -k github_pages_homepage -q
```

Expected: failure because `docs/site/index.html` does not exist.

- [ ] **Step 3: Implement semantic HTML and responsive CSS**

Create the approved hybrid layout with header navigation, hero, installation copy control via selectable command text, feature cards, quick start, compact commands, S3/HTTP deployment examples, audience statement, FAQ, and footer. Use CSS-only decoration and responsive grids.

- [ ] **Step 4: Run focused tests and verify success**

```bash
uv run pytest tests/test_repository_urls.py -k github_pages_homepage -q
```

Expected: all selected tests pass.

### Task 2: Deploy through GitHub Pages Actions

**Files:**
- Create: `.github/workflows/pages.yml`
- Modify: `tests/test_repository_urls.py`

**Interfaces:**
- Consumes: `docs/site/` from Task 1
- Produces: GitHub Pages deployment on relevant `main` pushes and manual dispatch

- [ ] **Step 1: Write a failing workflow contract test**

Assert the workflow contains the official configure, upload, and deploy Pages actions; uploads `docs/site`; uses the `github-pages` environment; contains the required minimal permissions and concurrency policy; and supports `workflow_dispatch`.

- [ ] **Step 2: Run the workflow test and verify failure**

```bash
uv run pytest tests/test_repository_urls.py -k github_pages_workflow -q
```

Expected: failure because `.github/workflows/pages.yml` does not exist.

- [ ] **Step 3: Implement the Pages workflow**

Trigger on relevant `main` paths and manual dispatch. Configure Pages, upload `docs/site`, and deploy it with the official actions under the `github-pages` environment.

- [ ] **Step 4: Run workflow tests and verify success**

```bash
uv run pytest tests/test_repository_urls.py -k github_pages -q
```

Expected: homepage and workflow contract tests pass.

### Task 3: Integrate documentation and verify the combined release

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `AGENTS.md`

**Interfaces:**
- Consumes: Tasks 1-2 homepage URL and the combined version `1.2.0` changes
- Produces: discoverable homepage and current maintainer documentation

- [ ] **Step 1: Add homepage links and release notes**

Place the homepage URL near the README introduction, list the site structure in AGENTS.md, and add the Pages homepage to the existing `1.2.0` CHANGELOG entry.

- [ ] **Step 2: Inspect desktop and mobile layouts**

Serve `docs/site/` locally, open it in a browser, and inspect desktop and narrow mobile viewport screenshots. Fix overflow, unreadable contrast, broken anchors, or layout collisions.

- [ ] **Step 3: Run the combined project quality gates**

```bash
uv run ruff check compman tests
uv run mypy compman
uv run pytest --cov=compman --cov-report=term-missing
```

Expected: all checks pass with 100% statement and branch coverage.

- [ ] **Step 4: Build and smoke-test the Windows executable**

Build and install version `1.2.0` in an isolated Windows environment. Exercise `-v`, `-h`, `init --scaffold`, rejection of `init --skeleton`, and HTTP zip deployment against a local HTTP server.

- [ ] **Step 5: Commit the combined implementation**

```bash
git add .github compman docs/site docs/superpowers/plans tests README.md AGENTS.md CHANGELOG.md pyproject.toml uv.lock
git commit -m "feat: publish homepage and HTTP archive deployment"
```
