# Release & Semantic Versioning Strategy

This project follows strict [Semantic Versioning (SemVer) 2.0.0](https://semver.org/). 
Given the nature of a data-driven quant application, version bumps mean the following:

- **MAJOR (X.y.z)**: Breaking changes to `config.yaml` schema, database schema (requiring migrations or full wipes), or profound changes to the core math that invalidates previous historical backtests.
- **MINOR (x.Y.z)**: Backwards-compatible new features (e.g., adding a new `engine`, supporting Discord alerts).
- **PATCH (x.y.Z)**: Backwards-compatible bug fixes (e.g., fixing a division by zero error on newly listed stocks).

---

## Pre-Release Checklist

Before tagging a new release (e.g., `v1.1.0`) on GitHub, ensure the following steps are completed.

### 1. Code Quality
- [ ] Run `uv run ruff check .` - No linting errors.
- [ ] Run `uv run ruff format .` - Formatting applied.
- [ ] Run `uv run pytest tests/` - All unit tests pass locally.

### 2. Math & Data Verification
- [ ] Run a manual `main.py` pipeline against a realistic config.
- [ ] Verify that `rs_strength_pct` for a known high-flyer (e.g., Trent, Zomato) manually matches a TradingView chart relative strength curve.
- [ ] Ensure no `yfinance` deprecation warnings are present.

### 3. Documentation & Versioning
- [ ] Update `CHANGELOG.md` with the new version and date. Move items from `[Unreleased]` to the new version header.
- [ ] Update the `version` string in `pyproject.toml`.
- [ ] Ensure `README.md` and `docs/` reflect any new configuration keys.

### 4. Git & GitHub
- [ ] Commit all changes: `git commit -m "chore: prepare release v1.1.0"`
- [ ] Create a git tag: `git tag -a v1.1.0 -m "Release v1.1.0"`
- [ ] Push tags: `git push origin main --tags`
- [ ] Create a GitHub Release referencing the tag, copying the changelog contents into the release description.
