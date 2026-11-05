---
type: d2-architect-index
feature: _shared
status: approved
updated: 2026-11-05
links:
  - docs/_shared/d2-architect/kms_tuvi_architect.d2
  - docs/_shared/d2-architect/kms_tuvi_architect.svg
---

# KMS Tử Vi — Kiến trúc Hệ thống Mức Nghiệp vụ (System Architecture Index)

> Sơ đồ kiến trúc mức nghiệp vụ hệ thống KMS Tử Vi sử dụng D2 nested container với layout engine ELK theo quy chuẩn kỹ năng `d2-architect`.

## 1. Metadata

- **Source D2**: `docs/_shared/d2-architect/kms_tuvi_architect.d2`
- **Rendered SVG**: `docs/_shared/d2-architect/kms_tuvi_architect.svg`
- **Compiler & Flags**: `d2 --layout elk --theme 1 --pad 40`
- **Tốc độ biên dịch thực tế**: ~108ms (ELK layout engine bundled)
- **Quy mô kiến trúc**: 4 Container cấp cao (`Client`, `Backend`, `Data`, `External`), 1 Tác nhân người dùng (`User`), 14 Khối con nghiệp vụ, và 4 Luồng dữ liệu chính có nhãn tiếng Việt.

---

## 2. Danh sách các Khối Kiến trúc (Architecture Blocks)

| Khối Cấp cao (Container) | Khối Con (Sub-block) | Thành phần chức năng | Vai trò nghiệp vụ | Giao thức / Công nghệ |
|---|---|---|---|---|
| **User** | Người dùng | Đương số, Học giả, Kiểm định viên | Tác nhân gửi yêu cầu tra cứu, lập lá số và đối chiếu nghiệm lý | Con người |
| **Client** | `AppUnified` | Điều hướng Hợp nhất (`app.py`) | Cổng giao diện tập trung, điều hướng 3 trang chức năng | Streamlit `st.navigation` |
| | `HoroscopeUI` | Luận giải Lá số (`horoscope_ui.py`) | Hiển thị lá số 12 cung lưới 4x4 và 7 khối luận giải | Streamlit, SVG/HTML Grid |
| | `StarDossierUI` | Hồ sơ Sao (`star_dossier_ui.py`) | Tra cứu thông tin chuyên sâu 108 sao Tử Vi | Streamlit, REST |
| | `ValidationUI` | Nhật ký Nghiệm lý (`case_validation_ui.py`) | Tạo ca ẩn danh, nhập dự đoán, khóa chốt và đối soát | Streamlit, REST |
| | `AcademicUI` | Tra cứu RAG (`frontend/app.py`) | Tra cứu từ khóa FTS5, hỏi đáp 3 sách nguồn, thống kê | Streamlit, REST |
| **Backend** | `Gateway` | Cổng API & Bảo mật | Kiểm tra X-API-Key, Rate Limiter (10 req/phút), định tuyến 17 API | FastAPI, HTTP/REST, NDJSON Streaming |
| | `Guardrails` | Lớp Phòng vệ & Kiểm soát | Phễu lọc ngoài phạm vi (chặn bói toán cá nhân), Cổng tri thức T7, Citation Validator | Python Core, Regex, Pydantic |
| | `RAGCore` | Động cơ Tìm kiếm Hybrid | Query Cache, Retriever đa sách (RRF k=60), FTS5 BM25, Dense Vector, Context Assembly | SQLite FTS5, Qdrant Client |
| | `HoroscopeCore` | Nghiệp vụ Tử Vi & Luận giải | Chart Engine tất định (`vendor/lasotuvi`), Bóc tách đặc trưng, Cách cục bằng mã, Horoscope Cache | Python (không AI khi an sao), Multi-mode LLM |
| | `ValidationCore` | Động cơ Nghiệm lý Bất biến | Quản lý ca nghiệm lý Journal T8, khóa bất biến qua trigger SQLite, chấm điểm đối soát | SQLite Triggers, REST |
| **Data** | `SQLiteDB` | Cơ sở dữ liệu Quan hệ | 17 bảng nghiệp vụ (`knowledge_items`, `chunks`,...), 6 bảng ảo FTS5, bảng cache | SQLite 3, WAL mode, FTS5 |
| | `VectorDB` | Cơ sở dữ liệu Vector | Collection `kms_chunks` lưu dense vectors 1024 chiều khoảng cách Cosine | Qdrant Vector Store (local disk) |
| | `MasterFiles` | Tri thức Nguồn Master | File Master Excel v1.0, cấu hình YAML ánh xạ và mầm sao | Excel (.xlsx), YAML, Markdown |
| **External** | `LLMPool` | Chuỗi Nhà cung cấp LLM | Gemini API (`flash-3.8`/`3.5-lite`), Groq API, DeepSeek API, Mock Provider | HTTPS REST API |
| | `EmbeddingAPI` | Dịch vụ Vector Embedding | Local model BAAI/bge-m3 (1024D) hoặc Google Gemini Embedding | HuggingFace, Google Cloud API |

---

## 3. Bản đồ 4 Luồng Dữ liệu Nghiệp vụ Chính (Business Data Flows)

### Luồng 1: Tra cứu & Hỏi đáp RAG Học thuật (Academic Q&A Flow)
1. **Yêu cầu đầu vào**: Người dùng nhập câu hỏi nghiên cứu Tử Vi học thuật trên `Client.AcademicUI`.
2. **Kiểm tra an toàn**: `Gateway.RouterKMS` chuyển qua `Guardrails.OutOfScope` để phát hiện và từ chối các yêu cầu bói toán cá nhân.
3. **Tra cứu Cache**: `RAGCore.QueryCache` kiểm tra xem câu hỏi chuẩn hóa đã có phản hồi trong cache chưa.
4. **Truy xuất Hỗn hợp (Hybrid Retrieval)**: Nếu miss cache, `RetrieverHybrid` đồng thời truy vấn từ khóa BM25 qua `FTSAdapter` (trên bảng `chunks_fts`) và ngữ nghĩa qua `DenseAdapter` (trên `VectorDB.CollectionChunks`).
5. **Hợp nhất & Cân bằng Nguồn**: `ContextAssembly` áp dụng công thức Reciprocal Rank Fusion ($k=60$) lấy top-10 ứng viên cho từng cuốn sách (NPL, BD, DAU) độc lập nhằm bảo toàn "3 tiếng nói".
6. **Sinh câu trả lời & Kiểm tra Trích dẫn**: `External.LLMPool` tổng hợp câu trả lời; sau đó `Guardrails.CitationValidator` đối soát các thẻ trích dẫn `[n]`, loại bỏ trích dẫn ảo trước khi lưu vào `QueryCache` và hiển thị cho người dùng.

### Luồng 2: Lập & Luận giải Lá số Cá nhân (Horoscope Analysis Flow)
1. **Lập lá số tất định**: `Client.HoroscopeUI` gửi thông tin ngày giờ sinh; `Backend.Gateway.RouterHoroscope` kích hoạt `HoroscopeCore.ChartEngine` (`vendor/lasotuvi`) tính toán tọa độ 108 sao và 12 cung hoàn toàn bằng thuật toán tất định (không dùng AI).
2. **Bóc tách đặc trưng**: `FeatureExtractor` trích xuất 20 nhóm đặc trưng và các quan hệ tam hợp, xung chiếu, nhị hợp.
3. **Nhận diện Cách cục**: `CachCucDetector` áp dụng các hàm nhận diện tất định bằng mã nguồn Python để xác định cách cục chuẩn xác.
4. **Cầu nối RAG (RAG Bridge)**: Truy xuất các đoạn văn bản giải nghĩa từ sách nguồn tương ứng với các sao/cung của lá số.
5. **Kiểm duyệt Đầu ra**: `Guardrails.OutputGuard` áp dụng chính sách độ tin cậy giờ sinh A-D, gán nhãn mức tin cậy và bắt buộc bổ sung yếu tố phản chứng.
6. **Luận giải Đa Chế độ**: 
   - Chế độ "Dữ liệu": Trả về kết quả trực tiếp từ mã nguồn, không gọi LLM.
   - Chế độ "Giải thích" / "Chuyên sâu": Gọi `External.LLMPool` sinh bài luận giải 7 khối có cấu trúc, lưu đệm vào `HoroscopeCache`.

### Luồng 3: Quản trị & Nhật ký Nghiệm lý Bất biến (Validation Journal Flow)
1. **Tạo hồ sơ ẩn danh**: `Client.ValidationUI` gửi dữ liệu lập ca; `ValidationCore.JournalService` lưu snapshot lá số vào `validation_cases` với mã `TV-YYYY-NNN` (không lưu PII).
2. **Ghi nhận dự đoán mù**: Người dùng nhập kết luận dự đoán có thể kiểm chứng trước khi biến cố xảy ra kèm yếu tố phản chứng (`phan_chung`).
3. **Khóa chốt bất biến**: Người dùng bấm "Khóa dự đoán"; `ValidationCore.ImmutabilityLock` cập nhật `locked_at` và kích hoạt Triggers SQLite, ngăn chặn mọi thao tác sửa/xóa trực tiếp.
4. **Đối chiếu Biến cố Đời thực**: Khi sự kiện thực tế diễn ra, người dùng cung cấp thông tin vào bảng `events`; hệ thống đối soát và chấm điểm kết quả (`clear_match`, `partial_match`, `no_match`, `not_verifiable`).

### Luồng 4: Nạp Dữ liệu Tri thức & Lập chỉ mục Offline (ETL & Indexing Flow)
1. **Thẩm định đầu vào**: Dữ liệu từ file Master Excel đi qua `Guardrails.KnowledgeGate` kiểm tra các tiêu chí chất lượng A/B/C và cách ly nguồn D vào `trust_tier = 9`.
2. **Nhập kho dữ liệu**: Nạp vào các bảng `books`, `knowledge_items`, `evidences` trong `SQLiteDB`.
3. **Tạo chỉ mục từ khóa**: Phân đoạn thành các chunk và lập chỉ mục vào bảng ảo SQLite FTS5 `chunks_fts`.
4. **Sinh vector embedding**: Gọi `External.EmbeddingAPI` tạo vector 1024 chiều và nạp vào Qdrant Collection `kms_chunks`.

---

## 4. Hướng dẫn Tái tạo & Biên dịch

```bash
# Biên dịch sơ đồ D2 sang SVG với ELK layout
d2 --layout elk --theme 1 --pad 40 docs/_shared/d2-architect/kms_tuvi_architect.d2 docs/_shared/d2-architect/kms_tuvi_architect.svg

# Hoặc sử dụng script Python của kỹ năng d2-architect
python C:\Users\Admin\.gemini\config\skills\d2-architect\render.py docs/_shared/d2-architect/kms_tuvi_architect.d2
```
