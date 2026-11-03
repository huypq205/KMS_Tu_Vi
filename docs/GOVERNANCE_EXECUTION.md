# Governance completion and review ledger

User authorization: finish T1–T11, review each task, commit and push each completed
task to origin/main. Do not publish private input workbooks or CSV summaries.

## Execution sequence (completed)

1. Merge origin/feature/t3-evidence-labels (aaa0951), review and push.
2. Review T1/T2 and correct any remaining acceptance gaps.
3. Review T4/T5; T4 differences remain documented in GitHub issue #1.
4. Confirm real workbook and record T7 real-data review; push.
5. Implement/review/test/push T6 star dossiers.
6. Implement/review/test/push T8 locked case validation.
7. Implement/review/test/push T9 annual report.
8. Implement/review/test/push T10 skill (use skill-creator).
9. Complete T11 changelog and end-to-end review; push.

## Findings and evidence

- Local main started clean at ab7e636, already includes T7 and origin/main.
- T3 merged, reviewed and pushed to origin/main at 5b5d508 (2089 passed, 351 known T4 xfailed).
- T1 review fixed final-retry leakage for C/D, added conclusion classification
  across schema/UI/fixture. Regression: 2091 passed, 351 known T4 xfailed.
- T1 review pushed at bd428c3. T2 review fixed duplicate-id inflation and aligned
  strong minimum to three distinct facts; cache v5. Regression 2092 passed,
  351 known T4 xfailed. T4/T5 reviewed through integration plus existing vectors
  and 40-entry comparison; mismatches remain in issue #1, no vendor edits.
- Test suite modified tracked kms.db cache; this generated DB change was not
  committed. Final backup/fingerprint review and restoration are recorded below.
- T3 initial integration regression: 2087 passed, 351 known T4 xfailed.
- T3 review reproductions found uncited evidence labels accepted and Tị/Tỵ
  inconsistent in adjacent-palace classification. Regression tests and fixes
  were reviewed and pushed in 5b5d508. `suy_luan` may accompany a cited kind, but an uncited empirical
  kind must not be accepted.
- Real input discovered at
  D:/FPT/2026/FA26/KMS301/Project_TuVi/Final/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx.
  Gate passed all 10456 records as new with zero errors, no source-D rows.
- T7 real-data review also passed against existing DB: 10456 checked, zero new
  ids, zero errors. Workbook SHA256 27901de589ec69959b43a80c3d108b83f5ebbc4c53489795b3301cf31ae72f40.
  Source distribution matches NPL 2191, BD 4450, DAU 3815. No production import run.
- Same-name CSV (1559 bytes) contains Indicator/Value/Explanation, not knowledge
  exports. `tuvi_import/` is a hypothetical export directory, not that CSV.
- Frontend skill and full app-screens reference were read before new screens;
  existing Streamlit shell, palette and typography were retained.

## T6 review

- Implemented 14 source-aware slots, 20 gated and explicitly unverified seeds,
  read-only API aliases, API-key/error paths and Streamlit navigation.
- Review: separate books/citations, no invented missing data, seed toggle on
  both client/server. Real corpus checked for Vũ Khúc and Cự Môn.
- Tests: 8 targeted passed; regression 2100 passed / 351 known T4 xfailed.
- Browser review: desktop/tablet/mobile; existing typography/palette retained.

## Completion criteria

All T1–T11 implemented/reviewed. Reviewed contracts, source attribution, empty
states, errors, immutability, API/UI integration and publication in addition to
test counts. See GOVERNANCE_ACCEPTANCE.md for the final task matrix and limits.

## T8 review

- Append-only anonymous cases/predictions/events; freeze enforced by SQLite.
- Reviewed lock/revision/failed results, same-case links, no hindsight grading,
  input confidence, distinct facts, server timestamps and 29/30 eligible cases.
- API + Streamlit implemented; no production cases invented or written in review.
- Tests 11 passed; global 2111 passed, 351 known T4 xfailed (56.52s).
- Browser 1440/768/390px: no findings; source notes in CASE_VALIDATION.md.

## T9 review

- Server-derived four-layer matrix, adjacent-year comparison, missing-basis
  section and read-only annual API; model text cannot fill monthly gaps.
- Reviewed C/D, confidence, selected table, boundaries, escaping and missing year.
- Screenshot review caught branch/domain mismatch for decade facts; fixed and
  covered with a regression. Narrative specificity ignores server matrix years.
- 10 T9 tests passed; global through T9: 2121 passed / 351 known T4 xfailed
  (87.14s; pending T10 validator tests excluded from this scope).
- Cache v6; browser review closed/open rows at 1440/768/390px.

## T10 review

- Skill version 1.0 uses KMS APIs for four modes, with 14 principal-star triggers,
  scoped references and MIT attribution. Kept in the requested repo location;
  not installed into global Codex configuration.
- Reviewed realistic star/ask/annual/two-hour crosscheck requests against actual
  TestClient endpoints, no external LLM calls. Missing inputs/errors cannot be
  substituted with an invented chart. Corpus/book licensing remains separate.
- Validator detects duplicate YAML, >=500 lines, broken files/anchors and repo
  escapes; CI runs it. 13 targeted passed, KMS and skill-creator validators pass.
- Regression all tests: 2134 passed / 351 known T4 xfailed (57.41s).

## Final CI review finding

- GitHub run 41567301223 (e051f0b) passed both gates but failed three legacy
  singleton tests: missing optional qdrant_client/sentence_transformers in the
  intentionally light backend environment. This was not visible in the full
  local environment.
- Kept singleton tests meaningful with an isolated counting vector-store factory
  rather than opening production Qdrant files; lazy-import the optional model
  only when EmbeddingAdapter is instantiated. Added a subprocess regression
  that explicitly blocks sentence_transformers import.
- RED reproduced, then 6 singleton tests passed. Global: 2135 passed / 351 known
  T4 xfailed (55.73s). Remote CI PASSED on bc497f9, run 41567801027.

## Final T11 review

- Changelog covers all task changes, source attribution and affected conclusions;
  plan updated from draft to implemented/reviewed with explicit T4 limitations.
- T4 issue #1 remains open, consistent with the allowed document+issue DoD.
- DB fingerprints: only original horoscope_cache row removed by tests and three
  new empty journal tables; every original knowledge/evidence/chunk table unchanged.
- Full SQLite backup at .pytest_cache/kms-after-governance-tests.db, preview
  servers stopped, WAL checkpointed and tracked DB restored; no user cases lost.
- No private workbook, CSV summary, production journal rows or screenshot binary
  was staged. Individual task commits pushed to origin/main.
- Launch-guide follow-up: RUN_HOROSCOPE.md now uses app.py like run_local.bat,
  so the documented command exposes both new research pages.
