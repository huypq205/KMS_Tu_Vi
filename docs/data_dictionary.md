# Data dictionary — KMS Tử Vi

- File: `TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1_0.xlsx`
- SHA-256: `b53280f9f1146a3244ba2d7dc0afddc6bf5f6f3e8b891ed323f5c0d7739e9035`
- Sinh lúc: 2026-10-21 03:32 (tự động bởi `scripts/inspect_excel.py`, không sửa tay)
- Số sheet: 24

## 1. Danh sách sheet

| sheet | dòng | cột | vai trò |
|---|---|---|---|
| OVERVIEW | 15 | 3 | bỏ qua |
| SOURCE_AUDIT | 3 | 9 | bỏ qua |
| SOURCES | 3 | 13 | dùng (sources) |
| SOURCE_PARTS | 9 | 6 | dùng (source_parts) |
| TAXONOMY | 82 | 7 | dùng (taxonomy) |
| CANONICAL_KNOWLEDGE_V1_0 | 10456 | 32 | dùng (knowledge_items) |
| CANONICAL_KNOWLEDGE | 10456 | 22 | bỏ qua |
| ALL_CANONICAL_ORIGINAL | 10489 | 30 | bỏ qua |
| ALL_CANONICAL_V0 | 10490 | 23 | bỏ qua |
| EXTRACTION | 10492 | 26 | dùng (extraction_review) |
| EVIDENCE | 10492 | 21 | dùng (evidence) |
| DEDUPE_LOG | 88 | 13 | bỏ qua |
| CANONICAL_ID_REDIRECTS | 34 | 5 | dùng (id_redirects) |
| VOCABULARY_INDEX | 506 | 7 | chưa phân loại |
| VOCABULARY | 669 | 15 | dùng (vocabulary) |
| OCR_PAGE_TEXT | 926 | 18 | bỏ qua |
| SOURCE_SEGMENTS | 10386 | 17 | bỏ qua |
| REVIEW_QUEUE | 1512 | 11 | chưa phân loại |
| OCR_REVIEW_WORKLIST | 82 | 17 | chưa phân loại |
| SEMANTIC_REVIEW_WORKLIST | 1650 | 17 | chưa phân loại |
| MISC_SOURCE_ROWS | 1237 | 5 | bỏ qua |
| MERGE_QA | 16 | 3 | bỏ qua |
| SHEET_INVENTORY | 63 | 5 | bỏ qua |
| TAXONOMY_DIFFERENCES | 0 | 4 | bỏ qua |

## 2. Kiểm tra column_mapping.yaml

Đã kiểm 70 cột được ánh xạ; lỗi: **0**.

## 3. Kiểm tra chất lượng dữ liệu

### 3.1 Số bản ghi active so với kỳ vọng

| sách | kỳ vọng | thực tế | kết quả |
|---|---|---|---|
| NPL | 2191 | 2191 | OK |
| BD | 4450 | 4450 | OK |
| DAU | 3815 | 3815 | OK |
| TỔNG | 10456 | 10456 | OK |

- `Canonical_ID` duy nhất: **CÓ**
- Cột bắt buộc `Canonical_ID` bị trống: **0** dòng
- Cột bắt buộc `Book_Code` bị trống: **0** dòng
- Cột bắt buộc `Canonical_Knowledge` bị trống: **0** dòng
- Cột bắt buộc `PDF_Pages` bị trống: **0** dòng

### 3.2 Evidence

| sách | bản ghi active | có evidence | tỷ lệ |
|---|---|---|---|
| BD | 4450 | 4450 | 100.0% |
| DAU | 3815 | 3815 | 100.0% |
| NPL | 2191 | 2191 | 100.0% |

- Evidence trỏ tới ID không còn active: **33** (tra được qua id_redirects: **33**)

**evidence.Printed_Page**

| sách | tỷ lệ trống |
|---|---|
| BD | 100.0% trống |
| DAU | 0.0% trống |
| NPL | 100.0% trống |

**evidence.Part_Number**

| sách | tỷ lệ trống |
|---|---|
| BD | 0.0% trống |
| DAU | 100.0% trống |
| NPL | 100.0% trống |

**evidence.PDF_Page**

| sách | tỷ lệ trống |
|---|---|
| BD | 0.0% trống |
| DAU | 0.0% trống |
| NPL | 0.0% trống |

**evidence.origin**

| sách | origin | số dòng |
|---|---|---|
| BD | ORIGINAL_EVIDENCE_SHEET | 4477 |
| DAU | ORIGINAL_EVIDENCE_SHEET | 3821 |
| NPL | SYNTHESIZED_FROM_EXTRACTION; CANONICAL_V1_LINK | 2194 |

### 3.3 Dấu vết review (sheet extraction)

| sách | dòng | có Reviewer | có Review_Date |
|---|---|---|---|
| BD | 4477 | 0 | 0 |
| DAU | 3821 | 0 | 0 |
| NPL | 2194 | 0 | 0 |

_Nếu cột 'có Reviewer' = 0 thì file chưa có dấu vết người duyệt nào._

| sách | review_status | số dòng |
|---|---|---|
| BD | OCR_REVIEW_PENDING | 1766 |
| BD | SOURCE_REVIEW_PENDING | 2711 |
| DAU | CONTENT_REVIEW_REQUIRED | 1708 |
| DAU | OCR_REVIEW_REQUIRED | 17 |
| DAU | SEMANTIC_REVIEW_PENDING | 2096 |
| NPL | REVIEW_NEEDED | 2194 |

### 3.4 Độ dài `text` (ký tự)

| sách | n | p25 | trung vị | p75 | max | <40 ký tự |
|---|---|---|---|---|---|---|
| BD | 4450 | 71 | 129 | 255 | 1000 | 289 |
| DAU | 3815 | 31 | 37 | 113 | 519 | 2010 |
| NPL | 2191 | 88 | 106 | 126 | 218 | 4 |

### 3.5 Parse số trang `PDF_Pages`

| sách | bản ghi | không parse được |
|---|---|---|
| BD | 4450 | 0 |
| DAU | 3815 | 0 |
| NPL | 2191 | 0 |

### 3.6 Phân bố trust tier

| sách | tier 1 | tier 2 | tier 3 | tier 9 | sẽ index |
|---|---|---|---|---|---|
| BD | 0 | 0 | 2691 | 1759 | 2691 |
| DAU | 0 | 3798 | 0 | 17 | 3798 |
| NPL | 2191 | 0 | 0 | 0 | 2191 |
| TỔNG | 2191 | 3798 | 2691 | 1776 | 8680 |

enabled_tiers = [1, 2, 3]

- tier 1: NPL — có cấu trúc, release LOCKED
- tier 2: DAU — text layer, chưa duyệt
- tier 3: BD — OCR, chưa duyệt
- tier 9: Loại khỏi index cho đến khi review

### 3.7 Vocabulary

- Số dòng: **669**, thuật ngữ khác nhau: **477**
- Dòng có alias: **7.2%**

| status | số dòng |
|---|---|
| CONTROLLED_TERM | 422 |
| CONTROLLED_MAPPING_PENDING_REVIEW | 151 |
| CANDIDATE_SOURCE_VOCAB | 51 |
| APPROVED_TERM | 45 |

## 4. Chi tiết từng sheet

### OVERVIEW  (15 dòng, 3 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Indicator | 100.0% | 15 | Project ; Book sources ; Original final-layer canoni… |
| Value | 100.0% | 15 | TuVi Team 6 — Three-book Kn… ; 3 ; 10489 |
| Explanation | 100.0% | 15 | Multi-source organizational… ; 3 book/source entries; Bửu … ; ALL_CANONICAL_ORI… |

### SOURCE_AUDIT  (3 dòng, 9 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Source_ID | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| Book_Title | 100.0% | 3 | Tử Vi Tổng Hợp — Nguyễn Phá… ; Tử Vi Ứng Dụng — Bửu Đình ; Tử Vi Đẩu Số Toàn Th… |
| Original_Canonical_V1 | 100.0% | 3 | 2191 ; 4477 ; 3821 |
| New_Strict_Duplicate_Rows | 100.0% | 3 | 0 ; 27 ; 6 |
| Active_Canonical | 100.0% | 3 | 2191 ; 4450 ; 3815 |
| Original_Extraction | 100.0% | 3 | 2194 ; 4477 ; 3821 |
| Original_Evidence | 100.0% | 3 | 0 ; 4477 ; 3821 |
| Original_Canonical_V0 | 100.0% | 3 | 2192 ; 4477 ; 3821 |

### SOURCES  (3 dòng, 13 cột — dùng (sources))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Source_ID | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| Title | 100.0% | 3 | Tử Vi Tổng Hợp ; Tử Vi Ứng Dụng ; Tử Vi Đẩu Số Toàn Thư |
| Author | 100.0% | 3 | Nguyễn Phát Lộc ; Bửu Đình ; Hi Di Trần Đoàn (nguyên tác… |
| Source_Type | 100.0% | 1 | BOOK |
| File_Name | 100.0% | 3 | tu vi tong hop-nguyen-phat-… ; Tử vi ứng dụng - Bửu Đình -… ; tu vi dau so toan… |
| Primary_Source | 100.0% | 1 | YES |
| Language | 100.0% | 1 | Vietnamese |
| Total_Pages | 100.0% | 3 | 442 ; 579 ; 347 |
| Scope | 100.0% | 3 | Nguồn tri thức chính của pr… ; Toàn bộ 7 phần PDF của cùng… ; Bản Ngân Hà Thư X… |
| Source_Status | 100.0% | 3 | ACTIVE ; OCR_SOURCE_REVIEW_PENDING ; OCR_TRANSCRIPTION_DRAFT |
| Notes | 100.0% | 3 | Dùng làm nguồn chuẩn trong … ; Một Source_ID duy nhất SRC_… ; Phân biệt lời bìn… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Workbook_File | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |

### SOURCE_PARTS  (9 dòng, 6 cột — dùng (source_parts))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Source_ID | 100.0% | 3 | SRC_BD_001 ; SRC001 ; SRC_DAU_001 |
| Part_Number | 100.0% | 8 | 1 ; 2 ; 3 |
| PDF_File | 100.0% | 9 | Tử vi ứng dụng - Bửu Đình -… ; Tử vi ứng dụng - Bửu Đình -… ; Tử vi ứng dụng - … |
| Total_PDF_Pages | 100.0% | 6 | 88 ; 92 ; 85 |
| PDF_Page_Numbering | 100.0% | 2 | Part-local PDF page (1-base… ; PDF page 1-based |
| Extraction_Status | 100.0% | 2 | OCR_COMPLETE_REVIEW_PENDING ; FROM_CANONICAL_SOURCE |

### TAXONOMY  (82 dòng, 7 cột — dùng (taxonomy))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Taxonomy_Code | 100.0% | 82 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Parent_Code | 100.0% | 12 | TV-01 ; TV-02 ; TV-03 |
| Level_1_Domain | 100.0% | 11 | Scope & Foundations ; Methodology & Philosophy ; Birth & Chart Fundamentals |
| Level_2_Subdomain | 100.0% | 72 | Nature of Tử Vi ; Object of Study ; Scope of Application |
| Level_3_or_Examples | 100.0% | 82 | Khoa Tử Vi; Thuật Tử Vi ; Con người; đời người ; Phạm vi áp dụng |
| Description | 100.0% | 82 | Bản chất và phạm vi chung c… ; Đối tượng mà sách xác định … ; Phạm vi mà tác gi… |
| Typical_Knowledge_Types | 100.0% | 44 | CONCEPT; THEORY ; SOURCE_CLAIM; LIMITATION ; EXCEPTION; LIMITATION |

**TAXONOMY.Parent_Code**

| Parent_Code | số dòng |
|---|---|
| TV-04 | 12 |
| TV-05.04 | 9 |
| TV-02 | 8 |
| TV-05 | 8 |
| TV-08 | 7 |
| TV-03 | 6 |
| TV-06 | 6 |
| TV-07 | 6 |
| TV-09 | 6 |
| TV-11 | 6 |
| TV-01 | 5 |
| TV-10 | 3 |

**TAXONOMY.Level_1_Domain**

| Level_1_Domain | số dòng |
|---|---|
| Star Knowledge | 17 |
| Palace Knowledge | 12 |
| Methodology & Philosophy | 8 |
| Interpretation Methodology | 7 |
| Birth & Chart Fundamentals | 6 |
| Relationships & Configurations | 6 |
| Time & Fortune Periods | 6 |
| Applied Interpretation | 6 |
| Limitations, Uncertainty & Modification | 6 |
| Scope & Foundations | 5 |
| Case-Based Knowledge | 3 |

### CANONICAL_KNOWLEDGE_V1_0  (10456 dòng, 32 cột — dùng (knowledge_items))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Canonical_ID | 100.0% | 10456 | KN-000001 ; KN-000002 ; KN-000003 |
| Version | 100.0% | 3 | 1.0 ; 0.1-DRAFT ; 0.1 |
| Release_Status | 100.0% | 2 | LOCKED_V1_0 ; DRAFT_NOT_RELEASED |
| Validation_Status | 100.0% | 3 | STRUCTURAL_QA_PASS / SOURCE… ; OCR_SOURCE_REVIEW_PENDING ; OCR_TEXT_LAYER / SOU… |
| Taxonomy_L1 | 100.0% | 11 | TV-01 ; TV-02 ; TV-03 |
| Primary_Taxonomy_Code | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Knowledge_Type | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Subject | 66.7% | 1549 | Khoa Tử Vi ; Quyển I ; Quyển II |
| Predicate | 66.7% | 58 | IS_A ; HAS_ATTRIBUTE ; REPRESENTS |
| Object | 66.7% | 5990 | Hệ thống tri thức có đối tư… ; Gồm sáu chương lý thuyết ; Khoa Tử Vi – phần lý … |
| Condition_Context | 16.6% | 345 | Khoảng dưới 13 tuổi theo qu… ; Không kết luận từ một cung … ; Mệnh ~ giai đoạn … |
| Canonical_Knowledge | 100.0% | 10411 | Nguồn định nghĩa 'khoa' là … ; Quyển I được tác giả cấu tr… ; Sách chia Quyển I… |
| Evidence_Count | 100.0% | 3 | 1 ; 2 ; 6 |
| Supporting_Extract_IDs | 100.0% | 10456 | EXT-M1-0011 ; EXT-M1-0015 ; EXT-M1-0006 |
| Source_IDs | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| PDF_Pages | 100.0% | 1040 | 4 ; 5 ; 2 |
| Chapters | 100.0% | 118 | Lời mở đầu ; Chương 1 – Đối tượng của kh… ; Chương 4 – Văn hóa Trung Ho… |
| Author_Stances | 100.0% | 11 | AUTHOR_ASSERTION ; AUTHOR_CRITIQUE ; EXAMPLE_ONLY |
| Source_Certainty | 100.0% | 5 | HIGH ; MEDIUM ; LOW |
| Extractors | 100.0% | 12 | M1 ; M5 ; M2 |
| Review_Flag | 100.0% | 26 | STANDARD ; AUTHOR_CRITIQUE ; LOW_CERTAINTY |
| Conflict_Status | 100.0% | 5 | NONE ; SOURCE_POSITION_RETAINED ; NUANCE_OVERLAP_NOT_CONFLICT |
| Dedupe_Status | 100.0% | 8 | UNIQUE ; MERGED_SEMANTIC_DUPLICATE ; KEEP_SEPARATE_NUANCE |
| Merged_From_Canonical_IDs | 0.3% | 30 | KN-000297; KN-000298 ; BD-KN-000366 ; BD-KN-000555 |
| Alternate_Statements | 0.0% | 1 | Nguồn ghi Cung Mệnh tiếp gi… |
| Supporting_Taxonomy_Codes | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Supporting_Knowledge_Types | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Normalization_Notes | 79.8% | 789 | Object alias normalized: Ta… ; Vocabulary normalization Su… ; V1.0 semantic ded… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Book_Title | 100.0% | 3 | Tử Vi Tổng Hợp — Nguyễn Phá… ; Tử Vi Ứng Dụng — Bửu Đình ; Tử Vi Đẩu Số Toàn Th… |
| Master_Dedupe_Key | 100.0% | 10456 | 88bd2e15dc7a65ea ; 7e3dadbc1cb0775c ; d91237d9a3e58347 |
| Original_File | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |

**CANONICAL_KNOWLEDGE_V1_0.Version**

| Version | BD | DAU | NPL |
|---|---|---|---|
| 0.1 | 0 | 3815 | 0 |
| 0.1-DRAFT | 4450 | 0 | 0 |
| 1.0 | 0 | 0 | 2191 |

**CANONICAL_KNOWLEDGE_V1_0.Release_Status**

| Release_Status | BD | DAU | NPL |
|---|---|---|---|
| DRAFT_NOT_RELEASED | 4450 | 3815 | 0 |
| LOCKED_V1_0 | 0 | 0 | 2191 |

**CANONICAL_KNOWLEDGE_V1_0.Validation_Status**

| Validation_Status | BD | DAU | NPL |
|---|---|---|---|
| OCR_SOURCE_REVIEW_PENDING | 4450 | 0 | 0 |
| OCR_TEXT_LAYER / SOURCE_REVIEW_PENDING | 0 | 3815 | 0 |
| STRUCTURAL_QA_PASS / SOURCE_REVIEW_PENDING | 0 | 0 | 2191 |

**CANONICAL_KNOWLEDGE_V1_0.Taxonomy_L1**

| Taxonomy_L1 | BD | DAU | NPL |
|---|---|---|---|
| TV-01 | 721 | 1658 | 32 |
| TV-02 | 0 | 76 | 100 |
| TV-03 | 0 | 0 | 32 |
| TV-04 | 123 | 107 | 30 |
| TV-05 | 2411 | 791 | 65 |
| TV-06 | 603 | 338 | 147 |
| TV-07 | 151 | 321 | 2 |
| TV-08 | 111 | 85 | 89 |
| TV-09 | 63 | 0 | 1276 |
| TV-10 | 267 | 439 | 120 |
| TV-11 | 0 | 0 | 298 |

**CANONICAL_KNOWLEDGE_V1_0.Knowledge_Type**

| Knowledge_Type | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 439 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 426 | 752 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 73 |
| RULE | 260 | 338 | 279 |
| SOURCE_CLAIM | 3166 | 2040 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**CANONICAL_KNOWLEDGE_V1_0.Evidence_Count**

| Evidence_Count | BD | DAU | NPL |
|---|---|---|---|
| 1 | 4427 | 3809 | 2188 |
| 2 | 22 | 6 | 3 |
| 6 | 1 | 0 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Source_IDs**

| Source_IDs | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 2191 |
| SRC_BD_001 | 4450 | 0 | 0 |
| SRC_DAU_001 | 0 | 3815 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Author_Stances**

| Author_Stances | BD | DAU | NPL |
|---|---|---|---|
| ALTERNATIVE_VIEW | 0 | 0 | 40 |
| AUTHOR_ASSERTION | 0 | 0 | 1095 |
| AUTHOR_ASSERTION_UNVERIFIED | 1559 | 0 | 0 |
| AUTHOR_CRITIQUE | 0 | 0 | 63 |
| AUTHOR_UNCERTAINTY | 0 | 45 | 39 |
| CITED_TRADITION | 0 | 0 | 827 |
| EXAMPLE_ONLY | 0 | 0 | 121 |
| HISTORICAL_NARRATION_UNVERIFIED | 200 | 0 | 0 |
| NOT_APPLICABLE | 0 | 0 | 6 |
| NOT_YET_ATTRIBUTED | 2691 | 0 | 0 |
| SOURCE_CLAIM | 0 | 3770 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Source_Certainty**

| Source_Certainty | BD | DAU | NPL |
|---|---|---|---|
| HIGH | 0 | 2093 | 744 |
| LOW | 0 | 17 | 955 |
| MEDIUM | 0 | 1705 | 492 |
| UNKNOWN | 2691 | 0 | 0 |
| UNVERIFIED | 1759 | 0 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Extractors**

| Extractors | BD | DAU | NPL |
|---|---|---|---|
| AUTOMATED_SOURCE_CAPTURE | 0 | 3815 | 0 |
| M1 | 0 | 0 | 307 |
| M2 | 0 | 0 | 132 |
| M3 | 0 | 0 | 414 |
| M4 | 0 | 0 | 381 |
| M5 | 0 | 0 | 522 |
| M6 | 0 | 0 | 435 |
| OCR_TESSERACT_VIE_P4 | 744 | 0 | 0 |
| OCR_TESSERACT_VIE_P5 | 725 | 0 | 0 |
| OCR_TESSERACT_VIE_P6 | 747 | 0 | 0 |
| OCR_TESSERACT_VIE_P7 | 475 | 0 | 0 |
| TESSERACT_OCR | 1759 | 0 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Conflict_Status**

| Conflict_Status | BD | DAU | NPL |
|---|---|---|---|
| NONE | 0 | 0 | 2045 |
| NOT_CHECKED | 1759 | 0 | 0 |
| NOT_EVALUATED | 2691 | 3815 | 0 |
| NUANCE_OVERLAP_NOT_CONFLICT | 0 | 0 | 2 |
| SOURCE_POSITION_RETAINED | 0 | 0 | 144 |

**CANONICAL_KNOWLEDGE_V1_0.Dedupe_Status**

| Dedupe_Status | BD | DAU | NPL |
|---|---|---|---|
| EXACT_INTRA_BOOK_CONSOLIDATED | 23 | 6 | 0 |
| EXACT_OCR_REPEAT_REVIEW | 8 | 0 | 0 |
| KEEP_SEPARATE_NUANCE | 0 | 0 | 2 |
| MERGED_SEMANTIC_DUPLICATE | 0 | 0 | 1 |
| NOT_CHECKED | 1744 | 0 | 0 |
| NOT_EVALUATED | 0 | 3809 | 0 |
| UNIQUE | 0 | 0 | 2188 |
| UNREVIEWED | 2675 | 0 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Supporting_Knowledge_Types**

| Supporting_Knowledge_Types | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 439 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 426 | 752 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 73 |
| RULE | 260 | 338 | 279 |
| SOURCE_CLAIM | 3166 | 2040 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**CANONICAL_KNOWLEDGE_V1_0.Book_Title**

| Book_Title | BD | DAU | NPL |
|---|---|---|---|
| Tử Vi Tổng Hợp — Nguyễn Phát Lộc | 0 | 0 | 2191 |
| Tử Vi Đẩu Số Toàn Thư — Hi Di Trần Đoàn / Vũ Tài Lục | 0 | 3815 | 0 |
| Tử Vi Ứng Dụng — Bửu Đình | 4450 | 0 | 0 |

**CANONICAL_KNOWLEDGE_V1_0.Original_File**

| Original_File | BD | DAU | NPL |
|---|---|---|---|
| TuVi_BuuDinh_7Parts_ONE_SOURCE_CANONICAL_MASTER_v1.0.xlsx | 4450 | 0 | 0 |
| TuVi_DauSoToanThu_CANONICAL_KNOWLEDGE_DRAFT_v0_2_AI_PRECHECK.xlsx | 0 | 3815 | 0 |
| TuVi_KM_Team6_CANONICAL_KNOWLEDGE_v1.0.xlsx | 0 | 0 | 2191 |

### CANONICAL_KNOWLEDGE  (10456 dòng, 22 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Canonical_ID | 100.0% | 10456 | KN-000001 ; KN-000002 ; KN-000003 |
| Taxonomy_L1 | 100.0% | 11 | TV-01 ; TV-02 ; TV-03 |
| Primary_Taxonomy_Code | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Knowledge_Type | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Subject | 66.7% | 1549 | Khoa Tử Vi ; Quyển I ; Quyển II |
| Predicate | 66.7% | 58 | IS_A ; HAS_ATTRIBUTE ; REPRESENTS |
| Object | 66.7% | 5991 | Hệ thống tri thức có đối tư… ; Gồm sáu chương lý thuyết ; Khoa Tử Vi – phần lý … |
| Condition_Context | 16.6% | 345 | Khoảng dưới 13 tuổi theo qu… ; Không kết luận từ một cung … ; Mệnh ~ giai đoạn … |
| Canonical_Knowledge | 100.0% | 10411 | Nguồn định nghĩa 'khoa' là … ; Quyển I được tác giả cấu tr… ; Sách chia Quyển I… |
| Evidence_Count | 100.0% | 2 | 1 ; 2 |
| Supporting_Extract_IDs | 100.0% | 10456 | EXT-M1-0011 ; EXT-M1-0015 ; EXT-M1-0006 |
| Source_IDs | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| PDF_Pages | 100.0% | 1016 | 4 ; 5 ; 2 |
| Chapters | 100.0% | 117 | Lời mở đầu ; Chương 1 – Đối tượng của kh… ; Chương 4 – Văn hóa Trung Ho… |
| Author_Stances | 100.0% | 11 | AUTHOR_ASSERTION ; AUTHOR_CRITIQUE ; EXAMPLE_ONLY |
| Source_Certainty | 100.0% | 5 | HIGH ; MEDIUM ; LOW |
| Extractors | 100.0% | 12 | M1 ; M5 ; M2 |
| Review_Flag | 100.0% | 26 | STANDARD ; AUTHOR_CRITIQUE ; LOW_CERTAINTY |
| Supporting_Taxonomy_Codes | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Supporting_Knowledge_Types | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Normalization_Notes | 79.8% | 788 | Object alias normalized: Ta… ; Vocabulary normalization Su… ; Subject alias nor… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |

**CANONICAL_KNOWLEDGE.Taxonomy_L1**

| Taxonomy_L1 | BD | DAU | NPL |
|---|---|---|---|
| TV-01 | 721 | 1658 | 32 |
| TV-02 | 0 | 76 | 100 |
| TV-03 | 0 | 0 | 32 |
| TV-04 | 123 | 107 | 30 |
| TV-05 | 2411 | 791 | 65 |
| TV-06 | 603 | 338 | 147 |
| TV-07 | 151 | 321 | 2 |
| TV-08 | 111 | 85 | 89 |
| TV-09 | 63 | 0 | 1276 |
| TV-10 | 267 | 439 | 120 |
| TV-11 | 0 | 0 | 298 |

**CANONICAL_KNOWLEDGE.Knowledge_Type**

| Knowledge_Type | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 439 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 426 | 752 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 73 |
| RULE | 260 | 338 | 279 |
| SOURCE_CLAIM | 3166 | 2040 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**CANONICAL_KNOWLEDGE.Evidence_Count**

| Evidence_Count | BD | DAU | NPL |
|---|---|---|---|
| 1 | 4450 | 3815 | 2189 |
| 2 | 0 | 0 | 2 |

**CANONICAL_KNOWLEDGE.Source_IDs**

| Source_IDs | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 2191 |
| SRC_BD_001 | 4450 | 0 | 0 |
| SRC_DAU_001 | 0 | 3815 | 0 |

**CANONICAL_KNOWLEDGE.Author_Stances**

| Author_Stances | BD | DAU | NPL |
|---|---|---|---|
| ALTERNATIVE_VIEW | 0 | 0 | 40 |
| AUTHOR_ASSERTION | 0 | 0 | 1095 |
| AUTHOR_ASSERTION_UNVERIFIED | 1559 | 0 | 0 |
| AUTHOR_CRITIQUE | 0 | 0 | 63 |
| AUTHOR_UNCERTAINTY | 0 | 45 | 39 |
| CITED_TRADITION | 0 | 0 | 827 |
| EXAMPLE_ONLY | 0 | 0 | 121 |
| HISTORICAL_NARRATION_UNVERIFIED | 200 | 0 | 0 |
| NOT_APPLICABLE | 0 | 0 | 6 |
| NOT_YET_ATTRIBUTED | 2691 | 0 | 0 |
| SOURCE_CLAIM | 0 | 3770 | 0 |

**CANONICAL_KNOWLEDGE.Source_Certainty**

| Source_Certainty | BD | DAU | NPL |
|---|---|---|---|
| HIGH | 0 | 2093 | 744 |
| LOW | 0 | 17 | 955 |
| MEDIUM | 0 | 1705 | 492 |
| UNKNOWN | 2691 | 0 | 0 |
| UNVERIFIED | 1759 | 0 | 0 |

**CANONICAL_KNOWLEDGE.Extractors**

| Extractors | BD | DAU | NPL |
|---|---|---|---|
| AUTOMATED_SOURCE_CAPTURE | 0 | 3815 | 0 |
| M1 | 0 | 0 | 307 |
| M2 | 0 | 0 | 132 |
| M3 | 0 | 0 | 414 |
| M4 | 0 | 0 | 381 |
| M5 | 0 | 0 | 522 |
| M6 | 0 | 0 | 435 |
| OCR_TESSERACT_VIE_P4 | 744 | 0 | 0 |
| OCR_TESSERACT_VIE_P5 | 725 | 0 | 0 |
| OCR_TESSERACT_VIE_P6 | 747 | 0 | 0 |
| OCR_TESSERACT_VIE_P7 | 475 | 0 | 0 |
| TESSERACT_OCR | 1759 | 0 | 0 |

**CANONICAL_KNOWLEDGE.Supporting_Knowledge_Types**

| Supporting_Knowledge_Types | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 439 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 426 | 752 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 73 |
| RULE | 260 | 338 | 279 |
| SOURCE_CLAIM | 3166 | 2040 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

### ALL_CANONICAL_ORIGINAL  (10489 dòng, 30 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Canonical_ID | 100.0% | 10489 | KN-000001 ; KN-000002 ; KN-000003 |
| Version | 100.0% | 3 | 1.0 ; 0.1-DRAFT ; 0.1 |
| Release_Status | 100.0% | 2 | LOCKED_V1_0 ; DRAFT_NOT_RELEASED |
| Validation_Status | 100.0% | 3 | STRUCTURAL_QA_PASS / SOURCE… ; OCR_SOURCE_REVIEW_PENDING ; OCR_TEXT_LAYER / SOU… |
| Taxonomy_L1 | 100.0% | 11 | TV-01 ; TV-02 ; TV-03 |
| Primary_Taxonomy_Code | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Knowledge_Type | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Subject | 66.8% | 1549 | Khoa Tử Vi ; Quyển I ; Quyển II |
| Predicate | 66.8% | 58 | IS_A ; HAS_ATTRIBUTE ; REPRESENTS |
| Object | 66.8% | 5993 | Hệ thống tri thức có đối tư… ; Gồm sáu chương lý thuyết ; Khoa Tử Vi – phần lý … |
| Condition_Context | 16.6% | 345 | Khoảng dưới 13 tuổi theo qu… ; Không kết luận từ một cung … ; Mệnh ~ giai đoạn … |
| Canonical_Knowledge | 100.0% | 10415 | Nguồn định nghĩa 'khoa' là … ; Quyển I được tác giả cấu tr… ; Sách chia Quyển I… |
| Evidence_Count | 100.0% | 2 | 1 ; 2 |
| Supporting_Extract_IDs | 100.0% | 10489 | EXT-M1-0011 ; EXT-M1-0015 ; EXT-M1-0006 |
| Source_IDs | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| PDF_Pages | 100.0% | 1017 | 4 ; 5 ; 2 |
| Chapters | 100.0% | 118 | Lời mở đầu ; Chương 1 – Đối tượng của kh… ; Chương 4 – Văn hóa Trung Ho… |
| Author_Stances | 100.0% | 11 | AUTHOR_ASSERTION ; AUTHOR_CRITIQUE ; EXAMPLE_ONLY |
| Source_Certainty | 100.0% | 5 | HIGH ; MEDIUM ; LOW |
| Extractors | 100.0% | 12 | M1 ; M5 ; M2 |
| Review_Flag | 100.0% | 26 | STANDARD ; AUTHOR_CRITIQUE ; LOW_CERTAINTY |
| Conflict_Status | 100.0% | 5 | NONE ; SOURCE_POSITION_RETAINED ; NUANCE_OVERLAP_NOT_CONFLICT |
| Dedupe_Status | 100.0% | 7 | UNIQUE ; MERGED_SEMANTIC_DUPLICATE ; KEEP_SEPARATE_NUANCE |
| Merged_From_Canonical_IDs | 0.0% | 1 | KN-000297; KN-000298 |
| Alternate_Statements | 0.0% | 1 | Nguồn ghi Cung Mệnh tiếp gi… |
| Supporting_Taxonomy_Codes | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Supporting_Knowledge_Types | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Normalization_Notes | 79.9% | 789 | Object alias normalized: Ta… ; Vocabulary normalization Su… ; V1.0 semantic ded… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Original_File | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |

**ALL_CANONICAL_ORIGINAL.Version**

| Version | BD | DAU | NPL |
|---|---|---|---|
| 0.1 | 0 | 3821 | 0 |
| 0.1-DRAFT | 4477 | 0 | 0 |
| 1.0 | 0 | 0 | 2191 |

**ALL_CANONICAL_ORIGINAL.Release_Status**

| Release_Status | BD | DAU | NPL |
|---|---|---|---|
| DRAFT_NOT_RELEASED | 4477 | 3821 | 0 |
| LOCKED_V1_0 | 0 | 0 | 2191 |

**ALL_CANONICAL_ORIGINAL.Validation_Status**

| Validation_Status | BD | DAU | NPL |
|---|---|---|---|
| OCR_SOURCE_REVIEW_PENDING | 4477 | 0 | 0 |
| OCR_TEXT_LAYER / SOURCE_REVIEW_PENDING | 0 | 3821 | 0 |
| STRUCTURAL_QA_PASS / SOURCE_REVIEW_PENDING | 0 | 0 | 2191 |

**ALL_CANONICAL_ORIGINAL.Taxonomy_L1**

| Taxonomy_L1 | BD | DAU | NPL |
|---|---|---|---|
| TV-01 | 724 | 1661 | 32 |
| TV-02 | 0 | 76 | 100 |
| TV-03 | 0 | 0 | 32 |
| TV-04 | 124 | 107 | 30 |
| TV-05 | 2432 | 791 | 65 |
| TV-06 | 605 | 338 | 147 |
| TV-07 | 151 | 323 | 2 |
| TV-08 | 111 | 85 | 89 |
| TV-09 | 63 | 0 | 1276 |
| TV-10 | 267 | 440 | 120 |
| TV-11 | 0 | 0 | 298 |

**ALL_CANONICAL_ORIGINAL.Knowledge_Type**

| Knowledge_Type | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 440 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 428 | 754 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 73 |
| RULE | 261 | 338 | 279 |
| SOURCE_CLAIM | 3190 | 2043 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**ALL_CANONICAL_ORIGINAL.Evidence_Count**

| Evidence_Count | BD | DAU | NPL |
|---|---|---|---|
| 1 | 4477 | 3821 | 2188 |
| 2 | 0 | 0 | 3 |

**ALL_CANONICAL_ORIGINAL.Source_IDs**

| Source_IDs | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 2191 |
| SRC_BD_001 | 4477 | 0 | 0 |
| SRC_DAU_001 | 0 | 3821 | 0 |

**ALL_CANONICAL_ORIGINAL.Author_Stances**

| Author_Stances | BD | DAU | NPL |
|---|---|---|---|
| ALTERNATIVE_VIEW | 0 | 0 | 40 |
| AUTHOR_ASSERTION | 0 | 0 | 1095 |
| AUTHOR_ASSERTION_UNVERIFIED | 1566 | 0 | 0 |
| AUTHOR_CRITIQUE | 0 | 0 | 63 |
| AUTHOR_UNCERTAINTY | 0 | 45 | 39 |
| CITED_TRADITION | 0 | 0 | 827 |
| EXAMPLE_ONLY | 0 | 0 | 121 |
| HISTORICAL_NARRATION_UNVERIFIED | 200 | 0 | 0 |
| NOT_APPLICABLE | 0 | 0 | 6 |
| NOT_YET_ATTRIBUTED | 2711 | 0 | 0 |
| SOURCE_CLAIM | 0 | 3776 | 0 |

**ALL_CANONICAL_ORIGINAL.Source_Certainty**

| Source_Certainty | BD | DAU | NPL |
|---|---|---|---|
| HIGH | 0 | 2096 | 744 |
| LOW | 0 | 17 | 955 |
| MEDIUM | 0 | 1708 | 492 |
| UNKNOWN | 2711 | 0 | 0 |
| UNVERIFIED | 1766 | 0 | 0 |

**ALL_CANONICAL_ORIGINAL.Extractors**

| Extractors | BD | DAU | NPL |
|---|---|---|---|
| AUTOMATED_SOURCE_CAPTURE | 0 | 3821 | 0 |
| M1 | 0 | 0 | 307 |
| M2 | 0 | 0 | 132 |
| M3 | 0 | 0 | 414 |
| M4 | 0 | 0 | 381 |
| M5 | 0 | 0 | 522 |
| M6 | 0 | 0 | 435 |
| OCR_TESSERACT_VIE_P4 | 753 | 0 | 0 |
| OCR_TESSERACT_VIE_P5 | 726 | 0 | 0 |
| OCR_TESSERACT_VIE_P6 | 751 | 0 | 0 |
| OCR_TESSERACT_VIE_P7 | 481 | 0 | 0 |
| TESSERACT_OCR | 1766 | 0 | 0 |

**ALL_CANONICAL_ORIGINAL.Conflict_Status**

| Conflict_Status | BD | DAU | NPL |
|---|---|---|---|
| NONE | 0 | 0 | 2045 |
| NOT_CHECKED | 1766 | 0 | 0 |
| NOT_EVALUATED | 2711 | 3821 | 0 |
| NUANCE_OVERLAP_NOT_CONFLICT | 0 | 0 | 2 |
| SOURCE_POSITION_RETAINED | 0 | 0 | 144 |

**ALL_CANONICAL_ORIGINAL.Dedupe_Status**

| Dedupe_Status | BD | DAU | NPL |
|---|---|---|---|
| EXACT_OCR_REPEAT_REVIEW | 16 | 0 | 0 |
| KEEP_SEPARATE_NUANCE | 0 | 0 | 2 |
| MERGED_SEMANTIC_DUPLICATE | 0 | 0 | 1 |
| NOT_CHECKED | 1750 | 0 | 0 |
| NOT_EVALUATED | 0 | 3821 | 0 |
| UNIQUE | 0 | 0 | 2188 |
| UNREVIEWED | 2711 | 0 | 0 |

**ALL_CANONICAL_ORIGINAL.Supporting_Knowledge_Types**

| Supporting_Knowledge_Types | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 440 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 428 | 754 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 73 |
| RULE | 261 | 338 | 279 |
| SOURCE_CLAIM | 3190 | 2043 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**ALL_CANONICAL_ORIGINAL.Original_File**

| Original_File | BD | DAU | NPL |
|---|---|---|---|
| TuVi_BuuDinh_7Parts_ONE_SOURCE_CANONICAL_MASTER_v1.0.xlsx | 4477 | 0 | 0 |
| TuVi_DauSoToanThu_CANONICAL_KNOWLEDGE_DRAFT_v0_2_AI_PRECHECK.xlsx | 0 | 3821 | 0 |
| TuVi_KM_Team6_CANONICAL_KNOWLEDGE_v1.0.xlsx | 0 | 0 | 2191 |

### ALL_CANONICAL_V0  (10490 dòng, 23 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Canonical_ID | 100.0% | 10490 | KN-000001 ; KN-000002 ; KN-000003 |
| Taxonomy_L1 | 100.0% | 11 | TV-01 ; TV-02 ; TV-03 |
| Primary_Taxonomy_Code | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Knowledge_Type | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Subject | 66.8% | 1549 | Khoa Tử Vi ; Quyển I ; Quyển II |
| Predicate | 66.8% | 58 | IS_A ; HAS_ATTRIBUTE ; REPRESENTS |
| Object | 66.8% | 5994 | Hệ thống tri thức có đối tư… ; Gồm sáu chương lý thuyết ; Khoa Tử Vi – phần lý … |
| Condition_Context | 16.5% | 345 | Khoảng dưới 13 tuổi theo qu… ; Không kết luận từ một cung … ; Mệnh ~ giai đoạn … |
| Canonical_Knowledge | 100.0% | 10416 | Nguồn định nghĩa 'khoa' là … ; Quyển I được tác giả cấu tr… ; Sách chia Quyển I… |
| Evidence_Count | 100.0% | 2 | 1 ; 2 |
| Supporting_Extract_IDs | 100.0% | 10490 | EXT-M1-0011 ; EXT-M1-0015 ; EXT-M1-0006 |
| Source_IDs | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| PDF_Pages | 100.0% | 1016 | 4 ; 5 ; 2 |
| Chapters | 100.0% | 117 | Lời mở đầu ; Chương 1 – Đối tượng của kh… ; Chương 4 – Văn hóa Trung Ho… |
| Author_Stances | 100.0% | 11 | AUTHOR_ASSERTION ; AUTHOR_CRITIQUE ; EXAMPLE_ONLY |
| Source_Certainty | 100.0% | 5 | HIGH ; MEDIUM ; LOW |
| Extractors | 100.0% | 12 | M1 ; M5 ; M2 |
| Review_Flag | 100.0% | 26 | STANDARD ; AUTHOR_CRITIQUE ; LOW_CERTAINTY |
| Supporting_Taxonomy_Codes | 100.0% | 80 | TV-01.01 ; TV-01.02 ; TV-01.03 |
| Supporting_Knowledge_Types | 100.0% | 15 | CONCEPT ; BACKGROUND ; SOURCE_CLAIM |
| Normalization_Notes | 79.9% | 788 | Object alias normalized: Ta… ; Vocabulary normalization Su… ; Subject alias nor… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Original_File | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |

**ALL_CANONICAL_V0.Taxonomy_L1**

| Taxonomy_L1 | BD | DAU | NPL |
|---|---|---|---|
| TV-01 | 724 | 1661 | 32 |
| TV-02 | 0 | 76 | 100 |
| TV-03 | 0 | 0 | 32 |
| TV-04 | 124 | 107 | 30 |
| TV-05 | 2432 | 791 | 65 |
| TV-06 | 605 | 338 | 148 |
| TV-07 | 151 | 323 | 2 |
| TV-08 | 111 | 85 | 89 |
| TV-09 | 63 | 0 | 1276 |
| TV-10 | 267 | 440 | 120 |
| TV-11 | 0 | 0 | 298 |

**ALL_CANONICAL_V0.Knowledge_Type**

| Knowledge_Type | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 440 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 428 | 754 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 74 |
| RULE | 261 | 338 | 279 |
| SOURCE_CLAIM | 3190 | 2043 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**ALL_CANONICAL_V0.Evidence_Count**

| Evidence_Count | BD | DAU | NPL |
|---|---|---|---|
| 1 | 4477 | 3821 | 2190 |
| 2 | 0 | 0 | 2 |

**ALL_CANONICAL_V0.Source_IDs**

| Source_IDs | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 2192 |
| SRC_BD_001 | 4477 | 0 | 0 |
| SRC_DAU_001 | 0 | 3821 | 0 |

**ALL_CANONICAL_V0.Author_Stances**

| Author_Stances | BD | DAU | NPL |
|---|---|---|---|
| ALTERNATIVE_VIEW | 0 | 0 | 40 |
| AUTHOR_ASSERTION | 0 | 0 | 1096 |
| AUTHOR_ASSERTION_UNVERIFIED | 1566 | 0 | 0 |
| AUTHOR_CRITIQUE | 0 | 0 | 63 |
| AUTHOR_UNCERTAINTY | 0 | 45 | 39 |
| CITED_TRADITION | 0 | 0 | 827 |
| EXAMPLE_ONLY | 0 | 0 | 121 |
| HISTORICAL_NARRATION_UNVERIFIED | 200 | 0 | 0 |
| NOT_APPLICABLE | 0 | 0 | 6 |
| NOT_YET_ATTRIBUTED | 2711 | 0 | 0 |
| SOURCE_CLAIM | 0 | 3776 | 0 |

**ALL_CANONICAL_V0.Source_Certainty**

| Source_Certainty | BD | DAU | NPL |
|---|---|---|---|
| HIGH | 0 | 2096 | 745 |
| LOW | 0 | 17 | 955 |
| MEDIUM | 0 | 1708 | 492 |
| UNKNOWN | 2711 | 0 | 0 |
| UNVERIFIED | 1766 | 0 | 0 |

**ALL_CANONICAL_V0.Extractors**

| Extractors | BD | DAU | NPL |
|---|---|---|---|
| AUTOMATED_SOURCE_CAPTURE | 0 | 3821 | 0 |
| M1 | 0 | 0 | 308 |
| M2 | 0 | 0 | 132 |
| M3 | 0 | 0 | 414 |
| M4 | 0 | 0 | 381 |
| M5 | 0 | 0 | 522 |
| M6 | 0 | 0 | 435 |
| OCR_TESSERACT_VIE_P4 | 753 | 0 | 0 |
| OCR_TESSERACT_VIE_P5 | 726 | 0 | 0 |
| OCR_TESSERACT_VIE_P6 | 751 | 0 | 0 |
| OCR_TESSERACT_VIE_P7 | 481 | 0 | 0 |
| TESSERACT_OCR | 1766 | 0 | 0 |

**ALL_CANONICAL_V0.Supporting_Knowledge_Types**

| Supporting_Knowledge_Types | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 440 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 428 | 754 | 742 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 74 |
| RULE | 261 | 338 | 279 |
| SOURCE_CLAIM | 3190 | 2043 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**ALL_CANONICAL_V0.Original_File**

| Original_File | BD | DAU | NPL |
|---|---|---|---|
| TuVi_BuuDinh_7Parts_ONE_SOURCE_CANONICAL_MASTER_v1.0.xlsx | 4477 | 0 | 0 |
| TuVi_DauSoToanThu_CANONICAL_KNOWLEDGE_DRAFT_v0_2_AI_PRECHECK.xlsx | 0 | 3821 | 0 |
| TuVi_KM_Team6_CANONICAL_KNOWLEDGE_v1.0.xlsx | 0 | 0 | 2192 |

### EXTRACTION  (10492 dòng, 26 cột — dùng (extraction_review))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Extract_ID | 100.0% | 10492 | EXT-M1-0001 ; EXT-M1-0002 ; EXT-M1-0003 |
| Source_ID | 100.0% | 3 | SRC001 ; SRC_BD_001 ; SRC_DAU_001 |
| PDF_Page | 100.0% | 436 | 1 ; 2 ; 3 |
| Book_Part | 100.0% | 350 | PREFACE ; VOLUME_I_KHOA_TU_VI ; VOLUME_II_THUAT_TU_VI |
| Chapter | 100.0% | 117 | Lời mở đầu ; Chương 1 – Đối tượng của kh… ; Chương 2 – Phương pháp của … |
| Section | 100.0% | 1092 | Mục tiêu biên soạn ; Phương châm biên soạn ; Mục tiêu sách |
| Taxonomy_L1 | 100.0% | 11 | TV-01 ; TV-11 ; TV-02 |
| Taxonomy_Code | 100.0% | 80 | TV-01.01 ; TV-11.01 ; TV-01.03 |
| Knowledge_Type | 100.0% | 15 | BACKGROUND ; CONCEPT ; SOURCE_CLAIM |
| Subject | 66.8% | 1568 | Tử Vi Tổng Hợp ; Tổng hợp ; Sáng tạo |
| Predicate | 66.8% | 58 | HAS_ATTRIBUTE ; REPRESENTS ; APPLIES_WHEN |
| Object | 66.8% | 5994 | Tiếp nối và khai triển Tử V… ; Chọn lọc, hệ thống hóa và q… ; Bổ sung, cập nhật… |
| Condition_Context | 16.6% | 345 | Không kết luận từ một cung … ; Âm/Dương; giờ; tháng; năm; … ; Theo Ngũ Hành |
| Normalized_Knowledge | 100.0% | 10416 | Tác giả trình bày Tử Vi Tổn… ; Theo lời mở đầu, 'tổng hợp'… ; Theo tác giả, 'sá… |
| Original_Text | 100.0% | 10395 | [Phiên âm/chuẩn hóa chính t… ; [Phiên âm/chuẩn hóa chính t… ; [Phiên âm/chuẩn h… |
| Author_Stance | 100.0% | 11 | AUTHOR_ASSERTION ; AUTHOR_CRITIQUE ; ALTERNATIVE_VIEW |
| Certainty | 100.0% | 5 | HIGH ; MEDIUM ; LOW |
| Related_Items | 45.4% | 3728 | Tài Bạch; Phu Thê; Thiên Di ; Thiên Di; Tài Bạch; Quan Lộc ; TV-05 |
| Extractor | 100.0% | 12 | M1 ; M2 ; M3 |
| Extract_Date | 100.0% | 5 | 46300 ; 46299 ; 2026-10-05 |
| Review_Status | 100.0% | 6 | REVIEW_NEEDED ; OCR_REVIEW_PENDING ; SOURCE_REVIEW_PENDING |
| Reviewer | 0.0% | 0 |  |
| Review_Date | 0.0% | 0 |  |
| Review_Comment | 81.9% | 751 | AUTO_BULLET từ text layer P… ; Cần kiểm tra OCR/điều kiện/… ; SOURCE_REVIEW_PEN… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Original_File | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |

**EXTRACTION.Source_ID**

| Source_ID | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 2194 |
| SRC_BD_001 | 4477 | 0 | 0 |
| SRC_DAU_001 | 0 | 3821 | 0 |

**EXTRACTION.Taxonomy_L1**

| Taxonomy_L1 | BD | DAU | NPL |
|---|---|---|---|
| TV-01 | 724 | 1661 | 32 |
| TV-02 | 0 | 76 | 100 |
| TV-03 | 0 | 0 | 32 |
| TV-04 | 124 | 107 | 30 |
| TV-05 | 2432 | 791 | 65 |
| TV-06 | 605 | 338 | 148 |
| TV-07 | 151 | 323 | 2 |
| TV-08 | 111 | 85 | 89 |
| TV-09 | 63 | 0 | 1278 |
| TV-10 | 267 | 440 | 120 |
| TV-11 | 0 | 0 | 298 |

**EXTRACTION.Knowledge_Type**

| Knowledge_Type | BD | DAU | NPL |
|---|---|---|---|
| ATTRIBUTE | 100 | 0 | 79 |
| AUTHOR_CRITIQUE | 0 | 0 | 50 |
| BACKGROUND | 200 | 123 | 31 |
| CASE | 267 | 440 | 117 |
| CONCEPT | 0 | 36 | 124 |
| ENTITY | 0 | 0 | 1 |
| EXCEPTION | 0 | 0 | 39 |
| INTERPRETATION | 428 | 754 | 744 |
| LIMITATION | 0 | 0 | 99 |
| OPINION | 2 | 0 | 38 |
| PROCEDURE | 29 | 85 | 75 |
| RELATION | 0 | 0 | 74 |
| RULE | 261 | 338 | 279 |
| SOURCE_CLAIM | 3190 | 2043 | 417 |
| UNCERTAINTY | 0 | 2 | 27 |

**EXTRACTION.Author_Stance**

| Author_Stance | BD | DAU | NPL |
|---|---|---|---|
| ALTERNATIVE_VIEW | 0 | 0 | 40 |
| AUTHOR_ASSERTION | 0 | 0 | 1096 |
| AUTHOR_ASSERTION_UNVERIFIED | 1566 | 0 | 0 |
| AUTHOR_CRITIQUE | 0 | 0 | 63 |
| AUTHOR_UNCERTAINTY | 0 | 45 | 39 |
| CITED_TRADITION | 0 | 0 | 829 |
| EXAMPLE_ONLY | 0 | 0 | 121 |
| HISTORICAL_NARRATION_UNVERIFIED | 200 | 0 | 0 |
| NOT_APPLICABLE | 0 | 0 | 6 |
| NOT_YET_ATTRIBUTED | 2711 | 0 | 0 |
| SOURCE_CLAIM | 0 | 3776 | 0 |

**EXTRACTION.Certainty**

| Certainty | BD | DAU | NPL |
|---|---|---|---|
| HIGH | 0 | 2096 | 745 |
| LOW | 0 | 17 | 957 |
| MEDIUM | 0 | 1708 | 492 |
| UNKNOWN | 2711 | 0 | 0 |
| UNVERIFIED | 1766 | 0 | 0 |

**EXTRACTION.Extractor**

| Extractor | BD | DAU | NPL |
|---|---|---|---|
| AUTOMATED_SOURCE_CAPTURE | 0 | 3821 | 0 |
| M1 | 0 | 0 | 308 |
| M2 | 0 | 0 | 132 |
| M3 | 0 | 0 | 414 |
| M4 | 0 | 0 | 381 |
| M5 | 0 | 0 | 524 |
| M6 | 0 | 0 | 435 |
| OCR_TESSERACT_VIE_P4 | 753 | 0 | 0 |
| OCR_TESSERACT_VIE_P5 | 726 | 0 | 0 |
| OCR_TESSERACT_VIE_P6 | 751 | 0 | 0 |
| OCR_TESSERACT_VIE_P7 | 481 | 0 | 0 |
| TESSERACT_OCR+HEURISTIC_CLASSIFICATION | 1766 | 0 | 0 |

**EXTRACTION.Extract_Date**

| Extract_Date | BD | DAU | NPL |
|---|---|---|---|
| 2026-10-05 | 0 | 0 | 61 |
| 2026-10-08 | 4477 | 0 | 0 |
| 2026-10-09 | 0 | 3821 | 0 |
| 46299 | 0 | 0 | 1298 |
| 46300 | 0 | 0 | 835 |

**EXTRACTION.Review_Status**

| Review_Status | BD | DAU | NPL |
|---|---|---|---|
| CONTENT_REVIEW_REQUIRED | 0 | 1708 | 0 |
| OCR_REVIEW_PENDING | 1766 | 0 | 0 |
| OCR_REVIEW_REQUIRED | 0 | 17 | 0 |
| REVIEW_NEEDED | 0 | 0 | 2194 |
| SEMANTIC_REVIEW_PENDING | 0 | 2096 | 0 |
| SOURCE_REVIEW_PENDING | 2711 | 0 | 0 |

**EXTRACTION.Original_File**

| Original_File | BD | DAU | NPL |
|---|---|---|---|
| TuVi_BuuDinh_7Parts_ONE_SOURCE_CANONICAL_MASTER_v1.0.xlsx | 4477 | 0 | 0 |
| TuVi_DauSoToanThu_CANONICAL_KNOWLEDGE_DRAFT_v0_2_AI_PRECHECK.xlsx | 0 | 3821 | 0 |
| TuVi_KM_Team6_CANONICAL_KNOWLEDGE_v1.0.xlsx | 0 | 0 | 2194 |

### EVIDENCE  (10492 dòng, 21 cột — dùng (evidence))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Evidence_ID | 100.0% | 10492 | BD-EV-000001 ; BD-EV-000002 ; BD-EV-000003 |
| Canonical_ID | 100.0% | 10489 | BD-KN-000001 ; BD-KN-000002 ; BD-KN-000003 |
| Extract_ID | 100.0% | 10492 | BD-EXT-000001 ; BD-EXT-000002 ; BD-EXT-000003 |
| Source_ID | 100.0% | 3 | SRC_BD_001 ; SRC_DAU_001 ; SRC001 |
| PDF_Page | 100.0% | 436 | 1 ; 2 ; 3 |
| Printed_Page | 36.4% | 340 | 2 ; 3 ; 4 |
| Source_Segment_ID | 36.4% | 3673 | DAU-SEG-000004 ; DAU-SEG-000005 ; DAU-SEG-000006 |
| Chapter | 57.3% | 110 | Lời tác giả / dẫn ; Tử vi đẩu số qua truyền thu… ; Trần Đoàn và sách Tử Vi đẩu… |
| Original_Text | 100.0% | 10395 | ki LA ki ` TƯ VI ỨNG DỤNG B… ; Trong thập niên 1960 trở lạ… ; học huyền bí nhưn… |
| OCR_Legibility | 57.3% | 3 | HIGH ; MEDIUM ; LOW |
| Evidence_Method | 57.3% | 2 | TEXT_LAYER ; EXTRACTION_ORIGINAL_TEXT |
| Review_Status | 57.3% | 4 | SEMANTIC_REVIEW_PENDING ; CONTENT_REVIEW_REQUIRED ; OCR_REVIEW_REQUIRED |
| Part_Number | 42.7% | 7 | 1 ; 2 ; 3 |
| Section_Auto | 42.7% | 417 | Lịch sử và phương pháp ; NHỮNG TẢNG ĐÁ TRÊN ĐƯỜNG ĐẾ… ; TẢNG ĐÁ 1 |
| Original_OCR_Excerpt | 42.7% | 4429 | ki LA ki ` TƯ VI ỨNG DỤNG B… ; Trong thập niên 1960 trở lạ… ; học huyền bí nhưn… |
| Full_Page_Text_SHA256 | 42.7% | 578 | 5747602e1068284c8dbc7849fa1… ; 7df3fd463a9edae7870dd1b7b51… ; c4a2abe11082e4a4e… |
| Extraction_Method | 42.7% | 2 | TESSERACT_OCR ; TESSERACT_OCR_VIE_PSM3 |
| Evidence_Status | 42.7% | 1 | OCR_REVIEW_PENDING |
| Book_Part | 63.6% | 10 | 1 ; 2 ; 3 |
| Book_Code | 100.0% | 3 | BD ; DAU ; NPL |
| Evidence_Origin | 100.0% | 2 | ORIGINAL_EVIDENCE_SHEET ; SYNTHESIZED_FROM_EXTRACTION… |

**EVIDENCE.Source_ID**

| Source_ID | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 2194 |
| SRC_BD_001 | 4477 | 0 | 0 |
| SRC_DAU_001 | 0 | 3821 | 0 |

**EVIDENCE.OCR_Legibility**

| OCR_Legibility | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 4477 | 0 | 0 |
| HIGH | 0 | 2096 | 745 |
| LOW | 0 | 17 | 957 |
| MEDIUM | 0 | 1708 | 492 |

**EVIDENCE.Evidence_Method**

| Evidence_Method | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 4477 | 0 | 0 |
| EXTRACTION_ORIGINAL_TEXT | 0 | 0 | 2194 |
| TEXT_LAYER | 0 | 3821 | 0 |

**EVIDENCE.Review_Status**

| Review_Status | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 4477 | 0 | 0 |
| CONTENT_REVIEW_REQUIRED | 0 | 1708 | 0 |
| OCR_REVIEW_REQUIRED | 0 | 17 | 0 |
| REVIEW_NEEDED | 0 | 0 | 2194 |
| SEMANTIC_REVIEW_PENDING | 0 | 2096 | 0 |

**EVIDENCE.Part_Number**

| Part_Number | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 0 | 3821 | 2194 |
| 1 | 600 | 0 | 0 |
| 2 | 580 | 0 | 0 |
| 3 | 586 | 0 | 0 |
| 4 | 753 | 0 | 0 |
| 5 | 726 | 0 | 0 |
| 6 | 751 | 0 | 0 |
| 7 | 481 | 0 | 0 |

**EVIDENCE.Extraction_Method**

| Extraction_Method | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 0 | 3821 | 2194 |
| TESSERACT_OCR | 1766 | 0 | 0 |
| TESSERACT_OCR_VIE_PSM3 | 2711 | 0 | 0 |

**EVIDENCE.Book_Part**

| Book_Part | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 0 | 3821 | 0 |
| 1 | 600 | 0 | 0 |
| 2 | 580 | 0 | 0 |
| 3 | 586 | 0 | 0 |
| 4 | 753 | 0 | 0 |
| 5 | 726 | 0 | 0 |
| 6 | 751 | 0 | 0 |
| 7 | 481 | 0 | 0 |
| PREFACE | 0 | 0 | 10 |
| VOLUME_II_THUAT_TU_VI | 0 | 0 | 1810 |
| VOLUME_I_KHOA_TU_VI | 0 | 0 | 374 |

**EVIDENCE.Evidence_Origin**

| Evidence_Origin | BD | DAU | NPL |
|---|---|---|---|
| ORIGINAL_EVIDENCE_SHEET | 4477 | 3821 | 0 |
| SYNTHESIZED_FROM_EXTRACTION; CANONICAL_V1_LINK | 0 | 0 | 2194 |

### DEDUPE_LOG  (88 dòng, 13 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Rule | 100.0% | 3 | EXACT_INTRA_BOOK ; REPEAT_DIFFERENT_CONTEXT ; MATCHING_TEXT_DIFFERENT_SPOC |
| Book_Code | 100.0% | 3 | BD ; DAU ; NPL |
| Source_ID | 100.0% | 3 | SRC_BD_001 ; SRC_DAU_001 ; SRC001 |
| Duplicate_ID | 100.0% | 88 | BD-KN-000366 ; BD-KN-000555 ; BD-KN-000899 |
| Primary_ID | 100.0% | 78 | BD-KN-000290 ; BD-KN-000402 ; BD-KN-000746 |
| Duplicate_Pages | 100.0% | 56 | P1:57 ; P1:82 ; P2:45 |
| Primary_Pages | 100.0% | 56 | P1:47 ; P1:62 ; P2:24 |
| Chapter | 100.0% | 20 | Lịch sử, phương pháp và luậ… ; Luận sao và cách cục (Phần … ; Luận sao và cách … |
| Subject | 63.6% | 17 | Tri thức / phương pháp Tử Vi ; Tử Vi ; Vũ Khúc |
| Predicate | 63.6% | 3 | CLAIMS ; MODIFIED_BY ; HAS_ATTRIBUTE |
| Object | 63.6% | 48 | Bên trong vẫn còn sự sống. … ; *TỬ VI QUYỀN LỘC hội DƯƠNG … ; *VŨ KHÚC nhập miế… |
| Canonical_Knowledge | 100.0% | 80 | Bên trong vẫn còn sự sống. … ; *TỬ VI QUYỀN LỘC hội DƯƠNG … ; *VŨ KHÚC nhập miế… |
| Decision | 100.0% | 3 | CONSOLIDATE_IN_ACTIVE_KEEP_… ; KEEP_SEPARATE_CONTEXT ; KEEP_SEPARATE_UNVERIFIED… |

**DEDUPE_LOG.Rule**

| Rule | BD | DAU | NPL |
|---|---|---|---|
| EXACT_INTRA_BOOK | 27 | 6 | 0 |
| MATCHING_TEXT_DIFFERENT_SPOC | 4 | 16 | 1 |
| REPEAT_DIFFERENT_CONTEXT | 24 | 10 | 0 |

**DEDUPE_LOG.Source_ID**

| Source_ID | BD | DAU | NPL |
|---|---|---|---|
| SRC001 | 0 | 0 | 1 |
| SRC_BD_001 | 55 | 0 | 0 |
| SRC_DAU_001 | 0 | 32 | 0 |

**DEDUPE_LOG.Predicate**

| Predicate | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 0 | 32 | 0 |
| CLAIMS | 52 | 0 | 0 |
| HAS_ATTRIBUTE | 1 | 0 | 1 |
| MODIFIED_BY | 2 | 0 | 0 |

**DEDUPE_LOG.Decision**

| Decision | BD | DAU | NPL |
|---|---|---|---|
| CONSOLIDATE_IN_ACTIVE_KEEP_RAW_AND_EVIDENCE | 27 | 6 | 0 |
| KEEP_SEPARATE_CONTEXT | 24 | 10 | 0 |
| KEEP_SEPARATE_UNVERIFIED_SEMANTIC | 4 | 16 | 1 |

### CANONICAL_ID_REDIRECTS  (34 dòng, 5 cột — dùng (id_redirects))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Original_Canonical_ID | 100.0% | 34 | BD-KN-000366 ; BD-KN-000555 ; BD-KN-000899 |
| Active_Canonical_ID | 100.0% | 30 | BD-KN-000290 ; BD-KN-000402 ; BD-KN-000746 |
| Source_ID | 100.0% | 3 | SRC_BD_001 ; SRC_DAU_001 ; SRC001 |
| Reason | 100.0% | 2 | EXACT_SAME_BOOK_SAME_CHAPTE… ; PREVIOUS_SOURCE_RELEASE_SEM… |
| Original_Row_Preserved | 100.0% | 2 | YES — ALL_CANONICAL_ORIGINAL ; YES — ALL_CANONICAL_V0 |

**CANONICAL_ID_REDIRECTS.Source_ID**

| Source_ID | số dòng |
|---|---|
| SRC_BD_001 | 27 |
| SRC_DAU_001 | 6 |
| SRC001 | 1 |

**CANONICAL_ID_REDIRECTS.Reason**

| Reason | số dòng |
|---|---|
| EXACT_SAME_BOOK_SAME_CHAPTER_SAME_MEANING_SIGNATURE | 33 |
| PREVIOUS_SOURCE_RELEASE_SEMANTIC_DUPLICATE | 1 |

**CANONICAL_ID_REDIRECTS.Original_Row_Preserved**

| Original_Row_Preserved | số dòng |
|---|---|
| YES — ALL_CANONICAL_ORIGINAL | 33 |
| YES — ALL_CANONICAL_V0 | 1 |

### VOCABULARY_INDEX  (506 dòng, 7 cột — chưa phân loại)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Canonical_Term | 100.0% | 477 | Huynh Đệ ; Mệnh ; Nô Bộc |
| Entity_Type | 100.0% | 19 | PALACE ; ELEMENT ; YIN_YANG |
| Taxonomy_Code | 88.9% | 59 | TV-04.12 ; TV-04.01 ; TV-04.06 |
| Source_Count | 100.0% | 3 | 3 ; 2 ; 1 |
| Source_IDs | 100.0% | 5 | SRC001; SRC_BD_001; SRC_DAU… ; SRC001; SRC_DAU_001 ; SRC001; SRC_BD_001 |
| All_Vocab_IDs | 100.0% | 506 | VOC-0001; BD-VOC-0001; DAU-… ; VOC-0002; BD-VOC-0002; DAU-… ; VOC-0003; DAU-VOC… |
| Definitions_Are_Source_Specific | 100.0% | 1 | YES; see VOCABULARY for ori… |

**VOCABULARY_INDEX.Source_Count**

| Source_Count | số dòng |
|---|---|
| 1 | 354 |
| 2 | 141 |
| 3 | 11 |

**VOCABULARY_INDEX.Source_IDs**

| Source_IDs | số dòng |
|---|---|
| SRC001 | 315 |
| SRC001; SRC_BD_001 | 140 |
| SRC_DAU_001 | 39 |
| SRC001; SRC_BD_001; SRC_DAU_001 | 11 |
| SRC001; SRC_DAU_001 | 1 |

### VOCABULARY  (669 dòng, 15 cột — dùng (vocabulary))

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Vocab_ID | 100.0% | 669 | VOC-0001 ; VOC-0002 ; VOC-0003 |
| Canonical_Term | 100.0% | 477 | Huynh Đệ ; Mệnh ; Nô Bộc |
| Entity_Type | 100.0% | 19 | PALACE ; ELEMENT ; YIN_YANG |
| Aliases | 7.2% | 33 | Bào; Cung Bào; Huynh ; Cung Mệnh ; Cung Nô; Nô |
| Taxonomy_Code | 91.0% | 59 | TV-04.12 ; TV-04.01 ; TV-04.06 |
| Definition_or_Note | 100.0% | 96 | Cung liên quan anh chị em. ; Cung liên quan nội tâm/cá n… ; Cung liên quan bạn … |
| Source_ID | 99.4% | 4 | SRC001 ; MASTER_CANONICAL ; SRC_BD_001 |
| Source_Pages | 91.0% | 351 | 10 ; 9; 23; 24; 28; 30; 64; 66; … ; 23; 65; 66; 193; 225; 227; … |
| Usage_Subject | 92.4% | 43 | 1 ; 17 ; 6 |
| Usage_Object | 92.4% | 29 | 0 ; 1 ; 2 |
| Usage_Total | 92.4% | 97 | 1 ; 17 ; 7 |
| Status | 100.0% | 4 | APPROVED_TERM ; CONTROLLED_TERM ; CONTROLLED_MAPPING_PENDING_… |
| Normalization_Rule | 100.0% | 5 | SAFE_ALIAS_TO_CANONICAL ; EXACT_MATCH ; UPPERCASE_EXACT |
| Notes | 100.0% | 44 | Term derived from master ca… ; V1.0 alias collision fix: c… ; Predicate vocabul… |
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |

**VOCABULARY.Source_ID**

| Source_ID | BD | DAU | NPL |
|---|---|---|---|
| (trống) | 0 | 0 | 4 |
| MASTER_CANONICAL | 0 | 0 | 56 |
| SRC001 | 0 | 0 | 407 |
| SRC_BD_001 | 151 | 0 | 0 |
| SRC_DAU_001 | 0 | 51 | 0 |

**VOCABULARY.Status**

| Status | BD | DAU | NPL |
|---|---|---|---|
| APPROVED_TERM | 0 | 0 | 45 |
| CANDIDATE_SOURCE_VOCAB | 0 | 51 | 0 |
| CONTROLLED_MAPPING_PENDING_REVIEW | 151 | 0 | 0 |
| CONTROLLED_TERM | 0 | 0 | 422 |

**VOCABULARY.Normalization_Rule**

| Normalization_Rule | BD | DAU | NPL |
|---|---|---|---|
| EXACT_MATCH | 0 | 0 | 378 |
| Merged count from Part1-3 and Part4-7; original normalization statements preser… | 151 | 0 | 0 |
| REVIEW_ALIAS_AND_DEFINITION | 0 | 51 | 0 |
| SAFE_ALIAS_TO_CANONICAL | 0 | 0 | 33 |
| UPPERCASE_EXACT | 0 | 0 | 56 |

### OCR_PAGE_TEXT  (926 dòng, 18 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Part_Number | 62.5% | 7 | 1 ; 2 ; 3 |
| PDF_Page | 100.0% | 347 | 1 ; 2 ; 3 |
| Page_Reference | 62.5% | 579 | Phần 1 \\| PDF 1 ; Phần 1 \\| PDF 2 ; Phần 1 \\| PDF 3 |
| OCR_Full_Text | 62.5% | 579 | ki LA ki ` TƯ VI ỨNG DỤNG B… ; Nguồn: Trích lục của Yên tử… ; Lý do, khi tiếp x… |
| OCR_Char_Count | 62.5% | 417 | 117 ; 1843 ; 1841 |
| Text_SHA256 | 62.5% | 579 | 5747602e1068284c8dbc7849fa1… ; 7df3fd463a9edae7870dd1b7b51… ; c4a2abe11082e4a4e… |
| Extraction_Method | 62.5% | 2 | OCR_TESSERACT_VIE_PSM6 ; TESSERACT_OCR_VIE_PSM3 |
| QA_Status | 62.5% | 2 | LOW_TEXT_REVIEW ; OCR_REVIEW_PENDING |
| Paragraphs_Presplit | 62.5% | 22 | 1 ; 10 ; 8 |
| Printed_Page | 37.4% | 346 | 1 ; 2 ; 3 |
| Page_Type | 37.5% | 5 | COVER ; TITLE_PAGE ; BODY |
| Raw_Extracted_Text | 37.4% | 346 | Hi Di Trần Đoàn          Vũ… ; Vũ Tài Lục                 … ; ra triều đình ngh… |
| Source_Block_Count | 37.5% | 26 | 0 ; 8 ; 9 |
| Knowledge_Unit_Count | 37.5% | 26 | 0 ; 4 ; 9 |
| Coverage_Status | 37.5% | 3 | EXCLUDE_NONKNOWLEDGE ; HAS_KU ; REVIEW_REQUIRED |
| Flagged_Review_Units | 36.7% | 24 | 0 ; 2 ; 3 |
| Notes | 0.6% | 3 | COVER IMAGE: NOT TEXT-EXTRA… ; Only printed page number, n… ; Back-of-book auto… |
| Book_Code | 100.0% | 2 | BD ; DAU |

**OCR_PAGE_TEXT.Part_Number**

| Part_Number | BD | DAU |
|---|---|---|
| (trống) | 0 | 347 |
| 1 | 88 | 0 |
| 2 | 92 | 0 |
| 3 | 85 | 0 |
| 4 | 85 | 0 |
| 5 | 85 | 0 |
| 6 | 85 | 0 |
| 7 | 59 | 0 |

**OCR_PAGE_TEXT.Extraction_Method**

| Extraction_Method | BD | DAU |
|---|---|---|
| (trống) | 0 | 347 |
| OCR_TESSERACT_VIE_PSM6 | 265 | 0 |
| TESSERACT_OCR_VIE_PSM3 | 314 | 0 |

**OCR_PAGE_TEXT.QA_Status**

| QA_Status | BD | DAU |
|---|---|---|
| (trống) | 0 | 347 |
| LOW_TEXT_REVIEW | 2 | 0 |
| OCR_REVIEW_PENDING | 577 | 0 |

**OCR_PAGE_TEXT.Page_Type**

| Page_Type | BD | DAU |
|---|---|---|
| (trống) | 579 | 0 |
| BLANK_OR_PAGE_NUMBER_ONLY | 0 | 1 |
| BODY | 0 | 340 |
| COVER | 0 | 1 |
| TABLE_OF_CONTENTS | 0 | 4 |
| TITLE_PAGE | 0 | 1 |

**OCR_PAGE_TEXT.Coverage_Status**

| Coverage_Status | BD | DAU |
|---|---|---|
| (trống) | 579 | 0 |
| EXCLUDE_NONKNOWLEDGE | 0 | 7 |
| HAS_KU | 0 | 90 |
| REVIEW_REQUIRED | 0 | 250 |

**OCR_PAGE_TEXT.Notes**

| Notes | BD | DAU |
|---|---|---|
| (trống) | 579 | 341 |
| Back-of-book autogenerated TOC | 0 | 4 |
| COVER IMAGE: NOT TEXT-EXTRACTED | 0 | 1 |
| Only printed page number, no KU expected | 0 | 1 |

### SOURCE_SEGMENTS  (10386 dòng, 17 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Part_Number | 57.2% | 7 | 1 ; 2 ; 3 |
| PDF_Page | 100.0% | 342 | 1 ; 2 ; 3 |
| Original_OCR_Segment | 57.2% | 5720 | ki LA ki ` TƯ VI ỨNG DỤNG B… ; Nguồn: Trích lục của Yên tử… ; Trong thập niên 1… |
| Segment_Class | 57.2% | 3 | TEXT ; HEADING ; OCR_PARAGRAPH |
| Characters | 57.2% | 665 | 117 ; 45 ; 664 |
| Source_Segment_ID | 42.8% | 4443 | DAU-SEG-000001 ; DAU-SEG-000002 ; DAU-SEG-000003 |
| Source_ID | 42.8% | 1 | SRC_DAU_001 |
| Printed_Page | 42.8% | 340 | 2 ; 3 ; 4 |
| Y_Start | 42.8% | 492 | 29.2 ; 51 ; 124.9 |
| Y_End | 42.8% | 518 | 43.8 ; 65.5 ; 144.6 |
| Chapter | 42.8% | 75 | Lời tác giả / dẫn ; Tử vi đẩu số qua truyền thu… ; Trần Đoàn và sách Tử Vi đẩu… |
| Section | 42.8% | 118 | Mở đầu ; Lời Tác Giả ; Dẫn |
| Segment_Type | 42.8% | 2 | SOURCE_PASSAGE ; SECTION_TITLE |
| Original_Text | 42.8% | 4259 | Vũ Tài Lục ; Dịch và bình chú ; Lời Tác Giả |
| Clean_Spaced_Text | 42.8% | 4257 | Vũ Tài Lục ; Dịch và bình chú ; Lời Tác Giả |
| Disposition | 42.8% | 2 | CANDIDATE_KU ; NONE |
| Book_Code | 100.0% | 2 | BD ; DAU |

**SOURCE_SEGMENTS.Part_Number**

| Part_Number | BD | DAU |
|---|---|---|
| (trống) | 0 | 4443 |
| 1 | 946 | 0 |
| 2 | 889 | 0 |
| 3 | 927 | 0 |
| 4 | 890 | 0 |
| 5 | 870 | 0 |
| 6 | 850 | 0 |
| 7 | 571 | 0 |

**SOURCE_SEGMENTS.Segment_Class**

| Segment_Class | BD | DAU |
|---|---|---|
| (trống) | 0 | 4443 |
| HEADING | 532 | 0 |
| OCR_PARAGRAPH | 2914 | 0 |
| TEXT | 2497 | 0 |

**SOURCE_SEGMENTS.Segment_Type**

| Segment_Type | BD | DAU |
|---|---|---|
| (trống) | 5943 | 0 |
| SECTION_TITLE | 0 | 80 |
| SOURCE_PASSAGE | 0 | 4363 |

**SOURCE_SEGMENTS.Disposition**

| Disposition | BD | DAU |
|---|---|---|
| (trống) | 5943 | 0 |
| CANDIDATE_KU | 0 | 4363 |
| NONE | 0 | 80 |

### REVIEW_QUEUE  (1512 dòng, 11 cột — chưa phân loại)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Canonical_ID | 100.0% | 1512 | BD-KN-000002 ; BD-KN-000007 ; BD-KN-000010 |
| Extract_ID | 100.0% | 1512 | BD-EXT-000002 ; BD-EXT-000007 ; BD-EXT-000010 |
| Part_Number | 100.0% | 7 | 1 ; 2 ; 3 |
| PDF_Page | 100.0% | 91 | 2 ; 3 ; 4 |
| Review_Reason | 100.0% | 13 | LONG_SOURCE_FRAGMENT ; CONDITIONAL_MEANING_CHECK ; POTENTIAL_DUPLICATE |
| Review_Status | 100.0% | 1 | SOURCE_REVIEW_PENDING |
| Subject_Auto | 100.0% | 52 | Mệnh ; Tử Vi ; Tuần |
| Taxonomy_Code_Auto | 100.0% | 23 | TV-01.01 ; TV-10.02 ; TV-08.02 |
| Potential_Duplicate_Of | 1.1% | 14 | BD-KN-000290 ; BD-KN-000402 ; BD-KN-000746 |
| Reviewer_Action | 100.0% | 2 | Đối chiếu ảnh PDF và tách đ… ; Compare with PDF image; spl… |
| Book_Code | 100.0% | 1 | BD |

**REVIEW_QUEUE.Part_Number**

| Part_Number | BD |
|---|---|
| 1 | 229 |
| 2 | 253 |
| 3 | 261 |
| 4 | 160 |
| 5 | 162 |
| 6 | 249 |
| 7 | 198 |

**REVIEW_QUEUE.Review_Reason**

| Review_Reason | BD |
|---|---|
| CONDITIONAL_MEANING_CHECK | 797 |
| CONDITIONAL_MEANING_CHECK; PAGE_OR_PARAGRAPH_CONTINUATION | 17 |
| EXAMPLE_CONTEXT_CHECK | 149 |
| EXAMPLE_CONTEXT_CHECK; PAGE_OR_PARAGRAPH_CONTINUATION | 36 |
| LONG_SOURCE_FRAGMENT | 27 |
| LONG_SOURCE_FRAGMENT; CONDITIONAL_MEANING_CHECK | 4 |
| LONG_SOURCE_FRAGMENT; CONDITIONAL_MEANING_CHECK; PAGE_OR_PARAGRAPH_CONTINUATION | 6 |
| LONG_SOURCE_FRAGMENT; EXAMPLE_CONTEXT_CHECK | 6 |
| LONG_SOURCE_FRAGMENT; EXAMPLE_CONTEXT_CHECK; PAGE_OR_PARAGRAPH_CONTINUATION | 3 |
| LONG_SOURCE_FRAGMENT; PAGE_OR_PARAGRAPH_CONTINUATION | 6 |
| OCR_NOISE_CHECK | 2 |
| PAGE_OR_PARAGRAPH_CONTINUATION | 443 |
| POTENTIAL_DUPLICATE | 16 |

**REVIEW_QUEUE.Potential_Duplicate_Of**

| Potential_Duplicate_Of | BD |
|---|---|
| (trống) | 1496 |
| BD-KN-000290 | 1 |
| BD-KN-000402 | 1 |
| BD-KN-000746 | 2 |
| BD-KN-000827 | 1 |
| BD-KN-000931 | 1 |
| BD-KN-000934 | 1 |
| BD-KN-000935 | 1 |
| BD-KN-001020 | 1 |
| BD-KN-001052 | 1 |
| BD-KN-001055 | 1 |
| BD-KN-001183 | 2 |
| BD-KN-001188 | 1 |
| BD-KN-001213 | 1 |
| BD-KN-001352 | 1 |

**REVIEW_QUEUE.Reviewer_Action**

| Reviewer_Action | BD |
|---|---|
| Compare with PDF image; split multiple claims, validate conditions, record exac… | 769 |
| Đối chiếu ảnh PDF và tách điều kiện thành rule riêng nếu đủ căn cứ. | 743 |

### OCR_REVIEW_WORKLIST  (82 dòng, 17 cột — chưa phân loại)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Review_ID | 100.0% | 82 | DAU-REV-000018 ; DAU-REV-000052 ; DAU-REV-000063 |
| Canonical_ID | 98.8% | 81 | DAU-KN-000132 ; DAU-KN-000293 ; DAU-KN-000353 |
| Extract_ID | 98.8% | 81 | DAU-EXT-000132 ; DAU-EXT-000293 ; DAU-EXT-000353 |
| Source_Segment_ID | 100.0% | 81 | DAU-SEG-000124 ; DAU-SEG-000289 ; DAU-SEG-000361 |
| Source_ID | 100.0% | 1 | SRC_DAU_001 |
| PDF_Page | 100.0% | 68 | 20 ; 39 ; 47 |
| Printed_Page | 100.0% | 68 | 19 ; 38 ; 46 |
| Chapter | 100.0% | 44 | Tử vi đẩu số qua truyền thu… ; Chư tinh vấn đáp luận ; SAO THIÊN CƠ |
| Priority | 100.0% | 3 | HIGH ; MEDIUM ; LOW |
| Issue_Types | 100.0% | 14 | SUSPECTED_TERM_TRANSCRIPTION ; DIGITS_INSIDE_WORD; SUSPECT… ; SUSPECTED_OCR_WORD |
| Suspicious_Original_Text | 100.0% | 82 | Rượu say, Trụ Vương chẳng g… ; nghĩa là : Sao Tam Lang, Vũ… ; / Thiên Cơ sao củ… |
| Block_Context_OCR | 100.0% | 81 | Ân triều có ông quan trung … ; nghĩa là : Sao Tam Lang, Vũ… ; / Thiên Cơ sao củ… |
| Verified_Text_Manual | 98.8% | 81 | Rượu say, Trụ Vương chẳng g… ; nghĩa là : Sao Tham Lang, V… ; / Thiên Cơ sao củ… |
| Correction_Notes_Manual | 100.0% | 15 | Cùng mẫu "Thái Âm m" đã xác… ; Bản in (PDF 39, tr.38) in "… ; Bản in (PDF 47) c… |
| Review_Status | 100.0% | 3 | AI_PRECHECK_TEXT_ONLY_PENDI… ; AI_CHECKED_VISUAL_PENDING_H… ; OPEN |
| How_to_Find_Source | 100.0% | 2 | PDF page number is 1-based;… ; Compare PDF heading visuall… |
| Book_Code | 100.0% | 1 | DAU |

**OCR_REVIEW_WORKLIST.Priority**

| Priority | DAU |
|---|---|
| HIGH | 17 |
| LOW | 2 |
| MEDIUM | 63 |

**OCR_REVIEW_WORKLIST.Issue_Types**

| Issue_Types | DAU |
|---|---|
| CHECK_WITH_PAGE_40_TU_VI | 1 |
| CHECK_WITH_PAGE_42_TU_VI | 1 |
| DIGITS_INSIDE_WORD; SUSPECTED_OCR_WORD | 1 |
| EXPLICIT_SOURCE_UNCERTAINTY | 42 |
| EXPLICIT_SOURCE_UNCERTAINTY; POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 2 |
| EXPLICIT_SOURCE_UNCERTAINTY; SUSPECTED_OCR_DIACRITIC | 1 |
| POSSIBLE_CORRUPTED_SECTION_HEADING | 1 |
| POSSIBLE_SELF_CONTRADICTORY_POSITION | 1 |
| POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT; SUSPECTED_OCR_DIACRITIC | 2 |
| SUSPECTED_OCR_DIACRITIC | 14 |
| SUSPECTED_OCR_WORD | 1 |
| SUSPECTED_OCR_WORD; POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 1 |
| SUSPECTED_TERM_TRANSCRIPTION | 13 |
| SUSPECTED_TERM_TRANSCRIPTION; POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 1 |

**OCR_REVIEW_WORKLIST.Correction_Notes_Manual**

| Correction_Notes_Manual | DAU |
|---|---|
| Bản in (PDF 39, tr.38) in "Tam Lang" — đây là lỗi của bản in, không phải OCR. Đ… | 1 |
| Bản in (PDF 47) có "ti61ng" -> "tiếng" và "Thiện Cơ" -> "Thiên Cơ" (lỗi gõ của … | 1 |
| Bản in (PDF 56) in đúng "ThÂm Dương Đà"; phần giảng ngay sau ghi "Tham Lang, Dư… | 1 |
| Bản in (PDF 66) in "Ơ" thay cho "Ở" (đã thấy trên ảnh). Đề xuất chuẩn hóa thành… | 1 |
| Bản in (PDF 77, tr.76) đã in "Thái Âm m" — không phải lỗi OCR. Chữ "m" thừa, có… | 1 |
| Chưa xem ảnh trang này. Đoạn có "Thái Âm" và "Ơ số mệnh" (nhiều khả năng "Ở"); … | 1 |
| Cùng mẫu "Thái Âm m" đã xác nhận in thật ở PDF 77. Giữ nguyên, chưa suy diễn "m… | 10 |
| Mẫu "Ơ" thay cho "Ở" cũng thấy in thật trên ảnh PDF 40 và 66, nên nhiều khả năn… | 15 |
| Phần giảng trong cùng đoạn viết "Thiên Phủ", nên "Thiên Phú" nhiều khả năng là … | 1 |
| Tác giả/người bình chú tự nêu không chắc (dấu "(?)", "không rõ nghĩa", "tam sao… | 45 |
| Đã xem ảnh PDF 55: bản in in đúng "văn măc", "hng bạo", "At." (lỗi của bản in).… | 1 |
| Đã xác nhận trên ảnh (PDF 40, tr.39): bản in ghi "Tử Vi ở nơi miếu vượng là cực… | 1 |
| Đã xác nhận trên ảnh (PDF 42, tr.41): bản in ghi Tử Vi miếu Dần Ngọ, vượng Thân… | 1 |
| Đã xác nhận trên ảnh (PDF 66, tr.65): bản in đúng là "vượng địa Tí, Ngọ, hãm đị… | 1 |
| Đã đối chiếu ảnh (PDF 330): đúng như bản in, "thiệt" là từ thuần Việt (thật), K… | 1 |

**OCR_REVIEW_WORKLIST.Review_Status**

| Review_Status | DAU |
|---|---|
| AI_CHECKED_VISUAL_PENDING_HUMAN | 10 |
| AI_PRECHECK_TEXT_ONLY_PENDING_HUMAN | 71 |
| OPEN | 1 |

**OCR_REVIEW_WORKLIST.How_to_Find_Source**

| How_to_Find_Source | DAU |
|---|---|
| Compare PDF heading visually; do not alter transcription without confirmation. | 1 |
| PDF page number is 1-based; match printed page p-1; compare screenshot/PDF befo… | 81 |

### SEMANTIC_REVIEW_WORKLIST  (1650 dòng, 17 cột — chưa phân loại)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Review_ID | 100.0% | 1650 | DAU-REV-000001 ; DAU-REV-000002 ; DAU-REV-000004 |
| Canonical_ID | 100.0% | 1650 | DAU-KN-000012 ; DAU-KN-000013 ; DAU-KN-000019 |
| Extract_ID | 100.0% | 1650 | DAU-EXT-000012 ; DAU-EXT-000013 ; DAU-EXT-000019 |
| Source_Segment_ID | 100.0% | 1649 | DAU-SEG-000016 ; DAU-SEG-000017 ; DAU-SEG-000023 |
| Source_ID | 100.0% | 1 | SRC_DAU_001 |
| PDF_Page | 100.0% | 215 | 4 ; 5 ; 6 |
| Printed_Page | 100.0% | 215 | 3 ; 4 ; 5 |
| Chapter | 100.0% | 62 | Lời tác giả / dẫn ; Tử vi đẩu số qua truyền thu… ; Trần Đoàn và sách Tử Vi đẩu… |
| Priority | 100.0% | 3 | MEDIUM ; LOW ; HIGH |
| Issue_Types | 100.0% | 6 | POSSIBLE_VERSE_OR_CONTINUAT… ; LONG_COMPOUND_PASSAGE_NEEDS… ; POSSIBLE_VERSE_OR… |
| Suspicious_Original_Text | 100.0% | 1633 | Đạo được chuộng do mệnh vậy ; Đạo bị vứt bỏ cũng do mệnh … ; tự nhủ : / Cuộc đờ… |
| Block_Context_OCR | 100.0% | 1634 | Đạo được chuộng do mệnh vậy ; Đạo bị vứt bỏ cũng do mệnh … ; tự nhủ : / Cuộc đờ… |
| Verified_Text_Manual | 0.0% | 0 |  |
| Correction_Notes_Manual | 0.0% | 0 |  |
| Review_Status | 100.0% | 1 | OPEN |
| How_to_Find_Source | 100.0% | 1 | PDF page number is 1-based;… |
| Book_Code | 100.0% | 1 | DAU |

**SEMANTIC_REVIEW_WORKLIST.Priority**

| Priority | DAU |
|---|---|
| HIGH | 2 |
| LOW | 2 |
| MEDIUM | 1646 |

**SEMANTIC_REVIEW_WORKLIST.Issue_Types**

| Issue_Types | DAU |
|---|---|
| EXPLICIT_SOURCE_UNCERTAINTY; POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 2 |
| LONG_COMPOUND_PASSAGE_NEEDS_SPLITTING | 2 |
| POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 1642 |
| POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT; SUSPECTED_OCR_DIACRITIC | 2 |
| SUSPECTED_OCR_WORD; POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 1 |
| SUSPECTED_TERM_TRANSCRIPTION; POSSIBLE_VERSE_OR_CONTINUATION_FRAGMENT | 1 |

### MISC_SOURCE_ROWS  (1237 dòng, 5 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Workbook_File | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |
| Original_Sheet | 100.0% | 21 | OVERVIEW ; README ; VOCAB_QA |
| Original_Excel_Row | 100.0% | 347 | 2 ; 3 ; 4 |
| Original_Row_JSON | 100.0% | 1179 | {"TỬ VI KNOWLEDGE MANAGEMEN… ; {"TỬ VI KNOWLEDGE MANAGEMEN… ; {"TỬ VI KNOWLEDGE… |

**MISC_SOURCE_ROWS.Workbook_File**

| Workbook_File | BD | DAU | NPL |
|---|---|---|---|
| TuVi_BuuDinh_7Parts_ONE_SOURCE_CANONICAL_MASTER_v1.0.xlsx | 544 | 0 | 0 |
| TuVi_DauSoToanThu_CANONICAL_KNOWLEDGE_DRAFT_v0_2_AI_PRECHECK.xlsx | 0 | 434 | 0 |
| TuVi_KM_Team6_CANONICAL_KNOWLEDGE_v1.0.xlsx | 0 | 0 | 259 |

### MERGE_QA  (16 dòng, 3 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Rule | 100.0% | 16 | BOOK_SOURCE_COUNT ; ALL_ORIGINAL_CANONICAL ; RAW_V0_PRESENT |
| Result | 100.0% | 2 | PASS ; USER_REPORTED; ORIGINAL_STA… |
| Details | 100.0% | 15 | 3 ; 10489 ; 10490 |

### SHEET_INVENTORY  (63 dòng, 5 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Book_Code | 100.0% | 3 | NPL ; BD ; DAU |
| Original_Workbook | 100.0% | 3 | TuVi_KM_Team6_CANONICAL_KNO… ; TuVi_BuuDinh_7Parts_ONE_SOU… ; TuVi_DauSoToanThu… |
| Original_Sheet | 100.0% | 34 | OVERVIEW ; README ; SOURCES |
| Original_Data_Rows | 100.0% | 38 | 31 ; 17 ; 1 |
| Preserved_In | 100.0% | 14 | MISC_SOURCE_ROWS ; CORE_TABLE SOURCES ; CORE_TABLE TAXONOMY |

**SHEET_INVENTORY.Original_Workbook**

| Original_Workbook | BD | DAU | NPL |
|---|---|---|---|
| TuVi_BuuDinh_7Parts_ONE_SOURCE_CANONICAL_MASTER_v1.0.xlsx | 22 | 0 | 0 |
| TuVi_DauSoToanThu_CANONICAL_KNOWLEDGE_DRAFT_v0_2_AI_PRECHECK.xlsx | 0 | 19 | 0 |
| TuVi_KM_Team6_CANONICAL_KNOWLEDGE_v1.0.xlsx | 0 | 0 | 22 |

**SHEET_INVENTORY.Preserved_In**

| Preserved_In | BD | DAU | NPL |
|---|---|---|---|
| CORE_TABLE CANONICAL_KNOWLEDGE | 1 | 1 | 1 |
| CORE_TABLE CANONICAL_KNOWLEDGE_V1_0 | 1 | 1 | 1 |
| CORE_TABLE EVIDENCE | 1 | 1 | 0 |
| CORE_TABLE EXTRACTION | 1 | 1 | 1 |
| CORE_TABLE OCR_PAGE_TEXT | 1 | 1 | 0 |
| CORE_TABLE OCR_REVIEW_WORKLIST | 0 | 1 | 0 |
| CORE_TABLE REVIEW_QUEUE | 1 | 0 | 0 |
| CORE_TABLE SEMANTIC_REVIEW_WORKLIST | 0 | 1 | 0 |
| CORE_TABLE SOURCES | 1 | 1 | 1 |
| CORE_TABLE SOURCE_PARTS | 1 | 0 | 0 |
| CORE_TABLE SOURCE_SEGMENTS | 1 | 1 | 0 |
| CORE_TABLE TAXONOMY | 1 | 1 | 1 |
| CORE_TABLE VOCABULARY | 1 | 1 | 1 |
| MISC_SOURCE_ROWS | 11 | 8 | 16 |

### TAXONOMY_DIFFERENCES  (0 dòng, 4 cột — bỏ qua)

| cột | có dữ liệu | giá trị khác nhau | ví dụ |
|---|---|---|---|
| Book_Code | 0% | 0 |  |
| Taxonomy_Code | 0% | 0 |  |
| NPL_Definition_JSON | 0% | 0 |  |
| Other_Definition_JSON | 0% | 0 |  |

## Trường phái an sao KMS đang dùng

Phần bổ sung T5, ngày 2026-11-03. Các thống kê workbook ở trên được sinh tự động;
phần này mô tả cấu hình an sao của ứng dụng.

Engine an sao: `vendor/lasotuvi` (doanguyen, 2016), được gọi qua adapter
`backend/app/services/horoscope_features.py`. Những bất đồng an sao còn mở được
ghi trong [báo cáo T4](LASOTUVI_CROSSCHECK.md) và [issue #1](https://github.com/huypq205/KMS_Tu_Vi/issues/1).

### Hai bảng Tứ Hóa giữ riêng

Nguồn cấu hình: [`configs/tu_hoa_tables.yaml`](../configs/tu_hoa_tables.yaml),
schema version 1. Mỗi dòng theo thứ tự **Lộc / Quyền / Khoa / Kỵ**, đủ 10 Can.

| ID | Nhãn trường phái / nguồn | Trạng thái |
|---|---|---|
| `lasotuvi` | Bảng hiện hành; chú thích trong `App.py` dẫn Thiên Lương, *Số tử vi dưới mắt khoa học* | `vendor_baseline`; mặc định, chưa coi là đã được ba sách KMS xác nhận |
| `hung_ngm_reference` | Bảng §10 của [computation.md tại commit d0238e9](https://github.com/hung-ngm/tu-vi-dau-so/blob/d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7/tu-vi-dau-so/skills/tu-vi-dau-so/references/computation.md) | `reference_unverified`; tham khảo, chưa đối chiếu sách KMS |

Đối chiếu 40 mục bằng `python scripts/compare_tu_hoa_tables.py` xác nhận 37 mục
khớp và 3 mục khác:

| Can | Hóa tinh | `lasotuvi` | `hung_ngm_reference` |
|---|---|---|---|
| Canh | Hóa Khoa | Thiên Đồng | Thái Âm |
| Canh | Hóa Kỵ | Thái Âm | Thiên Đồng |
| Nhâm | Hóa Khoa | Thiên Phủ | Tả Phụ |

Script đọc nhánh an Tứ Hóa và tên sao bằng AST từ `App.py`/`Sao.py`, so với bảng
tham khảo đã cố định trong YAML; không gọi mạng khi chạy. Script cũng kiểm tra
bảng cấu hình `lasotuvi` khớp đủ 40 mục với vendor. Nếu lệch, trả exit code 1.
Bất đồng giữa hai nguồn được báo cáo riêng và không làm script lỗi.

Không tự hòa giải, gộp bảng hay coi repo tham khảo là canonical. Việc phân xử
bằng sách KMS vẫn theo issue #1. Đây chỉ là metadata phương pháp an sao;
không nhập bảng tham khảo vào RAG hoặc tạo tri thức canonical mới.

### Chọn bảng và phạm vi áp dụng

Mặc định không cần thêm cấu hình. Để chọn rõ trong `.env`:

```dotenv
KMS_TU_HOA_TABLE=lasotuvi
```

Hoặc chủ động dùng bảng tham khảo:

```dotenv
KMS_TU_HOA_TABLE=hung_ngm_reference
```

Khởi động lại backend sau khi đổi `.env`. Có thể đổi `default_table` trong YAML
khi biến môi trường không được đặt. Tên bảng sai, thiếu Can, thiếu nhãn nguồn,
sai tên sao hoặc sai số lượng bốn hóa đều bị từ chối; không âm thầm dùng bảng khác.

Bảng được chọn áp dụng đồng bộ cho hóa tinh lá số gốc (Can năm sinh âm lịch),
lưu Tứ Hóa (Can năm xem), vai trò Tứ Hóa trong facts, prompt luận giải/hỏi nhanh
và nhãn UI ở bảng vận năm. Adapter chỉ chuyển các hóa tinh có vị trí khác;
không sửa file vendor hay các quy tắc an sao khác.

`generate_raw_horoscope(..., tu_hoa_table_id="lasotuvi")` cho phép công cụ nội bộ
ghim bảng kiểm chứng; API người dùng chọn theo cấu hình backend. T4 ghim bảng
vendor để giữ ý nghĩa kiểm tra chéo khi cấu hình ứng dụng đổi.

### Trường dữ liệu bổ sung

| Vị trí | Trường | Ý nghĩa |
|---|---|---|
| Raw chart, `thong_tin_co_ban`, `luu_nien` | `tu_hoa_table.id` | ID bảng đã chọn |
| Như trên | `tu_hoa_table.school` | Nhãn bảng/trường phái đang dùng |
| Như trên | `tu_hoa_table.source` | Nguồn cụ thể; URL tham khảo cố định theo commit |
| Như trên | `tu_hoa_table.verification_status` | Phân biệt baseline và tham khảo chưa xác minh |
| Như trên | `tu_hoa_table.signature` | SHA-256 của bảng cùng metadata; dùng tách cache |
| `features.tu_hoa[]` | `ten_sao` | Tên sao gốc nhận hóa; cung chứa sao này là cung an hóa |

Metadata đi vào prompt qua `thong_tin_co_ban` và `luu_nien` hiện có, không đổi
schema JSON của bài luận T1/T2. Cache bài luận chứa cả ID và signature bảng để
không dùng lại kết quả theo bảng khác. Fixture chung cũng kiểm tra các trường mới.

Tên Tả Phụ của bảng tham khảo được chuẩn hóa với cách viết Tả phù trong catalog;
vị trí Tả/Hữu hoặc các sao gốc không bị thay đổi khi đổi bảng Tứ Hóa.

