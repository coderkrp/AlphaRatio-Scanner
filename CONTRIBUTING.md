# Contributing to AlphaRatio Scanner

First off, thank you for considering contributing to AlphaRatio Scanner! It's people like you that make open-source software such a powerful tool.

## Code of Conduct

By participating in this project, you are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to the project maintainers.

## Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/ratio-scanner.git
   cd ratio-scanner
   ```
3. **Set up the development environment**:
   We use `uv` for lightning-fast dependency management.
   ```bash
   uv venv
   uv pip install -e .[dev]
   ```
4. **Install Pre-commit hooks**:
   ```bash
   pre-commit install
   ```
   This ensures that `ruff` and `black` (or `ruff format`) automatically format your code before every commit.

## Development Workflow

1. **Create a branch**: `git checkout -b feature/your-feature-name` or `fix/issue-description`.
2. **Make your changes**: Write modular, clean code. If you are adding a new indicator, consider placing it in the `src/engines/` directory and writing an accompanying unit test.
3. **Run the tests**:
   ```bash
   pytest tests/
   ```
4. **Commit your changes**: Write clear, descriptive commit messages.
5. **Push to your fork**: `git push origin feature/your-feature-name`
6. **Open a Pull Request**: Provide a clear description of the problem you solved or the feature you added. Ensure all CI checks pass.

## Engineering Standards

- **Type Hints**: All new functions must include Python type hints (`def func(data: pd.DataFrame) -> float:`).
- **Docstrings**: We use Google-style docstrings for all classes and public methods.
- **Stateless Engines**: Any new calculation engine must be purely functional. It should take a DataFrame, apply transformations, and return a DataFrame. Do not mix DB state reads/writes inside mathematical engine loops.
- **Dependencies**: Keep dependencies lightweight. If a feature can be done natively in `pandas` or `numpy` efficiently, avoid adding a new third-party library. (Note: `ta-lib` may have platform-specific compilation issues; we prefer `pandas-ta` for ease of distribution unless strict performance dictates otherwise).

## Review Process

- A maintainer will review your PR, focusing on code quality, performance (vectorization), and architectural fit.
- We may request changes or suggest alternative implementations.
- Once approved, your PR will be squash-merged into the `main` branch.
