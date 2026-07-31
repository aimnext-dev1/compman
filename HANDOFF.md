# compman Handoff

## Current State

- Branch: `main`
- Latest commit: `52b6558 test: isolate runtime command calls`
- Worktree was clean after latest push.
- GitHub Actions run for `52b6558`: https://github.com/aimnext-dev1/compman/actions/runs/30630886815
- CI matrix issue fixed: runtime passthru calls in `tests/test_docker.py` are mocked, so tests do not require Docker installed on macOS runners.

## Verification

- `151 passed, 2 skipped`
- Ruff passed.
- mypy passed.
- Wheel build passed earlier.
- CI previously passed on Ubuntu and Windows; latest run includes macOS fix.

## Next Work

1. Confirm GitHub Actions run `30630886815` is fully green.
2. Update CI actions to current major versions (`actions/checkout`, `astral-sh/setup-uv`) to remove Node.js 20 warnings.
3. Add packaging smoke test: build wheel, install it, run `compman --help` and `compman version`.
4. Add separate Linux Docker/Ministack integration job; keep OS matrix focused on unit tests.
5. Continue replacing remaining hardcoded CLI messages with i18n keys.

## Constraints

- Python `>=3.10`.
- Keep changes minimal; avoid new dependencies unless necessary.
- Docker is not guaranteed on macOS/Windows CI runners.
- Do not commit generated `.coverage`, `build/`, or `dist/` artifacts.
