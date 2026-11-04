# KIỂM KÊ TẦNG BACKEND — KMS Tử Vi (audit chỉ-đọc)

> **Thời điểm khảo sát:** 2026-11-05 (Asia/Saigon) · **Phạm vi:** `backend/app/**`, `configs/**`, `.env.example`, `docs/REPORT_KMS_TU_VI.md`.
> **Phương pháp:** đọc file + đếm tĩnh bằng AST (`python 3.12`) + liệt kê route bằng cách import `backend.app.main:app` (FastAPI 0.156.4 / Starlette 1.9.0) + truy vấn SQLite **read-only** (`file:...?mode=ro`). Không chạy `pytest` (tránh ghi `.pytest_cache`), nên số test PASS **chưa xác định** — chỉ có số đếm tĩnh.
> **Quy ước dẫn chứng:** `file:line` tính từ repo root. Chỉ ghi "chưa xác định" khi không có bằng chứng trong mã nguồn.
> **Cảnh báo snapshot:** trong lúc audit, working tree đang có **15 file bị sửa dở** bởi tiến trình khác (`git status`: `core/config.py`, `llm_provider.py`, `horoscope_interpreter.py`, `horoscope_features.py`, `horoscope_service.py`, 4 file `frontend/*`, 4 file `tests/*`…). Toàn bộ số liệu dưới đây là **ảnh chụp lúc đọc**; riêng số file test tăng 41 → 42 ngay trong phiên audit. Cần chạy lại `git status` + `pytest` trước khi chốt báo cáo.

---

## 1. Endpoints & routers

### 1.1. Cách app được lắp ghép

- `app = FastAPI(title="KMS Tử Vi", version="0.1.0")` — `backend/app/main.py:50-54`.
- **Chỉ 2 router được include**, cả hai ở **cuối file** (`backend/app/main.py:303-306`):
  - `governance.router` — `APIRouter()` **không prefix**, path tuyệt đối (`backend/app/api/governance.py:7,10,26-27`).
  - `case_validation.router` — `APIRouter(prefix='/api/v1/validation', tags=['Validation journal'])` (`backend/app/api/case_validation.py:8`).
- `backend/app/api/__init__.py` **rỗng**; **không tồn tại** `api/search.py`, `api/chat.py`, `api/horoscope.py` → các endpoint search/chat/horoscope được khai báo trực tiếp trong `main.py` bằng `@app.*` (`backend/app/main.py:139,155,209,261,278,284,290`).
- Tổng số route API **đếm được khi chạy = 17** (7 của `main.py` + 3 của `governance` + 7 của `case_validation`), chưa tính 4 route mặc định `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc`.

### 1.2. Cơ chế bảo vệ (X-API-Key, rate limit, CORS)

| Cơ chế | Hành vi chính xác | Dẫn chứng |
|---|---|---|
| **X-API-Key** | Áp cho mọi path bắt đầu `/api/v1/` **hoặc** `/api/stars/`, **trừ** path kết thúc bằng `/health`. Nếu `KMS_API_KEY` rỗng → **API mở** (mặc định). Sai/thiếu key → **401** `{"detail": "Thiếu hoặc sai X-API-Key."}` | `backend/app/main.py:77,93-98` |
| **Rate limit** | Chỉ áp cho path bắt đầu `/api/v1/horoscope` (nên gồm cả `/annual`). Giới hạn `KMS_RATE_LIMIT_PER_MIN` (mặc định **10** req/phút/IP, cửa sổ trượt 60 s). Vượt → **429** | `backend/app/main.py:78,83-90,99-106` |
| **CORS** | `KMS_CORS_ORIGINS`, mặc định `http://localhost:8501,http://localhost:8502`; `allow_credentials` chỉ bật khi danh sách **không** chứa `*`; `allow_methods/headers = ["*"]` | `backend/app/main.py:58-72` |
| Liên quan | Frontend gửi key qua helper `_headers()` → `{"X-API-Key": ...}` và map 429 thành thông báo thân thiện | `frontend/horoscope_transport.py:10-11,16-25` |

### 1.3. Bảng endpoint (đầy đủ)

| # | Method | Path đầy đủ | Router gốc (khai báo) | Mục đích / trả về | Bảo vệ |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/health` | app — `main.py:139` | Đếm `knowledge_items` + `chunks`; lỗi DB trả `status:"error"` (vẫn HTTP 200) | **Không** (path kết thúc `/health`) |
| 2 | POST | `/api/v1/search` | app — `main.py:155` | Truy xuất thuần (FTS/dense, RRF) → `SearchResponse{query,status,results[],citations[],meta{count,books,enabled_tiers}}`; `status` = `ok`/`no_result` | API key |
| 3 | GET | `/api/v1/stats` | app — `main.py:209` | Thống kê: `total_records`, `by_tier[{trust_tier,count,label,ui_badge,enabled}]`, `by_book`, `chunks`, `fts_rows` | API key |
| 4 | POST | `/api/v1/chat/ask` | app — `main.py:261` | RAG pipeline (`RAGPipeline.ask`): cache → out-of-scope → ngưỡng RRF → LLM → citation validator; `status ∈ answered/insufficient_evidence/out_of_scope/error` | API key |
| 5 | POST | `/api/v1/horoscope/read` | app — `main.py:278` | Lập lá số + truy xuất nguồn + luận giải; chạy hết stream rồi trả report cuối (`horoscope_service.read_horoscope:175`) | API key + rate limit |
| 6 | POST | `/api/v1/horoscope/ask` | app — `main.py:284` | Hỏi nhanh 1 chủ đề, 1 lần gọi Gemini JSON + mock fallback; validate `topic ∈ {tong_quan,su_nghiep,tai_chinh,tinh_cam,van_han}` | API key + rate limit |
| 7 | POST | `/api/v1/horoscope/read-stream` | app — `main.py:290` | NDJSON streaming (`application/x-ndjson`), event `progress/stage`, `chart_ready`, `prepared`, `result`, `error`; header chống buffer | API key + rate limit |
| 8 | POST | `/api/v1/horoscope/annual` | governance — `governance.py:10` | Lưu niên/niên hạn **không gọi LLM**: `{annual_report, facts, input_confidence, source_status}`; lỗi lịch/lá số → 422 | API key + rate limit |
| 9 | GET | `/api/v1/stars/{name}/dossier` | governance — `governance.py:27` | Hồ sơ sao tách nguồn; query `include_seeds` (mặc định `false`); 404 `UnknownStar`, 503 khi DB/seed lỗi | API key |
| 10 | GET | `/api/stars/{name}/dossier` | governance — `governance.py:26` | **Alias cũ** của #9 (không `/v1`) | API key (`/api/stars/` có trong middleware) |
| 11 | POST | `/api/v1/validation/cases` | case_validation (`prefix=/api/v1/validation`) — `case_validation.py:29` | Tạo ca nghiệm lý (201); trùng mã → 409 | API key |
| 12 | GET | `/api/v1/validation/statistics` | `case_validation.py:34` | Thống kê journal (đếm ca/dự đoán/kết quả) | API key |
| 13 | GET | `/api/v1/validation/cases/{cid}` | `case_validation.py:39` | Đọc 1 ca (kèm predictions/events); không thấy → 404 | API key |
| 14 | POST | `/api/v1/validation/cases/{cid}/predictions` | `case_validation.py:44` | Ghi dự đoán **trước** khi xảy ra (201); sai → 409 | API key |
| 15 | POST | `/api/v1/validation/predictions/{pid}/lock` | `case_validation.py:49` | Khoá dự đoán (bất biến vĩnh viễn) | API key |
| 16 | POST | `/api/v1/validation/predictions/{pid}/revisions` | `case_validation.py:54` | Tạo bản sửa (supersedes) kèm `reason` (201) | API key |
| 17 | POST | `/api/v1/validation/cases/{cid}/events` | `case_validation.py:59` | Ghi biến cố đã xảy ra + kết quả đối chiếu (201); mỗi prediction chỉ 1 event | API key |

**Ghi chú vận hành (bằng chứng):**
- Docstring đầu `main.py` vẫn ghi *"Hiện tại (Sprint 1) chỉ có endpoint tìm kiếm, chưa nối LLM"* (`backend/app/main.py:3`) — **đã lỗi thời**, trong khi file có 3 endpoint horoscope + chat.
- Health dùng `engine.connect()` trực tiếp + `sql_text` (`main.py:141-149`); stats dùng `fts_count()` (`main.py:257`).
- `/api/v1/search` trả `ui_badge` lấy từ `column_mapping.yaml` qua `_tier_badge_map()` (`main.py:110-120`).

---

## 2. Services (`backend/app/services/*.py` + `core/`)

Đếm được: **33 file .py có nội dung + `__init__.py` rỗng**; tổng 6.700+ dòng.

| File | Mục đích | Hàm / class chính | Hằng số quan trọng |
|---|---|---|---|
| `cache.py` (212 d) | Query cache tất định, khoá phức hợp (câu hỏi chuẩn hoá + sách + model + prompt hash + index version) trên bảng `query_cache` | `CacheService.lookup/save/clear/stats`, `compute_cache_key:76`, `get_index_version`, `get_prompt_hash` | tôn trọng `ENABLE_QUERY_CACHE` (`:101,143,206`); không lưu khi `status=error` |
| `cach_cuc_catalog.py` (254 d) | P2 — nạp & validate danh mục **cách cục** từ `configs/cach_cuc_catalog.yaml` | `load_catalog:201`, `filter_rules`, `batch_candidates:242`, `catalog_signature`, `get_rule`, `CatalogError` | `MAX_BATCH_CANDIDATES=8:51`, `RULE_STATUSES:42`, `RULE_GROUPS`, `RELATIONSHIPS`, `TIME_LAYERS`, `DAC_TINH_STATES`, `REVIEWER_UNSET='chua_chi_dinh'` |
| `cach_cuc_detector.py` (610 d) | P3 — **nhận diện cách cục bằng code** trên dữ kiện lá số + chặn AI bịa rule_id | `detect_cach_cuc:536`, `check_rule_ids:584`, `_evaluate_rule`, `_actual_relation`, `_outcome` | `DETECTION_VERSION=1:96`, `DETECTION_CAVEAT:97`, `OUTCOME_FULL/PARTIAL/NONE/UNKNOWN:66-70`, `CONDITION_STATUSES:75` |
| `case_validation.py` (121 d) | Journal nghiệm lý **append-only**; DB tự chặn sửa/xoá | `install_immutability:12` (SQLite `CREATE TRIGGER freeze_*`), `create_case:44`, `add_prediction:52`, `lock_prediction`, `revise_prediction`, `reveal_event`, `get_case`, `statistics:113` | `RESULTS:9`; C/D chỉ được kết luận cấu trúc (`:54-56`); `min chứng cứ` theo `muc_tin_cay` (`:59`) |
| `chunker.py` (202 d) | T05 — sinh chunk từ DB theo `column_mapping.yaml` | `build_chunks:42`, `_chunk_npl`, `_chunk_merge_adjacent`, `_page_numbers`, `ChunkSpec` | chiến lược NPL 1-record-1-chunk; DAU/BD merge 150–600 ký tự (theo YAML) |
| `citation_validator.py` (120 d) | T11 — kiểm `[n]` tồn tại, câu có nội dung nhưng không dẫn nguồn, loại citation giả | `extract_refs:36`, `validate_citations:71`, `strip_invalid_citations:111`, `CitationCheck:17` | `CITATION_RE = \[(\d+)\] :13` |
| `embeddings.py` (64 d) | Adapter embedding local + upsert vector store | `EmbeddingAdapter.encode/upsert_chunks/search:19-52`, `get_embedding_adapter:59` (singleton) | dùng `EMBEDDING_MODEL`/`EMBEDDING_DIM`; **SentenceTransformer device="cpu"** (`:21-22`) |
| `excel_reader.py` (39 d) | Đọc sheet Excel theo mapping, đổi tên cột | `read_sheet`, `read_section`, `find_excel` | — |
| `fts.py` (155 d) | T07 — FTS5 từ khoá, bỏ dấu tiếng Việt | `create_fts_table`, `rebuild_fts_index`, `search_fts:80`, `fts_count:146` | `FTS_TABLE="chunks_fts":14` |
| `horoscope_analysis.py` (196 d) | Biến dữ kiện lá số thành **fact** có `kind` chứng cứ + tóm tắt cung | `build_star_facts:129`, `palace_summary:24`, `_palace_evidence_kind`, `_matching_refs` | `NATAL_GROUPS`, `CHI_ORDER`, `TU_HOA_MARKERS` |
| `horoscope_annual.py` (509 d) | An lưu niên: vòng Thái Tuế 12 sao + lưu Tứ Hóa theo can năm + mức "kích hoạt" | `build_annual_report:214`, `compute_luu_nien:387`, `classify_activation:126`, `validate_annual_report`, `build_year_comparison`, `can_chi_of_year`, `tu_hoa_stars_for_can` | `TU_HOA_BY_CAN` lấy từ bảng `lasotuvi:40`; `VONG_THAI_TUE:43`; `CAUTION_STARS:58`; `LIMITATIONS:63`; `ACTIVATION_RULE_VERSION=2:70`; `ACTIVATION_LEVELS:71` |
| `horoscope_ask.py` (377 d) | Endpoint ask: 1 lệnh Gemini JSON có kiểm soát + mock | `ask_horoscope:301`, `build_ask_context:105`, `mock_ask_answer:204`, `_request_gemini_ask`, `validate_ask`, `select_facts`, `ask_response_schema` | `TOPIC_TITLES`, `TOPIC_PALACE` (5 chủ đề), `ASK_SYSTEM_PROMPT` |
| `horoscope_cache.py` (130 d) | Cache bài luận giải theo (lá số, năm, provider, model, hash ngữ cảnh) | `compute_key:46`, `context_hash:36`, `lookup:69`, `save:93`, `hash_payload`, `clear` | `CACHE_SCHEMA_VERSION=8:29`; tôn trọng `ENABLE_HOROSCOPE_CACHE` (`:71,96`) |
| `horoscope_confidence.py` (167 d) | Chính sách độ tin cậy giờ sinh A–D | `normalize_level`, `level_of`, `is_low_confidence`, `check_input_confidence`, `check_ask_input_confidence`, `contains_timing_claim`, `confidence_prompt_line` | `INPUT_CONFIDENCE_LEVELS=('A','B','C','D'):13`, `LOW_CONFIDENCE_POLICY:32`, `LOW_CONFIDENCE_CAVEAT`, `DEFAULT_INPUT_CONFIDENCE='A'` |
| `horoscope_features.py` (620 d) | An sao (vendor `lasotuvi`) + trích toàn bộ đặc trưng lá số | `generate_raw_horoscope:136`, `extract_horoscope_features:503`, `analyze_menh_cuc`, `get_tam_phuong_tu_chinh`, `detect_star_group`, `extract_tu_hoa`, `analyze_year`, `find_current_dai_han` | `TIME_ZONE=7`, `NGU_HANH_SINH/KHAC`, `TU_HOA_DEF`, `LUC_SAT_TINH_IDS`, `CAT_TINH_IDS`, `CUNG_DOMAIN`; output 20 khoá gồm `palaces`, `nam_xem`, `luu_nien` (`:574-620`) |
| `horoscope_interpreter.py` (1088 d) | Luận giải: **1 request Gemini có timeout + retry 1 lần + fallback model/provider + mock** | `interpret_horoscope:890`, `validate_reading:379`, `check_specificity:578`, `check_sensitive_content:163`, `check_conclusion_confidence`, `check_evidence_labels`, `generate_mock_reading:607`, `_model_chain:201`, `get_max_tokens_for_mode:148`, `_request_groq/_request_deepseek/_request_gemini` | `MODEL_FALLBACK_CODES:135`, `SENSITIVE_PHRASES:156`, `CONCLUSION_CONFIDENCE_LEVELS:140`, `MIN_FACTS_BY_CONFIDENCE:144`, `READING_FIELDS:102` |
| `horoscope_rag_bridge.py` (183 d) | Truy xuất riêng cho horoscope: sinh query theo sao/cung, FTS **AND tên sao đầy đủ** | `generate_horoscope_queries:68`, `search_fts_sqlite:97`, `retrieve_horoscope_context:139`, `format_context_for_prompt:178`, `mentioned_stars`, `strip_accents` | `BOOK_FULL_NAMES`, `TOPIC_TITLES`, `STAR_NAMES`; SQL lọc `c.trust_tier IN (1,2,3)` (`:114`); excerpt 500 ký tự (`:133`) nhưng prompt cắt **300** (`:181`); trần 22 chunk (`:167`) |
| `horoscope_service.py` (185 d) | Đường orchestration duy nhất cho cả JSON và stream | `reading_events:24`, `read_horoscope:175` | timeout qua `ThreadPoolExecutor` 1 worker + heartbeat mỗi 1 s (`:141-148`); chỉ **lưu cache khi `actual_provider == 'gemini'`** (`:152-156`) |
| `knowledge_gate.py` (310 d) | T7 — cổng provenance khi import: quarantine nguồn D (FORUM/VIDEO), cờ giả thuyết | `validate_records:125`, `validate_path`, `normalize_record`, `existing_knowledge_ids:306`, `GateReport`, `GateError` | `HYPOTHESIS_FLAG='HYPOTHESIS_NEEDS_VALIDATION':20`, `DRAFT_STATUS:21`, `RESTRICTED_SOURCE_TYPES={'FORUM','VIDEO'}:22`, `EMPTY_VALUES:23` |
| `llm_provider.py` (317 d) | Adapter **4 provider**: mock / gemini / deepseek / groq + prompt theo sách | `get_llm_provider:306`, `LLMProvider.generate`, `MockLLMProvider:104`, `GeminiLLMProvider:141`, `DeepSeekLLMProvider:196`, `GroqLLMProvider:252`, `LLMError`, `LLMResponse` | `SYSTEM_PROMPT`, `ANSWER_PROMPT`, `BOOK_TITLES`; timeout HTTP **60 s** (`:231,287`); gemini dùng SDK `google-genai` (`:160-176`) |
| `mapping.py` (90 d) | Đọc `column_mapping.yaml` — nguồn sự thật duy nhất cho mapping/tier/chunking | `load_mapping`, `Mapping.enabled_tiers/tier_badge/tier_label/chunking_for`, `Section` | `default_tier` từ YAML |
| `normalize.py` (44 d) | NFC, bỏ dấu, hash nội dung/tệp | `nfc`, `strip_accents`, `content_hash`, `sha256_file` | `_D_MAPPING` (đ→d) |
| `pages.py` (59 d) | Parse `PDF_Pages` ("P7:36") và tạo nhãn trang | `parse_page_refs`, `format_page_label`, `PageRef` | theo `page_parsing.patterns` trong YAML |
| `palace_relations.py` (338 d) | P2b — chuẩn hoá **quan hệ cung** (đồng cung/tam hợp/xung chiếu/giáp cung) | `doi_cung:210`, `tam_hop:215`, `giap_cung:221`, `quan_he:241`, `evidence_kind:275`, `resolve_anchor`, `dac_tinh_in_palace`, `palace_so_by_role` | `RELATIONS:...`, `REL_DONG_CUNG/TAM_HOP/XUNG_CHIEU/GIAP_CUNG/KHONG`, `DAC_TINH_CODES`, `EVIDENCE_KIND_BY_RELATION` |
| `rag.py` (352 d) | T12 — RAG orchestrator: cache → out-of-scope → retrieval → ngưỡng → prompt → LLM → citation | `detect_out_of_scope:47`, `RAGPipeline.ask:193`, `build_context:133`, `build_prompt`, `_select_with_book_coverage` | `DIRECT_DIVINATION_PATTERNS`, `FIRST_PERSON_PATTERNS`, `PERSONAL_TOPICS`, `TIME_MARKERS`, `BIRTH_INFO_PATTERNS`; đọc `max_context_chunks`/`abstain_rrf_threshold` từ YAML (`:116-121`) |
| `retriever.py` (194 d) | T08 — Hybrid FTS5 + dense, gộp bằng RRF, top-N mỗi sách, lọc tier | `search:100`, `_rrf:90`, `_dense_search:72`, `get_knowledge_items`, `RetrievedChunk` | `RRF_K=60:23`, `BOOK_CODES=['NPL','DAU','BD']:22`, `top_n_per_book=10:58` |
| `star_classification.py` (160 d) | P5 — phân nhóm sao dùng chung backend & frontend | `classify_star:102`, `partition_palace_stars:138`, `_normalize_name` | `GROUPS` 5 nhóm:22, `CHINH_TINH_IDS`, `TU_HOA_IDS`, `CAT_TINH_IDS`, `HUNG_TINH_IDS`, `DAC_TINH_COLOR/LABEL` |
| `star_dossier.py` (164 d) | T6 — hồ sơ sao tách nguồn, tra cứu tất định, **không để LLM tạo tri thức** | `get_star_dossier:142`, `load_star_seed:45`, `canonical_star`, `_slot_keys` | `SLOTS` **14 slot**:14, `SEED_STARS` **20 sao**:26, `KNOWN_STARS` **108**:29, `SEED_MESSAGE='Tham khảo, chưa đối chiếu sách KMS':25`, `MISSING:24`; cờ bật seed `KMS_STAR_SEEDS_ENABLED` (`:154`) |
| `star_meanings_reference.py` (579 d) | Đọc Markdown bộ skill như **dữ liệu tham khảo có gán nguồn**, lọc chỉ thị (prompt-injection) | `load_meanings`, `get_meaning`, `load_skill_knowledge:326`, `select_meanings:506`, `select_all_references_for_chart:488`, `format_knowledge_references:554`, `load_cach_cuc` | `ALLOWED_SECTIONS` 6 mục:30, `DEFAULT_PATH` (skill `star_meanings.md`):23, `SOURCE='Tử Vi Đẩu Số Toàn Tập'`, `SOURCE_NOTE='...chưa đối chiếu bản sách'` |
| `tiering.py` (68 d) | Gán `trust_tier` theo rule đầu tiên khớp trong YAML | `assign_tier:44`, `_matches`, `_matches_condition`, `rule_description` | — |
| `tu_hoa_tables.py` (114 d) | T5 — bảng Tứ Hóa khai báo tách riêng, **không sửa vendor** | `load_tu_hoa_config:33`, `get_tu_hoa_table:69`, `apply_natal_table:87`, `table_metadata`, `find_parent_palace` | `CONFIG_PATH`:16, `STEMS` 10 can, `TU_HOA_CODES`, `TU_HOA_STAR_IDS` (94/93/92/95), `PARENT_STARS`; chọn bảng qua `KMS_TU_HOA_TABLE` (`:71`) |
| `vector_store.py` (131 d) | Abstraction vector store: Qdrant local / numpy fallback | `VectorStore:16`, `NumpyVectorStore:39`, `get_vector_store:116` | chọn qua `VECTOR_STORE` (`qdrant` mặc định) |
| `vector_store_qdrant.py` (92 d) | Qdrant persistent local | `QdrantVectorStore:17` (+`upsert/search/delete/count/close`, `_chunk_id_to_int`) | collection `kms_chunks` (theo `data/qdrant/collection/kms_chunks`) |
| `core/evidence_types.py` (49 d) | Từ điển **loại chứng cứ** cho fact/luận điểm | `EvidenceType` (StrEnum), `evidence_label` | **10 loại**: `toa_thu, tam_hop, xung_chieu, giap_cung, tu_hoa, menh_cuc, van_han, nghiem_ly, truong_phai, suy_luan` (`:11-23`), `EVIDENCE_TYPE_VALUES:38`, `NO_COUNTER_EVIDENCE:41` |
| `core/config.py` (73 d) | Nạp `.env` **thủ công** bằng `os.environ.setdefault` rồi khai báo hằng số runtime | `_load_env:10`, `ensure_dirs:71` | xem §3 |
| `services/__init__.py`, `repositories/__init__.py` | Rỗng (0 nội dung) | — | — |

---

## 3. Config & model mặc định

### 3.1. `backend/app/core/config.py` — toàn bộ biến có ý nghĩa KMS

| Biến env | Mặc định trong code | Dòng | Ghi chú |
|---|---|---|---|
| `KMS_EXCEL` | `data/raw/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx` | 24 | đường dẫn nguồn |
| `KMS_MAPPING` | `configs/column_mapping.yaml` | 25 | |
| `KMS_RETRIEVAL_CONFIG` | `configs/retrieval.yaml` | 26 | |
| `KMS_DB` | `data/processed/kms.db` | 27 | |
| `KMS_QDRANT` | `data/qdrant` | 28 | |
| `KMS_REPORTS` | `data/reports` | 29 | |
| `KMS_MANIFEST` | `data/processed/index_manifest.json` | 30 | |
| `KMS_EMBEDDING_MODEL` | **`BAAI/bge-m3`** | 33 | local SentenceTransformer |
| `KMS_EMBEDDING_DIM` | `1024` | 34 | |
| `KMS_VECTOR_STORE` | **`qdrant`** (`qdrant \| numpy`) | 35 | |
| `KMS_EMBEDDING_PROVIDER` | **`local`** (`local \| gemini`) | 37 | giá trị `gemini` **không có nhánh code nào dùng** (xem §5) |
| `KMS_LLM_PROVIDER` | **`groq`** (`groq\|gemini\|deepseek\|mock`) | 40 | luồng chat KMS |
| `GEMINI_API_KEY` | `""` | 41 | |
| `DEEPSEEK_API_KEY` | `""` | 42 | |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | 43 | |
| `DEEPSEEK_MODEL` | `deepseek-chat` | 44 | |
| `GROQ_API_KEY` | `""` | 45 | |
| `GROQ_BASE_URL` | `https://api.groq.com/openai/v1` | 46 | |
| `GROQ_MODEL` | **`openai/gpt-oss-20b`** | 47 | model chat mặc định |
| `KMS_HOROSCOPE_PROVIDER` | **`auto`** (`auto\|groq\|deepseek\|gemini\|mock`) | 48 | điều phối provider horoscope |
| `KMS_GEMINI_MODEL` | **`gemini-3.8-flash`** | 49 | chỉ dùng cho `GeminiLLMProvider` của luồng chat |
| `KMS_LLM_MAX_TOKENS` | **`2048`** | 50 | |
| `KMS_LLM_TEMPERATURE` | **`0.0`** | 51 | dùng chung **mọi** provider (kể cả horoscope: `horoscope_interpreter.py:809,844,870`) |
| `KMS_ENABLE_QUERY_CACHE` | **`true`** | 52 | |
| `KMS_HOROSCOPE_MODEL` | **`gemini-3.5-flash-lite`** | 56 | model chính của luồng horoscope |
| `KMS_HOROSCOPE_TIMEOUT_SECONDS` | **`45`**, bị **clamp 5–60** | 57 | `min(60, max(5, ...))` |
| `KMS_HOROSCOPE_MAX_TOKENS` | **`12288`** | 58 | mode mặc định (`du_lieu`) |
| `KMS_HOROSCOPE_MAX_TOKENS_GIAI_THICH` | **`12288`** | 59 | |
| `KMS_HOROSCOPE_MAX_TOKENS_CHUYEN_SAU` | **`12288`** | 60 | |
| `KMS_HOROSCOPE_FALLBACK_MODELS` | **`()` rỗng** | 62-64 | danh sách model dự phòng, phân tách phẩy |
| `KMS_ENABLE_HOROSCOPE_CACHE` | **`true`** | 65 | |
| `KMS_EXCERPT_MAX_CHARS` | `300` | 68 | trích đoạn trong citation |
| `KMS_CORS_ORIGINS` | `http://localhost:8501,http://localhost:8502` | `main.py:61` | **không** nằm trong `config.py` |
| `KMS_API_KEY` | `""` (mở) | `main.py:77` | **không** nằm trong `config.py` |
| `KMS_RATE_LIMIT_PER_MIN` | `10` (0 = tắt) | `main.py:78` | **không** nằm trong `config.py` |
| `KMS_TU_HOA_TABLE` | mặc định lấy `default_table: lasotuvi` trong YAML | `tu_hoa_tables.py:71` | đọc **trực tiếp**, không qua `config.py` |
| `KMS_STAR_SEEDS_ENABLED` | `'1'` → bật | `star_dossier.py:154` | đọc trực tiếp |
| `KMS_STAR_MEANINGS_ENABLED` | `'1'` → bật | `star_meanings_reference.py:59` | đọc trực tiếp |
| `KMS_STAR_MEANINGS_PATH` | rỗng → dùng `DEFAULT_PATH` (skill md) | `star_meanings_reference.py:62` | đọc trực tiếp |
| `KMS_API_BASE` | rỗng → `http://127.0.0.1:8000` | `frontend/research_transport.py:8` | phía frontend |

**Lưu ý quan trọng:** 4 biến `KMS_TU_HOA_TABLE`, `KMS_STAR_SEEDS_ENABLED`, `KMS_STAR_MEANINGS_ENABLED`, `KMS_STAR_MEANINGS_PATH` có trong `.env.example` nhưng **không được khai báo trong `config.py`** → không có `import`-time default ở đó; chúng chỉ được đọc khi module tương ứng được gọi.

### 3.2. Model mặc định THEO TỪNG LUỒNG

| Luồng | Provider chọn mặc định | Model mặc định | Dẫn chứng |
|---|---|---|---|
| **Chat KMS** `POST /api/v1/chat/ask` | `KMS_LLM_PROVIDER` = **groq** | **`openai/gpt-oss-20b`** (`GROQ_MODEL`) | `config.py:40,47` → `llm_provider.py:264,306-317` |
| Chat khi `KMS_LLM_PROVIDER=gemini` | gemini | **`gemini-3.8-flash`** (`GEMINI_MODEL`) | `llm_provider.py:152` |
| Chat khi `=deepseek` | deepseek | `deepseek-chat` | `llm_provider.py:208` |
| **Horoscope read/ask** | `KMS_HOROSCOPE_PROVIDER=auto` → thử **groq** (nếu có `GROQ_API_KEY`) → **deepseek** → **gemini** | Mode auto: groq `openai/gpt-oss-20b`, hoặc deepseek `deepseek-chat`, hoặc gemini **`gemini-3.5-flash-lite`** | `horoscope_interpreter.py:920-993`; `config.py:48,56` |
| Chuỗi model dự phòng (Gemini) | — | `[HOROSCOPE_MODEL] + KMS_HOROSCOPE_FALLBACK_MODELS` (khử trùng lặp) | `horoscope_interpreter.py:201-206` |
| **Embedding** | `KMS_EMBEDDING_PROVIDER=local` | **`BAAI/bge-m3`** (1024 dim, CPU) | `config.py:33-37`, `embeddings.py:21-22` |
| Mock | `provider='mock'` / `reading_mode='du_lieu'` | `mock-echo-v1` (chat) / `mock-data` (horoscope) | `llm_provider.py:106`; `horoscope_ask.py:369` |

### 3.3. `.env.example` — đối chiếu với `config.py`

| Biến trong `.env.example` | Giá trị mẫu | Khớp `config.py`? |
|---|---|---|
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | ✔ khớp tên |
| `KMS_HOROSCOPE_MODEL` | `gemini-3.5-flash-lite` | ✔ khớp default |
| `KMS_HOROSCOPE_FALLBACK_MODELS` | `gemini-3.5-flash,gemini-3.5-flash-lite` | ⚠ khác default (`()` rỗng) |
| `KMS_HOROSCOPE_TIMEOUT_SECONDS` | `45` | ✔ |
| `KMS_HOROSCOPE_MAX_TOKENS` | **`8192`** | ✘ **lệch** so với `12288` trong `config.py:58` |
| `KMS_TU_HOA_TABLE` | `lasotuvi` | ⚠ biến **không có trong `config.py`** |
| `KMS_STAR_SEEDS_ENABLED` | `1` | ⚠ không có trong `config.py` |
| `KMS_STAR_MEANINGS_ENABLED` | `1` | ⚠ không có trong `config.py` |
| `KMS_STAR_MEANINGS_PATH` | rỗng | ⚠ không có trong `config.py` |
| `KMS_API_KEY` | rỗng (API mở) | ⚠ không có trong `config.py` (đọc ở `main.py:77`) |
| `KMS_RATE_LIMIT_PER_MIN` | `10` | ⚠ không có trong `config.py` (đọc ở `main.py:78`) |
| `KMS_CORS_ORIGINS` | `http://localhost:8501,http://localhost:8502` | ⚠ không có trong `config.py` (đọc ở `main.py:61`) |
| `KMS_API_BASE` | rỗng (frontend) | ⚠ không có trong `config.py` |

**Biến `config.py` dùng nhưng `.env.example` KHÔNG có:** `KMS_LLM_PROVIDER`, `KMS_GEMINI_MODEL`, `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, `DEEPSEEK_BASE_URL`, `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL`, `KMS_HOROSCOPE_PROVIDER`, `KMS_LLM_MAX_TOKENS`, `KMS_LLM_TEMPERATURE`, `KMS_ENABLE_QUERY_CACHE`, `KMS_ENABLE_HOROSCOPE_CACHE`, `KMS_HOROSCOPE_MAX_TOKENS_GIAI_THICH`, `KMS_HOROSCOPE_MAX_TOKENS_CHUYEN_SAU`, `KMS_EMBEDDING_MODEL`, `KMS_EMBEDDING_DIM`, `KMS_EMBEDDING_PROVIDER`, `KMS_VECTOR_STORE`, `KMS_EXCEL`, `KMS_MAPPING`, `KMS_RETRIEVAL_CONFIG`, `KMS_DB`, `KMS_QDRANT`, `KMS_REPORTS`, `KMS_MANIFEST`, `KMS_EXCERPT_MAX_CHARS`.
→ `.env.example` **không còn là bản sao đầy đủ** của `config.py` (chỉ phủ luồng horoscope + bảo mật).

**Ghi chú runtime:** file `.env` thật trong repo **có** đặt `KMS_LLM_PROVIDER`, `KMS_HOROSCOPE_PROVIDER`, `KMS_HOROSCOPE_MODEL`, `KMS_GEMINI_MODEL`, `GROQ_MODEL`, `DEEPSEEK_MODEL`, `KMS_HOROSCOPE_FALLBACK_MODELS` (đã kiểm tra **tên biến**, không trích giá trị/khoá). Vì `.env` được nạp bằng `setdefault` (`config.py:18`), giá trị chạy thực tế **có thể khác** mặc định trong code — báo cáo nên nêu theo mặc định code và ghi rõ "cấu hình cục bộ có thể ghi đè".

---

## 4. Configs YAML (số liệu đếm được)

### 4.1. `configs/column_mapping.yaml` (209 dòng) — trust tier

| Nội dung | Số liệu | Dòng |
|---|---|---|
| `trust_tiers.enabled_tiers` | `[1, 2, 3]` | 168 |
| `default_tier` | `9` | 169 |
| **Định nghĩa tier** | **4** tier: 1 (NPL, release LOCKED), 2 (DAU text layer), 3 (BD OCR), 9 (loại khỏi index) | 170-174 |
| **Quy tắc xét (khớp đầu tiên thắng, có `enabled` ngầm qua `enabled_tiers`)** | **5 rule**: ① tier 9 nếu `review_flag_contains: HYPOTHESIS_NEEDS_VALIDATION`; ② tier 9 nếu `book_code ∈ [BD,DAU]` **và** `review_flag_contains: OCR_REVIEW_REQUIRED`; ③ tier 1 nếu `book_code: NPL`; ④ tier 2 nếu `book_code: DAU`; ⑤ tier 3 nếu `book_code: BD` | 175-185 |
| `expected_counts` | NPL 2191 · BD 4450 · DAU 3815 · **total 10456** | 17-21 |
| `sheets_ignored` | **13** sheet | 24-37 |
| Section mapping | 8 section: `sources`, `source_parts`, `knowledge_items` (required `[knowledge_id, book_code, text]`), `evidence`, `id_redirects`, `vocabulary`, `taxonomy`, `extraction_review` | 42-150 |
| `chunking` | NPL `one_record_one_chunk`; DAU/BD `merge_adjacent` (`group_by: [pdf_page, chapter]`, `min_chars 150`, `max_chars 600`); BD thêm `PAGE_OR_PARAGRAPH_CONTINUATION` | 190-209 |
| `page_parsing` | BD `^P(?P<part>\d+):(?P<page>\d+)$`; default `^(?P<page>\d+)$` | 155-159 |

### 4.2. `configs/retrieval.yaml` (15 dòng)

| Key | Giá trị | Dòng |
|---|---|---|
| `top_n_per_book` | 10 | 2 |
| `rrf_k` | 60 | 3 |
| `top_k_default` | 10 | 4 |
| `max_context_chunks` | **8** | 5 |
| `enabled_tiers` | `[1, 2, 3]` | 9 |
| `abstain_rrf_threshold` | **0.005** | 12 |
| `excerpt_max_chars` | 300 | 15 |

(Lưu ý: `Retriever.__init__` **hard-code** `top_n_per_book=10`, `rrf_k=60` — `retriever.py:58`; `rag.py` chỉ đọc `max_context_chunks` + `abstain_rrf_threshold` — `rag.py:116-121`.)

### 4.3. `configs/cach_cuc_catalog.yaml` (36.549 bytes)

| Chỉ số | Giá trị | Cách đếm |
|---|---|---|
| Số quy tắc | **30** | `len(rules)` |
| Nhóm | **21 `quy_cach`** + **9 `pha_cach`** | `Counter(nhom)` |
| Trạng thái | **15 `chi_tham_khao`** + **15 `can_doi_chieu`**; **0 `duyet_dung`** | `Counter(trang_thai)` |
| `reviewer_role` / `source_status` | `chua_chi_dinh` / `reference_unverified` | 13-14 |
| `san_sang_thuc_thi = true` | **16** quy tắc | |
| `ung_vien_ban_dau = true` | **8** quy tắc (= `MAX_BATCH_CANDIDATES`, `cach_cuc_catalog.py:51`) | |
| Quan hệ | `dong_cung` 17 · `tam_hop` 6 · `xung_chieu` 2 · `giap_cung` 2 · hỗn hợp 1 · rỗng 2 | |
| `tang_thoi_gian` | **30/30 `la_so_goc`** | |
| `noi_dung_nhay_cam = true` | **4** | |
| `sections_khong_phan_van` | **8** mục | |
| Khoá bắt buộc mỗi rule | `id, ten, nhom, sao, dieu_kien, quan_he, chi, can_tuoi, cung_neo, cung_muc_tieu, tang_thoi_gian, diem_mo_ho, noi_dung_nhay_cam, ca_kiem_thu, diem_giai_trinh, san_sang_thuc_thi, ung_vien_ban_dau, trang_thai, nguoi_duyet, ngay_duyet` (20 khoá) | `REQUIRED_RULE_FIELDS` |

### 4.4. `configs/tu_hoa_tables.yaml` (1.746 bytes)

- **2 bảng**: `lasotuvi` (`verification_status: vendor_baseline`, nguồn `vendor/lasotuvi/App.py, lapDiaBan`) và `hung_ngm_reference` (`verification_status: reference_unverified`, nguồn GitHub hung-ngm) — `configs/tu_hoa_tables.yaml:6-34`.
- `default_table: lasotuvi` (dòng 4); mỗi bảng có `by_can` cho **10 Thiên Can**, thứ tự giá trị **Hóa Lộc / Hóa Quyền / Hóa Khoa / Hóa Kỵ**.
- Hai bảng chỉ khác nhau ở can **Canh** và **Nhâm**; các can còn lại dùng YAML anchor.

### 4.5. `configs/star_seeds/*.yaml`

- **20 file** (khớp `SEED_STARS` 20 sao: 14 Chính tinh + Tả/Hữu Bật + Văn Xương/Văn Khúc + Thiên Khôi/Thiên Việt).
- Cấu trúc mỗi file: `name` (tên sao) · `source` (chuỗi gán nguồn) · `slots{core_function|yin_yang_five_element: {text, source, reference(url), status}}`.
- **34 slot entry** tổng cộng: `core_function` có ở **20/20** file, `yin_yang_five_element` ở **14/20**.
- **Cờ "chưa xác minh"**: mọi slot đều `status: seed_unverified` (**34/34**); thêm `source` ghi rõ *"nguồn gián tiếp do repo tham khảo gán, chưa xác minh"*. Ở tầng code, nhãn này được expose qua `SEED_MESSAGE='Tham khảo, chưa đối chiếu sách KMS'` (`star_dossier.py:25`).

### 4.6. Số liệu DB hiện tại (chạy read-only, `data/processed/kms.db`, 20,4 MB)

| Bảng | Số dòng | Bảng | Số dòng |
|---|---|---|---|
| `knowledge_items` | **10.456** | `chunks` / `chunks_fts` | **4.350** / 4.350 |
| `evidences` | 10.492 | `chunk_members` | **8.680** |
| `knowledge_pages` | 10.483 | `book_parts` / `books` | 9 / 3 |
| `id_redirects` | 34 | `term_aliases` | 156 |
| `import_runs` | 2 | `audit_samples` | 300 |
| `validation_cases` / `predictions` / `events` | 0 / 0 / 0 | `horoscope_cache` / `query_cache` | 0 / 0 |
| `evaluation_cases` | 0 | | |

Phân bố tier (khớp báo cáo cũ): tier 1 = 2.191 (NPL) · tier 2 = 3.798 (DAU) · tier 3 = 2.691 (BD) · tier 9 = 1.776 (BD 1.759 + DAU 17); tổng được index = **8.680**.
Chunk theo sách: NPL 2.191 · BD 1.189 · DAU 970.
`data/processed/index_manifest.json`: `embedding_model = gemini-embedding-001`, `embedding_dim 1024`, `embedding_provider gemini`, `vector_store qdrant`, **`vectors_indexed = 30`**, `chunks_built 4350`, `indexed_at 2026-10-22`.

---

## 5. DELTA so với báo cáo 01/11/2026

> Đối chiếu `docs/REPORT_KMS_TU_VI.md` (398 dòng). Mỗi mục là một điểm **sai / thiếu / lỗi thời** kèm bằng chứng.

### 5.1. Endpoint & API surface

1. **Thiếu 12/17 endpoint.** Báo cáo chỉ nêu `chat/ask`, `horoscope/read (+ -stream)`, `search`, `stats`, `health` (`docs/REPORT_KMS_TU_VI.md:142-145`). Thực tế có thêm:
   - `POST /api/v1/horoscope/ask` (`main.py:284`),
   - `POST /api/v1/horoscope/annual` (`governance.py:10`),
   - `GET /api/v1/stars/{name}/dossier` + alias `GET /api/stars/{name}/dossier` (`governance.py:26-27`),
   - **7 endpoint journal nghiệm lý** `/api/v1/validation/*` (`case_validation.py:8,29-59`).
2. **Báo cáo không nhắc bảo mật API.** Không có chỗ nào nói `X-API-Key` (401), rate limit 10 req/phút/IP cho `/api/v1/horoscope*` (429) hay CORS allowlist (`main.py:58-107`). Đây là "hành vi mới" hoàn toàn.
3. **Router chưa được mô tả.** Báo cáo trình bày như thể mọi endpoint nằm trong `main.py`; thực tế có 2 `APIRouter` được include ở cuối file (`main.py:303-306`), trong đó `case_validation` dùng `prefix='/api/v1/validation'` — mô hình "modular router" chỉ mới áp cho 2 module.
4. **Sai prefix trong sơ đồ kiến trúc.** Hình vẽ ghi `POST /chat/ask` và `POST /horoscope/read` (`REPORT:121-122`) — thiếu `/api/v1`.
5. **Docstring `main.py` cũng lỗi thời**: *"hiện tại (Sprint 1) chỉ có endpoint tìm kiếm, chưa nối LLM"* (`main.py:3`) trong khi file đã có 3 endpoint horoscope + chat.

### 5.2. Provider & model (thay đổi lớn nhất về cấu hình)

6. **Báo cáo nói LLM chỉ có "Gemini/mock"** (`REPORT:358`). Thực tế **4 provider**: `mock`, `gemini`, `deepseek`, `groq` (`llm_provider.py:104,141,196,252,306-317`).
7. **Model mặc định của luồng chat đã đổi.** Báo cáo: `KMS_GEMINI_MODEL = gemini-3.8-flash` (`REPORT:274`). Thực tế `KMS_LLM_PROVIDER` mặc định **`groq`** → model chat mặc định là **`openai/gpt-oss-20b`** (`config.py:40,47`; `llm_provider.py:264`). `gemini-3.8-flash` chỉ dùng khi set `KMS_LLM_PROVIDER=gemini`.
8. **Luồng horoscope có chuỗi provider auto** không có trong báo cáo: `auto → groq (nếu có key) → deepseek → gemini` (`horoscope_interpreter.py:920-993`). Báo cáo chỉ mô tả "Gemini + fallback mock" (`REPORT:143,268`).
9. **"gọi tối đa 2 lần" không còn đúng.** Báo cáo: *"gọi tối đa 2 lần"* (`REPORT:277`). Thực tế: mỗi model được gọi tối đa **2 lần** (lần đầu + 1 lần "BỔ SUNG BẮT BUỘC", `horoscope_interpreter.py:1003-1048`) **nhân với số model trong chain** (`_model_chain:201-206`) → có thể tới `2 × len(chain)` lần, cộng thêm nhánh groq/deepseek phía trước.
10. **Max tokens sai.** Báo cáo: *"max tokens 2.500"* (`REPORT:277`). Thực tế: `KMS_HOROSCOPE_MAX_TOKENS = 12288`, và **3 mode riêng** (`config.py:58-60`; `get_max_tokens_for_mode:148-153`); `.env.example` lại ghi `8192`. Ba con số khác nhau → cần chốt lại.
11. **`temperature = 0.0` vẫn đúng** nhưng nay áp cho **cả 4 provider** (`llm_provider.py:174,227,283`; `horoscope_interpreter.py:809,844,870`).
12. **Timeout 45 s vẫn đúng**, nhưng bị **clamp 5–60** (`config.py:57`) và được dùng làm `timeout=(5, HOROSCOPE_TIMEOUT_SECONDS)` (`horoscope_interpreter.py:812,847,876`); báo cáo không nêu clamp.
13. **Cache horoscope**: báo cáo nói "có cache theo (lá số + năm + model + hash ngữ cảnh)" (`REPORT:277`) — đúng một phần: khoá còn gồm `provider`, `index_version`, `reading_mode`, `schema_version=8` (`horoscope_cache.py:29,46-58`); **chỉ lưu khi `actual_provider == 'gemini'`** (`horoscope_service.py:152-156`) → lượt đọc bằng groq/deepseek **không được cache**.

### 5.3. Module mới báo cáo chưa từng nhắc (11 module + 1 core)

14. `services/cach_cuc_catalog.py` + `services/cach_cuc_detector.py` — **engine nhận diện cách cục bằng code** (30 quy tắc, 8 ứng viên bản đầu, `check_rule_ids` chặn AI bịa `rule_id`). Báo cáo **không có khái niệm "cách cục"** ở bất kỳ dòng nào.
15. `services/horoscope_annual.py` — lưu niên **vòng Thái Tuế 12 sao + lưu Tứ Hóa**, `ACTIVATION_RULE_VERSION=2`, mức `nhan/vua/nang`; kèm endpoint `/api/v1/horoscope/annual`. Báo cáo không nhắc `annual`, `lưu niên`, `Thái Tuế`.
16. `services/tu_hoa_tables.py` + `configs/tu_hoa_tables.yaml` — **2 bảng Tứ Hóa khai báo tách biệt** (`lasotuvi` vendor_baseline vs `hung_ngm_reference` reference_unverified). Báo cáo chỉ có một dòng "Tứ Hóa" chung chung.
17. `services/palace_relations.py` — chuẩn hoá **4 quan hệ cung** + `evidence_kind`, `PALACE_ROLE_CODES`, `DAC_TINH_CODES`. Không có trong báo cáo.
18. `core/evidence_types.py` — **10 loại chứng cứ** (`toa_thu…suy_luan`) + `NO_COUNTER_EVIDENCE`. Báo cáo §6.4 chỉ nói `fact_ids`/`source_refs`, **không** nói phân loại chứng cứ hay trường `phan_chung`.
19. `services/horoscope_confidence.py` — **chính sách input_confidence A–D** (C/D chỉ kết luận cấu trúc, cấm kết luận thời điểm, mỗi `gioi_han` phải nêu caveat). Báo cáo không có.
20. `services/star_dossier.py` + `services/star_meanings_reference.py` + `services/star_classification.py` — hồ sơ sao 108 sao / 20 seed / 14 slot, và lớp đọc Markdown skill **như dữ liệu có gán nguồn** (lọc chỉ thị, `ALLOWED_SECTIONS`). Báo cáo không nhắc; đây cũng là **bề mặt prompt-injection mới** cần nêu ở mục rủi ro.
21. `services/knowledge_gate.py` (T7) — cổng provenance/quarantine `FORUM`/`VIDEO`, `HYPOTHESIS_NEEDS_VALIDATION`. Báo cáo §4.4 chỉ nói suy tier, **không** nói gate.
22. `services/case_validation.py` + `schemas/case_validation.py` — **journal nghiệm lý append-only** (bảng `validation_cases`, `predictions`, `events`; trigger SQLite `freeze_*`; cấm `%` trong kết luận; C/D không được kết luận thời điểm).
23. `services/horoscope_cache.py` (schema v8) và `services/cache.py` (query cache) — báo cáo chỉ nhắc "cache tất định" một dòng (`REPORT:244`), chưa nêu 2 bảng cache, versioning và `ENABLE_*_CACHE`.

### 5.4. Hành vi / hợp đồng mới

24. **3 `reading_mode`** (`du_lieu` / `giai_thich` / `chuyen_sau`) + `CONTRACT_VERSION` (`schemas/horoscope.py`, `schemas/horoscope_contract.py`) — báo cáo hoàn toàn không có; báo cáo chỉ phân biệt `provider=auto|mock`.
25. **Kiểm tra nội dung nhạy cảm** (`SENSITIVE_PHRASES`: chết yểu/tử vong/dâm đãng…, `horoscope_interpreter.py:156-198`) là lớp kiểm mới; báo cáo chỉ nói prompt "không phán tai nạn/bệnh tật" (`REPORT:265`).
26. **Kiểm `check_rule_ids` + `check_evidence_labels` + `check_conclusion_confidence`** bổ sung vào vòng "sinh lại 1 lần"; báo cáo chỉ nêu `check_specificity` (`REPORT:267`).
27. **Ngưỡng trích đoạn gửi model đã đổi**: báo cáo nói "trích đoạn ≤ 500 ký tự gửi mô hình" (`REPORT:227`); thực tế `excerpt` 500 ký tự (`horoscope_rag_bridge.py:133`) nhưng **prompt cắt 300 ký tự** (`:181`).
28. **Trần ngữ cảnh horoscope**: tối đa **22 chunk** (`horoscope_rag_bridge.py:167`), lọc cứng `trust_tier IN (1,2,3)` (`:114`) — báo cáo không nêu con số.

### 5.5. Số liệu / phụ lục sai hoặc lỗi thời

29. **`gemini_embeddings.py` không tồn tại.** Phụ lục A dẫn `backend/app/services/gemini_embeddings.py` (`REPORT:360`) — trong `services/` chỉ có `embeddings.py` (SentenceTransformer local, `BAAI/bge-m3`, CPU). Không có nhánh code nào gọi Gemini embedding API dù `EMBEDDING_PROVIDER` có giá trị `gemini` (`config.py:37`) → biến này **hiện là dead config**.
30. **Bất nhất code ↔ artifact**: `index_manifest.json` ghi `embedding_model: gemini-embedding-001`, `embedding_provider: gemini`, 30 vector; nhưng default code là **local bge-m3** (`config.py:33-37`). Báo cáo (`REPORT:175`) đang trích **manifest**, không trích code → cần ghi rõ nguồn để tránh hiểu sai.
31. **Số test lỗi thời.** Báo cáo: "74 passed (01/11/2026)" (`REPORT:302`) và "74 passed, 1 skipped" (`REPORT:309`). Hiện tại: **42 file `tests/test_*.py`, 397 hàm test** (đếm AST; lúc bắt đầu audit là 41 file/392 hàm — có file mới được thêm trong phiên). Số PASS **chưa xác định** (không chạy pytest trong audit chỉ-đọc) → phải chạy lại `pytest tests/ -q` trước khi báo cáo.
32. **§4.2 thiếu 5 bảng mới**: `validation_cases`, `predictions`, `events`, `horoscope_cache`, `query_cache` (bảng `REPORT:166-177` chỉ liệt kê 8 bảng cũ). DB hiện có **23 bảng**.
33. **Các số tier trong báo cáo vẫn ĐÚNG** (đã kiểm lại read-only): 2.191 / 3.798 / 2.691 / 1.776, tổng index 8.680, `chunks` 4.350 (NPL 2.191 · BD 1.189 · DAU 970), `evidences` 10.492, `knowledge_pages` 10.483, `id_redirects` 34, `term_aliases` 156, `import_runs` 2 — **không cần sửa**.
34. **§8 giới hạn #3 đã lỗi thời một phần**: báo cáo coi "vòng phản hồi tri thức" là *hướng phát triển* (`REPORT:321`) — nay đã có **journal nghiệm lý** (7 endpoint + 3 bảng + trigger bất biến), dù mới ở mức "ghi nhận", chưa có vòng nâng `verification_status`.
35. **Phụ lục A thiếu** các file mới: `knowledge_gate.py`, `cach_cuc_*.py`, `case_validation.py` (+api), `star_dossier.py`, `star_meanings_reference.py`, `star_classification.py`, `horoscope_annual.py`, `horoscope_confidence.py`, `palace_relations.py`, `tu_hoa_tables.py`, `core/evidence_types.py`, `main.py` API security; và thiếu tài liệu mới trong `docs/`: `KNOWLEDGE_GATE.md`, `STAR_DOSSIER.md`, `CASE_VALIDATION.md`, `EVIDENCE_DICTIONARY.md`, `ANNUAL_REPORT.md`, `CHANGELOG_KNOWLEDGE.md`, `LASOTUVI_CROSSCHECK.md`.

### 5.6. Điểm cần kiểm (đã thấy dấu hiệu bất thường, chưa kết luận)

36. `horoscope_service.py:120-124` tính **cache key bằng `req.provider` + `HOROSCOPE_MODEL`** bất kể provider thực tế là groq/deepseek → khoá cache có thể không phản ánh model đã sinh bài; kết hợp với #13 (chỉ lưu khi gemini) tạo nguy cơ **cache miss/không nhất quán**. Cần test riêng trước khi khẳng định là bug.
37. `rag.py:213` đọc `os.getenv("KMS_LLM_PROVIDER", "gemini")` với default **"gemini"** trong khi `config.py:40` default **"groq"** — hai default khác nhau cho cùng biến (chỉ ảnh hưởng tên model ghi vào cache key, không đổi provider thực tế). Nên thống nhất.
38. `horoscope_interpreter.py:120-123` khai báo trùng khoá `'busy'` và `'quota'` trong `ERROR_MESSAGES` (dict literal lặp key) — không sai hành vi nhưng là dead code.
