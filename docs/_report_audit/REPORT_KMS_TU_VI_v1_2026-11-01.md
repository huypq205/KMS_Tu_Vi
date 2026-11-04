# BÁO CÁO DỰ ÁN KMS TỬ VI
### Hệ thống Quản trị Tri thức (Knowledge Management System) về Tử Vi, có tầng ứng dụng LLM được kiểm soát trích dẫn

> **Môn học:** Quản trị Tri thức (KMS) — *[điền mã học phần / tín chỉ]*
> **Nhóm / Sinh viên:** *[điền tên các thành viên]*
> **Giảng viên phụ trách:** *[điền tên GV]*
> **Ngày báo cáo:** 01/11/2026
> **Phạm vi mã nguồn & số liệu:** repository `KMS_Tu_Vi` (số liệu trích trực tiếp từ DB `data/processed/kms.db`, cấu hình `configs/`, và tài liệu `docs/`).

---

## Tóm tắt (Abstract)

Dự án xây dựng một **hệ thống quản trị tri thức (KMS) cho lĩnh vực Tử Vi**, dựa trên 3 cuốn sách kinh điển (Nguyễn Phát Lộc, Bửu Đình, Đẩu Số Toàn Thư). Hệ thống **thu thập (capture)**, **cấu trúc hóa (organize)**, **lưu trữ (storage)**, **truy xuất (retrieval)** và **ứng dụng (application)** tri thức có dẫn nguồn, kèm cơ chế **quản trị chất lượng tri thức** (trust tier, kiểm tra trích dẫn, truy xuất gốc provenance).

Điểm then chốt: **LLM (Gemini) là tầng ứng dụng (Use), không phải nguồn tri thức.** Mô hình ngôn ngữ **chỉ tổng hợp từ ngữ cảnh đã truy xuất**, bị ràng buộc phải dẫn trích dẫn, và hệ thống **từ chối** khi không đủ căn cứ. Toàn bộ số liệu, kiến trúc, chỉ tiêu đánh giá và giới hạn được trình bày trung thực tại các mục sau.

---

## MỤC LỤC

1. [Đặt vấn đề & mục tiêu](#1-đặt-vấn-đề--mục-tiêu)
2. [Cơ sở lý thuyết Quản trị Tri thức](#2-cơ-sở-lý-thuyết-quản-trị-tri-thức)
3. [Tổng quan kiến trúc hệ thống](#3-tổng-quan-kiến-trúc-hệ-thống)
4. [Xây dựng & quản trị kho tri thức (Build – Hold)](#4-xây-dựng--quản-trị-kho-tri-thức-build--hold)
5. [Truy xuất tri thức (Pool)](#5-truy-xuất-tri-thức-pool)
6. [Ứng dụng tri thức & LLM (Use)](#6-ứng-dụng-tri-thức--llm-use)
7. [Đo lường chất lượng tri thức (Evaluation)](#7-đo-lường-chất-lượng-tri-thức-evaluation)
8. [Giới hạn & rủi ro](#8-giới-hạn--rủi-ro)
9. [Kết luận & hướng phát triển](#9-kết-luận--hướng-phát-triển)
- [Phụ lục A](#phụ-lục-a--tham-chiếu-mã-nguồn-và-cấu-hình) · [Phụ lục B](#phụ-lục-b--hướng-dẫn-chạy-hệ-thống) · [Phụ lục C](#phụ-lục-c--thuyết-minh-báo-cáo)

---

## 1. Đặt vấn đề & mục tiêu

### 1.1. Bài toán quản trị tri thức

Tri thức Tử Vi nằm rải trong **3 cuốn sách kinh điển với "ba tiếng nói" khác nhau** (cách giải nghĩa sao/cung không đồng nhất). Đây là **tri thức tường minh (explicit knowledge)** nhưng:

- Khó **tra cứu** theo cách người mới hỏi (dùng từ thông thường, không dùng thuật ngữ Hán–Việt).
- Khó **ứng dụng** cá nhân (diễn giải cho một lá số cụ thể) mà vẫn **có căn cứ, có nguồn, có kiểm soát**.
- Thiếu **cơ chế kiểm soát chất lượng**: nguồn OCR có thể sai, chưa được người duyệt, và AI có thể "bịa" (hallucinate).

### 1.2. Mục tiêu dự án

Xây dựng một KMS Tử Vi với các khả năng cốt lõi:

| # | Mục tiêu | Mức đạt (thực tế) |
|---|---|---|
| M1 | Thu thập & cấu trúc hóa kho tri thức từ 3 sách | **Đạt** — 10.456 bản ghi, 4.350 chunk, có metadata |
| M2 | Quản trị chất lượng tri thức (tier, provenance, citation) | **Đạt** — trust tier, citation validator, nhãn "chưa kiểm" |
| M3 | Truy xuất hybrid (từ khóa + ngữ nghĩa) | **Đạt (cơ bản)** — FTS5 + vector + RRF; dense index chưa phủ đủ |
| M4 | Ứng dụng tri thức: hỏi đáp học thuật + luận giải cá nhân | **Đạt (luồng chạy)** — RAG + Gemini, có fallback & abstention |
| M5 | Đo lường chất lượng tri thức | **Đạt (khung + baseline)** — hold-out FTS-only, chưa đạt ngưỡng mục tiêu |

> **Định vị quan trọng (cần nói rõ với giảng viên):** Sản phẩm là **một KMS có tầng ứng dụng LLM được kiểm soát trích dẫn**. LLM **không tạo ra tri thức canonical**, chỉ **diễn đạt lại** tri thức đã có trong kho — đúng nguyên tắc "không để LLM bịa nguồn".

---

## 2. Cơ sở lý thuyết Quản trị Tri thức

### 2.1. Vòng đời tri thức (Knowledge Lifecycle)

Một KMS phải khép kín (closed-loop) qua các giai đoạn: **tạo/thu thập → lưu trữ → tổ chức → truy xuất → ứng dụng → kiểm soát → đo lường**. Hệ thống của dự án phủ đủ 7 giai đoạn này (bảng ánh xạ ở §4–§7).

### 2.2. Chu trình KM của Wiig (Build – Hold – Pool – Use)

Đây là khung lý thuyết chính để **chứng minh "đúng môn KMS"**. J. Thomas Wiig (1997) mô hình hóa 4 công đoạn quản trị tri thức:

| Công đoạn Wiig | Định nghĩa | Thành phần tương ứng trong hệ thống | Bằng chứng (mã) |
|---|---|---|---|
| **Build** (xây dựng) | Thu thập, chuẩn hóa, tạo tri thức cấu trúc | Bóc 3 sách → làm sạch → 10.456 bản ghi → DB + FTS5 + Qdrant | `import_excel.py`, `data/processed/kms.db` |
| **Hold** (giữ) | Lưu trữ & bảo toàn tri thức, có cấu trúc | SQLite (bản ghi + evidence + trang), mô hình tri thức sách→chương→phần→chunk, trust tier, Qdrant vector | `db/models.py`, `chunks`, `evidences`, `chunks_fts` |
| **Pool** (hòa/tập hợp) | Phân phối, truy xuất, tổ chức lại tri thức phục vụ nhu cầu | Retriever hybrid (FTS5 + dense + RRF, top-N mỗi sách, lọc tier), sinh query theo lá số | `retriever.py`, `horoscope_rag_bridge.py`, `fts.py` |
| **Use** (sử dụng) | Ứng dụng tri thức thành giá trị cho người dùng | RAG + Gemini (hỏi đáp học thuật + luận giải), citation kiểm soát, mock fallback | `rag.py`, `horoscope_interpreter.py`, `citation_validator.py` |

> **Cách thuyết trình:** "Chúng tôi ánh xạ từng công đoạn Wiig vào mã nguồn thật — Build/Hold/Pool/Use đều có module và bằng chứng cụ thể, không chỉ lý thuyết."

### 2.3. Tri thức tường minh (explicit) vs tri thức ẩn (tacit)

- Hệ thống quản lý **tri thức tường minh** (nội dung sách đã mã hóa thành dữ liệu).
- **Tri thức ẩn** (kinh nghiệm thực tế của người đọc lá số) **chưa được mã hóa** — là giới hạn đã khai báo (§8) và hướng phát triển (vòng phản hồi tri thức).

### 2.4. Mô hình SECI (Nonaka & Takeuchi)

Hệ thống chủ yếu thực hiện **Combination** (kết hợp tri thức tường minh từ 3 nguồn thành ngữ cảnh có cấu trúc) và **Internalization** (người dùng lĩnh hội qua bài luận dễ hiểu). **Socialization/Externalization** (trao đổi & mã hóa tri thức ẩn) là hướng mở rộng.

### 2.5. Quản trị tri thức (Knowledge Governance)

KMS không chỉ "lưu–truy" mà phải **kiểm soát chất lượng & nguồn gốc**. Dự án có 4 lớp kiểm soát: **trust tier** (gating chất lượng nguồn), **provenance** (sách/chương/phần/trang), **citation validation** (kiểm trích dẫn), **abstention** (từ chối khi thiếu căn cứ). Chi tiết §4.5 & §6.

---

## 3. Tổng quan kiến trúc hệ thống

```
                          ┌─────────────────────────────────────────────┐
                          │        NGUỒN TRI THỨC (3 sách Tử Vi)        │
                          │  NPL (Nguyễn Phát Lộc) · BD (Bửu Đình)       │
                          │  DAU (Đẩu Số Toàn Thư)  — "ba tiếng nói"    │
                          └───────────────────────┬─────────────────────┘
                                                  │ Build: bóc tách + làm sạch
                                                  ▼
        ┌──────────────────────────────────────────────────────────────────┐
        │                  KHO TRI THỨC (HOLD) — SQLite `kms.db`           │
        │  10.456 knowledge_items · 10.492 evidences · 4.350 chunks       │
        │  trust_tier (gating) · provenance (sách/chương/phần/trang)       │
        │  FTS5 (không dấu) · Qdrant (vector, gemini-embedding-001)       │
        └───────────────┬───────────────────────────────┬────────────────┘
                        │ Pool: truy xuất               │ Pool: truy xuất
                        ▼                               ▼
        ┌───────────────────────────┐   ┌──────────────────────────────────┐
        │ Retriever HYBRID          │   │ RAG Bridge (horoscope)           │
        │ FTS5 + dense + RRF (k=60) │   │ sinh query theo tên sao/tổ hợp   │
        │ top-N mỗi sách, lọc tier  │   │ FTS5 trực tiếp (AND tên sao)     │
        └─────────────┬─────────────┘   └───────────────┬──────────────────┘
                      │ Use: RAG                        │ Use: RAG
                      ▼                                 ▼
        ┌───────────────────────────┐   ┌──────────────────────────────────┐
        │ POST /chat/ask            │   │ POST /horoscope/read(+stream)    │
        │ LLM grounded (Gemini)     │   │ LLM grounded (Gemini) + fact_ids │
        │ citation validator        │   │ an sao (deterministic) → features│
        │ abstention / out_of_scope │   │ JSON schema luận giải + mock     │
        └─────────────┬─────────────┘   └───────────────┬──────────────────┘
                      │                                 │
                      └───────────────┬─────────────────┘
                                      ▼
                          ┌───────────────────────────────┐
                          │  UI Streamlit (frontend/...)  │
                          │  báo cáo + lá số 12 cung +     │
                          │  thẻ nguồn (trích dẫn, tier)   │
                          └───────────────────────────────┘
```

> Ghi chú: **an sao** (thuật toán 108 sao, 12 cung, đại/tiểu hạn) là mã **xử lý tất định (deterministic), KHÔNG phải AI** — thuộc thư viện `vendor/lasotuvi`. AI chỉ xuất hiện ở bước **tổng hợp văn bản** (Use).

### 3.1. Hai luồng ứng dụng

| Luồng | Endpoint | Mục đích | Kỹ thuật LLM |
|---|---|---|---|
| **Hỏi đáp học thuật (KMS)** | `POST /api/v1/chat/ask` | Tra cứu nội dung 3 sách, trả lời **tách theo sách**, có trích dẫn | RAG pipeline: retrieval → ngưỡng → prompt → Gemini → kiểm citation |
| **Luận giải cá nhân** | `POST /api/v1/horoscope/read` (+ `-stream`) | Sinh bài luận từ lá số + ngữ cảnh sách, **dẫn `fact_id` & `source_refs`** | Gemini (prompt JSON schema) + fallback `mock` offline |

Ngoài ra: `POST /api/v1/search` (truy xuất thuần, không LLM), `GET /api/v1/stats`, `GET /api/v1/health`.

---

## 4. Xây dựng & quản trị kho tri thức (Build – Hold)

### 4.1. Nguồn dữ liệu

Ba sách nguồn, mỗi sách một "tiếng nói":

| Mã | Sách | Bản ghi active | Nguồn trích xuất | `Release_Status` |
|---|---|---|---|---|
| NPL | Nguyễn Phát Lộc | 2.191 | Extraction từ PDF (có cấu trúc SPO 100%) | `LOCKED_V1_0` |
| BD | Tử Vi Bửu Đình | 4.450 | Tesseract OCR (7 PDF, trang theo từng phần) | `DRAFT_NOT_RELEASED` |
| DAU | Đẩu Số Toàn Thư | 3.815 | Text layer (nhiều câu thơ/phú) | `DRAFT_NOT_RELEASED` |
| **Tổng** | | **10.456** | | |

> Nguyên tắc: **giữ 3 tiếng nói riêng**, không gộp/dung hòa nội dung giữa các sách — câu trả lời luôn "theo sách X".

### 4.2. Quy mô kho tri thức (số liệu thật từ `kms.db`)

| Thành phần | Số lượng |
|---|---|
| `knowledge_items` (bản ghi tri thức active) | **10.456** |
| `evidences` (bằng chứng đối chiếu trang) | **10.492** |
| `knowledge_pages` (liên kết bản ghi ↔ trang PDF) | **10.483** |
| `book_parts` (phần PDF; BD có 7 phần) | **9** |
| `id_redirects` (ID đã gộp trùng, tra về ID active) | **34** |
| `chunks` (đơn vị tri thức sau chunking) | **4.350** (NPL 2.191 · BD 1.189 · DAU 970) |
| `chunks_fts` (index từ khóa, bỏ dấu) | **4.350** |
| Qdrant vector (mô hình `gemini-embedding-001`, 1024-chiều) | **30** vector (chưa phủ đủ — xem §8) |
| `term_aliases` (từ điển alias) | **156** |
| `import_runs` (import idempotent, SHA-256) | **2** lần |

### 4.3. Mô hình tri thức (knowledge model)

- **Cấp phân tầng (hierarchy):** `books → book_parts → chapters → chunks`, mỗi chunk gắn `knowledge_id`, `trust_tier`, trang (đầu/cuối, kèm `part_number` cho BD).
- **Bản ghi tri thức** có cấu trúc `Subject–Predicate–Object` + `Condition_Context` + `text` (nội dung chính để embed/hiển thị) + metadata nguồn & trạng thái.
- **Chunking theo đơn vị tri thức:** NPL = 1 bản ghi/chunk; DAU & BD = gộp các bản ghi liền kề (cùng trang/chương, 150–600 ký tự) để tránh "bản ghi vụn".

### 4.4. Quản trị chất lượng nguồn — Trust Tier

Thay vì gate "approved + verified" (hiện **0** bản ghi có người duyệt), hệ thống **suy ra trust tier từ dữ liệu** bằng quy tắc trong `configs/column_mapping.yaml` (khớp quy tắc đầu tiên thắng, thực thi bởi `services/tiering.py`):

| Tier | Điều kiện | Số bản ghi | Chính sách index |
|---|---|---|---|
| **1** | Sách NPL | 2.191 | **Index** |
| **2** | Sách DAU (trừ `OCR_REVIEW_REQUIRED`) | 3.798 | **Index** |
| **3** | Sách BD (trừ `OCR_REVIEW_REQUIRED`) | 2.691 | **Index** (bật/tắt qua config) |
| **9** | `OCR_REVIEW_REQUIRED` (BD 1.759 + DAU 17) | 1.776 | **LOẠI khỏi index** |

- **Tổng bản ghi được index: 8.680.** Muốn chặt hơn chỉ cần đổi `enabled_tiers` trong YAML, **không sửa code** — đây là cơ chế **quản trị tri thức linh hoạt**.
- **`verification_status`** (mức xác minh thủ công) là một lớp **riêng**, mặc định `unverified`; UI hiển thị nhãn "chưa kiểm" — không ngụy trang dữ liệu là "đã duyệt".

### 4.5. Truy xuất gốc (provenance)

Mọi kết quả truy xuất và mọi trích dẫn đều mang: **sách (book_code) → phần (part_number) → chương → trang PDF (đầu/cuối) → trust_tier → verification_status → knowledge_ids**. Người dùng có thể đối chiếu ngược về trang sách gốc — nền tảng của **khuôn khổ KMS có kiểm soát nguồn**.

---

## 5. Truy xuất tri thức (Pool)

### 5.1. Retriever hybrid (luồng hỏi đáp KMS)

`services/retriever.py` kết hợp **hai nguồn xếp hạng** và gộp bằng **Reciprocal Rank Fusion (RRF, k = 60)**:

```
score(d) = Σ_rankers 1 / (k + rank(d))     với k = 60
```

Chiến lược (theo kế hoạch §4.2):
- Lấy **top-N ứng viên MỖI SÁCH** (tránh sách lớn áp đảo sách nhỏ) → **giữ "ba tiếng nói"**.
- Kết hợp **FTS5** (từ khóa, chịu lỗi dấu tiếng Việt) + **dense vector** (ngữ nghĩa, Qdrant).
- **Lọc theo trust_tier** (chỉ tier được `enabled_tiers`).
- Gộp kết quả, tra metadata từ SQLite, trả về `RetrievedChunk` (kèm `knowledge_ids`).

### 5.2. RAG Bridge (luận giải horoscope)

`services/horoscope_rag_bridge.py`:
- **Tự sinh câu hỏi** từ đặc trưng lá số: theo **cung trọng tâm** (Mệnh, Quan Lộc, Tài Bạch, Phu Thê), **đại hạn / tiểu hạn**, **Tứ Hóa**, **lưu niên**.
- Dùng **`AND` tên sao đầy đủ** (không dùng `OR` từng âm tiết) → **không lấy nhầm "Văn Khúc" khi hỏi "Vũ Khúc"**.
- Giữ **điều kiện tổ hợp** (Tuần/Triệt/đắc–hãm) trong truy vấn; **loại tier 9**.
- Mặc định lấy **2 đoạn chính mỗi chủ đề** + bổ sung đoạn cho sao chưa được đại diện; trích đoạn ≤ 500 ký tự gửi mô hình.

### 5.3. FTS5 tiếng Việt không dấu

`services/fts.py` — tìm kiếm **bỏ dấu** (chuẩn hóa NFD/NFC), chịu lỗi gõ sai dấu; là **baseline bắt buộc** cho mọi so sánh retrieval.

---

## 6. Ứng dụng tri thức & LLM (Use)

### 6.1. Nguyên tắc cốt lõi

> **LLM chỉ tổng hợp từ ngữ cảnh đã truy xuất, không tạo tri thức canonical.** Mọi đoạn sách truy xuất được coi là **dữ liệu, không phải chỉ thị** (chống prompt-injection).

### 6.2. Pipeline hỏi đáp KMS (`services/rag.py`)

Trật tự thực thi trong `RAGPipeline.ask()`:
1. **Cache tất định** (deterministic) — trùng câu hỏi + model + prompt-hash thì trả ngay.
2. **Phát hiện ngoài phạm vi (defense-in-depth layer 1)** — chặn yêu cầu "luận lá số / bói toán cá nhân" (trả `out_of_scope`).
3. **Truy xuất** ngữ cảnh (top-N mỗi sách, lọc ngưỡng RRF).
4. **Abstention** — không chunk nào vượt ngưỡng → trả `insufficient_evidence` (không để LLM phỏng đoán).
5. **Dựng prompt** (câu hỏi + ngữ cảnh đánh số `[1]…`, kèm metadata sách/phần/trang/tier).
6. **Gọi LLM (Gemini)** — tổng hợp **tách theo sách**, giọng "theo sách", không lời khuyên y khoa/tài chính.
7. **Kiểm citation** (`citation_validator.py`) — mọi `[n]` phải tồn tại trong ngữ cảnh; phát hiện câu không dẫn nguồn; loại citation giả.
8. Trả JSON (kèm `citations`, `retrieval`, `citation_check`, `request_id`).

`status ∈ {answered, insufficient_evidence, out_of_scope, error}`.

### 6.3. Kiểm tra trích dẫn (`services/citation_validator.py`)

Kiểm **3 điều**:
1. Mọi số `[n]` trong câu trả lời **phải tồn tại** trong ngữ cảnh đã đưa cho LLM.
2. Phát hiện **câu có nội dung nhưng không kèm trích dẫn**.
3. Trích dẫn phải thuộc **đúng sách/phần/trang** đã khai báo.

### 6.4. Luận giải cá nhân (`services/horoscope_interpreter.py`)

- **An sao + feature extraction là tất định** (không AI).
- **Prompt** chỉ chứa: dữ kiện lá số (đã loại mọi trường văn mẫu tĩnh), `fact_ids`, và ngữ cảnh sách. Hệ thống **cấm** dùng kiến thức ngoài nguồn.
- **JSON schema đầu ra** có `luan_diem` liên kết `fact_ids` + `source_refs` (phải khớp thực tế trong ngữ cảnh).
- **Kiểm độ cụ thể** (`check_specificity`): bắt tối thiểu 3 `fact_id` khác nhau, phần vận trình phải nhắc đúng năm/can chi → gọi **thêm 1 lần** nếu thiếu.
- **Fallback `mock` offline** (báo cáo dữ kiện thật, không bịa dự báo) khi thiếu key / lỗi dịch vụ; UI **phân biệt rõ** AI với mock.

### 6.5. Provider & cấu hình LLM

| Luồng | Biến | Mặc định |
|---|---|---|
| Hỏi đáp KMS (`/chat/ask`) | `KMS_GEMINI_MODEL` | `gemini-3.8-flash` |
| Luận giải (horoscope) | `KMS_HOROSCOPE_MODEL` | `gemini-3.5-flash-lite` |

`temperature = 0.0`; horoscope: timeout 45s, max tokens 2.500, gọi tối đa 2 lần, có cache theo (lá số + năm + model + hash ngữ cảnh).

---

## 7. Đo lường chất lượng tri thức (Evaluation)

### 7.1. Bộ chỉ tiêu (theo khung KMS)

| Chỉ tiêu | Định nghĩa | Mục tiêu (đề xuất, **chưa phải kết quả**) |
|---|---|---|
| **Recall@5** | Tỷ lệ câu có ≥1 evidence đúng trong top-5 | ≥ 0.80 |
| **MRR** | Trung bình nghịch vị trí của kết quả đúng đầu tiên | cao nhất có thể |
| **Cross-book leakage** | Kết quả tràn sang sách sai (vi phạm "ba tiếng nói") | = 0 |
| **Abstention accuracy** | Từ chối đúng câu thiếu căn cứ / ngoài phạm vi, không từ chối thừa | = 1.0 |
| **Citation validity** | Tỷ lệ trích dẫn trỏ tới ngữ cảnh có thật (về sự tồn tại) | = 100% |
| **Groundedness/faithfulness** | Tỷ lệ luận điểm được ngữ cảnh hỗ trợ (chấm tay / Ragas) | đánh giá thủ công |

### 7.2. Kết quả hiện có (trung thực)

| Kết quả | Giá trị | Ghi chú quan trọng |
|---|---|---|
| **FTS-only, hold-out 20 câu** — Recall@5 | **0.5882** | Đây là điểm của **FTS (từ khóa)**, KHÔNG phải của LLM hay embedding |
| **FTS-only** — MRR | **0.5** | |
| **FTS-only** — Cross-book leakage | **0** | ✅ Giữ đúng "ba tiếng nói" |
| **FTS-only** — Abstention accuracy | **1.0** | ✅ Từ chối đúng |
| Regression suite `pytest tests/` | **74 passed** (chạy 01/11/2026) | Luồng kỹ thuật & hiển thị mock đã kiểm |
| Index vector Qdrant | **30/4.350** chunk | ⚠️ Chưa phủ đủ — không kết luận tìm kiếm ngữ nghĩa đã sẵn sàng |

> **Cách đọc số 0.5882 với giảng viên:** "Recall FTS-only trên hold-out mới là 0.588, **dưới** ngưỡng mục tiêu 0.8. Đây là **baseline trung thực**, chưa phải kết quả cuối; kế tiếp là bật dense + hybrid, đo lại trên cùng bộ câu để so sánh." **Không** được trình bày con số này như "đã đạt".

### 7.3. Nghiệm thu UI (mock)

`pytest` **74 passed, 1 skipped**; kiểm tra trình duyệt (desktop/tablet/mobile, 1440/768/390px) với **provider mock**: mở đủ 12 cung + 10 nguồn, không tràn ngang, không lỗi JS. → **chứng minh luồng kỹ thuật**, **không** chứng minh chất lượng Gemini thật.

---

## 8. Giới hạn & rủi ro

Trình bày trung thực (nên nói trước, không đợi GV hỏi):

| # | Giới hạn / rủi ro | Kiểm soát hiện có | Việc cần làm |
|---|---|---|---|
| 1 | **LLM có thể diễn đạt sai** nội dung sách, bịa quan hệ nhân quả | Prompt ràng buộc bám ngữ cảnh; citation validator; abstention | Đo **groundedness/citation support** trên Gemini thật; kiểm thủ công từng nhận định |
| 2 | **Nguồn OCR (BD) có thể sai chính tả/dấu**, chưa người duyệt | Trust tier (loại tier 9), nhãn "chưa kiểm" trên UI | Kiểm mẫu theo trang PDF, sửa OCR, ghi `verification_status` |
| 3 | **Tri thức ẩn chưa mã hóa** (vòng đời một chiều) | — | Thiết kế **vòng phản hồi** (user/expert nạp tri thức & xác minh về KMS) — hướng phát triển |
| 4 | **Dense index chưa phủ đủ** (30/4.350 vector) | FTS5 làm baseline; hybrid fallback bỏ dense khi index rỗng | Build đủ vector, **đo lại Recall** trên cùng bộ câu |
| 5 | **Recall@5 còn thấp** (0.588 < 0.8 mục tiêu) | Baseline FTS-only trung thực | Reranker / cải thiện chunking / embedding tiếng Việt tốt hơn |
| 6 | **Chất lượng Gemini thật chưa nghiệm thu** | Mock + nhãn rõ | Chạy nghiệm thu nội dung + an toàn trên bộ lá số biên (Giai đoạn 6) |
| 7 | **Quyền riêng tư**: ngày giờ sinh gửi đến nhà cung cấp AI khi chọn Gemini | Có chế độ mock không gọi AI | Rà soát chính sách dữ liệu, thông báo người dùng trước triển khai công khai |

---

## 9. Kết luận & hướng phát triển

### 9.1. Kết luận

- Hệ thống là **một KMS Tử Vi đúng nghĩa**, phủ đủ vòng đời tri thức và **ánh xạ 4 công đoạn Wiig (Build–Hold–Pool–Use) vào mã nguồn có bằng chứng** (mục 2.2).
- Giá trị KMS rõ nhất nằm ở **quản trị tri thức**: kho dữ liệu có cấu trúc, **trust tier**, **provenance**, **citation validation** và **abstention** — những thứ phân biệt KMS với một chatbot thường.
- LLM được đặt đúng vai trò **tầng ứng dụng có kiểm soát**, không phải nguồn tri thức.
- Các số đo hiện có được trình bày **trung thực** (Recall FTS-only 0.588, index vector chưa đủ) — không phóng đại thành kết quả đã đạt.

### 9.2. Hướng phát triển

1. **Xây đủ dense index** (embedding tiếng Việt tốt) và **đo lại Recall** FTS vs dense vs hybrid trên cùng golden set.
2. **Vòng phản hồi tri thức**: người dùng/chuyên gia xác minh, sửa, nạp tri thức mới → nâng `verification_status` (hoàn thiện SECI: Externalization/Internalization).
3. **Reranker** (bổ sung khi Recall@5 chưa đạt) và bộ **golden set 40–50 câu** (một phần do người chưa xem đáp án viết).
4. **Nghiệm thu chất lượng & an toàn Gemini thật** (Giai đoạn 6: kiểm mẫu lá số biên, bộ ca gây nhiễu, tiêu chí an toàn nội dung).
5. **Reranker/alias** cho thuật ngữ Hán–Việt; xử lý nhập nhằng ("Tử Vi" là sao hay môn học).

---

## PHỤ LỤC A — Tham chiếu mã nguồn & cấu hình

| Khía cạnh KMS | File |
|---|---|
| Plan tổng thể KMS (khuôn Wiig, SECI, golden set, DoD) | `KMS_TuVi_Development_Plan.md` |
| Schema DB & bảng | `backend/app/db/models.py` |
| Trust tier & mapping cột Excel | `configs/column_mapping.yaml`, `backend/app/services/tiering.py` |
| Retrieval (hybrid, RRF, FTS5) | `backend/app/services/retriever.py`, `fts.py` |
| RAG hỏi đáp KMS | `backend/app/services/rag.py` |
| Kiểm trích dẫn | `backend/app/services/citation_validator.py` |
| Provider LLM (Gemini/mock) | `backend/app/services/llm_provider.py` |
| Luận giải horoscope | `backend/app/services/horoscope_interpreter.py`, `horoscope_features.py`, `horoscope_rag_bridge.py`, `horoscope_service.py` |
| Vector / embedding | `backend/app/services/vector_store_qdrant.py`, `embeddings.py`, `gemini_embeddings.py` |
| API (FastAPI) | `backend/app/main.py` |
| UI Streamlit | `frontend/horoscope_ui.py`, `frontend/lasoban.py` |
| Chạy hệ thống | `docs/RUN_HOROSCOPE.md` |
| Báo cáo sử dụng AI (trung thực) | `docs/BAO_CAO_SU_DUNG_AI.md` |
| Cấu hình runtime | `backend/app/core/config.py`, `.env.example` |

## PHỤ LỤC B — Hướng dẫn chạy hệ thống

Chi tiết trong `docs/RUN_HOROSCOPE.md`. Tóm tắt (Windows PowerShell, từ gốc repo):

```powershell
# 1) Tạo môi trường
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-horoscope.txt

# 2) Terminal 1 — backend (API FastAPI)
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 3) Terminal 2 — UI Streamlit
./.venv/Scripts/python.exe -m streamlit run frontend/horoscope_ui.py --server.address 127.0.0.1 --server.port 8502
```

Cần DB `data/processed/kms.db` đã import/index để xem nguồn sách. Khuyên demo: chạy chế độ **mock** (không cần API key, chạy offline) để trình bày luồng + nguồn; chạy chế độ **AI** khi có `GEMINI_API_KEY`.

## PHỤ LỤC C — Thuyết minh báo cáo

- **Nguồn số liệu:** trích trực tiếp từ `kms.db` (đếm bảng) và `configs/`, `data/processed/index_manifest.json`; kết quả test là lệnh `python -m pytest tests/` chạy ngày 01/11/2026.
- **Nguyên tắc trình bày:** phân biệt rõ (a) thành phần **xử lý thông thường** (an sao, FTS5, citation validator, UI) với (b) **AI tạo sinh** (Gemini tổng hợp văn bản); và (c) **chưa nghiệm thu** (chất lượng Gemini thật, dense index, Recall mục tiêu).
- **Tránh các tuyên bố vượt bằng chứng:** không gọi bài luận là "đã được sách chứng minh" (nguồn mới là ngữ cảnh đưa cho mô hình); không tuyên bố tìm kiếm ngữ nghĩa "đã triển khai đầy đủ" khi vector index mới có 30/4.350.

---

## Gợi ý khi THUYẾT TRÌNH trước giảng viên (kèm theo, không nằm trong báo cáo)

1. **Mở đầu bằng khung KMS** (Wiig Build–Hold–Pool–Use), không phải bằng "bói toán".
2. **Đổ spotlight** vào 4 lớp quản trị tri thức: trust tier → provenance → citation validation → abstention.
3. **Nói trước các giới hạn** (OCR chưa duyệt, Recall 0.588, vector index chưa đủ, chất lượng Gemini chưa nghiệm thu) → ăn điểm trung thực.
4. **Kịch bản demo 5–7 phút** (theo plan §11): mở bảng thống kê tier → mở 1 bản ghi đối chiếu PDF → hỏi đúng thuật ngữ → hỏi cách nói thông thường (hybrid) → hỏi so sánh 2 sách (tách tiếng nói) → hỏi câu ngoài dữ liệu + yêu cầu luận cá nhân (hệ thống từ chối) → chỉ Wiig Build/Hold/Pool/Use.
