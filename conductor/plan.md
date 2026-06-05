# Documentation Cleanup Plan

## Objective
Refine the AI-generated project documentation to prepare the repository for public release. This involves removing AI artifacts, applying the user's GitHub username (`coderkrp`), merging spec amendments, and updating terminology to reflect the current state (V1) versus future phases.

## Changes

### 1. `README.md` Updates
- Replace all instances of `yourusername` with `coderkrp`.
- Keep the architecture diagram placeholder note as a reminder to create the actual asset.
- Change the header `### Telegram Daily Digest (Placeholder)` to `### Telegram Daily Digest`.

### 2. `docs/setup.md` & `docs/deployment.md`
- Replace `yourusername` with `coderkrp` in git clone commands.

### 3. Merge and Delete `docs/spec_amendments.md`
- Systematically apply all PRD amendments from `spec_amendments.md` to `docs/prd.md`.
- Systematically apply all Architecture amendments from `spec_amendments.md` to `docs/architecture.md`.
- Delete `docs/spec_amendments.md` once the changes are merged.

### 4. `docs/prd.md` Refinement
- **Remove AI Headers**: Delete "Master Documentation Bundle (V1)", "DOCUMENT 1 — PRODUCT REQUIREMENTS DOCUMENT (PRD)", and redundant separators.
- **Terminology Shift**: Change references of "MVP" to "V1" or "Phase 1" to accurately reflect the currently built system while preserving the fact that V2/V3 features are planned.
- **Tense Shift**: Change future-tense requirements ("The MVP should...") to present-tense realities ("The system does...").

### 5. `docs/architecture.md` Refinement
- **Remove AI Headers**: Delete "Master Documentation Bundle (V1)", "DOCUMENT 2 — TECHNICAL ARCHITECTURE DOCUMENT", and redundant separators.
- **Terminology Shift**: Similar to the PRD, change "MVP" to "V1".
- **Integration**: Ensure the V2 deferred sections are clearly marked as future architecture phases rather than MVP exclusions.

### 6. `docs/AI Engineering Guidelines.md`
- Remove the "Master Documentation Bundle (V1)" and "DOCUMENT 3 — AI ENGINEERING GUIDELINES" headers.

## Verification
- Run `grep -ri "MVP" docs/` to ensure no lingering MVP references remain, unless specifically referring to past MVP definitions.
- Run `grep -ri "yourusername" .` to confirm the GitHub username is fully replaced.
- Ensure `docs/spec_amendments.md` is removed and its content is present in the PRD/Architecture docs.