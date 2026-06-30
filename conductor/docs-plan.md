# Documentation Update Plan: Telegram Formatting

## Objective
Update the project documentation to accurately reflect the recent changes to the Telegram message formatting (switching to HTML parse mode, adding `<pre>` tags for alignment, and condensing labels).

## Key Files & Context
- `CHANGELOG.md`: Needs an entry under `[Unreleased]` documenting the aesthetic and structural improvements to Telegram alerts.
- `docs/prd.md`: Sections `11.3`, `11.4`, and `11.6` need to be updated to show the new HTML-based message formats.
- `docs/spec_amendments.md`: Sections `§11.3`, `§11.4`, and `§11.6` need to be updated to mirror the PRD changes.

## Implementation Steps

1. **Update `CHANGELOG.md`**:
   - Insert an `## [Unreleased]` section at the top (above `1.0.0`).
   - Add a `### Changed` subsection.
   - Describe the transition from Markdown to HTML mode and the use of monospaced blocks for mobile-friendly alignment.

2. **Update `docs/prd.md`**:
   - In `11.3 Transition Summary Format`, update the example block to use HTML `<b>` tags.
   - In `11.4 Daily Digest Format`, update the example block to use `<b>`, `<i>`, and `<pre>` tags. Condense `Dist ATH:` to `Dist:`.
   - In `11.6 Telegram Message Length Limit`, update the example to show pagination combined with the new HTML tags.

3. **Update `docs/spec_amendments.md`**:
   - Apply the exact same changes made in step 2 to sections `§11.3`, `§11.4`, and `§11.6` to keep the specifications perfectly aligned.

## Verification & Testing
- Review the markdown files visually to ensure the formatting blocks are accurate and properly enclosed in code fences.