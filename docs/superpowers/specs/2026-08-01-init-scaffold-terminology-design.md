# Init Scaffold Terminology Design

## Goal

Replace the `skeleton` terminology in `compman init` with `scaffold` so the command describes generating a usable starting configuration more clearly.

## CLI behavior

- Replace `compman init --skeleton` with `compman init --scaffold`.
- Remove `--skeleton` without a compatibility alias. Calls using it must fail as an unknown option.
- Keep the generated `compman.yml` and all other initialization behavior unchanged.
- Change the interactive mode label and command help from `skeleton` to `scaffold`.

## Documentation and localization

- Update README command examples and reference syntax.
- Update AGENTS.md so repository guidance matches the CLI.
- Update English and Korean i18n strings that describe the initialization mode or show its direct command.
- Do not rename internal deploy-time scaffold modules or functions; they already use the preferred term.

## Compatibility and versioning

This intentionally removes a public option. Increase the minor version for the next release and record the breaking CLI rename in CHANGELOG.md.

## Verification

- Test `init --scaffold` creates the default configuration.
- Test `init --skeleton` is rejected.
- Test the interactive menu and localized guidance use `scaffold` terminology.
- Run Ruff, mypy, and the complete pytest suite with 100% statement and branch coverage.
- Build the distributable artifact and smoke-test the installed `compman` executable with `init --scaffold`, `-h`, and `-v`.
