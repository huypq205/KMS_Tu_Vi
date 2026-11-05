---
type: dbdiagram-index
feature: _shared
status: approved
updated: 2026-11-05
links:
  - docs/_shared/dbdiagram/kms_tuvi.dbml
  - docs/_shared/dbdiagram/kms_tuvi.sql
---

# KMS Tử Vi — Database Schema Index (DBML)

> Schema cơ sở dữ liệu hệ thống KMS Tử Vi (Database Markup Language) và bản xuất PostgreSQL DDL chuẩn theo quy chuẩn kỹ năng `dbdiagram`.

## 1. Metadata

- **Source DBML**: `docs/_shared/dbdiagram/kms_tuvi.dbml`
- **Exported SQL**: `docs/_shared/dbdiagram/kms_tuvi.sql`
- **Validation CLI**: `dbml2sql docs/_shared/dbdiagram/kms_tuvi.dbml --postgres` (exit code 0)
- **Target Engine**: SQLite (`data/processed/kms.db` trong runtime sản phẩm) & PostgreSQL (DDL Export chuẩn)
- **Tổng số bảng nghiệp vụ**: 17 bảng (phân thành 4 TableGroups)
- **Số bảng ảo phụ trợ**: 6 bảng ảo SQLite FTS5 (`chunks_fts*` phục vụ tìm kiếm BM25 không dấu)

---

## 2. Danh sách bảng dữ liệu (Tables Matrix)

| # | Bảng (Table) | Miền chức năng (TableGroup) | Mục đích nghiệp vụ | Khóa chính (PK) | Khóa ngoại / Tham chiếu (Refs) | Ghi chú & Ràng buộc chính |
|---|---|---|---|---|---|---|
| 1 | `books` | `core_knowledge` | Danh mục 3 bộ sách Tử Vi kinh điển | `book_code` | Không | Mã định danh: NPL, BD, DAU |
| 2 | `book_parts` | `core_knowledge` | Phân tập PDF của từng cuốn sách | `id` (auto) | `book_code > books.book_code` | `UNIQUE(source_id, part_number)` |
| 3 | `knowledge_items` | `core_knowledge` | 10.456 đơn vị tri thức canonical | `knowledge_id` | `book_code > books.book_code` | Cấu trúc Subject-Predicate-Object, `trust_tier`, `content_hash` |
| 4 | `knowledge_pages` | `core_knowledge` | Ánh xạ nhiều trang PDF cho một tri thức | `id` (auto) | `knowledge_id > knowledge_items.knowledge_id` | Phục vụ truy vết số trang PDF và phần sách |
| 5 | `id_redirects` | `core_knowledge` | Lịch sử chuyển hướng ID sau gộp trùng | `original_id` | Tham chiếu logic sang `knowledge_items` | Quản lý chuyển hướng 34 bản ghi deduplication |
| 6 | `term_aliases` | `core_knowledge` | Từ điển thuật ngữ kiểm soát & bí danh | `id` (auto) | Không | Ánh xạ tên sao, cung, ngũ hành chuẩn và alias |
| 7 | `evidences` | `evidence_audit` | Bằng chứng nguyên văn OCR đối soát | `evidence_id` | `knowledge_id > knowledge_items.knowledge_id`<br>`book_code > books.book_code` | Giữ nguyên trạng OCR, `verification_status` |
| 8 | `audit_samples` | `evidence_audit` | Mẫu kiểm định phân tầng (stratified) | `sample_id` | `knowledge_id > knowledge_items.knowledge_id`<br>`book_code > books.book_code` | 300 mẫu kiểm định chất lượng chéo độc lập |
| 9 | `import_runs` | `evidence_audit` | Nhật ký các phiên nạp dữ liệu ETL | `run_id` | Không | Ghi nhận SHA-256 file Master Excel, số dòng |
| 10 | `chunks` | `rag_retrieval` | 4.350 khối văn bản chunking RAG/FTS5 | `chunk_id` | `book_code > books.book_code` | Độc lập phân đoạn theo sách, `trust_tier` 1-3 |
| 11 | `chunk_members` | `rag_retrieval` | Bảng nối quan hệ N-N Chunk ↔ Fact | `id` (auto) | `chunk_id > chunks.chunk_id`<br>`knowledge_id > knowledge_items.knowledge_id` | `UNIQUE(chunk_id, knowledge_id)`, vị trí `position` |
| 12 | `evaluation_cases` | `rag_retrieval` | Golden Dataset kiểm thử truy xuất RAG | `case_id` | Không | Danh sách expected fact IDs, loại câu hỏi |
| 13 | `query_cache` | `rag_retrieval` | Bộ nhớ đệm kết quả hỏi đáp tất định | `cache_key` | Không | SHA-256 hash câu hỏi + cấu hình model |
| 14 | `horoscope_cache` | `astrology_validation` | Bộ nhớ đệm bài luận giải lá số 3 tầng | `cache_key` | Không | SHA-256 hash lá số + bảng Tứ Hóa + năm xem |
| 15 | `validation_cases` | `astrology_validation` | Hồ sơ ca nghiệm lý ẩn danh (Journal T8) | `case_id` | Không | Mã `TV-YYYY-NNN`, snapshot cung/sao, không lưu PII |
| 16 | `predictions` | `astrology_validation` | Dự đoán mù có thể kiểm chứng được | `prediction_id` | `case_id > validation_cases.case_id`<br>`supersedes > predictions.prediction_id` | Bắt buộc `phan_chung`, hỗ trợ phiên bản chỉnh sửa |
| 17 | `events` | `astrology_validation` | Biến cố đời thực dùng chấm điểm dự đoán | `event_id` | `case_id > validation_cases.case_id`<br>`prediction_id > predictions.prediction_id` | `UNIQUE(prediction_id)`, kết quả đối soát |

---

## 3. Phân nhóm Miền Chức năng (TableGroups)

### 3.1. Nhóm Tri thức Chuẩn hóa & Nguồn sách (`core_knowledge`)
- **Bao gồm**: `books`, `book_parts`, `knowledge_items`, `knowledge_pages`, `id_redirects`, `term_aliases`.
- **Vai trò**: Lưu trữ toàn bộ kho tri thức Tử Vi nền tảng được trích xuất từ 3 bộ sách kinh điển (NPL, BD, DAU). Cấu trúc tri thức được mô hình hóa theo dạng Subject-Predicate-Object kèm bối cảnh điều kiện (`condition_context`) và phân loại taxonomy (`TV-01.01` đến `TV-11.06`).

### 3.2. Nhóm Bằng chứng Nguồn & Kiểm thẩm Dữ liệu (`evidence_audit`)
- **Bao gồm**: `evidences`, `audit_samples`, `import_runs`.
- **Vai trò**: Đảm bảo tính minh bạch học thuật tuyệt đối. Mỗi đơn vị tri thức đều có bằng chứng trích xuất nguyên văn OCR từ số trang PDF tương ứng. Bảng `audit_samples` lưu 300 mẫu phân tầng ngẫu nhiên được kiểm định thủ công chéo để đánh giá sai số OCR và tính xác thực.

### 3.3. Nhóm Truy vết & Tìm kiếm Ngữ nghĩa (`rag_retrieval`)
- **Bao gồm**: `chunks`, `chunk_members`, `evaluation_cases`, `query_cache`.
- **Vai trò**: Tối ưu hóa cho pipeline truy xuất hỗn hợp (Hybrid Search: FTS5 BM25 + Qdrant Dense Vector). Bảng nối `chunk_members` cho phép hệ thống sau khi tìm thấy chunk có thể giải mã chính xác danh sách `knowledge_id` cụ thể cấu thành, hỗ trợ trích dẫn nguồn `[n]` không bị ảo giác.

### 3.4. Nhóm Luận giải & Nghiệm lý Lá số (`astrology_validation`)
- **Bao gồm**: `horoscope_cache`, `validation_cases`, `predictions`, `events`.
- **Vai trò**: Vận hành tính năng lập lá số, lưu đệm kết quả luận giải chuyên sâu và triển khai phương pháp nghiệm lý khoa học độc lập (Journal T8). Dữ liệu ca nghiệm lý tuân thủ nguyên tắc ẩn danh triệt để (không lưu họ tên, ngày giờ sinh thật), các dự đoán được khóa chốt bất biến trước thời điểm diễn ra sự kiện.

---

## 4. Mối quan hệ Thực thể & Ràng buộc Khóa ngoại (Entity Relationships)

```
[books]
  ├── (1:N) ──> [book_parts]
  ├── (1:N) ──> [knowledge_items]
  ├── (1:N) ──> [chunks]
  ├── (1:N) ──> [evidences]
  └── (1:N) ──> [audit_samples]

[knowledge_items]
  ├── (1:N) ──> [knowledge_pages]
  ├── (1:N) ──> [evidences]
  ├── (1:N) ──> [audit_samples]
  └── (1:N) ──> [chunk_members] <── (N:1) ── [chunks]

[validation_cases]
  ├── (1:N) ──> [predictions] ── (Self 1:N) ──> [predictions.supersedes]
  │                    │
  │                 (1:1)
  │                    ▼
  └── (1:N) ────────> [events]
```

### Các ràng buộc chính:
- `book_parts.book_code > books.book_code`: Khóa ngoại ràng buộc phần sách với cuốn sách cha.
- `knowledge_items.book_code > books.book_code`: Ràng buộc tri thức vào cuốn sách nguồn.
- `knowledge_pages.knowledge_id > knowledge_items.knowledge_id`: Xóa cascade khi tri thức bị xóa.
- `evidences.knowledge_id > knowledge_items.knowledge_id`: Xóa cascade đối soát.
- `chunk_members.chunk_id > chunks.chunk_id`: Xóa cascade liên kết chunk.
- `chunk_members.knowledge_id > knowledge_items.knowledge_id`: Liên kết fact tri thức vào khối chunk.
- `predictions.case_id > validation_cases.case_id`: Liên kết dự đoán vào ca nghiệm lý.
- `predictions.supersedes > predictions.prediction_id`: Tự tham chiếu quản lý lịch sử chỉnh sửa dự đoán.
- `events.prediction_id - predictions.prediction_id`: Quan hệ 1-1 duy nhất (`UNIQUE`), đảm bảo mỗi dự đoán chỉ liên kết với tối đa 1 sự kiện thực tế đối soát.

---

## 5. Quy tắc Nghiệp vụ Đặc thù & Bảo toàn Dữ liệu

1. **Nguyên tắc "Giữ 3 tiếng nói riêng biệt":**
   - Ba bộ sách NPL, BD, DAU được bảo toàn ranh giới trường phái, không trộn lẫn nội dung.
   - Thang đo `trust_tier`:
     - **Tier 1 (NPL)**: Nguyễn Phát Lộc, độ tin cậy tuyệt đối, trạng thái `LOCKED_V1_0`.
     - **Tier 2 (DAU)**: Đẩu Số Toàn Thư, tầng văn bản text layer sạch.
     - **Tier 3 (BD)**: Bửu Đình, OCR từ 7 tập PDF scan, giữ nguyên trạng khảo cứu.
     - **Tier 9**: Dữ liệu lỗi OCR hoặc nguồn D (chưa kiểm định), bị loại khỏi chỉ mục RAG.

2. **Cơ chế Bảo vệ Riêng tư Nghiệm lý (Privacy Preservation):**
   - Bảng `validation_cases` chỉ lưu snapshot lá số 12 cung dạng JSON cấu trúc và độ tin cậy giờ sinh (`input_confidence` A-D). Tuyệt đối cấm lưu ngày tháng năm sinh, họ tên, địa chỉ hoặc PII của đương số.

3. **Cơ chế Khóa Chốt Dự đoán Bất biến (Immutability Enforced via DB Triggers):**
   - Bảng `predictions` một khi đã được kích hoạt trường `locked_at` sẽ bị phong tỏa hoàn toàn thông qua trigger SQLite (`freeze_predictions_update`, `freeze_predictions_delete`). Mọi sự chỉnh sửa sau đó bắt buộc phải tạo bản ghi mới và dẫn chiếu qua trường `supersedes`.

---

## 6. Hướng dẫn Tái tạo & Kiểm chứng

```bash
# 1. Kiểm tra cú pháp DBML và xuất ra PostgreSQL DDL
dbml2sql docs/_shared/dbdiagram/kms_tuvi.dbml --postgres -o docs/_shared/dbdiagram/kms_tuvi.sql

# 2. Kiểm tra tính toàn vẹn của DDL sinh ra
# Exit code: 0
# Số bảng sinh ra trong DDL: 17 tables
```
