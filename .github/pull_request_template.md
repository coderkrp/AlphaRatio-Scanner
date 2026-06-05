## Description
<!-- Please include a summary of the change and which issue is fixed. -->
<!-- Describe the problem you are solving, not just the code you are changing. -->

Fixes # (issue)

## Type of change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance Optimization (Vectorization)

## How Has This Been Tested?
<!-- Please describe the tests that you ran to verify your changes. -->
- [ ] Added unit test utilizing static CSV mocks
- [ ] Executed `uv run pytest tests/` successfully
- [ ] Verified changes against historical DB data (no lookahead bias introduced)

## Quant Verification (If modifying Engines)
- [ ] Math logic verified against TradingView / external sources
- [ ] Execution remains fully vectorized (No Pandas `iterrows`)

## Checklist:
- [ ] My code follows the style guidelines of this project (Ruff / Black)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings in the linter
