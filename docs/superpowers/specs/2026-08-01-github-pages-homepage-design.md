# GitHub Pages Homepage Design

## Goal

Publish and maintain a fast, lightweight compman project homepage through GitHub Pages.

## Direction

Use the approved hybrid layout: a concise product landing section followed immediately by practical quick-start and guide content. The page should explain why compman exists, let a visitor install it quickly, and provide direct paths to deeper repository documentation.

## Implementation

- Store the standalone site in `docs/site/` with `index.html` and `styles.css`.
- Use semantic HTML and responsive CSS only.
- Do not add JavaScript, package managers, site generators, external fonts, analytics, cookies, or third-party assets.
- Use a dark, terminal-inspired visual style with accessible contrast and visible keyboard focus states.
- Support narrow mobile screens, tablets, and desktop layouts.

## Content

- Header navigation to Features, Quick Start, Commands, Deploy, FAQ, and GitHub.
- Hero statement: Docker Compose management without a heavyweight GUI.
- Installation command and primary calls to action.
- Feature cards for stack/service operations, backups, diagnostics, and S3 or HTTP archive deployment.
- Quick Start using `compman init --scaffold`.
- Compact command reference linked to the full README.
- Deployment examples for an S3 prefix/archive and a public HTTP/HTTPS archive.
- Audience statement for operators in environments where web GUIs or heavyweight management software are unavailable.
- FAQ covering runtime support, configuration, deployment sources, and safety.
- Footer with repository, changelog, and license links.

## Deployment

- Add `.github/workflows/pages.yml` using GitHub's official Pages actions.
- Trigger on pushes to `main` that affect site or workflow files, plus manual dispatch.
- Upload `docs/site/` as the Pages artifact and deploy it to the `github-pages` environment.
- Grant only `contents: read`, `pages: write`, and `id-token: write` permissions.
- Serialize deployments with a Pages-specific concurrency group without cancelling an in-progress deployment.

## Repository integration

- Add the public homepage URL `https://allbegray.github.io/compman/` near the top of README.md.
- Ignore `.superpowers/` because browser brainstorming artifacts are local design aids, not project content.
- Include the homepage in version `1.2.0` release notes.

## Verification

- Validate required HTML sections, links, metadata, and workflow permissions with repository tests.
- Serve the site locally and inspect desktop and mobile layouts in a real browser.
- Run the complete project quality gates and retain 100% statement and branch coverage.
- Keep the existing built-executable smoke test requirement for the combined `1.2.0` changes.
