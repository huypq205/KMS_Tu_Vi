# Kiểm kê Frontend · Tests · Tài liệu — KMS Tử Vi

> **Mục đích:** bản kiểm kê chỉ-đọc để cập nhật báo cáo đồ án (báo cáo cũ: `docs/REPORT_KMS_TU_VI.md`, 01/11/2026).
> **Thời điểm khảo sát:** 05/11/2026 ~01:50–01:55 (Asia/Saigon). **Phạm vi:** `frontend/`, `app.py`, `tests/`, `scripts/`, `docs/`, `skills/`, `data/tuvisonkhiem/`. **Không** chạy `pytest tests/` đầy đủ (chỉ `--collect-only`) nên báo cáo này **không** có số pass/fail.
> **Quy ước:** mọi khẳng định có `file:dòng`; số liệu đều đếm được. "Mới" = mtime ≥ 02/11/2026 (sau ngày báo cáo cũ 01/11/2026).

---

## 1. Frontend (bảng file → chức năng → bằng chứng)

`frontend/` có **15 file `.py`** (13 module + 2 `__init__.py` rỗng), **2 file CSS**, 3 font TTF + `OFL.txt`. Tổng 13 module = **2.519 dòng**.

| File (dòng) | Chức năng | Trang / entry / module con | Bằng chứng |
|---|---|---|---|
| `horoscope_ui.py` (278) | Trang chính "Luận giải lá số": form sidebar (tên, lịch, ngày/giờ, giới tính, năm chiêm nghiệm, chủ đề ưu tiên, mức đọc), gọi stream, render 7 khối | Page **default** của `app.py`; vẫn chạy standalone (`streamlit run frontend/horoscope_ui.py`) | `app.py:15`; `frontend/horoscope_ui.py:1`, `:110-139` (sidebar), `:168` (stream), `:253-276` (7 khối) |
| `horoscope_sections.py` (502) | 7 khối render: định danh → tổng quan năm → lá số → chân dung → chủ đề → gợi ý hành động → căn cứ (mặc định đóng); JS tương tác click cung (Tam hợp/Xung chiếu/Nhị hợp); Thiên Bàn trung tâm | Module con của `horoscope_ui.py` | `frontend/horoscope_sections.py:1-12`, `:26-117` (JS), `:175-262` (`chart_viewer_general`), `:402-497` (khối căn cứ) |
| `horoscope_view.py` (237) | Presentation thuần: `TOPICS`/`FIELDS`/`HOURS`/`BOOKS`, `annual_panel`, `star_table`, `evidence_table`, `validate_birth_date`; **không** import Streamlit/network | Thư viện hiển thị dùng chung | `frontend/horoscope_view.py:1` ("no Streamlit state, vendor engine or network"), `:5-35`, `:165-225` |
| `laso_renderer.py` (340) | Render HTML lá số 12 cung: lưới 4x4 desktop + danh sách mobile, chính tinh kèm M/V/Đ/B/H, Tứ Hóa riêng, cát/hung 2 cột, Tuần/Triệt, sao lưu niên, Thiên Bàn | Module render dùng chung (`horoscope_ui`, `lasoban`, `sections`) | `frontend/laso_renderer.py:1-11`, `:327-340` (`render_laso`), `:37-41` (`CHI_GRID_POS`); dùng `backend/app/services/star_classification` (`:18-31`) |
| `horoscope_transport.py` (63) | Ranh giới HTTP: `POST /api/v1/horoscope/read-stream` (SSE) và `/horoscope/ask`; gửi `X-API-Key`; dịch 429 thành thông điệp thân thiện; coi stream đứt là lỗi | Transport của trang chính + hỏi nhanh | `frontend/horoscope_transport.py:8-11`, `:14-24`, `:27-35`, `:38-63` |
| `horoscope_ask.py` (72) | Widget "Hỏi nhanh có đáp · kèm nguồn sách" (gợi ý câu hỏi, ô nhập 300 ký tự, render câu trả lời + trích dẫn) | **Không được nối vào trang nào** (dead code): không file nào import `ask_box`/`render_ask_answer` | `frontend/horoscope_ask.py:18`, `:43-72`; grep toàn repo chỉ thấy định nghĩa + test backend `tests/test_horoscope_ask.py:24` |
| `star_dossier_ui.py` (91) | Trang **Hồ sơ sao**: 4 tab, 14 slot, tách tiếng nói từng sách, checkbox seed chưa đối chiếu | Page `ho-so-sao` | `app.py:16`; `frontend/star_dossier_ui.py:11`, `:15-31`, `:39`, `:74-80` |
| `case_validation_ui.py` (135) | Trang **Nhật ký nghiệm lý**: 4 tab (tạo ca / dự đoán & khóa / đối chiếu sự kiện / thống kê); snapshot ẩn danh; ngưỡng 30 ca | Page `nghiem-ly` | `app.py:17`; `frontend/case_validation_ui.py:11`, `:26-35`, `:43`, `:129` |
| `research_ui.py` (18) | `setup(title)`: `set_page_config` + nhúng font base64 + `horoscope.css` + `research.css` cho 2 trang research | Module con của `star_dossier_ui` & `case_validation_ui` | `frontend/research_ui.py:9-18`; gọi ở `star_dossier_ui.py:15`, `case_validation_ui.py:13` |
| `research_transport.py` (18) | `api_get`/`api_post` tới `KMS_API_BASE` (mặc định `http://127.0.0.1:8000`), timeout 30s, không fallback dữ liệu mẫu | Transport của 2 trang research | `frontend/research_transport.py:1`, `:7-18` |
| `app.py` (342) | **Legacy**: UI 3 tab KMS (Tra cứu FTS5 / Hỏi đáp RAG / Thống kê tier), gọi `/search`, `/chat/ask`, `/stats`, `/health` | Entry riêng (`streamlit run frontend/app.py`), **không** nằm trong `st.navigation` của `app.py` gốc | `frontend/app.py:1-12`, `:125`, `:296` |
| `lasoban.py` (233) | **Legacy**: lập lá số bằng `vendor/lasotuvi` + phân tích rule-based; xuất JSON; không luận giải | Entry riêng (`streamlit run frontend/lasoban.py`) | `frontend/lasoban.py:1-11`, `:25-34`, `:199-208` |
| `phan_tich.py` (190) | Phân tích cấu trúc lá số rule-based offline (chính tinh, Tứ Hóa, Tuần/Triệt, đại hạn) | Chỉ `lasoban.py` dùng | `frontend/phan_tich.py:1-9`; `lasoban.py:36`, `:208` |
| `assets/horoscope.css` (584) | Theme chính: biến màu, `.horoscope-chart .cell`, `.is-selected/.is-tam-hop`, Thiên Bàn, `.danh-sach-card`, 3 breakpoint (1000/991/640px) | Inject ở trang chính + 2 trang research | `frontend/horoscope_ui.py:45-50`; `research_ui.py:15`; `assets/horoscope.css:298`, `:331`, `:540`, `:562-583` |
| `assets/research.css` (21) | Tinh chỉnh riêng cho 2 trang research (sidebar 230px, caption tương phản, form 44px, mobile 1 cột) | Chỉ 2 trang research | `frontend/assets/research.css:1-21`; `research_ui.py:16` |
| `assets/fonts/IBMPlexSans-{400,500,600}.ttf` + `OFL.txt` | Font nhúng base64 → chạy offline, không gọi Google Fonts | Trang chính + research | `horoscope_ui.py:46-49`; `research_ui.py:12-14` |
| `__init__.py`, `pages/__init__.py` | Rỗng; **`frontend/pages/` không có page nào** → điều hướng chỉ dựa `st.navigation` | — | `Get-ChildItem frontend\pages` chỉ trả `__init__.py` (0 byte) |

Ghi chú kỹ thuật:
- `confidence_badge()` **luôn trả chuỗi rỗng** (`horoscope_view.py:73-76`) — badge tin cậy bị ẩn có chủ đích theo "Gói 3" (`tests/plans/ACTIVE_TEST_PLAN.md:6`: "Ẩn toàn bộ badge tin cậy, nhãn độ nặng, mã giờ sinh C/D").
- 3 trang research/legacy dùng CSS chung nhưng `frontend/app.py` (legacy) dùng style riêng inline + `st.tabs` mặc định.

---

## 2. Điều hướng & chế độ UI

**Entry chính thức:** `app.py` gốc (19 dòng) dựng `st.navigation` 3 trang (`app.py:14-18`):

| # | Trang | `st.Page` | Ghi chú |
|---|---|---|---|
| 1 | Luận giải lá số | `frontend/horoscope_ui.py` | `default=True` (`app.py:15`) |
| 2 | Hồ sơ sao | `frontend/star_dossier_ui.py` | `url_path='ho-so-sao'` (`app.py:16`) |
| 3 | Nhật ký nghiệm lý | `frontend/case_validation_ui.py` | `url_path='nghiem-ly'` (`app.py:17`) |

- Launcher: `run_local.bat:16` chạy `streamlit run app.py` (cổng 8501); `docs/RUN_HOROSCOPE.md:36` dùng cổng 8502. `app.py:6-10` chèn `ROOT` và `ROOT/vendor` vào `sys.path` (cần cho vendor `lasotuvi`).
- **Entry "mồ côi"** (không nằm trong nav, không test): `frontend/app.py` (3 tab KMS), `frontend/lasoban.py` (lập lá số), `frontend/horoscope_ui.py` chạy trực tiếp (`horoscope_ui.py:1`).
- Lịch sử điều hướng có thay đổi trong tài liệu: `docs/RUN_HOROSCOPE.md:39` ("chọn Luận giải lá số trong điều hướng") vs báo cáo cũ hướng dẫn chạy thẳng `frontend/horoscope_ui.py` (`docs/REPORT_KMS_TU_VI.md:380`).

**Chế độ / provider trên UI:**

| Lớp | Giá trị thực tế | Bằng chứng |
|---|---|---|
| Mức đọc (UI) | **2 lựa chọn**: `du_lieu` ("Lá số & dữ kiện · không gọi AI") và `chuyen_sau` ("AI chuyên sâu"), mặc định `chuyen_sau` | `frontend/horoscope_ui.py:127-137` |
| Mức đọc (hợp đồng backend) | **3 giá trị**: `du_lieu`, `giai_thich`, `chuyen_sau`; `READING_MODE_DEFAULT="chuyen_sau"` | `backend/app/schemas/horoscope_contract.py:28-35` |
| Provider gửi từ UI | Hard-code `"provider": "auto"` (cả trang chính và widget hỏi) | `horoscope_ui.py:163`; `horoscope_ask.py:58` |
| Provider backend | `auto | groq | deepseek | gemini | mock` | `backend/app/core/config.py:48` |
| Provider cho luồng KMS chat | `KMS_LLM_PROVIDER` mặc định `groq` | `config.py:40` |
| Provider đang cấu hình (.env) | `KMS_LLM_PROVIDER=groq`, `KMS_HOROSCOPE_PROVIDER=groq`, có `DEEPSEEK_MODEL`, `GROQ_MODEL` | `.env` (không in giá trị key) |
| Nhãn provider trên báo cáo | Chỉ map `gemini` → "Luận giải thông minh (online)", `mock` → "Chỉ dữ kiện lá số"; `deepseek`/`groq` sẽ hiện **chuỗi thô** | `horoscope_sections.py:488-491` |
| Fallback / hạ cấp | Banner `is_mock`, `fallback_reason`, `specificity_low`; cảnh báo khi local backend không chạy (`PROD_FALLBACK`) | `horoscope_ui.py:76`, `:144-148`, `:240-251` |
| Cache & thời gian | Cache schema v8; nhãn "Cache: trúng/chưa có" + timing 4 mốc | `backend/app/services/horoscope_cache.py:29`; `horoscope_sections.py:486-497` |

**Nhãn "chưa kiểm" / "seed chưa xác minh" (có, rải ở 5 chỗ):**

| Nhãn | Vị trí |
|---|---|
| "Nội dung và nguồn trích dẫn chưa được kiểm duyệt thủ công" | `horoscope_ui.py:247` |
| "Chưa kiểm duyệt thủ công" trên từng trích dẫn | `horoscope_sections.py:473` |
| "chưa kiểm duyệt thủ công" ở ô hỏi nhanh | `horoscope_ask.py:35`, `:45` |
| "Tài liệu tham khảo từ bộ skill; chưa đối chiếu bản sách KMS" | `horoscope_sections.py:480` |
| Checkbox "Bổ sung tham khảo chưa đối chiếu sách KMS" + caption "Tham khảo, chưa đối chiếu sách KMS" cho `status == seed_unverified` | `star_dossier_ui.py:20`, `:77-79` |
| "xác minh: unverified" + "chưa có dấu vết duyệt thủ công" | `frontend/app.py:285`, `:332` |

---

## 3. Tests

**Tổng collect được: 2.665 test case / 42 file** — lệnh `python -m pytest tests/ --collect-only -q`, chạy 05/11/2026 01:52 (6,82s). Đây là **số case thu thập** (gồm parametrize), **không** phải số pass.
Lưu ý snapshot: `tests/test_groq_provider.py` (5 case) được tạo lúc 01:51 trong lúc khảo sát → lần collect đầu là 2.660/41 file, lần hai 2.665/42 file.
Hạ tầng: `tests/__init__.py` (package), **không có `conftest.py`**; `pytest.ini` đặt `testpaths=tests`, `addopts=--basetemp=.pytest_temp`, marker `heavy`; CI chạy `pytest tests/ -v -m "not heavy"` (`.github/workflows/test.yml`).

| Nhóm | File | Số case | Ghi chú |
|---|---|---|---|
| **Governance / tri thức** (103) | `test_knowledge_gate.py` | 39 | T7 gate CSV/Excel, quarantine nguồn D |
| | `test_skill_validation.py` | 13 | T10 validator skill (YAML trùng key, link, <500 dòng) |
| | `test_case_validation.py` | 11 | T8 nhật ký nghiệm lý + `AppTest` trên `frontend/case_validation_ui.py:137` |
| | `test_annual_report.py` | 10 | T9 bảng kích hoạt 4 tầng + `annual_activation_panel` |
| | `test_star_dossier.py` | 8 | T6 hồ sơ sao + `AppTest` `frontend/star_dossier_ui.py:92` |
| | `test_knowledge_references.py` | 8 | tham chiếu skill (`knowledge_references`) |
| | `test_singleton_services.py` | 6 | 1 instance/service, không phụ thuộc gói model tùy chọn |
| | `test_api_security.py` | 6 | X-API-Key, 401/403 |
| | `test_two_way_scope.py` | 2 | chặn câu hỏi bói cá nhân ở `/chat/ask` |
| **An sao / bảng / quan hệ cung** (2.332) | `test_lasotuvi_crosscheck.py` | **2.224** | 44 vector × nhiều tổ hợp → **chiếm 83,5% tổng số case**; có 351 XFAIL đã biết (T4) |
| | `test_tu_hoa_tables.py` | 29 | T5: 40 mục/10 Can, 3 khác biệt có tài liệu |
| | `test_palace_relations.py` | 22 | P2b chuẩn hóa quan hệ 12 cung |
| | `test_cach_cuc_detector.py` | 23 | P3 nhận diện cách cục bằng code, chặn AI tự thêm |
| | `test_cach_cuc_catalog.py` | 17 | P2 catalog 30 cách cục + trạng thái duyệt |
| | `test_luu_nien_signals.py` | 10 | P4 tín hiệu lưu niên + phần "vì sao" |
| | `test_horoscope_annual.py` | 7 | `compute_luu_nien`, tiểu hạn theo Can Chi |
| **Hợp đồng / nhãn / độ tin cậy** (117) | `test_horoscope_contract.py` | 17 | P1 hợp đồng 3 mức đọc, `CONTRACT_VERSION=2` |
| | `test_horoscope_evidence_labels.py` | 17 | T3 từ điển chứng cứ + phản chứng bắt buộc |
| | `test_horoscope_input_confidence.py` | 13 | T1 A–D, chặn C/D sau retry |
| | `test_p8_quality_acceptance.py` | 13 | P8 12 ca nghiệm thu + rubric 6 tiêu chí |
| | `test_horoscope_conclusion_confidence.py` | 12 | T2 bốn mức, cấm phần trăm |
| | `test_star_meanings_reference.py` | 11 | nạp `star_meanings.md` (34 sao) + cache key |
| | `test_horoscope_contract_g2.py` | 7 | Gói 2: `tom_tat_nam`, `can_cu_noi_dung`, token budget |
| | `test_horoscope_features.py` | 7 | feature extractor |
| | `test_horoscope_interpreter.py` | 7 | prompt/JSON luận giải |
| | `test_horoscope_integration_g4.py` | 5 | Gói 4 tích hợp |
| | `test_horoscope_facts_schema.py` | 4 | schema fact |
| | `test_horoscope_specificity.py` | 4 | `check_specificity` |
| **UI / frontend** (59) | `test_horoscope_feedback.py` | 16 | sửa theo phản hồi GV, `reading_events` (`:201`) |
| | `test_horoscope_chart_early.py` | 11 | sự kiện `chart_ready` + 2 layout (`:27`, `:241`) |
| | `test_horoscope_three_modes.py` | 10 | 3 mức đọc (UI chỉ mở 2) |
| | `test_horoscope_frontend.py` | 8 | `AppTest` trên `frontend/horoscope_ui.py:68-168` |
| | `test_horoscope_sections.py` | 7 | P7 tách module, thứ tự khối |
| | `test_horoscope_sections_g3.py` | 7 | Gói 3: thứ tự hiển thị + ẩn badge |
| **API / RAG / cache** (41) | `test_horoscope_ask.py` | 18 | `/api/v1/horoscope/ask` (backend, provider mock) |
| | `test_horoscope_api.py` | 10 | endpoint `/horoscope/read` |
| | `test_horoscope_cache.py` | 5 | cache theo lá số + năm + model + ngữ cảnh |
| | `test_cache.py` | 4 | cache tất định của RAG |
| | `test_horoscope_rag_bridge.py` | 4 | sinh query theo sao/tổ hợp (AND) |
| **Provider LLM** (13) | `test_deepseek_provider.py` | 5 | DeepSeek OpenAI-compatible |
| | `test_groq_provider.py` | 5 | Groq (file mới 05/11, chưa commit) |
| | `test_llm_provider_sdk.py` | 3 | chọn provider theo env |
| **Tổng** | **42 file** | **2.665** | |

**File test mới so với báo cáo cũ 01/11/2026** (báo cáo cũ chỉ nêu "74 passed", không nêu tên file nào — `docs/REPORT_KMS_TU_VI.md:302`, `:309`). 24 file dưới đây **không xuất hiện** trong báo cáo cũ:
`test_annual_report.py` (10), `test_star_dossier.py` (8), `test_star_meanings_reference.py` (11), `test_case_validation.py` (11), `test_knowledge_gate.py` (39), `test_knowledge_references.py` (8), `test_lasotuvi_crosscheck.py` (2.224), `test_palace_relations.py` (22), `test_cach_cuc_catalog.py` (17), `test_cach_cuc_detector.py` (23), `test_tu_hoa_tables.py` (29), `test_horoscope_evidence_labels.py` (17), `test_horoscope_input_confidence.py` (13), `test_deepseek_provider.py` (5), `test_two_way_scope.py` (2), `test_horoscope_conclusion_confidence.py` (12), `test_luu_nien_signals.py` (10), `test_p8_quality_acceptance.py` (13), `test_skill_validation.py` (13), `test_singleton_services.py` (6), `test_horoscope_contract_g2.py` (7), `test_horoscope_sections_g3.py` (7), `test_horoscope_integration_g4.py` (5), `test_api_security.py` (6).
Ngoài danh sách yêu cầu, còn **1 file mới chưa commit**: `tests/test_groq_provider.py` (5) — `git status` ghi `?? tests/test_groq_provider.py`.

**Khoảng trống test (không có test nào):** `app.py` gốc (điều hướng), `frontend/app.py` (UI 3 tab), `frontend/lasoban.py`, `frontend/phan_tich.py`, `frontend/horoscope_ask.py` (widget), `frontend/research_ui.py`, `frontend/research_transport.py`, `frontend/horoscope_transport.ask_horoscope` (chỉ test `reading_events`). Kiểm chứng: grep `lasoban|phan_tich|app\.py` trong `tests/` không có kết quả dương tính nào ngoài `AppTest` trên `horoscope_ui.py`.

**`tests/plans/`:** có `ACTIVE_TEST_PLAN.md` (1.306 dòng, 114 KB) + `TEST_PLAN_TEMPLATE.md`. **Không có plan nào ở trạng thái ACTIVE** (grep `\bACTIVE\b` = 0; chỉ có trong tên file). Toàn bộ plan/section đều **PASSED**: plan feedback gốc (`:76`, "34 passed"), T1 (`:511`), T2 (`:567`), T3 (`:623`), T4 (`:694-695`, "PASSED — có bất đồng nguồn ghi bằng strict XFAIL"), T5 (`:727`), T7 (`:765`, 39 test), T6/T8/T9/T10/T11 (`:807-855`), P1 (`:876`, 17 test), P2 (`:915`, 17), P2b (`:957`, 22), P3 (`:1021`, 23), P4 (`:1094`, 10), P5 (`:1160`, 11+8), P6 (`:1199`, 10), P7 (`:1235`, 7+8), P8 (`:1266`, 13 test; hồi quy ghi **2.276 passed / 351 xfailed**), và 4 gói review 04/11 (`:3-7`, PASSED 100%).
→ Chênh lệch cần lưu ý: plan ghi 2.276 passed (03/11) trong khi collect-only hiện tại 2.665 case (05/11) — phần tăng chủ yếu từ `test_groq_provider` + các test thêm sau 03/11.

---

## 4. Scripts & dữ liệu tuvisonkhiem

**`scripts/` — 8 script Python** (không tính `__pycache__`):

| Script | Mục đích | Bằng chứng |
|---|---|---|
| `import_excel.py` (18,7 KB) | **Import** Excel canonical → SQLite idempotent (books/book_parts/knowledge_items/evidences/id_redirects/vocabulary), gán trust tier, báo cáo `data/reports/` | `scripts/import_excel.py:2-15` |
| `inspect_excel.py` (15,8 KB) | **Khảo sát** Excel (sheet/cột/% dữ liệu/mapping/quality) và **sinh `docs/data_dictionary.md`**; chỉ đọc | `scripts/inspect_excel.py:3-19` |
| `build_index.py` (7,2 KB) | **Chunk + embed + index**: đọc knowledge_items eligible → chunk theo `configs/column_mapping.yaml` → embed (BAAI/bge-m3) → SQLite + Qdrant → `index_manifest.json` | `scripts/build_index.py:2-16` |
| `crawl_tuvisonkhiem.py` (8,9 KB) | **Crawl** 4 CPT của tuvisonkhiem.vn qua WP REST → raw JSON + Markdown + master index + README | `scripts/crawl_tuvisonkhiem.py:1-7`, `:21-25`, `:216-251` |
| `compare_tu_hoa_tables.py` (4,9 KB) | **Đối chiếu** 40 mục bảng Tứ Hóa của vendor vs bảng tham chiếu, offline; đọc vendor bằng `ast`, không chạy code | `scripts/compare_tu_hoa_tables.py:1`, `:19-22` |
| `validate_knowledge_import.py` (2,1 KB) | **Gate T7** read-only cho CSV `REPO_*` hoặc workbook Excel | `scripts/validate_knowledge_import.py:2`, `:15-19` |
| `validate_skill.py` (5,4 KB) | **Validator T10** cho `skills/` (YAML trùng key fail, <500 dòng bắt buộc, link đệ quy) | `scripts/validate_skill.py:2-7` |
| `test_horoscope_cli.py` (13,2 KB) | **CLI eval/demo** pipeline luận giải trên terminal (`--provider mock`), in JSON | `scripts/test_horoscope_cli.py:2-8` |

Không có script eval/audit riêng cho golden set; `docs/build_report_docx.py` (12,7 KB) là script sinh DOCX từ báo cáo markdown, nằm trong `docs/`.

**`data/tuvisonkhiem/` — nguồn dữ liệu gì:**

| Thành phần | Số liệu | Bằng chứng |
|---|---|---|
| Nguồn | Thư viện Tử Vi Sơn Khiêm (`https://tuvisonkhiem.vn/thu-vien/`), crawl 04/11/2026 17:55 | `data/tuvisonkhiem/README.md:3-5` |
| Tổng bài | **292** (292 file `.md`) | `README.md:5`; đếm: `sao` 96, `thuat-ngu` 97, `cach-cuc` 53, `sach` 46 |
| `raw_json/` | `tv_sao.json` (4,5 MB), `tv_thuat_ngu.json` (3,5 MB), `tv_cach_cuc.json` (1,36 MB), `tv_sach.json` (1,33 MB), `taxonomies.json` (68 KB) | `README.md:8-11`, `:16-21` |
| `markdown/<folder>/` | 292 file có frontmatter (id/title/slug/category/link/date/taxonomies) | `crawl_tuvisonkhiem.py:174-197` |
| `tuvisonkhiem_master.json` | 7,76 MB — toàn bộ 292 bài + `content_markdown` + `markdown_path` | `crawl_tuvisonkhiem.py:200-217` |
| Trạng thái git | **Chưa commit** (`?? data/tuvisonkhiem/`) | `git status` |

**Có nằm trong RAG không? KHÔNG.** Bằng chứng: grep `tuvisonkhiem|tvsk` trong `backend/` = **0 match**; chỉ xuất hiện ở `scripts/crawl_tuvisonkhiem.py` và `docs/research/*`. `build_index.py` chỉ đọc `knowledge_items` từ `kms.db` (3 sách NPL/BD/DAU). Vai trò thực tế: **tư liệu nghiên cứu tham khảo** để thiết kế contract dữ liệu lá số (xem `docs/research/tuvisonkhiem-data-org.md:128-158`, mục 5 "Áp dụng vào KMS" + "Những điểm KHÔNG nên copy").

**`docs/research/`** (4 file, đều 04/11/2026): `tuvisonkhiem-data-org.md` (phân tích kiến trúc dữ liệu TVSK → đề xuất cho KMS), `tvsk-laso.html` (297 KB HTML lá số mẫu), `tvsk_get_daivan_sample.json` (payload an sao), `tvsk_get_cachcuc_sample.txt`.

---

## 5. Tài liệu

`docs/` = **27 file**: 19 `.md` top-level, 1 `.docx`, 1 script build DOCX, 1 issue, 4 `research/`, 1 `_report_audit/db_stats.py`. **19 file mtime ≥ 02/11/2026** (mới), 8 file cũ.

| Tài liệu | Mục đích (1 dòng) | Mới/Cũ |
|---|---|---|
| `ANNUAL_REPORT.md` | T9: bảng kích hoạt 4 tầng (lá số gốc/đại hạn/lưu niên/lưu nguyệt) + so năm ±1 + "việc chưa đủ căn cứ" | **Mới** 03/11 |
| `CASE_VALIDATION.md` | T8: quy trình nhật ký nghiệm lý (ca ẩn danh, khóa dự đoán, sửa bằng phiên bản, ngưỡng 30 ca) | **Mới** 03/11 |
| `CHANGELOG_KNOWLEDGE.md` | Changelog tri thức theo task (trước→sau, schema/prompt/bảng an sao); 162 dòng | **Mới** 03/11 |
| `EVIDENCE_DICTIONARY.md` | T3: 10 loại chứng cứ + quy tắc `phan_chung` bắt buộc, bậc tin cậy | **Mới** 03/11 |
| `GOVERNANCE_ACCEPTANCE.md` | Nghiệm thu T1–T11: bảng task → kết quả review → commit + test | **Mới** 03/11 |
| `GOVERNANCE_EXECUTION.md` | Nhật ký thực thi/ủy quyền T1–T11, findings & bằng chứng từng bước | **Mới** 03/11 |
| `KNOWLEDGE_GATE.md` | T7: quy tắc gate (A dẫn nguồn/B trường phái/C ca kiểm chứng, OR), 188 dòng | **Mới** 03/11 |
| `LASOTUVI_CROSSCHECK.md` | T4: kiểm chéo an sao với `computation.md` (44 vector, 351 sai khác) | **Mới** 03/11 |
| `LOCAL_TUVI_SKILL_INTEGRATION.md` | Kết luận không thay được engine an sao bằng skill local + cách dùng `star_meanings` cho AI | **Mới** 03/11 |
| `STAR_DOSSIER.md` | T6: API + 14 nhóm hồ sơ sao, thứ tự ưu tiên nguồn A/B/C, seed ngoài canonical | **Mới** 03/11 |
| `data_dictionary.md` | Từ điển dữ liệu 73 KB (sinh bởi `inspect_excel.py`) | **Mới** 03/11 |
| `HOROSCOPE_APP_CHECKLIST.md` | Checklist 7 giai đoạn của app horoscope (165 dòng) | **Mới (mtime)** 03/11 — **nội dung lỗi thời** |
| `RUN_HOROSCOPE.md` | Hướng dẫn chạy: venv, backend 8000, Streamlit `app.py` 8502, biến môi trường horoscope | **Mới** 03/11 — **một phần lỗi thời** |
| `issues/T4_AN_SAO_DISCREPANCIES.md` | Các bất đồng an sao cần đối chiếu sách KMS (OPEN, GitHub issue #1) | **Mới** 03/11 |
| `research/tuvisonkhiem-data-org.md` | Phân tích kiến trúc dữ liệu tuvisonkhiem.vn → khuyến nghị cho KMS | **Mới** 04/11 |
| `research/tvsk-laso.html` | Bằng chứng HTML lá số mẫu (297 KB) | **Mới** 04/11 |
| `research/tvsk_get_daivan_sample.json` | Bằng chứng payload an sao chuẩn | **Mới** 04/11 |
| `research/tvsk_get_cachcuc_sample.txt` | Bằng chứng nội dung cách cục | **Mới** 04/11 |
| `_report_audit/db_stats.py` | Script audit số liệu `kms.db` (read-only) phục vụ cập nhật báo cáo | **Mới** 05/11 |
| `REPORT_KMS_TU_VI.md` | **Báo cáo đồ án cũ** (398 dòng, số liệu 01/11/2026) | Cũ 01/11 — **lỗi thời** |
| `REPORT_KMS_TU_VI.docx` | Bản Word của báo cáo cũ | Cũ 01/11 |
| `build_report_docx.py` | Script chuyển báo cáo `.md` → `.docx` | Cũ 01/11 |
| `BAO_CAO_SU_DUNG_AI.md` | Báo cáo sử dụng AI (trạng thái **trước** đợt sửa theo phản hồi GV) | Cũ 01/11 — **lỗi thời** |
| `HOROSCOPE_FEEDBACK_FIXES.md` | Sửa theo phản hồi giảng viên 31/10/2026 | Cũ 01/11 — **một phần lỗi thời** |
| `HOROSCOPE_UI_DESIGN.md` | Giai đoạn 5: quyết định thiết kế UI (Taste Skill, Framed sheet) | Cũ 01/11 — **một phần lỗi thời** |
| `CLAUDE_TO_GEMINI_WORKFLOW.md` | Quy trình phối hợp Claude (QA) ↔ Gemini (impl) | Cũ 10/31 — còn hiệu lực |
| `KMS_TuVi_Development_Plan.md` | Plan tổng thể KMS (Wiig/SECI/golden set/DoD), 35 KB | Cũ 10/31 — khung tham chiếu |

**Tài liệu đã lỗi thời — bằng chứng cụ thể:**
1. `REPORT_KMS_TU_VI.md` — "74 passed" (`:302`), "74 passed, 1 skipped" (`:309`), Phụ lục A chỉ có `frontend/horoscope_ui.py`, `frontend/lasoban.py` (`:362`), chỉ nêu provider Gemini/mock (`:270-277`), hướng dẫn chạy thẳng `frontend/horoscope_ui.py` (`:380`). Nay: 2.665 test, 3 trang nav, 3 provider + mock.
2. `HOROSCOPE_APP_CHECKLIST.md` — "Giai đoạn 6 … **0% CHƯA LÀM**" (`:23`), "LLM Adapter hỗ trợ Gemini API và Mock LLM offline" (`:44`). Nay Giai đoạn 6 đã có T1/T2/T3/P8 + `api_security`; provider có groq/deepseek.
3. `HOROSCOPE_UI_DESIGN.md` — "**70 passed, 1 skipped**" (`:33`), mô tả báo cáo theo 4 chủ đề + tổng quan/chân dung (`:21-25`) nhưng chưa có "Tổng quan năm" và thứ tự 7 khối hiện tại.
4. `BAO_CAO_SU_DUNG_AI.md` — tự ghi "báo cáo trạng thái **trước** đợt sửa theo phản hồi giảng viên" (`:3`); bảng AI chỉ có Gemini + embedding (`:17-20`), chưa có DeepSeek/Groq/3 mức đọc.
5. `HOROSCOPE_FEEDBACK_FIXES.md` — mốc 31/10, trước P1–P8; mô tả luồng/UI trước khi tách module và trước 7 khối.
6. `RUN_HOROSCOPE.md` — "AI · tự động: dùng cấu hình Gemini hiện có" (`:55`), chỉ 2 chế độ (`:53-57`), trong khi `.env` đặt `KMS_HOROSCOPE_PROVIDER=groq` và backend có 5 provider + 3 mức đọc.

---

## 6. Skills

`skills/` có **2 bộ**:

| Skill | Nội dung | Dùng thế nào | Bằng chứng |
|---|---|---|---|
| `skills/tu-vi-kms/` | Skill API KMS: `SKILL.md` (52 dòng, MIT) + `references/api.md`, `crosscheck.md`, `knowledge.md`, `LICENSE` | 4 chế độ **ASK / STAR_DOSSIER / CROSSCHECK / ANNUAL**; chỉ đọc API (`/horoscope/read`, `/horoscope/ask`, `/stars/{name}/dossier`, annual); bắt buộc giữ `fact_id` + nguồn + trang, giữ riêng NPL/DAU/BD, 4 bậc tin cậy, `seed_unverified` không thành canonical | `skills/tu-vi-kms/SKILL.md:1-7`, `:17-22`, `:34-46`; CI validate: `.github/workflows/test.yml` (step "Validate KMS skill") |
| `skills/tu-vi-dau-so-main/` | Upstream skill Claude Code "Tử Vi Đẩu Số Toàn Tập": `SKILL.md` + 3 reference (`computation.md`, `star_meanings.md`, `cach_cuc_luan_giai.md`), README + README.vi | **Nguồn tham khảo, không phải engine**: `star_meanings.md` được nạp vào `star_meanings_reference.py` (hiện 34 sao) cho cả luận giải AI và hồ sơ sao; `computation.md` trùng blob nguồn fixture T4 và **không** thay được vendor | `skills/tu-vi-dau-so-main/README.md:15-26`; `docs/LOCAL_TUVI_SKILL_INTEGRATION.md:12-21`; `docs/CHANGELOG_KNOWLEDGE.md:3-16`; UI: `frontend/star_dossier_ui.py:40-48`, `frontend/horoscope_sections.py:477-483` |

Cơ chế kiểm soát: `scripts/validate_skill.py` (YAML trùng key fail, <500 dòng, link đệ quy) + 13 test `tests/test_skill_validation.py` + 11 test `tests/test_star_meanings_reference.py`.

---

## 7. DELTA so với báo cáo cũ (01/11/2026)

Báo cáo cũ: `docs/REPORT_KMS_TU_VI.md` (398 dòng) + bản DOCX cùng ngày. Các khoảng thiếu/sai **về UI, test, tài liệu** (không xét số liệu DB — cần audit riêng):

**A. Về UI — thiếu gần như toàn bộ giai đoạn sau 01/11**
1. **Chỉ nêu 1 trang**: báo cáo chỉ nhắc UI Streamlit "báo cáo + lá số 12 cung + thẻ nguồn" (`:130-133`) và Phụ lục A liệt kê `horoscope_ui.py`, `lasoban.py` (`:362`). Nay có **3 trang điều hướng** qua `st.navigation` (`app.py:14-18`): Luận giải lá số, **Hồ sơ sao**, **Nhật ký nghiệm lý** — hai trang sau không tồn tại trong báo cáo cũ.
2. **Thiếu module render lá số**: `laso_renderer.py` (lưới 4x4 + danh sách mobile, Tứ Hóa riêng, Tuần/Triệt, Thiên Bàn trung tâm, click xem Tam hợp/Xung chiếu/Nhị hợp) — `laso_renderer.py:1-11`, `horoscope_sections.py:26-117`.
3. **Thiếu cấu trúc báo cáo 7 khối** và "Tổng quan năm" (`horoscope_sections.py:1-12`, `horoscope_ui.py:253-276`); báo cáo cũ chỉ mô tả "tổng quan, sự nghiệp, tài chính, tình cảm".
4. **Sai/thiếu về provider**: báo cáo cũ chỉ có Gemini + mock (`:274-277`). Nay backend có `auto|groq|deepseek|gemini|mock` (`config.py:48`), `.env` đang `groq`; UI hard-code `provider="auto"` (`horoscope_ui.py:163`) và **nhãn UI chỉ map gemini/mock** → provider groq/deepseek hiện chuỗi thô (`horoscope_sections.py:488-491`) = lỗi hiển thị cần sửa khi cập nhật báo cáo.
5. **Thiếu 3 mức đọc** (`du_lieu`/`giai_thich`/`chuyen_sau`, `horoscope_contract.py:28-35`); báo cáo cũ chỉ nói "mock vs AI". **Lưu ý:** UI hiện chỉ mở **2** mức (`horoscope_ui.py:127-137`) → mức `giai_thich` chỉ gọi được qua API.
6. **Thiếu lớp "căn cứ & chuyên môn"**: bảng luận điểm 3 cột, bảng sao, đối chiếu nguồn từng sao, tài liệu skill tham khảo, timing/cache (`horoscope_sections.py:402-497`).
7. **Thiếu nhãn trung thực mới**: "chưa kiểm duyệt thủ công" (3 chỗ), `seed_unverified` + checkbox "Bổ sung tham khảo chưa đối chiếu sách KMS" (`star_dossier_ui.py:20`, `:77-79`), "Tài liệu tham khảo từ bộ skill…" (`horoscope_sections.py:480`). Báo cáo cũ chỉ nói UI có nhãn "chưa kiểm" chung (`:197`, `:320`).
8. **Dead code chưa ghi nhận**: `frontend/horoscope_ask.py` (ô "Hỏi nhanh") không được trang nào import (`horoscope_ask.py:43`; grep = 0 usage) trong khi backend `/api/v1/horoscope/ask` vẫn tồn tại (`backend/app/main.py:284`) và có 18 test.
9. **Entry lệch**: báo cáo cũ hướng dẫn `streamlit run frontend/horoscope_ui.py` (`:380`); entry chính thức nay là `app.py` (`run_local.bat:16`, `docs/RUN_HOROSCOPE.md:36`).
10. **Thiếu 2 trang legacy** chưa được khai báo trong báo cáo: `frontend/app.py` (3 tab KMS, gọi `/search` `/chat/ask` `/stats`) và `frontend/lasoban.py` + `frontend/phan_tich.py`.

**B. Về test — số liệu cũ đã sai lệch lớn**
1. Báo cáo cũ: **74 passed** (01/11/2026, `:302`, `:309`) và tài liệu thiết kế ghi 70 passed (`HOROSCOPE_UI_DESIGN.md:33`). Hiện tại: **2.665 case / 42 file** collect được (05/11/2026) — tăng ~36×; riêng `test_lasotuvi_crosscheck.py` = 2.224 case (83,5%) nên khi viết báo cáo **phải tách** "case an sao parametrize" khỏi "case hành vi".
2. Báo cáo cũ **không nêu tên file test nào**; 24 file mới đã liệt kê ở §3 (governance T4–T11, P1–P8, hồ sơ sao, nghiệm lý, annual, provider DeepSeek/Groq, api security, singleton…).
3. Báo cáo cũ không nhắc **`tests/plans/ACTIVE_TEST_PLAN.md`** — nay là nhật ký PASSED đầy đủ T1–T11 + P1–P8 (`:76`–`:1266`) và là nguồn trích dẫn trạng thái cho báo cáo mới.
4. Báo cáo cũ không nhắc **CI**: `.github/workflows/test.yml` chạy `validate_knowledge_import` + `validate_skill` + `pytest -m "not heavy"`, Python 3.12, không cài torch.
5. Báo cáo cũ không nhắc **351 XFAIL T4** được quản lý như "sai khác đã biết" (`ACTIVE_TEST_PLAN.md:694`; `docs/issues/T4_AN_SAO_DISCREPANCIES.md:3`).

**C. Về tài liệu — thiếu 13 tài liệu mới + 4 bằng chứng research**
1. Báo cáo cũ chỉ tham chiếu `KMS_TuVi_Development_Plan.md`, `docs/RUN_HOROSCOPE.md`, `docs/BAO_CAO_SU_DUNG_AI.md` (Phụ lục A `:352-365`). Nay có thêm: `ANNUAL_REPORT`, `CASE_VALIDATION`, `CHANGELOG_KNOWLEDGE`, `EVIDENCE_DICTIONARY`, `GOVERNANCE_ACCEPTANCE`, `GOVERNANCE_EXECUTION`, `KNOWLEDGE_GATE`, `LASOTUVI_CROSSCHECK`, `LOCAL_TUVI_SKILL_INTEGRATION`, `STAR_DOSSIER`, `data_dictionary`, `HOROSCOPE_APP_CHECKLIST`, `RUN_HOROSCOPE` (bản 03/11) + `issues/T4_AN_SAO_DISCREPANCIES.md` + `research/*` (4 file).
2. Ba tài liệu cũ nay **mâu thuẫn** với trạng thái thật: `HOROSCOPE_APP_CHECKLIST.md:23` ("Giai đoạn 6 = 0%"), `BAO_CAO_SU_DUNG_AI.md:3` (tự khai "trạng thái trước đợt sửa"), `HOROSCOPE_UI_DESIGN.md:33` ("70 passed").
3. Báo cáo cũ không nhắc **`skills/`** (2 bộ skill + validator + CI) — trong khi T10 đã nghiệm thu (`GOVERNANCE_ACCEPTANCE.md:20`).
4. Báo cáo cũ không nhắc **`data/tuvisonkhiem/`** (292 bài, 7,76 MB master) và `scripts/crawl_tuvisonkhiem.py`; cần ghi rõ đây là **tư liệu nghiên cứu ngoài RAG**, không phải nguồn canonical của KMS.
5. Báo cáo cũ không nhắc **`docs/research/tuvisonkhiem-data-org.md`** — tài liệu duy nhất phân tích kiến trúc dữ liệu đối thủ và đề xuất contract cho KMS.

**D. Việc cần làm khi cập nhật báo cáo (gợi ý, không thuộc phạm vi file này)**
- Thay toàn bộ số "74 passed" bằng số collect + số pass thật của Lead; nêu rõ 42 file và tỷ trọng crosscheck.
- Vẽ lại sơ đồ kiến trúc UI: `app.py` (nav 3 trang) → 3 page → 3 transport → 5 nhóm endpoint (`read`, `read-stream`, `ask`, `stars/dossier`, `validation/*`) + legacy 2 entry.
- Sửa bảng provider: `auto|groq|deepseek|gemini|mock` + `.env` hiện tại; sửa nhãn UI `horoscope_sections.py:488-491` trước khi chụp ảnh minh họa.
- Cập nhật §"Giới hạn": UI chỉ có 2/3 mức đọc, widget hỏi nhanh chưa nối, `frontend/app.py`/`lasoban.py`/`phan_tich.py` không có test.
