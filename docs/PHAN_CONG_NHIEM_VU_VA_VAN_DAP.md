# CẨM NANG PHÂN CÔNG NHIỆM VỤ & BỘ BẰNG CHỨNG VẤN ĐÁP BẢO VỆ ĐỒ ÁN
## HỆ THỐNG QUẢN TRỊ TRI THỨC (KMS) TỬ VI
*(Tài liệu lưu hành nội bộ nhóm — Gồm 5 Thành viên + 1 Nhóm trưởng)*

---

## MỤC LỤC
1. [Chiến lược Tổng thể & Khung Thuyết trình của Nhóm](#1-chiến-lược-tổng-thể--khung-thuyết-trình-của-nhóm)
2. [Bảng Ma trận Phân công 6 Thành viên](#2-bảng-ma-trận-phân-công-6-thành-viên)
3. [Chi tiết Phân hệ, Bằng chứng & Kịch bản Vấn đáp từng Thành viên](#3-chi-tiết-phân-hệ-bằng-chứng--kịch-bản-vấn-đáp-từng-thành-viên)
   - [Thành viên 1: Kỹ sư Dữ liệu & Cổng Quản trị Tri thức](#thành-viên-1-kỹ-sư-dữ-liệu--cổng-quản-trị-tri-thức-build)
   - [Thành viên 2: Kỹ sư Động cơ Chiêm tinh & Phân tích Cách cục](#thành-viên-2-kỹ-sư-động-cơ-chiêm-tinh--phân-tích-cách-cục-deterministic-engine)
   - [Thành viên 3: Kỹ sư Cơ sở Dữ liệu & Tìm kiếm Lai](#thành-viên-3-kỹ-sư-cơ-sở-dữ-liệu--tìm-kiếm-lai-hold--pool)
   - [Thành viên 4: Kỹ sư RAG, Quản trị LLM & Kiểm soát Trích dẫn](#thành-viên-4-kỹ-sư-rag-quản-trị-llm--kiểm-soát-trích-dẫn-use--governance)
   - [Thành viên 5: Kỹ sư Giao diện & Nhật ký Nghiệm lý Thực nghiệm](#thành-viên-5-kỹ-sư-giao-diện--nhật-ký-nghiệm-lý-thực-nghiệm-presentation--validation)
   - [Nhóm trưởng: Kiến trúc sư Hệ thống & Trưởng nhóm Kỹ thuật](#nhóm-trưởng-kiến-trúc-sư-hệ-thống--trưởng-nhóm-kỹ-thuật-system-architect)
4. [Bộ Câu hỏi Bẫy / Phản biện Liên phân hệ của Giảng viên](#4-bộ-câu-hỏi-bẫy--phản-biện-liên-phân-hệ-của-giảng-viên)
5. [Quy trình 5 Phút Chuẩn bị Bằng chứng trên Máy tính](#5-quy-trình-5-phút-chuẩn-bị-bằng-chứng-trên-máy-tính)

---

## 1. CHIẾN LƯỢC TỔNG THỂ & KHUNG THUYẾT TRÌNH CỦA NHÓM

### 1.1. Triết lý ăn điểm của Đồ án
Khi giảng viên hỏi: *"Hệ thống này khác gì một con Chatbot dùng ChatGPT bình thường?"*
**Cả nhóm phải đồng thanh khẳng định 3 luận điểm cốt lõi:**
1. **Chatbot thông thường chỉ có tầng sinh text; KMS Tử Vi là một Hệ thống Quản trị Tri thức hoàn chỉnh có 6 lớp kiểm soát chất lượng.**
2. **Logic An sao & Phân tích Cung là TẤT ĐỊNH (Deterministic 100% bằng code thuật toán, không dùng AI).** AI tuyệt đối không được phép tự tính toán vị trí sao để tránh ảo giác (*hallucination*).
3. **AI chỉ là tầng Ứng dụng (Use), không phải nguồn tri thức.** Mọi câu chữ AI sinh ra đều bị ép buộc phải trích dẫn đến từng số trang sách có thật (`[NPL: p.12]`). Nếu không có sách bảo chứng, hệ thống sẽ **Từ chối trả lời (Abstention)**.

### 1.2. Kịch bản mở đầu của Nhóm trưởng (30 giây định hình ấn tượng)
> *"Kính thưa cô và hội đồng, dự án của nhóm em được thiết kế theo đúng chu trình Quản trị Tri thức kinh điển của Wiig gồm 4 giai đoạn: **Build (Xây dựng) – Hold (Lưu trữ) – Pool (Khai thác) – Use (Ứng dụng)**. Nhóm em gồm 6 thành viên, mỗi bạn phụ trách chuyên sâu một mắt xích kỹ thuật có sản phẩm mã nguồn và bài kiểm thử độc lập:*
> - *Bạn 1: Phụ trách **Build** — Chuẩn hóa 10.456 bản ghi và Cổng kiểm duyệt tri thức.*
> - *Bạn 2: Phụ trách **Động cơ An sao tất định** — 30 Cách cục cổ điển và Bảng Tứ Hóa.*
> - *Bạn 3: Phụ trách **Hold & Pool** — Schema 17 bảng SQLite, FTS5 tiếng Việt và Vector Search.*
> - *Bạn 4: Phụ trách **Use & Governance** — RAG Bridge, 3 mức đọc và Bộ kiểm soát trích dẫn.*
> - *Bạn 5: Phụ trách **Presentation & Validation** — Giao diện 12 cung và Nhật ký nghiệm lý khóa dự đoán.*
> - *Em (Nhóm trưởng): Phụ trách **Kiến trúc hệ thống**, điều phối 17 API FastAPI và chu trình kiểm thử TDD toàn cục."*

---

## 2. BẢNG MA TRẬN PHÂN CÔNG 6 THÀNH VIÊN

| STT | Thành viên | Phân hệ đảm nhiệm | File Code dẫn chứng | Lệnh Pytest riêng lẻ | File Tài liệu minh chứng |
|:---:|---|---|---|---|---|
| **1** | **Thành viên 1** | Quản trị Dữ liệu & Cổng Tri thức (Build) | `backend/app/services/knowledge_gate.py`<br>`backend/app/services/tiering.py`<br>`backend/app/services/chunker.py` | `pytest tests/test_knowledge_gate.py tests/test_two_way_scope.py -v` | `docs/data_dictionary.md`<br>`docs/KNOWLEDGE_GATE.md`<br>`docs/EVIDENCE_DICTIONARY.md` |
| **2** | **Thành viên 2** | Động cơ Chiêm tinh & Cách cục (Domain Rules) | `backend/app/services/cach_cuc_detector.py`<br>`backend/app/services/cach_cuc_catalog.py`<br>`backend/app/services/tu_hoa_tables.py` | `pytest tests/test_cach_cuc_detector.py tests/test_tu_hoa_tables.py -v` | `docs/LASOTUVI_CROSSCHECK.md`<br>`docs/issues/T4_AN_SAO_DISCREPANCIES.md` |
| **3** | **Thành viên 3** | Database & Tìm kiếm Lai (Hold - Pool) | `backend/app/db/models.py`<br>`backend/app/services/fts.py`<br>`backend/app/services/retriever.py` | `pytest tests/test_cache.py tests/test_dbdiagram_challenge.py -v` | `docs/_shared/dbdiagram/kms_tuvi.sql`<br>`docs/_shared/d2-architect/kms_tuvi_architect.d2` |
| **4** | **Thành viên 4** | RAG & Quản trị LLM (Use - Governance) | `backend/app/services/horoscope_rag_bridge.py`<br>`backend/app/services/citation_validator.py`<br>`backend/app/services/llm_provider.py` | `pytest tests/test_citation_validator.py tests/test_horoscope_three_modes.py -v` | `docs/BAO_CAO_SU_DUNG_AI.md`<br>`docs/ANNUAL_REPORT.md`<br>`docs/STAR_DOSSIER.md` |
| **5** | **Thành viên 5** | Giao diện & Nhật ký Nghiệm lý (Presentation) | `frontend/app.py`<br>`frontend/laso_renderer.py`<br>`frontend/case_validation_ui.py` | `pytest tests/test_case_validation.py tests/test_horoscope_frontend.py -v` | `docs/CASE_VALIDATION.md`<br>`docs/HOROSCOPE_UI_DESIGN.md` |
| **6** | **Nhóm trưởng** | Kiến trúc Hệ thống & Tích hợp (Architect) | `backend/app/main.py`<br>`backend/app/core/config.py`<br>`Dockerfile`, `render.yaml` | `pytest tests/ -q`<br>*(Chạy toàn bộ >2.100 tests)* | `docs/REPORT_KMS_TU_VI.md`<br>`docs/KMS_TuVi_Development_Plan.md` |

---

## 3. CHI TIẾT PHÂN HỆ, BẰNG CHỨNG & KỊCH BẢN VẤN ĐÁP TỪNG THÀNH VIÊN

---

### THÀNH VIÊN 1: Kỹ sư Dữ liệu & Cổng Quản trị Tri thức (Build)
*(Phù hợp: Bạn tỉ mỉ, thích làm sạch dữ liệu, xây dựng quy tắc đầu vào)*

#### 1. Phạm vi công việc:
- Thu thập và chuẩn hóa hơn **10.456 bản ghi tri thức** từ 3 cuốn sách kinh điển:
  - Nguyễn Phát Lộc (*Tử Vi Tổng Hợp*): 2.191 bản ghi (Trích xuất PDF cấu trúc SPO).
  - Bửu Đình (*Tử Vi Ứng Dụng*): 4.450 bản ghi (Tesseract OCR từ 7 tập PDF).
  - Đẩu Số Toàn Thư: 3.815 bản ghi (Text layer, nhiều thơ phú).
- Xây dựng **Cổng Kiểm duyệt Tri thức (Knowledge Gate - T7)**: Phê duyệt dữ liệu theo 3 tiêu chí:
  - **Điều kiện A:** Bắt buộc có tên sách và số trang thực tế.
  - **Điều kiện B:** Xác định rõ trường phái học thuật.
  - **Điều kiện C:** Đã qua đối chiếu ca thực tế.
- Xây dựng thuật toán phân tầng dữ liệu **Trust Tier (1, 2, 3, 9)** và cơ chế **Quarantine (Cách ly)** các nguồn dữ liệu trôi nổi trên mạng/diễn đàn.

#### 2. Dẫn chứng Mã nguồn (Mở các file này ra khi cô yêu cầu):
- `backend/app/services/knowledge_gate.py`:
  - Hàm `validate_item()`: Kiểm tra 3 điều kiện A, B, C.
  - Hàm `quarantine_source()`: Tự động gắn cờ và loại bản ghi thiếu trang hoặc nguồn diễn đàn ra vùng cách ly.
- `backend/app/services/tiering.py`:
  - Hàm `compute_trust_tier()`: Gán Tier 1 (NPL), Tier 2 (DAU), Tier 3 (BD), Tier 9 (Lỗi OCR).
- `backend/app/services/chunker.py`:
  - Thuật toán gộp các câu phú ngắn dưới 40 ký tự thành các chunk tri thức hoàn chỉnh mang đủ ngữ cảnh.
- `configs/column_mapping.yaml`: File cấu hình ánh xạ cột từ Excel sang Database (không hard-code tên cột).

#### 3. Dẫn chứng Tài liệu & Kiểm thử:
- **Tài liệu:** Mở file `docs/data_dictionary.md` và `docs/KNOWLEDGE_GATE.md`.
- **Lệnh chạy kiểm thử trực tiếp trên máy:**
  ```powershell
  pytest tests/test_knowledge_gate.py tests/test_two_way_scope.py -v
  ```
  *(Màn hình hiện xanh lá cây với hàng chục test cases pass: kiểm tra bản ghi thiếu trang bị chặn, bản ghi hợp lệ được thông qua).*

#### 4. Kịch bản Vấn đáp Giảng viên (Cheat Sheet):
- **Câu hỏi 1: "Em làm phần nào trong dự án?"**
  - **Trả lời:** *"Dạ thưa cô, em phụ trách tầng **Build (Xây dựng tri thức)**. Nhiệm vụ của em là chuẩn hóa hơn 10.400 bản ghi từ 3 cuốn sách cổ thành cấu trúc Subject - Predicate - Object, gán nhãn độ tin cậy Trust Tier và lập trình **Cổng Kiểm duyệt Tri thức (Knowledge Gate)** để ngăn chặn tri thức rác lọt vào Database."*
- **Câu hỏi 2: "Tại sao em không crawl hết dữ liệu các trang web tử vi trên mạng về cho phong phú?"**
  - **Trả lời:** *"Dạ thưa cô, nguyên lý của Quản trị Tri thức là **Garbage In, Garbage Out**. Các bài viết trên mạng đa phần sao chép lẫn nhau, không rõ tác giả, không có số trang kiểm chứng. Hệ thống của em áp dụng chính sách cách ly (Quarantine): Mọi dữ liệu không chứng minh được số trang sách thực tế đều bị cổng Knowledge Gate chặn lại, chỉ cho phép dữ liệu đạt Tier 1–3 đi tiếp vào hệ thống tìm kiếm."*
- **Câu hỏi 3: "Sách Bửu Đình bị lỗi OCR thì em xử lý như thế nào?"**
  - **Trả lời:** *"Dạ, sách Bửu Đình quét bằng OCR Tesseract nên có 1.759 bản ghi bị nghi ngờ lỗi chính tả. Em phân loại chúng vào **Tier 9 (OCR_REVIEW_REQUIRED)** và cấu hình mặc định loại hẳn Tier 9 ra khỏi chỉ mục tìm kiếm RAG để không làm hỏng câu trả lời của AI."*

---

### THÀNH VIÊN 2: Kỹ sư Động cơ Chiêm tinh & Phân tích Cách cục (Deterministic Engine)
*(Phù hợp: Bạn giỏi tư duy thuật toán, toán học, thích giải thích logic quy tắc)*

#### 1. Phạm vi công việc:
- Tích hợp và làm chủ động cơ an sao tất định 108 sao, 12 cung, can chi, cục số (Zero-AI).
- Lập trình **Bộ nhận diện 30 Cách cục kinh điển** (*Tử Phủ Vũ Tướng, Sát Phá Tham, Cự Nhật, Đồng Lương,...*) dựa trên ma trận tọa độ sao tại bản cung, tam hợp và xung chiếu.
- Xây dựng **Bộ Kiểm chuẩn chéo (Cross-check) độc lập** với 44 test vector lá số và 1.784 trường dữ liệu để phát hiện sai khác giữa các trường phái an sao.
- Thiết kế **Bảng Tứ Hóa đa trường phái** hỗ trợ chuyển đổi linh hoạt giữa các quan điểm chiêm tinh học.

#### 2. Dẫn chứng Mã nguồn:
- `backend/app/services/cach_cuc_detector.py`:
  - Hàm `detect_cach_cuc()`: Quét toàn bộ 12 cung, đối chiếu danh sách sao với điều kiện tiên quyết của từng cách cục.
- `backend/app/services/cach_cuc_catalog.py`:
  - Định nghĩa tường minh cấu trúc, tên gọi, tính chất và nguồn sách của 30 cách cục cổ điển.
- `backend/app/services/tu_hoa_tables.py`:
  - Cấu trúc dữ liệu 10 Can Tứ Hóa (Hóa Lộc, Hóa Quyền, Hóa Khoa, Hóa Kỵ), quản lý điểm khác biệt giữa các sách (ví dụ Can Canh: Hóa Khoa là Thái Âm hay Thiên Phủ).
- `backend/app/services/palace_relations.py`:
  - Hàm tính toán các quan hệ hình học: Tam hợp (Dần - Ngọ - Tuất,...), Xung chiếu, Nhị hợp, Giáp cung.

#### 3. Dẫn chứng Tài liệu & Kiểm thử:
- **Tài liệu:** Mở file `docs/LASOTUVI_CROSSCHECK.md` và `docs/issues/T4_AN_SAO_DISCREPANCIES.md`.
- **Lệnh chạy kiểm thử trực tiếp trên máy:**
  ```powershell
  pytest tests/test_cach_cuc_detector.py tests/test_tu_hoa_tables.py tests/test_palace_relations.py -v
  ```
  *(Chứng minh thuật toán nhận diện cách cục và ma trận tam hợp pass 100%).*

#### 4. Kịch bản Vấn đáp Giảng viên (Cheat Sheet):
- **Câu hỏi 1: "Em làm phần nào trong dự án?"**
  - **Trả lời:** *"Dạ thưa cô, em phụ trách tầng **Động cơ logic tất định (Deterministic Domain Logic)**. Em chịu trách nhiệm viết bộ nhận diện tự động 30 cách cục kinh điển và xây dựng bộ kiểm chuẩn chéo 44 lá số để kiểm soát tính chính xác của thuật toán an sao."*
- **Câu hỏi 2: "Tại sao phần an sao và nhận diện cách cục này không dùng AI cho nó tự học và đoán?"**
  - **Trả lời:** *"Dạ thưa cô, thuật toán Tử Vi là một hệ thống quy tắc toán học tất định (ví dụ ngũ hành nạp âm, cục số, phép nghịch số). Nếu để LLM tự an sao, mô hình xác suất sẽ bị ảo giác, đặt sai vị trí sao hoặc bịa ra sao không có thật. Vì vậy, nhóm em quyết định tầng An sao và Cách cục phải viết bằng code Python thuần túy 100%, bảo đảm kết quả đầu ra luôn chuẩn xác và có thể tái lập."*
- **Câu hỏi 3: "Khi có sự mâu thuẫn giữa các trường phái (ví dụ Can Canh Tứ Hóa), em giải quyết thế nào?"**
  - **Trả lời:** *"Dạ, em không tự ý chọn một bên mà tạo file cấu hình `tu_hoa_tables.py` minh bạch hóa cả 2 trường phái. Trong bộ test, em đánh dấu 351 điểm khác biệt đã biết dưới dạng `strict xfail` có tài liệu dẫn chứng, giúp hệ thống không bị crash mà người dùng vẫn tra cứu được nguồn gốc khác biệt."*

---

### THÀNH VIÊN 3: Kỹ sư Cơ sở Dữ liệu & Tìm kiếm Lai (Hold - Pool)
*(Phù hợp: Bạn thích Database, SQL, Indexing, Vector Embeddings)*

#### 1. Phạm vi công việc:
- Thiết kế Lược đồ cơ sở dữ liệu quan hệ gồm **17 bảng SQLite** chuẩn hóa (`books`, `knowledge_items`, `chunks`, `evidences`, `case_validations`,...).
- Lập trình hệ thống tìm kiếm từ khóa toàn văn **SQLite FTS5 (Full-Text Search)** có bộ tokenizer tùy chỉnh bỏ dấu tiếng Việt để tìm kiếm chính xác các thuật ngữ chiêm tinh.
- Tích hợp **Vector Database (Qdrant)** và mô hình Dense Embedding đa ngữ (`BAAI/bge-m3`).
- Cài đặt thuật toán xếp hạng lai **Reciprocal Rank Fusion (RRF, k=60)** kết hợp điểm số của FTS5 và Dense Vector.
- Thiết kế hệ thống **Bộ nhớ đệm (Cache)** giảm thiểu thời gian truy xuất lặp lại.

#### 2. Dẫn chứng Mã nguồn:
- `backend/app/db/models.py`: Khai báo 17 bảng SQLAlchemy đầy đủ quan hệ Khóa chính (PK), Khóa ngoại (FK) và Index.
- `backend/app/services/fts.py`:
  - Hàm `strip_accents()`: Bỏ dấu tiếng Việt phục vụ tìm kiếm FTS5.
  - Hàm `search_fts()`: Truy vấn bảng ảo `chunks_fts` với thuật toán chấm điểm BM25.
- `backend/app/services/retriever.py`:
  - Hàm `hybrid_search()`: Gọi song song FTS5 và Qdrant Vector Search.
  - Hàm `reciprocal_rank_fusion()`: Áp dụng công thức $Score(d) = \sum \frac{1}{60 + rank(d)}$ để hợp nhất thứ hạng tìm kiếm.
- `backend/app/services/cache.py`: Quản lý bộ nhớ đệm cache payload của lá số.

#### 3. Dẫn chứng Tài liệu & Kiểm thử:
- **Tài liệu:** Mở file `docs/_shared/dbdiagram/kms_tuvi.sql`, file `kms_tuvi.dbml` và sơ đồ kiến trúc `docs/_shared/d2-architect/kms_tuvi_architect.d2`.
- **Lệnh chạy kiểm thử trực tiếp trên máy:**
  ```powershell
  pytest tests/test_cache.py tests/test_horoscope_cache.py tests/test_dbdiagram_challenge.py -v
  ```
  *(Chứng minh 17 bảng quan hệ thỏa mãn toàn bộ ràng buộc và hệ thống Cache hoạt động trơn tru).*

#### 4. Kịch bản Vấn đáp Giảng viên (Cheat Sheet):
- **Câu hỏi 1: "Em làm phần nào trong dự án?"**
  - **Trả lời:** *"Dạ thưa cô, em phụ trách tầng **Hold (Lưu trữ) và Pool (Truy xuất)** trong khung KMS. Em thiết kế Schema 17 bảng SQLite, lập trình bộ tìm kiếm từ khóa FTS5 tiếng Việt không dấu và xây dựng bộ truy xuất lai Hybrid Search kết hợp Vector Search qua thuật toán RRF $k=60$."*
- **Câu hỏi 2: "Tại sao đã dùng Vector Search thông minh rồi mà em còn phải cài đặt thêm SQLite FTS5 làm gì?"**
  - **Trả lời:** *"Dạ thưa cô, Vector Search tìm kiếm theo ngữ nghĩa rất tốt nhưng lại thường xuyên bỏ sót hoặc tìm nhầm các danh từ riêng chiêm tinh (ví dụ tìm sao 'Hóa Kỵ' có thể nhầm sang sao mang nghĩa tiêu cực khác). Ngược lại, FTS5 bắt trúng 100% từ khóa tên sao. Em dùng thuật toán RRF để lấy điểm mạnh của cả hai: FTS5 đảm bảo độ chính xác danh từ, còn Vector đảm bảo độ phủ ngữ nghĩa."*
- **Câu hỏi 3: "Hệ thống bảo đảm nguyên tắc 'Ba tiếng nói' như thế nào ở tầng Database?"**
  - **Trả lời:** *"Dạ, trong hàm `hybrid_search()`, em truy vấn độc lập và lấy top-10 chunk cho từng cuốn sách (NPL, BD, DAU) riêng biệt, sau đó mới trả về cho tầng RAG. Nhờ đó không bao giờ có hiện tượng sách Nguyễn Phát Lộc đè bẹp hoặc tràn ngữ cảnh sang sách Bửu Đình."*

---

### THÀNH VIÊN 4: Kỹ sư RAG, Quản trị LLM & Kiểm soát Trích dẫn (Use - Governance)
*(Phù hợp: Bạn thích AI, Prompt Engineering, an toàn thông tin AI và chống ảo giác)*

#### 1. Phạm vi công việc:
- Xây dựng **RAG Bridge**: Bóc tách các đặc trưng của lá số thành các truy vấn tri thức chuyển cho bộ Retriever.
- Thiết kế **3 Mức đọc (Reading Modes)**: `du_lieu` (100% tất định, không gọi AI), `giai_thich`, và `chuyen_sau`.
- Xây dựng **Bộ xác thực trích dẫn (Citation Validator)**: Kiểm soát nghiêm ngặt đầu ra của LLM, bắt buộc mọi nhận định phải dẫn nguồn đúng `[Sách, Trang PDF]`.
- Thiết lập **Chính sách Giờ sinh (A–D)** và **Độ tin cậy kết luận**: Tự động hạ bậc tin cậy hoặc từ chối kết luận nếu giờ sinh thuộc nhóm C/D (không rõ giờ/ước lượng).
- Tích hợp 4 nhà cung cấp LLM (**Gemini, DeepSeek, Groq, Mock**) với cơ chế **Fallback Chain** tự động chuyển tuyến khi gặp sự cố mạng hoặc hết quota.

#### 2. Dẫn chứng Mã nguồn:
- `backend/app/services/horoscope_rag_bridge.py`: Hàm trích xuất sao bản cung, tam hợp, tứ hóa thành câu truy vấn tri thức chuẩn tắc.
- `backend/app/services/citation_validator.py`:
  - Hàm `validate_citations()`: Phân tích cú pháp văn bản của AI; nếu AI bịa ra trang sách không nằm trong Context được cấp, hàm sẽ hủy bỏ hoặc gán cờ cảnh báo vi phạm.
- `backend/app/services/horoscope_interpreter.py`:
  - Logic phân luồng 3 mức đọc và gắn kèm nhãn thuận chứng / phản chứng.
- `backend/app/services/horoscope_confidence.py`:
  - Đánh giá 4 bậc tin cậy: Yếu, Trung bình, Mạnh, Rất mạnh. Cấm hoàn toàn việc sinh tỷ lệ phần trăm giả tạo (như "80% giàu có").
- `backend/app/services/llm_provider.py`:
  - Class `MultiProviderLLM`: Điều phối gọi Gemini ➔ DeepSeek ➔ Groq ➔ Mock.

#### 3. Dẫn chứng Tài liệu & Kiểm thử:
- **Tài liệu:** Mở file `docs/BAO_CAO_SU_DUNG_AI.md`, `docs/ANNUAL_REPORT.md` và `docs/STAR_DOSSIER.md`.
- **Lệnh chạy kiểm thử trực tiếp trên máy:**
  ```powershell
  pytest tests/test_citation_validator.py tests/test_horoscope_conclusion_confidence.py tests/test_horoscope_three_modes.py -v
  ```
  *(Chứng minh cơ chế kiểm tra trích dẫn và chặn đứng câu phán khi thiếu căn cứ pass 100%).*

#### 4. Kịch bản Vấn đáp Giảng viên (Cheat Sheet):
- **Câu hỏi 1: "Em làm phần nào trong dự án?"**
  - **Trả lời:** *"Dạ thưa cô, em phụ trách tầng **Use (Ứng dụng tri thức)** và lớp **Quản trị LLM (AI Governance)**. Em xây dựng RAG Bridge kết nối lá số với tri thức sách, lập trình bộ Citation Validator kiểm duyệt trích dẫn số trang thực tế và quản lý chuỗi Fallback giữa Gemini, DeepSeek và Groq."*
- **Câu hỏi 2: "Làm thế nào để em chứng minh mô hình AI của em không bịa đặt (hallucination) số trang?"**
  - **Trả lời:** *"Dạ thưa cô, em xây dựng module `citation_validator.py` hoạt động độc lập sau khi LLM sinh bài. Hàm này dùng Regex bóc tách mọi thẻ trích dẫn `[Tên sách, Số trang]` và đối chiếu ngược lại với danh sách các chunk thực tế được đưa vào Prompt. Nếu AI tự ý bịa một số trang không có trong Context, hệ thống sẽ phát hiện ngay lập tức và từ chối hiển thị kết quả."*
- **Câu hỏi 3: "Người dùng không nhớ rõ giờ sinh thì hệ thống xử lý thế nào?"**
  - **Trả lời:** *"Dạ, em thiết kế Chính sách giờ sinh gồm 4 mức A–D. Nếu người dùng chọn mức C hoặc D (ước lượng trong khoảng 1–2 tiếng hoặc không nhớ rõ), hệ thống của em lập tức khóa chế độ luận giải chuyên sâu và chỉ đưa ra các xu hướng chung, kèm cảnh báo rõ ràng để người dùng không ngộ nhận."*

---

### THÀNH VIÊN 5: Kỹ sư Giao diện & Nhật ký Nghiệm lý Thực nghiệm (Presentation & Validation)
*(Phù hợp: Bạn thích Frontend, giao diện người dùng, CSS, trực quan hóa dữ liệu)*

#### 1. Phạm vi công việc:
- Thiết kế và phát triển toàn bộ giao diện Web đa trang trên nền tảng **Streamlit** trực quan, hỗ trợ typography IBM Plex Sans và theme ngũ hành.
- Lập trình bộ dựng **Bản đồ 12 Cung Lá số Tử Vi (Laso Renderer)** chuẩn tỷ lệ truyền thống bằng HTML/CSS responsive.
- Xây dựng thanh công cụ tương tác: Chọn 3 mức đọc, chọn nhà cung cấp AI, Drawer mở rộng xem chi tiết trích dẫn sách.
- Xây dựng **Hệ thống Nhật ký Nghiệm lý (Case Validation Journal - T8)**: Cho phép người dùng đối chiếu lá số với biến cố cuộc đời, đi kèm cơ chế **Khóa dự đoán bất biến (Prediction Locking)** bằng SQLite Trigger.

#### 2. Dẫn chứng Mã nguồn:
- `frontend/app.py`: Điều hướng chính của ứng dụng gồm 3 trang: Luận giải lá số, Tra cứu hồ sơ sao và Nhật ký nghiệm lý.
- `frontend/laso_renderer.py` & `frontend/lasoban.py`:
  - Thuật toán vẽ lưới 12 cung (Mệnh, Phụ, Phúc, Điền,...) chuẩn vị trí không gian, tô màu sao theo Ngũ hành (Kim - Mộc - Thủy - Hỏa - Thổ).
- `frontend/case_validation_ui.py`:
  - Giao diện nhập thông tin nghiệm lý, form khóa dự đoán và hiển thị ma trận kiểm chứng.
- `backend/app/services/case_validation.py`:
  - Hàm `lock_prediction()`: Khóa vĩnh viễn dự đoán bằng Trigger trong SQLite, biến bảng thành Append-only (không cho phép sửa lén sau khi biến cố đã xảy ra).
- `frontend/assets/app.css` & `frontend/ui_themes.py`: Hệ thống style sheet và bộ màu giao diện.

#### 3. Dẫn chứng Tài liệu & Kiểm thử:
- **Tài liệu:** Mở file `docs/CASE_VALIDATION.md`, `docs/HOROSCOPE_UI_DESIGN.md` và `docs/UI_REDESIGN_2026.md`.
- **Lệnh chạy kiểm thử trực tiếp trên máy:**
  ```powershell
  pytest tests/test_case_validation.py tests/test_ui_theme_payload.py tests/test_horoscope_frontend.py -v
  ```
  *(Chứng minh logic giao diện, cấu trúc payload và cơ chế khóa bất biến của bảng nghiệm lý pass 100%).*

#### 4. Kịch bản Vấn đáp Giảng viên (Cheat Sheet):
- **Câu hỏi 1: "Em làm phần nào trong dự án?"**
  - **Trả lời:** *"Dạ thưa cô, em phụ trách tầng **Presentation (Giao diện người dùng)** và **Hệ thống Nghiệm lý thực nghiệm (T8)**. Em lập trình bộ renderer vẽ bản đồ 12 cung Tử Vi trực quan trên Streamlit và xây dựng module Nhật ký nghiệm lý khoa học có cơ chế khóa cứng dự đoán."*
- **Câu hỏi 2: "Tại sao lại cần chức năng Khóa dự đoán (Prediction Locking) trong Nhật ký nghiệm lý?"**
  - **Trả lời:** *"Dạ thưa cô, trong nghiên cứu chiêm tinh học, người ta rất hay mắc lỗi thiên kiến xác nhận (sau khi việc xảy ra rồi mới quay lại gán ghép là lá số đúng). Em xây dựng cơ chế Prediction Locking bằng Trigger trong SQLite: Khi người dùng đưa ra dự đoán cho tương lai, hệ thống sẽ khóa bản ghi đó lại (Append-only). Người dùng chỉ được ghi nhận kết quả thực tế khi biến cố đã diễn ra chứ tuyệt đối không thể sửa lại nội dung dự đoán cũ."*
- **Câu hỏi 3: "Giao diện làm thế nào để người dùng biết đoạn văn nào là do AI viết, đoạn nào là trích từ sách?"**
  - **Trả lời:** *"Dạ, em thiết kế Drawer trích dẫn và các badge màu: Mọi câu khẳng định đều có gắn thẻ nguồn (ví dụ: `[NPL: p.45]`). Khi bấm vào thẻ, giao diện sẽ mở ra đoạn trích nguyên văn trong sách để người dùng tự mình kiểm chứng."*

---

### NHÓM TRƯỞNG: Kiến trúc sư Hệ thống & Trưởng nhóm Kỹ thuật (System Architect)
*(Đảm nhiệm vai trò cầm trịch, dẫn dắt bài thuyết trình và trả lời các câu hỏi bao quát)*

#### 1. Phạm vi công việc:
- Định nghĩa toàn bộ Khung Quản trị Tri thức theo mô hình **Wiig (Build – Hold – Pool – Use)** và mô hình chuyển hóa tri thức **SECI (Nonaka & Takeuchi)**.
- Xây dựng trục xương sống Backend RESTful API với **17 Endpoints trên FastAPI** (`backend/app/main.py`), quản lý Pydantic Schemas.
- Thiết lập quy trình phát triển định hướng kiểm thử **TDD (Test-Driven Development)**: Kết hợp Claude (QA Architect) và Gemini (Implementation Engineer) để viết hơn **2.100 test cases tự động**.
- Cấu hình hạ tầng triển khai: Dockerfile, `render.yaml`, CI/CD GitHub Actions và các kịch bản chạy tự động.
- Chịu trách nhiệm về tính liên kết giữa 5 phân hệ của các bạn thành viên.

#### 2. Dẫn chứng Mã nguồn & Báo cáo:
- `backend/app/main.py`: Khai báo và cấu hình 17 route API của hệ thống.
- `backend/app/core/config.py`: Quản lý biến môi trường, đường dẫn cơ sở dữ liệu và cấu hình mô hình.
- `Dockerfile`, `docker-compose.yml`, `render.yaml`: Cấu hình container hóa ứng dụng.
- [docs/REPORT_KMS_TU_VI.md](file:///d:/Ki7/KMS_Tu_Vi/docs/REPORT_KMS_TU_VI.md): Báo cáo kỹ thuật toàn diện đồ án.
- [docs/KMS_TuVi_Development_Plan.md](file:///d:/Ki7/KMS_Tu_Vi/docs/KMS_TuVi_Development_Plan.md): Bản kế hoạch phát triển kiến trúc v1.1.

#### 3. Lệnh chạy kiểm thử bao quát toàn hệ thống:
```powershell
pytest tests/ -q
```
*(Chạy toàn bộ test suite: Hơn 2.135 passed, minh chứng cho một hệ thống vững chắc, không có lỗi hồi quy).*

#### 4. Kịch bản Vấn đáp Giảng viên (Cheat Sheet):
- **Câu hỏi 1: "Là nhóm trưởng, em phân chia kiến trúc hệ thống như thế nào để các bạn làm việc hiệu quả?"**
  - **Trả lời:** *"Dạ thưa cô, em áp dụng mô hình phân lớp rõ ràng (Clean Architecture). Em tạo các Contract giao tiếp dữ liệu chuẩn bằng Pydantic schemas tại `backend/app/schemas/`. Nhờ có các Contract này, bạn làm Data chuẩn hóa dữ liệu độc lập, bạn làm Database thiết kế DB độc lập, bạn làm Logic an sao viết thuật toán độc lập, và bạn làm Frontend chỉ cần gọi đúng API endpoint mà không bị phụ thuộc chéo vào nhau."*
- **Câu hỏi 2: "Tại sao nhóm em lại đầu tư viết tới hơn 2.000 test cases cho một đồ án môn học?"**
  - **Trả lời:** *"Dạ thưa cô, vì Tử Vi là một hệ thống tri thức phức tạp với hàng nghìn quy tắc đan xen. Khi thay đổi một tham số ở tầng RAG hoặc tầng Database, nếu không có kiểm thử tự động (TDD), hệ thống rất dễ bị lỗi hồi quy (regression bugs). Toàn bộ 2.100 tests giúp nhóm em tự tin khẳng định mọi chức năng từ an sao, trích xuất dữ liệu đến kiểm duyệt trích dẫn đều hoạt động chính xác 100%."*

---

## 4. BỘ CÂU HỎI BẪY / PHẢN BIỆN LIÊN PHÂN HỆ CỦA GIẢNG VIÊN

Dưới đây là các câu hỏi "xoáy" mà giảng viên môn KMS và AI rất hay hỏi để kiểm tra xem sinh viên có thực sự hiểu hệ thống hay không:

### Bẫy 1: "Nếu sách Bửu Đình và sách Nguyễn Phát Lộc nói mâu thuẫn nhau về một ngôi sao thì hệ thống xử lý thế nào?"
- **Ai trả lời:** Thành viên 1 hoặc Thành viên 4.
- **Cách trả lời chuẩn:** *"Dạ thưa cô, hệ thống của nhóm em tuân thủ nguyên tắc **'Giữ ba tiếng nói' (Three Voices)**. Nhóm em không bao giờ dùng AI để 'hòa giải' hay gộp chung hai quan điểm trái ngược nhau thành một. Thay vào đó, trong câu trả lời, hệ thống chia rõ hai mục: 'Theo cuốn Tử Vi Tổng Hợp (Nguyễn Phát Lộc)...' và 'Theo cuốn Tử Vi Ứng Dụng (Bửu Đình)...' kèm số trang đối chiếu của từng sách để người dùng tự đánh giá."*

### Bẫy 2: "Tại sao không lưu luôn Vector vào SQLite mà phải dùng thêm Qdrant?"
- **Ai trả lời:** Thành viên 3.
- **Cách trả lời chuẩn:** *"Dạ, SQLite rất mạnh về lưu trữ quan hệ và tìm kiếm từ khóa FTS5 (BM25), nhưng các thuật toán tìm kiếm láng giềng gần nhất (HNSW index) của Vector Search đòi hỏi cấu trúc chỉ mục bộ nhớ chuyên biệt. Nhóm em sử dụng Qdrant chuyên trách cho việc tính toán khoảng cách cosine giữa các vector embedding 1024 chiều của mô hình BGE-M3, sau đó dùng thuật toán RRF để đồng bộ kết quả với SQLite."*

### Bẫy 3: "Khi người dùng đặt một câu hỏi hoàn toàn nằm ngoài sách Tử Vi (ví dụ hỏi về thị trường chứng khoán ngày mai), hệ thống sẽ làm gì?"
- **Ai trả lời:** Thành viên 4.
- **Cách trả lời chuẩn:** *"Dạ, hệ thống áp dụng cơ chế **Abstention (Quyền từ chối)**. Khi câu hỏi gửi vào, bộ Retriever sẽ tính điểm liên quan RRF. Nếu điểm liên quan của tất cả các chunk sách đều nằm dưới ngưỡng an toàn, hệ thống sẽ lập tức dừng lại và phản hồi: 'Nội dung câu hỏi nằm ngoài phạm vi tri thức của 3 cuốn sách kinh điển', hoàn toàn không gửi prompt sang cho LLM để tránh việc AI chém gió lan man."*

### Bẫy 4: "Kiến trúc này áp dụng mô hình SECI của Nonaka & Takeuchi như thế nào?"
- **Ai trả lời:** Nhóm trưởng hoặc Thành viên 5.
- **Cách trả lời chuẩn:** *"Dạ, mô hình SECI được áp dụng qua 2 khâu rõ rệt:
  1. **Combination (Kết hợp tri thức tường minh):** Tầng Build và Hold gom tri thức từ 3 nguồn sách khác nhau vào một cơ sở dữ liệu có cấu trúc.
  2. **Externalization & Socialization (Ngoại hóa tri thức ẩn):** Được thực hiện qua **Nhật ký nghiệm lý (T8)**, nơi người dùng mang kinh nghiệm thực tế ghi nhận lại thành dữ liệu kiểm chứng có khóa dự đoán."*

---

## 5. QUY TRÌNH 5 PHÚT CHUẨN BỊ BẰNG CHỨNG TRÊN MÁY TÍNH

Trước khi lên bàn vấn đáp hoặc thuyết trình, mỗi thành viên cần làm đúng 3 việc sau:

1. **Mở sẵn Visual Studio Code:**
   - Điều hướng con trỏ chuột đến đúng các file code thuộc phân hệ của mình (theo bảng ma trận ở Mục 2).
2. **Mở sẵn Terminal trên máy tính:**
   - Gõ sẵn câu lệnh `pytest` riêng của mình (nhưng chưa bấm Enter hoặc bấm sẵn để màn hình xanh lá cây hiện chữ `PASSED`).
   - Khi cô hỏi: *"Em có viết test cho phần này không?"* ➔ Lập tức chỉ tay vào màn hình Terminal: *"Dạ có, đây là bộ test tự động của riêng phân hệ em, em vừa chạy pass 100% ạ."*
3. **Mở sẵn Trình duyệt Web:**
   - Bật sẵn giao diện `http://localhost:8501` (Trang Streamlit) để khi cô hỏi chức năng nào là có thể click chuột thao tác trực tiếp ngay trong 3 giây.

