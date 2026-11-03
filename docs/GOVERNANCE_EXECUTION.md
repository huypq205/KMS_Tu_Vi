# Governance completion and review ledger

User authorization: finish T1–T11, review each task, commit and push each completed
task to origin/main. Do not publish private input workbooks or CSV summaries.

## Current sequence

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
- Test suite modifies the tracked kms.db cache; do not stage that generated DB
  change. Preserve a backup before cleaning it at the end.
- T3 initial integration regression: 2087 passed, 351 known T4 xfailed.
- T3 review reproductions found uncited evidence labels accepted and Tị/Tỵ
  inconsistent in adjacent-palace classification. Regression tests added; fixes
  under review. `suy_luan` may accompany a cited kind, but an uncited empirical
  kind must not be accepted.
- Real input discovered at
  D:/FPT/2026/FA26/KMS301/Project_TuVi/Final/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx.
  Gate passed all 10456 records as new with zero errors, no source-D rows.
- Same-name CSV (1559 bytes) contains Indicator/Value/Explanation, not knowledge
  exports. `tuvi_import/` is a hypothetical export directory, not that CSV.
- Frontend skill: design-taste-frontend has been read; app-screens reference is
  being read before new screens. Keep existing Streamlit shell and design.

## Remaining implementation

T6, T8, T9, T10, final T11; legacy T1/T2 acceptance review. No task should be marked
complete merely from its test count: review contracts, source attribution, empty
states, errors, immutability, API/UI integration and publication status.
