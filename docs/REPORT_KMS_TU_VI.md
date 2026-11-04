# BÁO CÁO DỰ ÁN KMS TỬ VI
### Hệ thống Quản trị Tri thức (Knowledge Management System) về Tử Vi, có tầng ứng dụng LLM được kiểm soát trích dẫn và lớp quản trị tri thức

> **Môn học:** Quản trị Tri thức (KMS) — *[điền mã học phần / tín chỉ]*
> **Nhóm / Sinh viên:** *[điền tên các thành viên]*
> **Giảng viên phụ trách:** *[điền tên GV]*
> **Ngày báo cáo:** 05/11/2026 — phiên bản 2.0 (cập nhật theo trạng thái dự án hiện tại)
> **Phạm vi mã nguồn & số liệu:** repository `KMS_Tu_Vi`, commit `b163d37` và các thay đổi đang có trong working tree tại thời điểm chụp số liệu (05/11/2026). Số liệu trích trực tiếp từ DB `data/processed/kms.db` (truy vấn chỉ đọc), `configs/`, `data/processed/index_manifest.json`, kết quả `pytest` và tài liệu `docs/`.

---

## Tóm tắt (Abstract)

Dự án xây dựng một **hệ thống quản trị tri thức (KMS) cho lĩnh vực Tử Vi**, dựa trên 3 cuốn sách kinh điển (Nguyễn Phát Lộc, Bửu Đình, Đẩu Số Toàn Thư). Hệ thống **thu thập (capture)**, **cấu trúc hóa (organize)**, **lưu trữ (storage)**, **truy xuất (retrieval)** và **ứng dụng (application)** tri thức có dẫn nguồn, kèm một **lớp quản trị chất lượng tri thức** gồm: cổng kiểm duyệt đầu vào, trust tier, provenance, từ điển loại chứng cứ, kiểm trích dẫn, kiểm độ chắc chắn của đầu ra và nhật ký nghiệm lý có khóa dự đoán.

Điểm then chốt: **LLM là tầng ứng dụng (Use), không phải nguồn tri thức.** Mô hình ngôn ngữ **chỉ tổng hợp từ ngữ cảnh đã truy xuất**, bị ràng buộc phải dẫn trích dẫn, bị kiểm tra cấu trúc đầu ra và **từ chối** khi không đủ căn cứ. Hệ thống hiện hỗ trợ **4 nhà cung cấp LLM** (mock, Gemini, DeepSeek, Groq) với chuỗi dự phòng, nhưng mọi nhà cung cấp đều dùng chung một khuôn kiểm soát: ngữ cảnh truy xuất là nguồn duy nhất, mọi kết luận phải mang nhãn chứng cứ và phản chứng.

Báo cáo trình bày trung thực cả phần đã đạt và phần chưa đạt: kho tri thức 10.456 bản ghi với 4.350 chunk đã được kiểm bằng cổng tri thức; 17 endpoint API; giao diện 3 trang; nhật ký nghiệm lý bất biến. Các điểm còn yếu được nêu rõ ở §8: vector index mới có 30/4.350 chunk, Recall@5 của FTS-only là 0,5882 (dưới ngưỡng mục tiêu 0,8), 351 sai khác an sao đã biết, và tại thời điểm chụp số liệu **7–16 ca kiểm thử còn đỏ tùy cấu hình môi trường** (đã nêu nguyên nhân cụ thể).

---

## MỤC LỤC

1. [Đặt vấn đề & mục tiêu](#1-đặt-vấn-đề--mục-tiêu)
2. [Cơ sở lý thuyết Quản trị Tri thức](#2-cơ-sở-lý-thuyết-quản-trị-tri-thức)
3. [Tổng quan kiến trúc hệ thống](#3-tổng-quan-kiến-trúc-hệ-thống)
4. [Xây dựng & quản trị kho tri thức (Build – Hold)](#4-xây-dựng--quản-trị-kho-tri-thức-build--hold)
5. [Truy xuất tri thức (Pool)](#5-truy-xuất-tri-thức-pool)
6. [Ứng dụng tri thức & LLM (Use)](#6-ứng-dụng-tri-thức--llm-use)
7. [Đo lường & nghiệm thu chất lượng tri thức](#7-đo-lường--nghiệm-thu-chất-lượng-tri-thức)
8. [Giới hạn & rủi ro](#8-giới-hạn--rủi-ro)
9. [Kết luận & hướng phát triển](#9-kết-luận--hướng-phát-triển)
- [Phụ lục A](#phụ-lục-a--tham-chiếu-mã-nguồn-và-cấu-hình) · [Phụ lục B](#phụ-lục-b--hướng-dẫn-chạy-hệ-thống) · [Phụ lục C](#phụ-lục-c--thuyết-minh-số-liệu-và-phương-pháp) · [Phụ lục D](#phụ-lục-d--ma-trận-nghiệm-thu-tri-thức-t1t11-và-p1p8) · [Phụ lục E](#phụ-lục-e--nhật-ký-cập-nhật-báo-cáo-v10--v20)

---

## 1. Đặt vấn đề & mục tiêu

### 1.1. Bài toán quản trị tri thức

Tri thức Tử Vi nằm rải trong **3 cuốn sách kinh điển với "ba tiếng nói" khác nhau** (cách giải nghĩa sao/cung không đồng nhất). Đây là **tri thức tường minh (explicit knowledge)** nhưng có bốn vấn đề quản trị:

- Khó **tra cứu** theo cách người mới hỏi (dùng từ thông thường, không dùng thuật ngữ Hán–Việt).
- Khó **ứng dụng** cá nhân (diễn giải cho một lá số cụ thể) mà vẫn **có căn cứ, có nguồn, có kiểm soát**.
- Thiếu **cơ chế kiểm soát chất lượng đầu vào**: nguồn OCR có thể sai (sách Bửu Đình là bản OCR), chưa có người duyệt, và các ý kiến diễn đàn/video không được trộn với sách.
- Thiếu **cơ chế kiểm soát chất lượng đầu ra**: LLM có thể "bịa" quan hệ nhân quả, tự thêm cách cục, hoặc biến một tín hiệu thành lời tiên đoán chắc chắn.

Báo cáo phiên bản trước (01/11/2026) đã xử lý ba vấn đề đầu. Phiên bản 2.0 này bổ sung toàn bộ phần đã triển khai sau đó: **cổng tri thức đầu vào (T7), từ điển chứng cứ (T3), chính sách giờ sinh A–D (T1), nhật ký nghiệm lý (T8), hồ sơ sao có nguồn (T6), vận năm bốn tầng (T9), skill đóng gói tri thức (T10)** và **các gói P1–P5 của kế hoạch cải tiến chất lượng luận giải**.

### 1.2. Mục tiêu dự án và mức đạt hiện tại

| # | Mục tiêu | Mức đạt (thực tế 05/11/2026) |
|---|---|---|
| M1 | Thu thập & cấu trúc hóa kho tri thức từ 3 sách | **Đạt** — 10.456 bản ghi, 4.350 chunk, 10.492 evidence, có metadata và trang PDF |
| M2 | Quản trị chất lượng tri thức đầu vào (tier, gate, provenance) | **Đạt** — trust tier 4 mức, cổng tri thức T7 (điều kiện A/B/C, quarantine nguồn D), nhãn "chưa kiểm" |
| M3 | Truy xuất hybrid (từ khóa + ngữ nghĩa) | **Đạt (cơ bản)** — FTS5 + vector + RRF; dense index mới phủ 30/4.350 chunk |
| M4 | Ứng dụng tri thức: hỏi đáp, luận giải, hồ sơ sao, vận năm | **Đạt (luồng chạy)** — 17 endpoint, 3 trang giao diện, 4 provider LLM, có fallback & abstention |
| M5 | Kiểm soát chất lượng đầu ra (chứng cứ, tin cậy, an toàn) | **Đạt** — 10 loại chứng cứ, phản chứng bắt buộc, 4 bậc tin cậy, chính sách C/D, lọc nội dung nhạy cảm |
| M6 | Nghiệm lý có khóa dự đoán | **Đạt (khung)** — 3 bảng bất biến, 7 endpoint, chưa đủ 30 ca thật để mở thống kê |
| M7 | Đo lường & đóng gói tri thức (skill, changelog) | **Đạt (khung + baseline)** — golden set 20 câu FTS-only, 42 file test, skill `tu-vi-kms` v1.0 |

> **Định vị cần nói rõ với giảng viên:** sản phẩm là **một KMS có tầng ứng dụng LLM được kiểm soát trích dẫn**. LLM **không tạo ra tri thức canonical**, chỉ **diễn đạt lại** tri thức đã có trong kho — đúng nguyên tắc "không để LLM bịa nguồn". Việc hỗ trợ nhiều nhà cung cấp mô hình (Gemini, DeepSeek, Groq, mock) **không** làm thay đổi nguyên tắc này: đổi nhà cung cấp chỉ đổi bộ diễn đạt, không đổi nguồn.

---

## 2. Cơ sở lý thuyết Quản trị Tri thức

### 2.1. Vòng đời tri thức (Knowledge Lifecycle)

Một KMS phải khép kín (closed-loop) qua các giai đoạn: **tạo/thu thập → lưu trữ → tổ chức → truy xuất → ứng dụng → kiểm soát → đo lường**. Hệ thống hiện phủ đủ 7 giai đoạn và đã bổ sung **vòng nghiệm lý** (ghi nhận kết quả đối chiếu sau khi sự kiện xảy ra) như bước đầu của vòng phản hồi:

| Giai đoạn | Nơi thực hiện | Bằng chứng |
|---|---|---|
| Tạo / thu thập | Import workbook canonical + cổng tri thức | `scripts/import_excel.py`, `services/knowledge_gate.py` |
| Lưu trữ | SQLite + FTS5 + Qdrant | `data/processed/kms.db`, `db/models.py` |
| Tổ chức | Mô hình sách → phần → chương → chunk; trust tier; taxonomy | `services/chunker.py`, `services/tiering.py` |
| Truy xuất | Retriever hybrid, RAG bridge, hồ sơ sao, dữ kiện vận năm | `services/retriever.py`, `horoscope_rag_bridge.py`, `star_dossier.py` |
| Ứng dụng | 3 mức đọc, 4 provider, 3 trang giao diện | `services/horoscope_interpreter.py`, `frontend/` |
| Kiểm soát | 6 lớp kiểm soát (mục 2.5) + nhật ký nghiệm lý | `horoscope_confidence.py`, `case_validation.py` |
| Đo lường | Golden set, cross-check an sao, bộ test, CI | `docs/BAO_CAO_SU_DUNG_AI.md`, `tests/`, `.github/workflows/test.yml` |

### 2.2. Chu trình KM của Wiig (Build – Hold – Pool – Use)

Đây là khung lý thuyết chính để **chứng minh "đúng môn KMS"**. J. Thomas Wiig (1997) mô hình hóa 4 công đoạn quản trị tri thức:

| Công đoạn Wiig | Định nghĩa | Thành phần tương ứng trong hệ thống | Bằng chứng (mã) |
|---|---|---|---|
| **Build** (xây dựng) | Thu thập, chuẩn hóa, tạo tri thức cấu trúc | Bóc 3 sách → làm sạch → 10.456 bản ghi → gate T7 → DB + FTS5 + Qdrant | `scripts/import_excel.py`, `knowledge_gate.py`, `chunker.py` |
| **Hold** (giữ) | Lưu trữ & bảo toàn tri thức, có cấu trúc | SQLite 17 bảng nghiệp vụ, `chunk_members`, trust tier, evidence gốc, audit sample, journal bất biến | `db/models.py`, `case_validation.py` |
| **Pool** (hòa/tập hợp) | Phân phối, truy xuất, tổ chức lại tri thức theo nhu cầu | Retriever hybrid (FTS5 + dense + RRF), RAG bridge, hồ sơ sao 14 nhóm, dữ kiện vận năm 4 tầng | `retriever.py`, `horoscope_rag_bridge.py`, `star_dossier.py`, `horoscope_annual.py` |
| **Use** (sử dụng) | Ứng dụng tri thức thành giá trị cho người dùng | 3 mức đọc; 4 provider LLM; kiểm chứng cứ/tin cậy/citation; mock offline; UI 3 trang | `horoscope_interpreter.py`, `llm_provider.py`, `citation_validator.py`, `app.py` |

> **Cách thuyết trình:** "Chúng tôi ánh xạ từng công đoạn Wiig vào mã nguồn thật — Build/Hold/Pool/Use đều có module và bằng chứng cụ thể, không chỉ lý thuyết."

### 2.3. Tri thức tường minh (explicit) vs tri thức ẩn (tacit)

- Hệ thống quản lý **tri thức tường minh** (nội dung sách đã mã hóa thành dữ liệu).
- **Tri thức ẩn** (kinh nghiệm thực tế của người đọc lá số) **chưa được mã hóa**. Bước tiến mới: **nhật ký nghiệm lý (T8)** cho phép người dùng ghi nhận định có điều kiện, khóa dự đoán trước khi biết kết quả và ghi lại đối chiếu — nhưng đây mới là **dữ liệu quan sát**, chưa tự động nâng `verification_status` của tri thức canonical. Đây là giới hạn đã khai báo (§8) và hướng phát triển.

### 2.4. Mô hình SECI (Nonaka & Takeuchi)

Hệ thống chủ yếu thực hiện **Combination** (kết hợp tri thức tường minh từ 3 nguồn thành ngữ cảnh có cấu trúc, nay kèm danh mục 30 cách cục và 2 bảng Tứ Hóa có nguồn) và **Internalization** (người dùng lĩnh hội qua 3 mức đọc, từ "lá số & dữ kiện" đến "AI chuyên sâu"). **Socialization/Externalization** (trao đổi & mã hóa tri thức ẩn) mới được hỗ trợ một phần qua nhật ký nghiệm lý; vòng quay lại kho tri thức canonical **chưa** khép kín.

### 2.5. Quản trị tri thức (Knowledge Governance)

KMS không chỉ "lưu–truy" mà phải **kiểm soát chất lượng & nguồn gốc**. Phiên bản hiện tại có **6 lớp kiểm soát**, mỗi lớp có mã nguồn riêng:

| Lớp | Câu hỏi được trả lời | Cơ chế |
|---|---|---|
| **1. Cổng đầu vào (T7)** | Bản ghi mới có đủ căn cứ để vào kho? | Điều kiện A (dẫn nguồn + trang) HOẶC B (trường phái) HOẶC C (ca kiểm chứng); quarantine nguồn FORUM/VIDEO |
| **2. Trust tier** | Nguồn này được tin đến mức nào? | 4 tier từ `configs/column_mapping.yaml`; tier 9 bị loại khỏi index |
| **3. Provenance & evidence (T3)** | Kết luận dựa trên đoạn sách nào, trang nào? | Chuỗi sách → phần → chương → trang PDF; 10 loại chứng cứ; phản chứng bắt buộc |
| **4. Kiểm soát sinh văn bản (T1/T2/P3)** | Bài luận có vi phạm chính sách không? | Chính sách giờ sinh A–D; 4 bậc tin cậy; chặn cách cục do AI tự thêm; lọc nội dung nhạy cảm |
| **5. Citation & abstention** | Câu trả lời có trích dẫn thật không? | `citation_validator.py`: 3 điều kiện; ngưỡng RRF để từ chối trả lời |
| **6. Nghiệm lý (T8)** | Dự đoán đã khóa có đúng không? | Journal append-only, trigger SQLite, ngưỡng 30 ca trước khi thống kê |

> **Cách thuyết trình:** đây là **6 lớp phân biệt KMS với một chatbot**: chatbot chỉ có lớp 4 (văn bản hay/dở); KMS có thêm 5 lớp quản trị nguồn, chứng cứ và nghiệm lý.

### 2.6. Sản phẩm tri thức (knowledge products) và đóng gói dịch vụ

Ngoài luồng hỏi đáp, hệ thống đã tách **các sản phẩm tri thức độc lập, chạy không cần LLM** — đúng hướng "tri thức là dịch vụ" của KMS:

| Sản phẩm | Nội dung | API | Dùng LLM |
|---|---|---|---|
| Hỏi đáp theo sách | Trả lời tách theo 3 sách, có trích dẫn | `POST /api/v1/chat/ask` | Có |
| Luận giải lá số | Bài luận 7 khối + dẫn `fact_id`/nguồn | `POST /api/v1/horoscope/read` | Có |
| Hồ sơ sao (T6) | 14 nhóm hiển thị, tách tiếng nói từng sách, 20 seed tham khảo | `GET /api/v1/stars/{ten}/dossier` | **Có** |
| Dữ kiện vận năm (T9) | Bảng 4 tầng, so năm ±1, việc chưa đủ căn cứ | `POST /api/v1/horoscope/annual` | **Có** |
| Nhật ký nghiệm lý (T8) | Ca ẩn danh, dự đoán khóa, đối chiếu kết quả | 7 endpoint `/api/v1/validation/*` | **Có** |
| Skill cho tác tử (T10) | Gói hướng dẫn dùng API, 4 chế độ, MIT | `skills/tu-vi-kms` | **Có** |

---

## 3. Tổng quan kiến trúc hệ thống

### 3.1. Sơ đồ luồng tri thức

```text
NGUỒN TRI THỨC: 3 sách Tử Vi (NPL · BD · DAU)
+ tài liệu tham khảo từ bộ skill (ngoài canonical, có gán nguồn)
        │
        │  BUILD — import_excel.py + knowledge_gate.py (T7)
        ▼
├─ HOLD — data/processed/kms.db (17 bảng nghiệp vụ + 6 bảng FTS5)
│    10.456 knowledge_items · 10.492 evidences · 4.350 chunks
│    chunk_members 8.680 · audit_samples 300 · trust tier 1/2/3/9
│    chunks_fts 4.350 · Qdrant vector 30/4.350 chunk đã embed
        │
        │  POOL — truy xuất, không gọi LLM
        ▼
├─ Retriever hybrid: FTS5 + dense + RRF k=60, top-10 mỗi sách
│  RAG bridge: AND tên sao đầy đủ, tier 1–3, tối đa 22 chunk
│  Hồ sơ sao 14 nhóm · Vận năm 4 tầng · Nhật ký nghiệm lý
        │
        │  USE — gọi LLM có kiểm soát (hoặc không gọi LLM)
        ▼
├─ 3 mức đọc: du_lieu · giai_thich · chuyen_sau
│  Provider: mock | gemini | deepseek | groq (chuỗi dự phòng)
│  Kiểm soát: chứng cứ + phản chứng · 4 bậc tin cậy · C/D
│  Citation validator · lọc nội dung nhạy cảm · cache v8
        │
        ▼
GIAO DIỆN — app.py, 3 trang:
  Luận giải lá số (7 khối + lá số 12 cung) · Hồ sơ sao · Nhật ký nghiệm lý
```

> Ghi chú: **an sao** (thuật toán 108 sao, 12 cung, đại/tiểu hạn) là mã **xử lý tất định (deterministic), KHÔNG phải AI** — thuộc thư viện `vendor/lasotuvi`. AI chỉ xuất hiện ở bước **tổng hợp văn bản** (Use). Nhật ký nghiệm lý và bảng vận năm **không gọi LLM**.

### 3.2. Bề mặt API hiện tại (17 endpoint)

Hệ thống có **17 route API** (đếm bằng `app.openapi()`): 7 route khai báo trực tiếp trong `backend/app/main.py`, 3 route trong `api/governance.py`, 7 route trong `api/case_validation.py`.

| # | Phương thức & đường dẫn | Mục đích | Dùng LLM |
|---|---|---|---|
| 1 | `GET /api/v1/health` | Kiểm tra DB: đếm `knowledge_items`, `chunks` | Không |
| 2 | `POST /api/v1/search` | Truy xuất thuần (FTS/dense, RRF), trả `citations` + `ui_badge` | Không |
| 3 | `GET /api/v1/stats` | Thống kê bản ghi theo tier/sách, số chunk, số dòng FTS | Không |
| 4 | `POST /api/v1/chat/ask` | Hỏi đáp RAG trên 3 sách, kiểm citation, abstention | Có |
| 5 | `POST /api/v1/horoscope/read` | Lập lá số + truy xuất nguồn + luận giải (trả kết quả cuối) | Có |
| 6 | `POST /api/v1/horoscope/read-stream` | Như trên nhưng stream NDJSON: `progress`, `chart_ready`, `prepared`, `result`, `error` | Có |
| 7 | `POST /api/v1/horoscope/ask` | Hỏi nhanh 1 chủ đề (5 chủ đề), 1 lần sinh JSON + mock | Có |
| 8 | `POST /api/v1/horoscope/annual` | Dữ kiện vận năm 4 tầng, so năm ±1 — **không truy xuất sách** | Không |
| 9 | `GET /api/v1/stars/{ten}/dossier` | Hồ sơ sao 14 nhóm; `include_seeds=false` mặc định | Không |
| 10 | `GET /api/stars/{ten}/dossier` | Alias tương thích của #9 | Không |
| 11 | `POST /api/v1/validation/cases` | Tạo ca nghiệm lý ẩn danh (snapshot bất biến) | Không |
| 12 | `GET /api/v1/validation/cases/{cid}` | Đọc ca + dự đoán + kết quả | Không |
| 13 | `POST /api/v1/validation/cases/{cid}/predictions` | Ghi dự đoán nháp trước khi xảy ra | Không |
| 14 | `POST /api/v1/validation/predictions/{pid}/lock` | Khóa dự đoán (bất biến) | Không |
| 15 | `POST /api/v1/validation/predictions/{pid}/revisions` | Tạo phiên bản mới kèm `supersedes` và lý do | Không |
| 16 | `POST /api/v1/validation/cases/{cid}/events` | Ghi sự kiện đã xảy ra + kết quả đối chiếu | Không |
| 17 | `GET /api/v1/validation/statistics` | Thống kê journal (chỉ mở khi đủ 30 ca đã đối chiếu) | Không |

### 3.3. Bảo mật & vận hành API

| Cơ chế | Hành vi | Cấu hình |
|---|---|---|
| **X-API-Key** | Mọi path `/api/v1/*` và `/api/stars/*` (trừ `/health`) phải có header đúng; sai/thiếu → 401 | `KMS_API_KEY` (rỗng = mở, mặc định) |
| **Rate limit** | `/api/v1/horoscope*` giới hạn 10 yêu cầu/phút/IP (cửa sổ trượt 60 giây); vượt → 429 | `KMS_RATE_LIMIT_PER_MIN` |
| **CORS** | Allowlist origin, không dùng wildcard khi bật credentials | `KMS_CORS_ORIGINS` (mặc định `localhost:8501,8502`) |
| **Frontend** | Gửi key qua header, dịch 429 thành thông báo thân thiện, coi stream đứt là lỗi | `frontend/horoscope_transport.py` |

### 3.4. Ba luồng ứng dụng và giao diện

| Luồng | Endpoint | Mục đích | Kỹ thuật LLM |
|---|---|---|---|
| **Hỏi đáp học thuật (KMS)** | `POST /api/v1/chat/ask` | Tra cứu nội dung 3 sách, trả lời **tách theo sách**, có trích dẫn | RAG: cache → out-of-scope → retrieval → ngưỡng → prompt → provider → kiểm citation |
| **Luận giải cá nhân** | `POST /api/v1/horoscope/read` (+ `-stream`, `-ask`) | Sinh bài luận 7 khối từ lá số + ngữ cảnh sách, **dẫn `fact_id` & `source_refs`** | 3 mức đọc; provider chain; 6 lớp kiểm đầu ra; cache v8 |
| **Nghiệm lý & sản phẩm dữ kiện** | `annual`, `stars/dossier`, `validation/*` | Bảng vận năm, hồ sơ sao, nhật ký ca | **Không gọi LLM** |

Giao diện: entrypoint duy nhất `app.py` dựng `st.navigation` gồm **3 trang**: **Luận giải lá số** (mặc định), **Hồ sơ sao** (`ho-so-sao`), **Nhật ký nghiệm lý** (`nghiem-ly`). Ngoài ra còn 2 entry cũ chạy độc lập (`frontend/app.py` — 3 tab tra cứu/hỏi đáp/thống kê; `frontend/lasoban.py` — lập lá số rule-based), không nằm trong điều hướng chính.

---

## 4. Xây dựng & quản trị kho tri thức (Build – Hold)

### 4.1. Nguồn dữ liệu

Ba sách nguồn, mỗi sách một "tiếng nói":

| Mã | Sách | Bản ghi | Số trang | Nguồn trích xuất | `Release_Status` |
|---|---|---|---|---|---|
| NPL | Nguyễn Phát Lộc — *Tử Vi Tổng Hợp* | 2.191 | 442 | Extraction từ PDF (cấu trúc SPO) | `LOCKED_V1_0` |
| BD | Bửu Đình — *Tử Vi Ứng Dụng* | 4.450 | 579 | Tesseract OCR (7 phần PDF) | `DRAFT_NOT_RELEASED` |
| DAU | *Tử Vi Đẩu Số Toàn Thư* | 3.815 | 347 | Text layer (nhiều câu thơ/phú) | `DRAFT_NOT_RELEASED` |
| **Tổng** | | **10.456** | | | |

> Nguyên tắc: **giữ 3 tiếng nói riêng**, không gộp/dung hòa nội dung giữa các sách — câu trả lời luôn "theo sách X". Nguyên tắc này được kiểm tự động bằng tiêu chí cross-book leakage (§7).

### 4.2. Quy mô kho tri thức (số liệu thật từ `kms.db`, 20,4 MB)

| Thành phần | Số lượng |
|---|---|
| `knowledge_items` (bản ghi tri thức) | **10.456** |
| `evidences` (bằng chứng đối chiếu trang, giữ `original_text`) | **10.492** |
| `knowledge_pages` (liên kết bản ghi ↔ trang PDF) | **10.483** |
| `chunks` (đơn vị tri thức sau chunking) | **4.350** (NPL 2.191 · BD 1.189 · DAU 970) |
| `chunks_fts` (index từ khóa, bỏ dấu) | **4.350** |
| `chunk_members` (bản ghi ↔ chunk, phục vụ dẫn `fact_id`) | **8.680** |
| `book_parts` (phần PDF; BD có 7 phần) | **9** |
| `id_redirects` (ID đã gộp trùng, tra về ID hiện hành) | **34** |
| `term_aliases` (từ điển alias) | **156** |
| `import_runs` (import idempotent, SHA-256) | **2** lần |
| `audit_samples` (mẫu kiểm chất lượng nguồn, seed=42) | **300** |
| `validation_cases` / `predictions` / `events` (journal T8) | 0 / 0 / 0 (bảng sẵn sàng) |
| `query_cache` / `horoscope_cache` | 0 / 0 (tự sinh khi dùng API) |
| Qdrant vector (`gemini-embedding-001`, 1024 chiều) | **30** vector (chưa phủ đủ — xem §8) |

Cấu trúc DB gồm **17 bảng nghiệp vụ** + **6 bảng phụ của FTS5** (`chunks_fts*`). Các bảng mới so với báo cáo trước: `chunk_members`, `audit_samples`, `validation_cases`, `predictions`, `events`, `query_cache`, `horoscope_cache`.

### 4.3. Mô hình tri thức (knowledge model)

- **Cấp phân tầng (hierarchy):** `books → book_parts → chapters → chunks`, mỗi chunk gắn `knowledge_id`, `trust_tier`, trang (đầu/cuối, kèm `part_number` cho BD); bảng `chunk_members` giữ ánh xạ nhiều-nhiều để truy ngược từ chunk về đúng bản ghi.
- **Bản ghi tri thức** có cấu trúc `Subject–Predicate–Object` + `Condition_Context` + `text` (nội dung chính để embed/hiển thị) + metadata nguồn, cờ review/validation/conflict/dedupe + `content_hash` + `version`.
- **Chunking theo đơn vị tri thức:** NPL = 1 bản ghi/chunk; DAU & BD = gộp các bản ghi liền kề (cùng trang/chương, 150–600 ký tự) theo `configs/column_mapping.yaml`; riêng BD thêm quy tắc `PAGE_OR_PARAGRAPH_CONTINUATION`.
- **Truy vết:** mỗi fact trong bài luận mang `fact_id` trỏ về bản ghi/chunk, kèm `source_refs` (sách, phần, trang) — đây là cầu nối giữa "văn bản do AI viết" và "trang sách gốc".

### 4.4. Cổng tri thức đầu vào (T7)

Báo cáo trước mới mô tả trust tier; phiên bản hiện tại có thêm **cổng kiểm duyệt trước khi ghi DB** (`services/knowledge_gate.py`), chạy được độc lập (dry-run) lẫn gắn vào import (`import_excel.py --gate`).

Mỗi `Knowledge_ID` mới phải có **ít nhất một** trong ba yếu tố:

| Yếu tố | Metadata được kiểm tra |
|---|---|
| **A — Dẫn nguồn và trang** | `Source_IDs` trỏ nguồn có trong registry + `PDF_Pages` hợp lệ; hoặc evidence liên kết đúng và có `PDF_Page` dương |
| **B — Trường phái hoặc lập trường** | `School` hoặc `Author_Stances` có nội dung rõ |
| **C — Ví dụ hoặc ca kiểm chứng** | `Validation_Example`, `Case_ID` hoặc trường tương đương có nội dung |

- Placeholder rỗng, `N/A`, `UNKNOWN`, `TBD`, `[]`, `{}`, `—` **không được tính**.
- **Nguồn D (FORUM/VIDEO)** bị quarantine: bắt buộc `DRAFT_NOT_RELEASED` + `HYPOTHESIS_NEEDS_VALIDATION` + `trust_tier = 9`, kể cả khi dùng chung `Book_Code` với sách; quy tắc này áp dụng cả khi không bật `--gate`.
- Kiểm chứng trên dữ liệu thật: **10.456/10.456 bản ghi pass** cổng (0 lỗi) trên workbook canonical; CI chạy gate trên fixture hợp lệ + toàn bộ test âm tính.
- Giới hạn: gate chỉ xác nhận **metadata**, không chứng minh nội dung đúng, trang khớp PDF hay bản quyền được phép dùng — việc đó vẫn cần review thủ công.

### 4.5. Trust tier (phân tầng độ tin cậy nguồn)

Vì hiện **chưa có bản ghi nào được người duyệt** (`validation_status` đều là "…_REVIEW_PENDING"), hệ thống **suy ra trust tier từ dữ liệu** bằng 5 quy tắc trong `configs/column_mapping.yaml` (khớp quy tắc đầu tiên thắng, thực thi bởi `services/tiering.py`):

| Tier | Điều kiện | Số bản ghi | Chính sách index |
|---|---|---|---|
| **1** | Sách NPL (đã LOCKED) | 2.191 | **Index** |
| **2** | Sách DAU (trừ `OCR_REVIEW_REQUIRED`) | 3.798 | **Index** |
| **3** | Sách BD (trừ `OCR_REVIEW_REQUIRED`) | 2.691 | **Index** (bật/tắt qua config) |
| **9** | `OCR_REVIEW_REQUIRED` hoặc `HYPOTHESIS_NEEDS_VALIDATION` (BD 1.759 + DAU 17) | 1.776 | **LOẠI khỏi index** |

- **Tổng bản ghi được index: 8.680** (khớp `chunk_members`). Muốn chặt hơn chỉ cần đổi `enabled_tiers` trong YAML, **không sửa code** — đây là cơ chế **quản trị tri thức linh hoạt**.
- **`verification_status`** (mức xác minh thủ công) là một lớp **riêng**, mặc định `unverified`; UI hiển thị nhãn "chưa kiểm duyệt thủ công" ở 3 vị trí — không ngụy trang dữ liệu là "đã duyệt".
- **Review flag** cho thấy quy mô công việc còn lại: `SEMANTIC_REVIEW_PENDING` 2.093 · `SOURCE_REVIEW_PENDING` 1.923 · `OCR_REVIEW_REQUIRED` 1.776 · `CONTENT_REVIEW_REQUIRED` 1.705 · `STANDARD` 1.123 · `LOW_CERTAINTY` 922.

### 4.6. Truy xuất gốc (provenance), chứng cứ và từ điển chứng cứ

Mọi kết quả truy xuất và mọi trích dẫn đều mang: **sách (book_code) → phần (part_number) → chương → trang PDF (đầu/cuối) → trust_tier → verification_status → knowledge_ids**. Bảng `evidences` giữ thêm: `original_text` (nguyên văn đoạn nguồn), `ocr_legibility`, `evidence_method`, `origin`, `source_review_status`.

Lớp mới (T3): **từ điển 10 loại chứng cứ** (`backend/app/core/evidence_types.py`) để mỗi nhận định phải khai báo **loại quan hệ** đã dùng:

| Nhóm | Loại chứng cứ |
|---|---|
| Quan hệ cung với Mệnh | `toa_thu` (tọa thủ) · `tam_hop` (tam hợp) · `xung_chieu` (xung chiếu) · `giap_cung` (giáp cung) |
| Tứ hóa | `tu_hoa` |
| Ngữ cảnh | `menh_cuc` · `van_han` (vận hạn) · `nghiem_ly` (nghiệm lý) · `truong_phai` (trường phái) |
| Nối mạch người viết | `suy_luan` (không thay thế chứng cứ thật) |

Mỗi luận điểm bắt buộc có `loi_chung_cu` khớp `kind` của fact được dẫn và **`phan_chung`** (phản chứng) không rỗng; nếu nguồn không ghi phản chứng, phải ghi nguyên văn câu chuẩn *"Không ghi nhận phản chứng trong nguồn đã lấy."* — câu này không có nghĩa là không tồn tại phản chứng.

### 4.7. Kiểm mẫu chất lượng nguồn (audit) và trạng thái xác minh

- `audit_samples` đã sinh **300 dòng** (lấy mẫu phân tầng, `seed=42`, `double_audit=False`) nhưng **chưa có kết quả chấm** (`auditor`, `text_matches_source`, `page_correct`, `ocr_error` còn trống). Đây là **kế hoạch kiểm mẫu đã tạo, chưa hoàn tất** — báo cáo không trình bày như đã kiểm.
- `validation_status` toàn bộ bản ghi vẫn ở trạng thái chờ review: BD `OCR_SOURCE_REVIEW_PENDING` (4.450), DAU `OCR_TEXT_LAYER / SOURCE_REVIEW_PENDING` (3.815), NPL `STRUCTURAL_QA_PASS / SOURCE_REVIEW_PENDING` (2.191).
- `import_runs` ghi 2 lần import cùng một workbook SHA-256, 10.456 dòng đọc/ghi, 0 dòng bị loại — chứng minh tính idempotent và khả năng tái lập.

### 4.8. Quản trị thay đổi tri thức (T11)

Mọi thay đổi về schema, prompt, bảng an sao, chính sách đều được ghi trong `docs/CHANGELOG_KNOWLEDGE.md` theo mẫu **trước → sau · lý do · phạm vi ảnh hưởng · nguồn · giới hạn**. Đây là cơ chế quản trị tri thức "phiên bản hóa" (versioned knowledge), cho phép trả lời câu hỏi của giảng viên: *"Vì sao kết luận hôm nay khác hôm qua?"* — trả lời bằng changelog, không bằng trí nhớ.

---

## 5. Truy xuất tri thức (Pool)

### 5.1. Retriever hybrid (luồng hỏi đáp KMS)

`services/retriever.py` kết hợp **hai nguồn xếp hạng** và gộp bằng **Reciprocal Rank Fusion (RRF, k = 60)**:

```
score(d) = Σ_rankers 1 / (k + rank(d))     với k = 60
```

Chiến lược (đọc từ `configs/retrieval.yaml`):
- Lấy **top-10 ứng viên MỖI SÁCH** (tránh sách lớn áp đảo sách nhỏ) → **giữ "ba tiếng nói"**.
- Kết hợp **FTS5** (từ khóa, chịu lỗi dấu tiếng Việt) + **dense vector** (ngữ nghĩa, Qdrant).
- **Lọc theo trust_tier** (chỉ tier trong `enabled_tiers = [1, 2, 3]`).
- Gộp kết quả, chọn tối đa **8 chunk ngữ cảnh**, ưu tiên phủ đủ 3 sách; tra metadata từ SQLite.
- **Abstention:** nếu điểm RRF thấp hơn ngưỡng `0.005` → trả `insufficient_evidence` thay vì để LLM đoán.

### 5.2. RAG bridge (luận giải horoscope)

`services/horoscope_rag_bridge.py`:
- **Tự sinh câu hỏi** từ đặc trưng lá số: theo **cung trọng tâm** (Mệnh, Quan Lộc, Tài Bạch, Phu Thê), **đại hạn / tiểu hạn**, **Tứ Hóa**, **lưu niên**.
- Dùng **`AND` tên sao đầy đủ** (không dùng `OR` từng âm tiết) → **không lấy nhầm "Văn Khúc" khi hỏi "Vũ Khúc"**; có **fallback nới query** khi truy vấn 3 thành phần không trả kết quả nào.
- Giữ **điều kiện tổ hợp** (Tuần/Triệt/đắc–hãm) trong truy vấn; **lọc cứng `trust_tier IN (1,2,3)`**.
- Giới hạn ngữ cảnh: tối đa **22 chunk**; trích đoạn lưu 500 ký tự nhưng **prompt chỉ gửi 300 ký tự** mỗi nguồn để tiết kiệm token.

### 5.3. Hồ sơ sao có nguồn (T6)

`GET /api/v1/stars/{ten}/dossier?include_seeds=false` trả **14 nhóm hiển thị** (`core_function`, `yin_yang_five_element`, `by_palace`, `supportive_combinations`, `challenging_combinations`, `transformation_behavior`, `with_tuan_triet`, `with_sat_tinh`, `school_differences`, `case_notes`, `source_citations`…), mỗi entry giữ `knowledge_id`, `book_code`, điều kiện, `trust_tier`, trang/phần.

- **Nguồn A (canonical):** bản ghi tier 1–3, không là giả thuyết, có trang dẫn thật; tối đa 30 bản ghi/sách; mục thiếu được công khai là thiếu (không suy diễn lấp chỗ trống).
- **Nguồn B (seed):** 20 file YAML (14 chính tinh + Tả/Hữu Bật + Văn Xương/Khúc + Thiên Khôi/Việt), **34 slot đều `seed_unverified`**, chỉ xuất hiện khi người dùng bật, **không vào RAG**, không ghi đè canonical.
- **`school_differences`** giữ riêng tiếng nói từng sách; không tự khẳng định ba sách mâu thuẫn.
- Danh mục tra cứu: **108 sao**; tên có/không dấu đều tra được.

Lớp mở rộng: `star_meanings_reference.py` đọc **tài liệu tham khảo do người dùng cung cấp** (`star_meanings.md` trong bộ skill local — 34 sao), coi đó là **dữ liệu có gán nguồn**, lọc các dòng chỉ thị chen trong tài liệu, gắn `reference_unverified`, không gán `book_code`/trang giả cho ba sách. Nội dung này chỉ hỗ trợ giải nghĩa, không thay chứng cứ để nâng mức tin cậy.

### 5.4. Dữ kiện vận năm bốn tầng (T9)

`POST /api/v1/horoscope/annual` trả bảng **ba chủ đề × bốn tầng**:

| Tầng | Nội dung | Giới hạn đã khai báo |
|---|---|---|
| Lá số gốc | Sao gốc trong các cung liên quan từng chủ đề | — |
| Đại hạn | Khoảng tuổi/cung hạn hiện tại; dẫn fact là **sao gốc tại cung hạn**, không giả làm lưu tinh | — |
| Lưu niên | Vòng Thái Tuế (12 sao) + lưu Tứ Hóa theo can năm (2 bảng cấu hình) | Cùng tầng, không nhân bản chứng cứ |
| Lưu nguyệt | Trạng thái `missing` | **Chưa an lưu nguyệt** — khai báo thiếu, không bịa |

- Mức của bảng hiện là **yếu**: bảng chỉ là dữ kiện để đối chiếu, chưa đủ điều kiện sách và phản chứng để nâng thành kết luận mạnh; kết luận của lời luận vẫn theo T2.
- **So năm ±1** (năm trước / năm xem / năm sau) giữ cùng bảng Tứ Hóa; năm ngoài 1900–2100 bị từ chối; không an 1899/2101 khi năm xem là 1900/2100 → trả `out_of_range`, Can Chi rỗng.
- Bảng do **server ghép từ dữ kiện**, LLM không được điền tầng còn thiếu.

### 5.5. FTS5 tiếng Việt không dấu

`services/fts.py` — tìm kiếm **bỏ dấu** (chuẩn hóa NFD/NFC), chịu lỗi gõ sai dấu; là **baseline bắt buộc** cho mọi so sánh retrieval. Đây là lý do con số Recall@5 hiện có (§7) phải được đọc là "điểm của FTS", không phải "điểm của hệ thống".

### 5.6. Giới hạn truy xuất ngữ nghĩa (dense)

Manifest index ghi **30/4.350 chunk** đã embed, trong khi code mặc định dùng embedding local `BAAI/bge-m3` (kích thước 1024, CPU) và manifest lịch sử ghi `gemini-embedding-001`. Hai điểm này cho thấy **dense index chưa phải là đường truy xuất chính** trong thực tế vận hành; hệ thống vẫn chạy được nhờ FTS5 + RRF và fallback bỏ dense khi index rỗng. Chi tiết bất nhất code ↔ artifact ở Phụ lục C.

---

## 6. Ứng dụng tri thức & LLM (Use)

### 6.1. Nguyên tắc cốt lõi

> **LLM chỉ tổng hợp từ ngữ cảnh đã truy xuất, không tạo tri thức canonical.** Mọi đoạn sách truy xuất được coi là **dữ liệu, không phải chỉ thị** (chống prompt-injection). Tài liệu tham khảo từ bộ skill cũng đi qua cùng nguyên tắc: chỉ đọc, lọc dòng chỉ thị, gắn nhãn chưa xác minh.

### 6.2. Ba mức đọc (reading mode) — tách khỏi nhà cung cấp

Từ gói P1, hợp đồng dữ liệu tách **mức đọc** (lựa chọn của người dùng) khỏi **provider** (bộ xử lý thực tế):

| Mức đọc | Nội dung chính | Gọi LLM | Trạng thái |
|---|---|---|---|
| `du_lieu` | Lá số, vị trí sao, hạn, tín hiệu, điều kiện khớp, giải thích theo mẫu | **Không** | UI có |
| `giai_thich` | Giải nghĩa thuật ngữ, giải thích từng nhận định, liên hệ dữ kiện | Có | Mới ở tầng API |
| `chuyen_sau` | Tổng hợp theo chủ đề, cân nhắc thuận/nghịch, phân biệt gốc–hạn, điều kiện thay đổi kết luận | Có | UI có (mặc định) |

Hợp đồng trả về gồm `mode`, `contract_version = 2`, `items` (mỗi nhận định có: nhận định · dữ kiện · quy tắc · lý do liên quan · thuận/nghịch · điều kiện thiếu · nguồn · giới hạn). Meta ghi **mức yêu cầu** và **mức thực tế đã hoàn thành** kèm lý do hạ cấp (`actual_reading_mode`, `fallback_reason`) — người đọc luôn biết mình đang đọc bản nào.

### 6.3. Provider và model

| Luồng | Provider mặc định | Model mặc định | Ghi chú |
|---|---|---|---|
| Hỏi đáp KMS (`/chat/ask`) | `KMS_LLM_PROVIDER` = `groq` | `openai/gpt-oss-20b` | Đổi `gemini` → `gemini-3.8-flash`; `deepseek` → `deepseek-chat`; `mock` offline |
| Luận giải horoscope | `KMS_HOROSCOPE_PROVIDER` = `auto` | chuỗi `groq` → `deepseek` → `gemini` (`gemini-3.5-flash-lite`) → `mock` | Chỉ đi tiếp khi thiếu key hoặc lỗi tạm thời; mỗi model tối đa 2 lần sinh (lần đầu + 1 lần bổ sung bắt buộc) |
| Embedding (index) | `KMS_EMBEDDING_PROVIDER` = `local` | `BAAI/bge-m3`, 1024 chiều, CPU | Manifest lịch sử ghi `gemini-embedding-001` — xem Phụ lục C |
| Mock | `provider = mock` | `mock-echo-v1` (chat) / `mock-data` (horoscope) | Không gọi mạng; dùng để demo offline và kiểm thử |

Tham số chung: `temperature = 0.0` cho **mọi** provider; timeout horoscope 45 giây (kẹp trong khoảng 5–60); ngân sách token **12.288** cho mỗi mức đọc (ba biến cấu hình riêng); danh sách model dự phòng cấu hình được (`KMS_HOROSCOPE_FALLBACK_MODELS`).

> **Cần nói rõ:** đổi provider **không đổi chất lượng tri thức**; nó đổi bộ diễn đạt và độ ổn định dịch vụ. Chất lượng nội dung thật vẫn phải đo bằng review thủ công trên bài do mô hình thật sinh ra — hệ thống chưa có số đo đó (§8).

### 6.4. Pipeline hỏi đáp KMS (`services/rag.py`)

Trật tự thực thi trong `RAGPipeline.ask()`:
1. **Cache tất định** — trùng câu hỏi + sách + model + prompt-hash + index-version thì trả ngay (không lưu kết quả lỗi).
2. **Phát hiện ngoài phạm vi** — chặn yêu cầu "luận lá số / bói toán cá nhân" (trả `out_of_scope`).
3. **Truy xuất** ngữ cảnh (top-N mỗi sách, lọc ngưỡng RRF, tối đa 8 chunk, ưu tiên phủ đủ sách).
4. **Abstention** — không chunk nào vượt ngưỡng → trả `insufficient_evidence`.
5. **Dựng prompt** (câu hỏi + ngữ cảnh đánh số `[1]…`, kèm metadata sách/phần/trang/tier).
6. **Gọi LLM** qua adapter provider — tổng hợp **tách theo sách**, giọng "theo sách", không lời khuyên y khoa/tài chính.
7. **Kiểm citation** (`citation_validator.py`) — mọi `[n]` phải tồn tại trong ngữ cảnh; phát hiện câu không dẫn nguồn; loại citation giả.
8. Trả JSON (kèm `citations`, `retrieval`, `citation_check`, `request_id`).

`status ∈ {answered, insufficient_evidence, out_of_scope, error}`.

### 6.5. Pipeline luận giải horoscope (`services/horoscope_service.py`)

Một đường orchestration duy nhất cho cả JSON và stream, phát sự kiện NDJSON:

1. **Tiến trình**: `progress`/`stage` → **`chart_ready`** (lá số + dữ kiện xong, phát **trước** khi chờ truy xuất/AI — gói P5) → `prepared` (nguồn đã truy xuất) → `result` → `error`.
2. **An sao tất định** bằng `vendor/lasotuvi`; sinh **20 nhóm đặc trưng** (palaces, nam_xem, luu_nien, tu_hoa, đại hạn…).
3. **Sinh facts** có `kind` chứng cứ và `fact_id`.
4. **Nhận diện cách cục bằng code** (`cach_cuc_detector.py`) trên 8 quy tắc đủ điều kiện, phân biệt **khớp đủ / khớp một phần / không khớp / chưa thể đánh giá**; AI bị chặn dẫn `rule_id` ngoài kết quả nhận diện.
5. **Truy xuất nguồn** qua RAG bridge (mục 5.2).
6. **Cache**: khoá theo (lá số, năm, provider, model, hash ngữ cảnh, index-version, mức đọc, schema-version = 8); chỉ **lưu khi `actual_provider == "gemini"` và không lỗi** — nên hiện groq/deepseek không được cache.
7. **Sinh văn bản** theo mức đọc, qua chuỗi provider; mỗi model tối đa 2 lần.
8. **Chuỗi kiểm đầu ra** (mục 6.6); vi phạm → sinh lại 1 lần → vẫn sai thì fallback mock hoặc lỗi có mã rõ ràng.
9. **Adapter hợp đồng** (`CONTRACT_VERSION = 2`) chuẩn hóa 3 mức đọc; mock có cùng cấu trúc và không tự nhận là AI.
10. **Trả report** cho UI; UI hiển thị 7 khối: định danh → tổng quan năm → lá số → chân dung/thế mạnh → chủ đề → gợi ý hành động → căn cứ chuyên môn (mặc định thu gọn).

### 6.6. Sáu lớp kiểm soát đầu ra

| Lớp kiểm | Kiểm gì | Hành vi khi vi phạm | Mã nguồn |
|---|---|---|---|
| **Giờ sinh A–D (T1)** | Mức C/D chỉ được kết luận cấu trúc; cấm kết luận thời điểm/sự kiện; mọi phần giới hạn phải nêu caveat | Sinh lại 1 lần; vẫn sai → mock có caveat hoặc lỗi rõ ràng | `horoscope_confidence.py` |
| **Bốn bậc tin cậy (T2)** | `rat_manh`/`manh` cần ≥3 `fact_id` khác nhau, `trung_binh` ≥1, `yeu` ≥0; cấm mọi mẫu phần trăm | Sinh lại 1 lần; vẫn sai → `invalid_response` | `horoscope_interpreter.py` |
| **Nhãn chứng cứ (T3)** | `loi_chung_cu` khớp `kind` fact được dẫn; `phan_chung` bắt buộc | Sinh lại; vẫn sai → không nhận bài | `interpreter.py` + `core/evidence_types.py` |
| **Độ cụ thể** | ≥3 `fact_id` khác nhau; phần vận trình phải nhắc đúng năm/can chi | Sinh lại 1 lần; ghi cờ `specificity_low` (không giấu) | `interpreter.py` |
| **Nội dung nhạy cảm** | Chặn câu khẳng định chết yểu/tử vong/bệnh nặng/dâm đãng… | Không cache, fallback/khai báo rõ | `interpreter.py` |
| **Cách cục (P3)** | AI chỉ được dẫn `rule_id` có trong kết quả detector | Chặn bài | `cach_cuc_detector.check_rule_ids` |

Riêng luồng hỏi đáp KMS còn lớp **citation validator** (3 điều kiện: `[n]` tồn tại; câu có nội dung mà không dẫn nguồn; citation phải thuộc đúng sách/phần/trang đã khai báo) và **abstention**.

### 6.7. Kiểm tra trích dẫn (`services/citation_validator.py`)

Kiểm **3 điều**:
1. Mọi số `[n]` trong câu trả lời **phải tồn tại** trong ngữ cảnh đã đưa cho LLM.
2. Phát hiện **câu có nội dung nhưng không kèm trích dẫn**.
3. Trích dẫn phải thuộc **đúng sách/phần/trang** đã khai báo.

### 6.8. Giao diện và tính trung thực hiển thị

- 3 trang điều hướng; trang luận giải dùng **7 khối** nội dung, lá số 12 cung có **lưới 4×4 trên desktop** và **danh sách từng cung rõ chữ trên điện thoại** (không thu nhỏ toàn bộ chữ để ép vừa màn hình).
- **Phân nhóm sao dùng chung backend–frontend** (`star_classification.py`): chính tinh nổi bật kèm đắc tính (M/V/Đ/B/H), **Tứ Hóa có nhận diện riêng** (badge Khoa/Quyền/Lộc/Kỵ, không ép vào cát/hung), phụ tinh chia 2 cột cát/hung, Tuần/Triệt và sao lưu niên hiển thị riêng.
- Nhãn trung thực: "chưa kiểm duyệt thủ công" trên từng trích dẫn; "Tham khảo, chưa đối chiếu sách KMS" cho seed; banner khi rơi vào mock/fallback; hiển thị thời gian và trạng thái cache.
- Hạn chế đã biết: UI mới mở **2/3 mức đọc**; nhãn provider trên báo cáo mới map `gemini`/`mock` nên `groq`/`deepseek` có thể hiện chuỗi thô; widget "Hỏi nhanh" (`frontend/horoscope_ask.py`) chưa được trang nào nối vào.

---

## 7. Đo lường & nghiệm thu chất lượng tri thức

### 7.1. Bộ chỉ tiêu (theo khung KMS)

| Chỉ tiêu | Định nghĩa | Mục tiêu (đề xuất, **chưa phải kết quả**) |
|---|---|---|
| **Recall@5** | Tỷ lệ câu có ≥1 evidence đúng trong top-5 | ≥ 0,80 |
| **MRR** | Trung bình nghịch vị trí của kết quả đúng đầu tiên | cao nhất có thể |
| **Cross-book leakage** | Kết quả tràn sang sách sai (vi phạm "ba tiếng nói") | = 0 |
| **Abstention accuracy** | Từ chối đúng câu thiếu căn cứ / ngoài phạm vi, không từ chối thừa | = 1,0 |
| **Citation validity** | Tỷ lệ trích dẫn trỏ tới ngữ cảnh có thật | = 100% |
| **Groundedness/faithfulness** | Tỷ lệ luận điểm được ngữ cảnh hỗ trợ | đánh giá thủ công (chưa đo) |
| **Test pass rate** | Tỷ lệ kiểm thử tự động xanh | 100% (hiện chưa đạt — §8) |

### 7.2. Kết quả hiện có (trung thực)

| Kết quả | Giá trị | Ghi chú quan trọng |
|---|---|---|
| **FTS-only, hold-out 20 câu** — Recall@5 | **0,5882** | Điểm của **FTS (từ khóa)**, KHÔNG phải của LLM hay embedding |
| **FTS-only** — MRR | **0,5** | |
| **FTS-only** — Cross-book leakage | **0** | Giữ đúng "ba tiếng nói" |
| **FTS-only** — Abstention accuracy | **1,0** | Từ chối đúng |
| Recall@5 theo chủ đề (đo 21/10/2026) | DAU 100% · NPL 80% · BD 70% | BD thấp nhất vì là nguồn OCR |
| Cổng tri thức trên workbook thật | **10.456/10.456 pass**, 0 lỗi | Không import lại DB |
| Cross-check an sao độc lập (T4) | **44 vector · 1.784 trường so sánh · 351 sai khác đã biết** · 12/44 vector khớp trọn | Giữ dạng `strict xfail`, issue #1 còn mở |
| Bảng Tứ Hóa (T5) | **40 mục / 10 Can · 3 khác biệt** (Canh Khoa/Kỵ, Nhâm Khoa) | Hai bảng giữ nhãn nguồn riêng, chưa phân xử |
| Index vector Qdrant | **30/4.350** chunk | ⚠️ Chưa phủ đủ — không kết luận tìm kiếm ngữ nghĩa đã sẵn sàng |
| Skill validator (T10) + gate CSV | PASSED | Chạy trong CI |

> **Cách đọc số 0,5882 với giảng viên:** "Recall FTS-only trên hold-out mới là 0,588, **dưới** ngưỡng mục tiêu 0,8. Đây là **baseline trung thực**, chưa phải kết quả cuối; kế tiếp là bật dense + hybrid, đo lại trên cùng bộ câu để so sánh." **Không** được trình bày con số này như "đã đạt".

### 7.3. Trạng thái kiểm thử tại thời điểm chụp số liệu

Bộ test hiện có **42 file**, `pytest --collect-only` thu được **2.665 test case** (05/11/2026), trong đó `test_lasotuvi_crosscheck.py` chiếm **2.224 case (83,5%)** — là các ca tham số hóa đối chiếu an sao, **không đại diện cho số "kịch bản hành vi"**. Các nhóm còn lại: governance/tri thức 103 · hợp đồng–nhãn–tin cậy 117 · UI 59 · API/RAG/cache 41 · provider 13.

| Lần chạy (05/11/2026) | Lệnh | Kết quả |
|---|---|---|
| Cấu hình local (`.env` đặt `KMS_LLM_PROVIDER=groq`, `KMS_HOROSCOPE_PROVIDER=groq`) | `python -m pytest tests/ -q` | **2.293 passed, 16 failed, 351 xfailed** (181,5 giây) |
| Ép provider Gemini (mô phỏng môi trường CI không có `.env`) | `KMS_HOROSCOPE_PROVIDER=gemini KMS_LLM_PROVIDER=gemini python -m pytest tests/ -q` | **2.307 passed, 7 failed, 351 xfailed** (197,2 giây) |

Diễn giải trung thực 16/7 ca đỏ:
- **9 ca** chỉ đỏ khi `.env` đặt `groq`: các test cũ giả định luồng Gemini/mock (cache, `input_confidence`, nhãn chứng cứ, phản hồi khi model quá tải) chưa cập nhật cho **chuỗi provider** mới.
- **7 ca** đỏ ở cả hai cấu hình: test chưa đồng bộ với **nhãn UI mới** ("Mức tập trung tín hiệu cần xem xét"), **token budget 3 mức đọc**, prompt 4 bậc tin cậy và tên model dự phòng.
- **351 `xfail`** là các sai khác an sao đã biết của T4, khai báo `strict` (thay đổi ngoài kỳ vọng sẽ làm test đỏ) — không phải lỗi mới.
- Đây là **ảnh chụp working tree** (có thay đổi chưa commit); con số trước đó (03/11, sau nghiệp thu T1–T11 + P1–P5) là **2.276 passed / 351 xfailed**. Việc đồng bộ test với thay đổi mới nhất là việc còn lại trước khi nộp (§8, §9).

### 7.4. Nghiệm thu giao diện

- Kiểm bằng **Streamlit AppTest** cho 3 trang (luận giải, hồ sơ sao, nhật ký nghiệm lý) và các trạng thái trống/lỗi.
- Kiểm thị giác trên trình duyệt ở **1440 / 768 / 390 px**: lá số 4×4 desktop, danh sách từng cung mobile, không tràn ngang, không lỗi JS; trạng thái mở/đóng của bảng bốn tầng và bảng căn cứ.
- Giới hạn: đây là kiểm **luồng kỹ thuật và hiển thị**, **không** chứng minh chất lượng văn bản do mô hình thật sinh ra.

### 7.5. CI và các cổng kiểm tự động

Workflow `.github/workflows/test.yml` chạy trên Python 3.12:
1. Validate fixture cổng tri thức (`scripts/validate_knowledge_import.py`).
2. Validate gói skill (`scripts/validate_skill.py` — frontmatter, trùng key, < 500 dòng, link nội bộ).
3. Validate CSV tri thức thật nếu có thư mục `tuvi_import/`; nếu vắng ghi rõ `SKIPPED`, không coi là đã pass.
4. `pytest tests/ -m "not heavy"` (loại các test nặng).

### 7.6. Ma trận nghiệm thu tri thức

Chi tiết 11 task quản trị tri thức (T1–T11) và 8 gói cải tiến (P1–P8) được tổng hợp ở **Phụ lục D**; tài liệu gốc: `docs/GOVERNANCE_ACCEPTANCE.md`, `docs/CHANGELOG_KNOWLEDGE.md`, `tests/plans/ACTIVE_TEST_PLAN.md` (toàn bộ plan ghi trạng thái PASSED tính đến 03/11/2026).

---

## 8. Giới hạn & rủi ro

Trình bày trung thực (nên nói trước, không đợi GV hỏi):

| # | Giới hạn / rủi ro | Kiểm soát hiện có | Việc cần làm |
|---|---|---|---|
| 1 | **LLM có thể diễn đạt sai** nội dung sách, bịa quan hệ nhân quả | Prompt bám ngữ cảnh; 6 lớp kiểm đầu ra; citation validator; abstention | Đo **groundedness** trên bài do mô hình thật sinh; review thủ công từng nhận định |
| 2 | **Nguồn OCR (BD) có thể sai chính tả/dấu**, chưa người duyệt | Trust tier (loại tier 9), nhãn "chưa kiểm", từ điển evidence | Hoàn tất 300 mẫu audit; sửa OCR, ghi `verification_status` |
| 3 | **Dense index chưa phủ đủ** (30/4.350 vector) | FTS5 làm baseline; hybrid fallback bỏ dense khi index rỗng | Build đủ vector, đo lại Recall trên cùng bộ câu |
| 4 | **Recall@5 còn thấp** (0,588 < 0,8 mục tiêu) | Baseline FTS-only trung thực | Reranker / cải thiện chunking / embedding tiếng Việt tốt hơn |
| 5 | **Chất lượng văn bản của mô hình thật chưa nghiệm thu** | Mock + nhãn rõ; đoạn test biên transport | Bộ ca nghiệm thu nội dung trên 3 provider thật, rubric chấm tay |
| 6 | **Test chưa xanh** (7–16 ca đỏ tùy môi trường) | 351 xfail có kiểm soát; CI chạy `-m "not heavy"` | Đồng bộ test với nhãn UI/prompt/chuỗi provider mới; chốt một mốc xanh trước khi nộp |
| 7 | **Đa provider làm hành vi khác nhau** (groq/deepseek/gemini) | Chuỗi dự phòng + kiểm cấu trúc chung | Đo chất lượng từng provider; thống nhất cấu hình cache theo provider thật |
| 8 | **Cache không đối xứng:** khoá cache dùng `req.provider` + model Gemini trong khi thực tế có thể sinh bằng groq/deepseek; chỉ lưu khi `actual_provider == "gemini"` | Không lưu lỗi; schema version tăng khi đổi định dạng | Thiết kế lại khoá cache theo provider/model thực; test riêng |
| 9 | **UI chưa đủ 3 mức đọc**; nhãn provider groq/deepseek hiện chuỗi thô; widget "Hỏi nhanh" chưa nối | 3 trang đã có; luồng mock phân biệt rõ | Bổ sung mức `giai_thich` trên UI, map nhãn provider, quyết định giữ/bỏ widget |
| 10 | **Prompt-injection qua tài liệu tham khảo** (Markdown người dùng cấp) | Loader lọc dòng chỉ thị, chỉ đọc `ALLOWED_SECTIONS`, không nhập vào RAG | Rà soát định kỳ; coi tài liệu là dữ liệu, không phải lệnh |
| 11 | **Tri thức ẩn mới chỉ ghi nhận**, chưa quay lại kho canonical | Journal append-only, trigger SQLite | Thiết kế vòng phản hồi: kết quả nghiệm lý → đề xuất sửa tri thức → review |
| 12 | **Journal chưa đủ 30 ca**; thống kê đóng; trigger chỉ chặn trong ứng dụng | Ngưỡng 30 ca, không tạo ca giả | Thu thập ca thật đúng quy trình; không dùng dữ liệu tự ghi như xác suất dự báo |
| 13 | **351 sai khác an sao** với tài liệu tham chiếu (T4); 2 bảng Tứ Hóa chưa phân xử | Ghi nhận dạng strict xfail; issue #1 mở | Đối chiếu bản sách giấy để kết luận từng trường |
| 14 | **Quyền riêng tư**: ngày giờ sinh được gửi tới nhà cung cấp AI khi chọn chế độ AI | Có chế độ `du_lieu`/`mock` không gọi AI; ẩn danh trong journal | Rà chính sách dữ liệu 3 provider; thông báo người dùng trước khi mở công khai |
| 15 | **Dữ liệu ngoài canonical** (292 bài crawl từ một thư viện Tử Vi) **chưa nằm trong RAG** | Chỉ dùng làm tư liệu nghiên cứu (`docs/research/`) | Chỉ đưa vào kho khi đã qua cổng T7 + review nguồn/bản quyền |

---

## 9. Kết luận & hướng phát triển

### 9.1. Kết luận

- Hệ thống là **một KMS Tử Vi đúng nghĩa**, phủ đủ vòng đời tri thức và **ánh xạ 4 công đoạn Wiig (Build–Hold–Pool–Use) vào mã nguồn có bằng chứng** (mục 2.2).
- Giá trị KMS rõ nhất nằm ở **6 lớp quản trị tri thức**: cổng đầu vào → trust tier → provenance/evidence → kiểm soát sinh văn bản → citation/abstention → nhật ký nghiệm lý. Đây là những thứ phân biệt KMS với một chatbot thường.
- LLM được đặt đúng vai trò **tầng ứng dụng có kiểm soát**, không phải nguồn tri thức; việc hỗ trợ 4 nhà cung cấp không làm thay đổi nguyên tắc này.
- Sản phẩm đã tách được **các dịch vụ tri thức không dùng AI** (hồ sơ sao, dữ kiện vận năm, nhật ký nghiệm lý) và **đóng gói tri thức cho tác tử** (skill `tu-vi-kms` v1.0, MIT, có validator trong CI).
- Các số đo hiện có được trình bày **trung thực** (Recall FTS-only 0,588; vector 30/4.350; 7–16 test đỏ tùy môi trường; 351 sai khác an sao) — không phóng đại thành kết quả đã đạt.

### 9.2. Hướng phát triển

1. **Đưa bộ test về xanh và giữ xanh**: đồng bộ 6 file test với nhãn UI/prompt/chuỗi provider mới; chạy `pytest -m "not heavy"` trong CI làm mốc nghiệm thu.
2. **Xây đủ dense index** (embedding tiếng Việt phù hợp) và **đo lại Recall** FTS vs dense vs hybrid trên cùng golden set; mở rộng golden set lên 40–50 câu (một phần do người chưa xem đáp án viết).
3. **Reranker** cho các câu Recall@5 còn thấp; xử lý thuật ngữ Hán–Việt và nhập nhằng ("Tử Vi" là sao hay môn học).
4. **Hoàn tất UI 3 mức đọc** (`giai_thich`), map nhãn provider groq/deepseek, quyết định số phận widget "Hỏi nhanh".
5. **Khép vòng phản hồi tri thức**: từ nhật ký nghiệm lý → đề xuất hiệu chỉnh tri thức → người duyệt → nâng `verification_status` (hoàn thiện SECI: Externalization/Internalization).
6. **Hoàn tất kiểm mẫu 300 hồ sơ** và đối chiếu 351 sai khác an sao bằng bản sách giấy (issue #1); ghi kết luận vào changelog tri thức.
7. **Nghiệm thu chất lượng theo provider** (Gemini/Groq/DeepSeek) trên cùng bộ lá số biên; công bố rubric và kết quả chấm tay, kèm giới hạn.

---

## PHỤ LỤC A — Tham chiếu mã nguồn & cấu hình

| Khía cạnh KMS | File / tài liệu |
|---|---|
| Plan tổng thể KMS (khuôn Wiig, SECI, golden set, DoD) | `KMS_TuVi_Development_Plan.md` |
| Schema DB & bảng | `backend/app/db/models.py` |
| Trust tier & mapping cột Excel | `configs/column_mapping.yaml`, `backend/app/services/tiering.py` |
| Cổng tri thức đầu vào (T7) | `backend/app/services/knowledge_gate.py`, `scripts/validate_knowledge_import.py`, `docs/KNOWLEDGE_GATE.md` |
| Từ điển chứng cứ (T3) | `backend/app/core/evidence_types.py`, `docs/EVIDENCE_DICTIONARY.md` |
| Quan hệ cung (P2b) | `backend/app/services/palace_relations.py` |
| Danh mục & nhận diện cách cục (P2/P3) | `configs/cach_cuc_catalog.yaml`, `backend/app/services/cach_cuc_catalog.py`, `cach_cuc_detector.py` |
| Bảng Tứ Hóa (T5) | `configs/tu_hoa_tables.yaml`, `backend/app/services/tu_hoa_tables.py` |
| Vận năm bốn tầng (T9) | `backend/app/services/horoscope_annual.py`, `docs/ANNUAL_REPORT.md` |
| Hồ sơ sao (T6) | `backend/app/services/star_dossier.py`, `configs/star_seeds/*.yaml`, `docs/STAR_DOSSIER.md` |
| Tài liệu tham khảo sao từ skill | `backend/app/services/star_meanings_reference.py`, `docs/LOCAL_TUVI_SKILL_INTEGRATION.md` |
| Phân nhóm sao dùng chung (P5) | `backend/app/services/star_classification.py` |
| Retrieval (hybrid, RRF, FTS5) | `backend/app/services/retriever.py`, `fts.py`, `configs/retrieval.yaml` |
| RAG bridge cho horoscope | `backend/app/services/horoscope_rag_bridge.py` |
| RAG hỏi đáp KMS | `backend/app/services/rag.py` |
| Kiểm trích dẫn | `backend/app/services/citation_validator.py` |
| Provider LLM (mock/gemini/deepseek/groq) | `backend/app/services/llm_provider.py` |
| Luận giải & 5 lớp kiểm đầu ra | `backend/app/services/horoscope_interpreter.py`, `horoscope_confidence.py` |
| Cache & hợp đồng 3 mức đọc | `backend/app/services/horoscope_cache.py`, `backend/app/schemas/horoscope_contract.py` |
| Nhật ký nghiệm lý (T8) | `backend/app/services/case_validation.py`, `backend/app/api/case_validation.py`, `docs/CASE_VALIDATION.md` |
| API (FastAPI) & bảo mật | `backend/app/main.py`, `backend/app/api/governance.py` |
| UI Streamlit 3 trang | `app.py`, `frontend/horoscope_ui.py`, `frontend/star_dossier_ui.py`, `frontend/case_validation_ui.py` |
| Render lá số 12 cung | `frontend/laso_renderer.py`, `frontend/horoscope_sections.py` |
| Vector / embedding | `backend/app/services/vector_store.py`, `vector_store_qdrant.py`, `embeddings.py` |
| Chạy hệ thống | `run_local.bat`, `docs/RUN_HOROSCOPE.md` |
| Nghiệm thu T1–T11 | `docs/GOVERNANCE_ACCEPTANCE.md`, `docs/CHANGELOG_KNOWLEDGE.md` |
| Changelog tri thức | `docs/CHANGELOG_KNOWLEDGE.md` |
| Báo cáo sử dụng AI | `docs/BAO_CAO_SU_DUNG_AI.md` |
| Skill cho tác tử (T10) | `skills/tu-vi-kms/SKILL.md`, `scripts/validate_skill.py` |
| Cấu hình runtime | `backend/app/core/config.py`, `.env.example` |
| CI | `.github/workflows/test.yml` |

## PHỤ LỤC B — Hướng dẫn chạy hệ thống

Tóm tắt (Windows PowerShell, từ gốc repo; chi tiết trong `docs/RUN_HOROSCOPE.md`):

```powershell
# 1) Môi trường (repo hiện chưa có .venv; máy phát triển dùng Python 3.12)
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements-backend.txt

# 2) Terminal 1 — backend API
./.venv/Scripts/python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# 3) Terminal 2 — giao diện (entrypoint chính, 3 trang)
./.venv/Scripts/python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501

# hoặc dùng script có sẵn
./run_local.bat

# 4) Kiểm thử
./.venv/Scripts/python.exe -m pytest tests/ -q
./.venv/Scripts/python.exe -m pytest tests/ -m "not heavy"   # như CI
```

Cần DB `data/processed/kms.db` đã import/index để xem nguồn sách. Các chế độ khi demo:

| Chế độ | Cách chạy | Ghi chú |
|---|---|---|
| Không AI (dữ kiện) | UI chọn mức **"Lá số & dữ kiện"**; hoặc `provider=mock` khi gọi API | Không cần API key, chạy offline |
| AI (mặc định) | Để trống/`auto`: backend tự chọn provider theo key có sẵn | Cần ít nhất một key Gemini/DeepSeek/Groq |
| Gọi API trực tiếp | `KMS_API_KEY` nếu bật bảo vệ; header `X-API-Key` | Có rate limit 10 req/phút cho `/horoscope*` |

## PHỤ LỤC C — Thuyết minh số liệu và phương pháp

- **Thời điểm chụp:** 05/11/2026 (Asia/Saigon), trên working tree tại commit `b163d37` **có thay đổi chưa commit** (đa provider, UI P4/P5). Số liệu là **ảnh chụp**, không phải mốc phát hành.
- **Dữ liệu DB:** đọc **chỉ đọc** (`file:...?mode=ro`) trên `data/processed/kms.db` (20,4 MB); đếm trực tiếp bằng SQL, không sửa dữ liệu. Script audit kèm theo: `docs/_report_audit/db_stats.py`, `spot_check.py`, `list_routes.py`.
- **API:** đếm route bằng `app.openapi()` (17 path), không suy đoán từ tài liệu.
- **Kiểm thử:** chạy `python -m pytest tests/ -q` trên Python 3.12 **hai lần** với hai cấu hình provider (mục 7.3); đếm case bằng `--collect-only`. Con số **351 `xfail`** là các sai khác an sao đã biết (T4), được khai báo strict.
- **Bất nhất cần nêu rõ (không tự ý sửa):**
  - `index_manifest.json` ghi `embedding_model: gemini-embedding-001`, `embedding_provider: gemini`, 30 vector; trong khi `config.py` mặc định embedding **local** `BAAI/bge-m3`. Báo cáo trích **artefact lịch sử** cho con số 30 vector và trích **code** cho cấu hình hiện hành.
  - `.env.example` ghi `KMS_HOROSCOPE_MAX_TOKENS=8192` trong khi `config.py` mặc định 12.288; `.env.example` cũng chưa phủ nhiều biến mới (`KMS_LLM_PROVIDER`, `GROQ_*`, `DEEPSEEK_*`, cache...).
  - `frontend/horoscope_view.py::confidence_badge` hiện trả chuỗi rỗng có chủ đích (ẩn badge tin cậy theo gói 3), trong khi tài liệu và test cũ vẫn mô tả badge — đây là điểm cần đồng bộ tài liệu/UI/test.
- **Nguyên tắc trình bày:** phân biệt rõ (a) thành phần **xử lý thông thường** (an sao, FTS5, citation validator, journal, UI); (b) **AI tạo sinh** (tổng hợp văn bản qua provider); và (c) **chưa nghiệm thu** (groundedness trên mô hình thật, dense index, Recall mục tiêu, audit 300 mẫu).
- **Tránh tuyên bố vượt bằng chứng:** không gọi bài luận là "đã được sách chứng minh" (nguồn mới là ngữ cảnh đưa cho mô hình); không tuyên bố tìm kiếm ngữ nghĩa "đã triển khai đầy đủ" khi vector index mới có 30/4.350; không tuyên bố "toàn bộ test xanh" khi còn ca đỏ.

## PHỤ LỤC D — Ma trận nghiệm thu tri thức (T1–T11) và P1–P8

Nguồn: `docs/GOVERNANCE_ACCEPTANCE.md` (nghiệm thu 03/11/2026), `docs/CHANGELOG_KNOWLEDGE.md`, `tests/plans/ACTIVE_TEST_PLAN.md`.

| Mã | Nội dung | Trạng thái | Bằng chứng chính |
|---|---|---|---|
| T1 | Độ tin cậy giờ sinh A–D; C/D chỉ kết luận cấu trúc | PASSED | `horoscope_confidence.py`, `test_horoscope_input_confidence.py` |
| T2 | Bốn bậc tin cậy, cấm phần trăm, đếm fact_id khác nhau | PASSED | `test_horoscope_conclusion_confidence.py` |
| T3 | 10 loại chứng cứ + phản chứng bắt buộc | PASSED | `core/evidence_types.py`, `docs/EVIDENCE_DICTIONARY.md` |
| T4 | Kiểm chéo an sao độc lập (44 vector, 351 sai khác) | PASSED (có xfail) | `docs/LASOTUVI_CROSSCHECK.md`, issue #1 |
| T5 | Bảng Tứ Hóa cấu hình, 2 nguồn, 40 mục | PASSED | `configs/tu_hoa_tables.yaml`, `test_tu_hoa_tables.py` |
| T6 | Hồ sơ sao 14 nhóm, seed ngoài canonical | PASSED | `star_dossier.py`, `docs/STAR_DOSSIER.md` |
| T7 | Cổng tri thức A/B/C + quarantine nguồn D | PASSED | `knowledge_gate.py`, `docs/KNOWLEDGE_GATE.md` |
| T8 | Nhật ký nghiệm lý bất biến, ngưỡng 30 ca | PASSED | `case_validation.py`, `docs/CASE_VALIDATION.md` |
| T9 | Vận năm bốn tầng, so năm ±1 | PASSED | `horoscope_annual.py`, `docs/ANNUAL_REPORT.md` |
| T10 | Skill API 4 chế độ, validator + CI | PASSED | `skills/tu-vi-kms/`, `scripts/validate_skill.py` |
| T11 | Changelog tri thức trước→sau + nghiệm thu tích hợp | PASSED | `docs/CHANGELOG_KNOWLEDGE.md`, `GOVERNANCE_ACCEPTANCE.md` |
| P1 | Hợp đồng 3 mức đọc, tách `reading_mode` khỏi provider | PASSED | `schemas/horoscope_contract.py` (contract v2) |
| P2 | Chuẩn hóa 30 quy tắc cách cục (4 trạng thái, chưa duyệt) | PASSED | `configs/cach_cuc_catalog.yaml` |
| P2b | Module quan hệ cung dùng chung | PASSED | `palace_relations.py` |
| P3 | Nhận diện cách cục bằng code, chặn AI thêm rule | PASSED | `cach_cuc_detector.py` |
| P4 | Tín hiệu lưu niên: gộp vai trò, mức tập trung v2, "vì sao" | PASSED | `test_luu_nien_signals.py` |
| P5 | Lá số lên đầu trang, phân nhóm sao dùng chung, mobile | PASSED | `star_classification.py`, `laso_renderer.py` |
| P6–P7 | Ba mức đọc, AI chuyên sâu, sắp xếp lại trang | PASSED (theo test plan) | `test_horoscope_three_modes.py`, `test_horoscope_sections.py` |
| P8 | Bộ 12 ca nghiệm thu chất lượng + rubric 6 tiêu chí | PASSED | `test_p8_quality_acceptance.py` |

> Lưu ý: "PASSED" ở đây là **trạng thái theo test plan tại thời điểm 03/11/2026** và các gói review 04/11. Bộ test hiện tại có 7–16 ca đỏ như nêu ở §7.3 do thay đổi mới nhất chưa được phản ánh hết trong test — báo cáo không dùng chữ "PASSED" để che các ca đỏ này.

## PHỤ LỤC E — Nhật ký cập nhật báo cáo (v1.0 → v2.0)

| # | Báo cáo v1.0 (01/11/2026) | Báo cáo v2.0 (05/11/2026) |
|---|---|---|
| 1 | 5 endpoint | **17 endpoint** (thêm `horoscope/ask`, `horoscope/annual`, 2 alias `stars/dossier`, 7 endpoint journal) |
| 2 | Chỉ Gemini + mock | **4 provider** (mock/gemini/deepseek/groq) + chuỗi dự phòng; chat mặc định Groq `openai/gpt-oss-20b` |
| 3 | "max tokens 2.500", "gọi tối đa 2 lần" | **12.288 token** theo 3 mức đọc; 2 lần sinh × số model trong chuỗi; timeout kẹp 5–60 giây |
| 4 | Chưa nhắc bảo mật API | **X-API-Key (401), rate limit 10 req/phút (429), CORS allowlist** |
| 5 | 8 bảng dữ liệu | **17 bảng nghiệp vụ** (thêm `chunk_members`, `audit_samples`, journal T8, 2 bảng cache) |
| 6 | "74 passed" (01/11) | **42 file, 2.665 case**; chạy 05/11: **2.293/16/351** và **2.307/7/351** (hai cấu hình) |
| 7 | UI 1 trang luận giải | **3 trang** (luận giải, hồ sơ sao, nhật ký nghiệm lý) + 7 khối + lá số 12 cung 2 layout |
| 8 | Chỉ "trust tier + citation + abstention" | **6 lớp quản trị**: gate T7, tier, evidence T3, kiểm sinh văn bản, citation, journal T8 |
| 9 | Nhắc `gemini_embeddings.py` (không tồn tại) | Sửa còn `embeddings.py`; nêu bất nhất manifest ↔ code (Phụ lục C) |
| 10 | "Vòng phản hồi" là tương lai | Đã có **nhật ký nghiệm lý** (ghi nhận), nhưng chưa khép vòng về canonical — ghi rõ là hạn chế |
| 11 | Không nhắc skill, tài liệu nghiên cứu | Bổ sung **skill `tu-vi-kms` v1.0**, 13 tài liệu mới, 292 bài tài liệu tham khảo ngoài RAG |
| 12 | Không nêu trạng thái test đỏ/CI | Nêu **CI 4 bước**, trạng thái test thật, 351 xfail T4 và nguyên nhân 7–16 ca đỏ |

---

## Gợi ý khi THUYẾT TRÌNH trước giảng viên (kèm theo, không nằm trong báo cáo)

1. **Mở đầu bằng khung KMS** (Wiig Build–Hold–Pool–Use), không phải bằng "bói toán".
2. **Đổ spotlight** vào 6 lớp quản trị tri thức: cổng T7 → trust tier → provenance/evidence → kiểm soát sinh văn bản → citation/abstention → nhật ký nghiệm lý.
3. **Nói trước các giới hạn** (OCR chưa duyệt, Recall 0,588, vector index 30/4.350, 7–16 test đỏ tùy môi trường, chất lượng văn bản mô hình thật chưa nghiệm thu) → ăn điểm trung thực.
4. **Kịch bản demo 5–7 phút:** mở bảng thống kê tier → mở 1 bản ghi đối chiếu trang PDF → mở hồ sơ sao (thấy 14 nhóm tách 3 sách) → hỏi đúng thuật ngữ → hỏi cách nói thông thường → mở bảng vận năm bốn tầng (chỉ dữ kiện, không AI) → tạo 1 ca nhật ký nghiệm lý và khóa dự đoán → chỉ 4 công đoạn Wiig trên màn hình.
5. **Chuẩn bị câu hỏi phản biện:** "Vì sao dùng nhiều nhà cung cấp AI?" → trả lời: để không phụ thuộc một dịch vụ, nhưng nguồn tri thức và khuôn kiểm soát không đổi; "Vì sao chưa dùng AI cho hồ sơ sao/vận năm?" → vì đó là **sản phẩm dữ kiện**, phải tất định và kiểm được, AI chỉ diễn đạt.
