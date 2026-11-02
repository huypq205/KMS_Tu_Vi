# TEST PLAN: Horoscope — Khắc phục 4 điểm feedback giảng viên + baseline facts schema

- **Ngày lập:** 2026-11-01
- **Người lập kế hoạch (Planner):** Claude (QA & Test Architect)
- **Người triển khai code (Coder):** Gemini (Antigravity IDE)
- **Trạng thái:** **PASSED** — chạy cuối 2026-11-01 (sau khi gắn index version vào cache): `python -m pytest tests/ -q` → **34 passed in 11.13s**

## 0. Bối cảnh & baseline hiện tại

4 điểm feedback cần khắc phục (nguồn: giảng viên, đã đối chiếu code trong repo):

| # | Vấn đề | Gốc đã verify trong code |
|---|--------|--------------------------|
| F1 | Nội dung luận giải quá chung, lá số nào cũng giống nhau | Prompt chứa các chuỗi `layman` tĩnh từ `horoscope_features.py` (dòng 198–338, 463–466) + section schema cố định + temperature 0; RAG query dạng AND ("sao + trạng thái + cung X") dễ rỗng với sách OCR (BD); `top_k_per_topic=2` mỏng |
| F2 | AI chạy rất chậm, chưa có dấu hiệu phản hồi | 1 call Gemini blocking: `KMS_HOROSCOPE_MAX_TOKENS=4096`, timeout 45s, không retry, **không có cache** → mỗi lần bấm "Tạo" đều chờ lại từ đầu; UI đã có stream NDJSON + heartbeat 1s (điểm yếu còn lại là cảm giác chờ lâu + không thể dùng lại kết quả) |
| F3 | Đổi "Năm chiêm nghiệm" nhưng không có sự thay đổi | Backend **có** truyền `target_year` (tiểu hạn + đại hạn + query van_han), nhưng: (a) `build_star_facts` **không có fact lưu niên** → `luan_diem` (bắt buộc dẫn `fact_ids`) không bao giờ nhắc sao của năm; (b) chưa an lưu tinh/lưu Tứ Hóa theo năm; (c) bẫy UX: ô năm nằm trong `st.form`, đổi năm không tự chạy lại, report cũ giữ trong `session_state` |
| F4 | Muốn phân tích các sao đã an (sao xấu, vận hạn) | Chỉ có bảng tô màu sơ bộ; chưa có phân tổ hợp, chưa có sao lưu niên theo năm đã chọn |

**Baseline (đã chạy 2026-11-01, Python 3.12, `data/processed/kms.db` sẵn có):**
`python -m pytest tests/ -q` → **1 failed, 10 passed**
- Test hỏng: `tests/test_horoscope_frontend.py::test_ui_submit_validation_report_toggles_and_transport_error`
- Nguyên nhân: **mất đồng bộ schema fact** — `frontend/horoscope_view.py:83` (`star_table`) đọc keys `dac_tinh`, `roles`, `tuan`, `triet`; còn `backend/app/services/horoscope_analysis.py` (`build_star_facts`) chỉ sinh `trang_thai`, `nhom`, `ngu_hanh`, `source_status`, `source_refs` → `KeyError: 'dac_tinh'` tại `horoscope_ui.py:166` mỗi khi render section "Sao & yếu tố cần đối chiếu".

**P0 (giai đoạn 1 của plan) bắt buộc đưa baseline về xanh trước khi làm P1–P3.**

---

## 1. Mục tiêu & Ranh giới (Scope & Objective)

- **Mục tiêu:**
  1. Đồng bộ schema fact (`build_star_facts` phát đủ keys UI đang đọc) — baseline xanh.
  2. Thêm **lớp lưu niên theo năm Can Chi đã chọn** (Thái Tuế + vòng Tuế + lưu Tứ Hóa + cờ "cần lưu ý") — deterministic, hiển thị ngay, không phụ thuộc AI. Đổi năm → kết quả đổi thật.
  3. Luận giải AI **riêng biệt theo lá số + năm**: prompt chỉ chứa dữ kiện (loại text layman tĩnh), query RAG có fallback, kiểm tra độ cụ thể.
  4. **Cache** kết quả luận giải theo (thông tin sinh, năm, provider, model, ngữ cảnh) + giảm tải prompt/token; UI có progress rõ ràng.
- **Ranh giới (In-scope):** các file horoscope trong §2; bảng lưu niên an theo quy tắc truyền thống (nguồn offset: `vendor/lasotuvi/App.py`); mock LLM trong test.
- **Ngoài phạm vi (Out-of-scope):**
  - Không sửa KMS RAG pipeline (`/api/v1/chat/ask`, guard `out_of_scope`, QueryCache, retriever hybrid).
  - Không an **lưu tinh bổ sung ngoài vòng Thái Tuế + lưu Tứ Hóa** (Thiên Quan, Thiên Sứ, Đào Hoa lưu niên...) — để giai đoạn sau.
  - Không stream token-level từ Gemini (`streamGenerateContent`) — đánh giá sau khi cache ổn.
  - Không lưu/xuất hồ sơ cá nhân (giữ nguyên chính sách `RUN_HOROSCOPE.md`).
  - Không sửa `frontend/lasoban.py` / `phan_tich.py` (tính năng khác, giữ hiện trạng).

---

## 2. Các file mục tiêu (Target Files)

- **File mã nguồn (Code Under Test):**
  - `backend/app/services/horoscope_analysis.py` — P0: mở rộng `build_star_facts`
  - `backend/app/services/horoscope_annual.py` — **MỚI** (P1): `compute_luu_nien(...)`
  - `backend/app/services/horoscope_features.py` — P1: gộp `features['luu_nien']`
  - `backend/app/services/horoscope_rag_bridge.py` — P1+P2: query lưu niên + query fallback
  - `backend/app/services/horoscope_interpreter.py` — P2: prompt chỉ-dữ-kiện + kiểm tra cụ thể
  - `backend/app/services/horoscope_service.py` — P3: chèn cache trước bước LLM
  - `backend/app/services/horoscope_cache.py` — **MỚI** (P3): lookup/save kết quả
  - `backend/app/db/models.py` + `backend/app/db/session.py` — P3: model `HoroscopeCache` (chuẩn y `QueryCache`)
  - `backend/app/core/config.py` — P3: default `KMS_HOROSCOPE_MAX_TOKENS` 4096 → 2500
  - `frontend/horoscope_view.py` — P1: mở rộng `annual_panel`
  - `frontend/horoscope_ui.py` — P1+P2+P3: filter "Lưu niên năm X", banner đổi năm, payload `top_k_per_topic=4`
  - `tests/test_horoscope_frontend.py` — bổ sung TC-19, TC-20
- **File kiểm thử (Test File):**
  - `tests/test_horoscope_facts_schema.py` — **MỚI** (TC-01…04)
  - `tests/test_horoscope_annual.py` — **MỚI** (TC-05…11)
  - `tests/test_horoscope_specificity.py` — **MỚI** (TC-12…14)
  - `tests/test_horoscope_cache.py` — **MỚI** (TC-15…18)
- **Fixtures / Cấu hình:** dùng DB thật `data/processed/kms.db` (FTS); provider `mock` cho tất cả test (không gọi Gemini thật). Không cần `conftest.py` mới nếu fixture chung là hàm `make_features()` (định nghĩa trong mỗi file test hoặc module `tests/support.py` nếu cần dùng lại — tự chọn, ưu tiên tối giản).

---

## 3. Ma trận ca kiểm thử (Test Matrix)

> Quy ước chung: mọi test dùng fixture lá số chuẩn `HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock")` (15/08/1995, giờ Thìn, Nam — lá số "Ất Hợi", Mệnh tại Thìn, Thân tại Tý) sinh features qua `generate_raw_horoscope` + `extract_horoscope_features`. Test phải **deterministic**: không gọi Gemini thật, không phụ thuộc năm hiện tại (trừ khi so sánh tương đối).

### P0 — Schema fact (baseline xanh)

#### TC-01: Fact có đủ keys UI đang đọc
- **Mã test:** `TC-01` — Loại: Unit (Happy Path)
- **Mục đích:** `build_star_facts(features, context)` trả list facts, **mỗi fact** chứa đủ keys: `fact_id, sao, cung, dia_chi, dac_tinh, nhom, roles, tuan, triet, ngu_hanh, source_status, source_refs`.
- **Input:**
  ```python
  req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock")
  report = read_horoscope(req)  # backend.app.services.horoscope_service
  facts = report["star_analysis"]
  REQUIRED = {"fact_id","sao","cung","dia_chi","dac_tinh","nhom","roles","tuan","triet","ngu_hanh","source_status","source_refs"}
  ```
- **Mocks & Setup:** DB thật (kèm citations); provider mock (không LLM).
- **Kỳ vọng:**
  - `assert facts` (không rỗng)
  - `assert all(REQUIRED <= set(f.keys()) for f in facts)`
  - `assert all(isinstance(f["roles"], list) and isinstance(f["tuan"], bool) and isinstance(f["triet"], bool) for f in facts)`
  - `assert all(f["dac_tinh"] in {"M","V","Đ","B","H","—"} for f in facts if f["nhom"] in {"chinh_tinh","cat_tinh"})` (sao phụ/risk được phép "—")

#### TC-02: Cờ Tuần/Triệt lấy từ cấp cung
- **Mã test:** `TC-02` — Loại: Unit
- **Mục đích:** fact của sao trong cung bị **Tuần** phải có `tuan=True`; trong cung bị **Triệt** phải có `triet=True`; các cung khác `False`.
- **Setup:** từ `features["palaces"]` chọn 1 cung có `tuan_trung=True` (nếu lá số mẫu không có Tuần/Triệt, dùng lá số khác tạo bằng cách đổi `ngay/thang/chi_gio` sao cho có — hard-code tổ hợp cụ thể vào test và assert cả điều kiện tiền đề).
- **Kỳ vọng:**
  - `assert any(p["tuan_trung"] for p in features["palaces"])` (tiền đề)
  - Với mọi fact có `cung == ten_cung_bị_tuan`: `assert f["tuan"] is True`
  - Với mọi fact ở cung khác: `assert f["tuan"] is False`

#### TC-03: Role "Tứ hóa" cho 4 hóa tinh
- **Mã test:** `TC-03` — Loại: Unit
- **Mục đích:** sao mà lá số đang mang một trong 4 hóa tinh (tên sao gốc tìm qua `features["tu_hoa"][*]` — mỗi mục có `sao_id` 92/93/94/95 và `cung_ten`; sao gốc = sao `saoLoai==1` trong cung đó có `saoID` trùng `sao_id` ở các mục tương ứng) phải có `"Tứ hóa"` trong `roles`.
- **Kỳ vọng:**
  ```python
  tu_hoa_stars = sao_goc_of(features["tu_hoa"])  # helper trong test
  for f in facts:
      if f["sao"] in tu_hoa_stars:
          assert "Tứ hóa" in f["roles"]
  ```

#### TC-04: Regression KeyError (test có sẵn)
- **Mã test:** `TC-04` — Loại: Regression (UI)
- **Mục đích:** `test_ui_submit_validation_report_toggles_and_transport_error` (hiện RED do `KeyError: 'dac_tinh'`) phải PASS sau P0.
- **Kỳ vọng:** `pytest tests/test_horoscope_frontend.py -v` → toàn bộ PASS, không exception khi render section sao.

### P1 — Lớp lưu niên theo năm (deterministic)

#### TC-05: Ánh xạ năm → Can Chi
- **Mã test:** `TC-05` — Loại: Unit (Happy Path)
- **Mục đích:** `compute_luu_nien(cungs, year)` trả đúng can–chi của năm âm lịch.
- **Input:** `year=2026` → `can=="Bính"`, `chi=="Ngọ"`, `can_chi=="Bính Ngọ"`; `year=1995` → `("Ất","Hợi")`.
- **Kỳ vọng:**
  ```python
  ln = compute_luu_nien(cungs, 2026)
  assert (ln["can"], ln["chi"]) == ("Bính", "Ngọ")
  ln2 = compute_luu_nien(cungs, 1995)
  assert (ln2["can"], ln2["chi"]) == ("Ất", "Hợi")
  ```

#### TC-06: Lưu Tứ Hóa theo can năm + đúng cung sao gốc đóng
- **Mã test:** `TC-06` — Loại: Unit
- **Mục đích:** năm Bính (2026) → lưu Tứ Hóa = Thiên Đồng (Lộc) · Thiên Cơ (Quyền) · Văn Xương (Khoa) · Liêm Trinh (Kỵ) (bảng §4.2); cung của mỗi lưu hóa = **cung trong lá số gốc mà sao đó đang đóng**.
- **Kỳ vọng:**
  ```python
  ln = compute_luu_nien(cungs, 2026)
  pairs = {(x["ten_sao"], x["code"]) for x in ln["luu_tu_hoa"]}
  assert pairs == {("Thiên Đồng","HOA_LOC"), ("Thiên Cơ","HOA_QUYEN"),
                   ("Văn Xương","HOA_KHOA"), ("Liêm Trinh","HOA_KY")}
  # sao đóng đúng cung (đối chiếu lá số gốc)
  for x in ln["luu_tu_hoa"]:
      cung_goc = next(c for c in cungs if any(s["saoTen"] == x["ten_sao"] and s.get("saoLoai")==1 for s in c["saos"]))
      assert x["cung_ten"] in (cung_goc["ten_cung"], cung_goc["chuan_ten"])
  ```

#### TC-07: Vòng Thái Tuế (Thái Tuế + offset Tuê)
- **Mã test:** `TC-07` — Loại: Unit
- **Mục đích:** Thái Tuế tại cung có địa chi == chi năm; Tuế Phá = `dichCung(thai_tue, 6)`, Bạch Hổ = `dichCung(thai_tue, 8)` (offset đúng `vendor/lasotuvi/App.py:150-185`, §4.2).
- **Kỳ vọng (năm 2026 — chi Ngọ):**
  - `assert ln["thai_tue"]["dia_chi"] == "Ngọ"`
  - `assert ln["vong_thai_tue"]["Tuế Phá"]["dia_chi"] == chi_cua_dichCung(cung_Ngọ, 6)` (implementer tính bằng `dichCung` import từ `vendor/lasotuvi/AmDuong.py`)
  - `assert ln["vong_thai_tue"]["Bạch Hổ"]["dia_chi"] == chi_cua_dichCung(cung_Ngọ, 8)`
  - Mỗi mục trong `vong_thai_tue` có `{"ten", "dia_chi", "cung_ten", "loai"}` với `loai ∈ {"hung","cat","trung"}` (phân loại §4.2).

#### TC-08: Tuần hoàn tiểu hạn theo năm (Y ≡ Y+12)
- **Mã test:** `TC-08` — Loại: Unit (Ranh giới chu kỳ)
- **Mục đích:** cung tiểu hạn của năm Y và Y+12 phải **giống hệt**; năm Y và Y+1 phải **khác**.
- **Kỳ vọng:**
  ```python
  f_y   = extract_horoscope_features(raw, 2026)["nam_xem"]["tieu_han"]
  f_y1  = extract_horoscope_features(raw, 2027)["nam_xem"]["tieu_han"]
  f_y12 = extract_horoscope_features(raw, 2038)["nam_xem"]["tieu_han"]
  assert f_y == f_y12
  assert f_y != f_y1
  ```

#### TC-09: Đổi năm → khối lưu niên + tiểu hạn đổi (Regression F3)
- **Mã test:** `TC-09` — Loại: Regression (điểm 3 feedback)
- **Mục đích:** với cùng lá số, 2 năm liên tiếp (thậm chí cùng đại hạn) phải cho `features["luu_nien"]` và `features["nam_xem"]` KHÁC nhau — cam kết "đổi năm là có thay đổi".
- **Kỳ vọng:**
  ```python
  a = extract_horoscope_features(raw, 2026)
  b = extract_horoscope_features(raw, 2027)
  assert a["luu_nien"]["can_chi"] != b["luu_nien"]["can_chi"]
  assert a["luu_nien"]["luu_tu_hoa"] != b["luu_nien"]["luu_tu_hoa"]
  assert a["nam_xem"]["tieu_han"] != b["nam_xem"]["tieu_han"]
  # đại hạn có thể giữ nguyên trong cùng thập kỷ — không assert (đơn vị so sánh là lưu niên)
  ```

#### TC-10: Facts có nhóm lưu niên (gắn với F4)
- **Mã test:** `TC-10` — Loại: Unit
- **Mục đích:** `build_star_facts` sinh thêm fact `nhom=="luu_nien"` (Thái Tuế + sao vòng Tuê + lưu Tứ Hóa năm đó), `roles` chứa `"Lưu niên"`, `dac_tinh=="—"`, `cung`/`dia_chi` đúng vị trí năm.
- **Kỳ vọng:**
  ```python
  ln_facts = [f for f in facts if f["nhom"] == "luu_nien"]
  assert ln_facts, "thiếu fact lưu niên"
  assert any("Lưu niên" in f["roles"] for f in ln_facts)
  assert all(f["dac_tinh"] == "—" for f in ln_facts)
  assert any(f["sao"] == "Thái Tuế" and f["dia_chi"] == "Ngọ" for f in ln_facts)  # năm 2026
  ```

#### TC-11: Query RAG chủ đề vận hạn chứa thông tin năm
- **Mã test:** `TC-11` — Loại: Unit
- **Mục đích:** `generate_horoscope_queries(features_year)` phải thêm query lưu niên vào topic `van_han`: chứa chuỗi **"lưu niên"** (so sau `normalized()`) và tên sao lưu Tứ Hóa của năm đó.
- **Kỳ vọng:**
  ```python
  qs = generate_horoscope_queries(extract_horoscope_features(raw, 2026))["van_han"]
  flat = " ".join(normalized(q) for q in qs)
  assert "luu nien" in flat
  assert "liem trinh" in flat  # năm Bính: lưu Kỵ = Liêm Trinh
  ```

### P2 — Luận giải riêng biệt (F1)

#### TC-12: Prompt không chứa text layman tĩnh
- **Mã test:** `TC-12` — Loại: Unit (Anti-regression cho F1)
- **Mục đích:** `build_horoscope_user_prompt(features, ctx)` **không chứa** các câu layman tĩnh có sẵn trong `horoscope_features.py` (không neo văn mẫu; layman chỉ dùng ở chế độ mock/UI).
- **Setup — 3 golden substring (trích nguyên văn từ code hiện tại, ~30–40 ký tự đầu mỗi câu):**
  1. `"Bạn là người mềm dẻo, linh hoạt"` (VO_CHINH_DIEU, `horoscope_features.py` ~dòng 279)
  2. `"Đại diện cho mẫu người hành động, dám nghĩ dám làm"` (SAT_PHA_THAM ~dòng 297)
  3. `"Bạn được hoàn cảnh và môi trường ưu ái nâng đỡ"` (CUC_SINH_MENH ~dòng 209)
- **Kỳ vọng:**
  ```python
  prompt = build_horoscope_user_prompt(features, format_context_for_prompt(context))
  for g in GOLDEN:
      assert g not in prompt
  # dữ kiện cụ thể VẪN phải có:
  assert "Ất Hợi" in prompt or ("Ất" in prompt and "Hợi" in prompt)   # can chi năm sinh
  assert "Bính Ngọ" in prompt or "2026" in prompt                     # năm xem
  ```

#### TC-13: Fallback query khi AND quá hẹp
- **Mã test:** `TC-13` — Loại: Unit (Edge case retrieval)
- **Mục đích:** khi query dạng `"<sao> <trạng thái> cung <cung>"` (AND 3 phần) không hit chunk nào, retriever thử **query nới** (rớt phần "cung X", giữ sao + trạng thái) trước khi bỏ cuộc; hit phải ghi `matched_query` là query nới.
- **Mocks:** patch `search_fts_sqlite`: lần gọi đầu (query đầy đủ) trả `[]`, lần gọi sau (query nới) trả `[hit_mãu]`.
- **Kỳ vọng:**
  - `hit["matched_query"]` bằng query nới (không phải query đầy đủ)
  - `context["reference_list"]` chứa hit; `context["query_count"]` phản ánh cả 2 lần gọi

#### TC-14: Kiểm tra độ cụ thể của bài đọc
- **Mã test:** `TC-14` — Loại: Unit (Negative)
- **Mục đích:** hàm mới `check_specificity(reading, features, context) -> str | None` trong `horoscope_interpreter`:
  - trả `None` (OK) khi: `luan_diem` dùng **≥3 fact_id khác nhau** (nếu số facts khả dụng ≥3) VÀ nội dung section `van_han_hien_tai` (các trường nối lại) **có nhắc năm xem** (số năm hoặc can–chi, có/không dấu đều được).
  - trả lý do (string) khi vi phạm một trong hai.
- **Kỳ vọng:**
  ```python
  assert check_specificity(reading_tot, features, ctx) is None
  assert check_specificity(reading_thieu_facts, features, ctx)  # <3 fact_id khác nhau
  assert check_specificity(reading_thieu_nam, features, ctx)     # không nhắc năm
  ```
  - Trong `interpret_horoscope`: fail → retry 1 lần (bổ sung chỉ dẫn vào user prompt: "Mỗi luận điểm phải dẫn ít nhất một fact_id khác nhau; phần vận trình phải nhắc năm xem <can_chi>"); vẫn fail → giữ bài, gắn `_generation["specificity_low"]=True` (không silent).

### P3 — Cache + tốc độ (F2)

#### TC-15: Cùng input + cùng năm → cache hit, LLM gọi đúng 1 lần
- **Mã test:** `TC-15` — Loại: Unit (Happy Path)
- **Setup:** provider `auto`, patch `requests.post` (trong `horoscope_interpreter`) trả 200 + JSON đọc hợp lệ (đủ schema + luan_diem đạt specificity). Chạy `read_horoscope(req)` **2 lần** với cùng payload.
- **Kỳ vọng:**
  - `mock_post.call_count == 1`
  - `result2["meta"]["cached"] is True`; `result1["meta"]["cached"] in (False, None)`
  - `result2["reading"] == result1["reading"]` (trừ `_generation` được cập nhật: giữ `reason` gốc, thêm cờ `cached`)

#### TC-16: Đổi năm → cache miss
- **Mã test:** `TC-16` — Loại: Unit
- **Setup:** như TC-15 nhưng lần 2 đổi `target_year` (+1).
- **Kỳ vọng:** `mock_post.call_count == 2`; `result2["meta"]["cached"] in (False, None)`

#### TC-17: Timeout/lỗi KHÔNG được cache (anti-stale)
- **Mã test:** `TC-17` — Loại: Negative
- **Setup:** lần 1: `requests.post` raise `requests.Timeout` → kết quả là fallback mock (`_generation.reason == "timeout"`). Lần 2: `requests.post` trả 200 hợp lệ.
- **Kỳ vọng:**
  - Lần 1: `result1["reading"]["_generation"]["actual_provider"] == "mock"`; **không có bản ghi cache** (chuẩn y quy tắc "không lưu lỗi" của `QueryCache`)
  - Lần 2: `mock_post.call_count == 2`, `result2["reading"]["_generation"]["actual_provider"] == "gemini"`

#### TC-18: Prompt nhẹ hơn, citation UI giữ nguyên
- **Mã test:** `TC-18` — Loại: Unit
- **Mục đích:** excerpt trong prompt (kết quả `format_context_for_prompt`) mỗi nguồn ≤ **300** ký tự; citation trong report UI vẫn ≤ **500** (giữ regression report contract).
- **Kỳ vọng:**
  ```python
  prompt = format_context_for_prompt(context)
  for ref in context["reference_list"]:
      # đo đoạn excerpt của "[n]" của ref trong prompt
      assert len(excerpt_in_prompt_of(ref)) <= 300
      assert len(ref["excerpt"]) <= 500
  ```

### Frontend (bổ sung vào `tests/test_horoscope_frontend.py`)

#### TC-19: Banner cảnh báo đổi năm (khử bẫy F3a)
- **Mã test:** `TC-19` — Loại: UI (AppTest)
- **Setup:** hoàn tất 1 report với `target_year=2025` (patch transport trả payload có `meta.target_year=2025`), sau đó set `app.number_input(key="target_year").set_value(2026)` và `.run()` **không submit form**.
- **Kỳ vọng:**
  - Có warning chứa năm đang hiển thị (2025 hoặc "Ất..." can-chi tương ứng) + lời gọi "Tạo lại"
  - `requests.post` **không** được gọi (chưa submit)

#### TC-20: Bộ lọc "Lưu niên năm X" render được bảng
- **Mã test:** `TC-20` — Loại: UI (AppTest)
- **Setup:** report mock có `star_analysis` chứa fact `nhom=="luu_nien"` (định dạng TC-10), `meta.target_year=2026`.
- **Kỳ vọng:**
  - selectbox `key="star_filter"` có lựa chọn chứa "Lưu niên" và năm 2026
  - chọn nó → `star_table` render không exception, hàng tương ứng có `roles` chứa "Lưu niên"

---

## 4. Yêu cầu triển khai mã nguồn cho Gemini (Implementation Specs)

### 4.0 Thứ tự thực thi (TDD)
1. **P0** → `python -m pytest tests/test_horoscope_facts_schema.py tests/test_horoscope_frontend.py -v` xanh (TC-01…04).
2. **P1** → `python -m pytest tests/test_horoscope_annual.py -v` (TC-05…11).
3. **P2** → `python -m pytest tests/test_horoscope_specificity.py -v` (TC-12…14).
4. **P3** → `python -m pytest tests/test_horoscope_cache.py tests/test_horoscope_frontend.py -v` (TC-15…20).
5. Hồi quy toàn cục: `python -m pytest tests/ -q` → 100% PASS (bao gồm `test_cache.py`, `test_two_way_scope.py`).

Mỗi phase: **viết test trước** (file test mới), chạy đỏ, rồi implement đến xanh. Đổi `ACTIVE_TEST_PLAN.md` sang `IN_PROGRESS` khi bắt đầu, `PASSED` khi toàn bộ xanh.

### 4.1 P0 — Mở rộng `build_star_facts` (`horoscope_analysis.py`)
- Giữ nguyên các key hiện có, **thêm** cho mỗi fact:
  - `dac_tinh`: `s.get("dac_tinh", "—")` của sao trong nhóm (fact lưu niên = "—").
  - `roles`: list str. P0 gán: sao là 1 trong 4 hóa tinh (tìm qua `features["tu_hoa"]`: mục `h` có `sao_id` (92/93/94/95) và `cung_ten`; sao gốc = sao `saoLoai==1` trong cung đó có `saoID==h["sao_id"]` — logic hiện có trong `extract_tu_hoa` giữ `sao_id`) → `roles.append("Tứ hóa")`. Fact khác: `roles=[]`.
  - `tuan`: `bool(p.get("tuan_trung"))` (p = dict cung trong `features["palaces"]`).
  - `triet`: `bool(p.get("triet_lo"))`.
- Không sửa `horoscope_view.py`/`horoscope_ui.py` trong P0 (chúng đã đúng schema mục tiêu).

### 4.2 P1 — `compute_luu_nien` (file MỚI `backend/app/services/horoscope_annual.py`)
```python
def compute_luu_nien(thap_ni_cung: list[dict], year: int,
                     cung_menh_so: int, cung_than_so: int,
                     dai_han_cung_so: int | None) -> dict
```
- **Can–chi năm:** `can = thienCan[(year-4) % 10 + 1]["tenCan"]`, `chi = diaChi[(year-4) % 12 + 1]["tenChi"]` (import từ `vendor/lasotuvi/AmDuong.py` — index 1-based, vị trí 0 placeholder; đã verify: 2026 → Bính Ngọ).
- **Thái Tuế:** cung có `chuan_ten == chi` → `{"cung_ten", "chuan_ten", "dia_chi"}`.
- **Vòng Tuê** (offset từ `dichCung(viTriThaiTue, n)`, nguồn `vendor/lasotuvi/App.py:150-185`; import `dichCung` từ `AmDuong.py`):

  | Sao | Offset | loai |
  |---|---|---|
  | Thiếu Dương | +1 | trung |
  | Tang Môn | +2 | hung |
  | Thiếu Âm | +3 | trung |
  | Quan Phù (Tuế) | +4 | cat |
  | Tử Phủ (Tuế) | +5 | cat |
  | Tuế Phá | +6 | hung |
  | Long Đức | +7 | cat |
  | Bạch Hổ | +8 | hung |
  | Phúc Đức | +9 | cat |
  | Điếu Khách | +10 | cat |
  | Trực Phù | +11 | cat |

  (Không an Thiên Không/Thiên Đức/Nguyệt Đức vào vòng năm — chúng là sao gốc, đã nằm trong lá số.)
- **Lưu Tứ Hóa theo can năm** — bảng chính xác (nguồn `vendor/lasotuvi/App.py:402-451`; can index 1=Giáp…10=Quý):

  | Can năm | Hóa Lộc | Hóa Quyền | Hóa Khoa | Hóa Kỵ |
  |---|---|---|---|---|
  | Giáp | Liêm Trinh | Phá Quân | Vũ Khúc | Thái Dương |
  | Ất | Thiên Cơ | Thiên Lương | Tử Vi | Thái Âm |
  | Bính | Thiên Đồng | Thiên Cơ | Văn Xương | Liêm Trinh |
  | Đinh | Thái Âm | Thiên Đồng | Thiên Cơ | Cự Môn |
  | Mậu | Tham Lang | Thái Âm | Hữu Bật | Thiên Cơ |
  | Kỷ | Vũ Khúc | Tham Lang | Thiên Lương | Văn Khúc |
  | Canh | Thái Dương | Vũ Khúc | Thiên Đồng | Thái Âm |
  | Tân | Cự Môn | Thái Dương | Văn Khúc | Văn Xương |
  | Nhâm | Thiên Lương | Tử Vi | Thiên Phủ | Vũ Khúc |
  | Quý | Phá Quân | Cự Môn | Thái Âm | Tham Lang |

  Vị trí lưu hóa = cung trong lá số gốc mà sao đó đang đóng (tìm theo `saoTen`, `saoLoai==1`).
- **Cờ "cần lưu ý":** `can_luu_y = {"count", "level", "hits"}`:
  - `hits`: mỗi (sao hung thuộc {Thái Tuế, Tuế Phá, Bạch Hổ, Tăng Môn} ∪ {lưu Kỵ}) rơi vào một trong các cung: Mệnh (`cung_menh_so`), Thân (`cung_than_so`), Đại hạn hiện tại (`dai_han_cung_so`), Tiểu hạn năm (cung từ `nam_xem`). Mỗi hit: `{"sao", "cung_ten", "don_vai": "menh"|"than"|"dai_han"|"tieu_han"}`.
  - `level`: không có hit → `"nhan"`; chỉ hit ở đại hạn/tiểu hạn → `"vua"`; ≥2 hit hoặc có hit ở Mệnh/Thân (đặc biệt lưu Kỵ) → `"nang"`.
  - Kèm `method` + `limitations` rõ: "an theo quy tắc truyền thống, chỉ để tham khảo và chiêm nghiệm; không phải dự báo sự kiện".
- **Gắn vào features** (`horoscope_features.extract_horoscope_features`):
  - `features["luu_nien"] = compute_luu_nien(cungs, current_year, raw_laso["cung_menh_so"], raw_laso["cung_than_so"], (dai_han or {}).get("cung_so"))`
  - `current_year` giữ logic hiện có (`target_year or datetime.now(...).year`).
- **Facts** (`horoscope_analysis.build_star_facts`): thêm nhóm `luu_nien`:
  - fact cho Thái Tuế + 11 sao vòng Tuê + 4 lưu Tứ Hóa: `nhom="luu_nien"`, `roles=["Lưu niên"]`, `sao=tên sao`, `cung`=cung đích, `dia_chi`, `dac_tinh="—"`, `tuan/triet` của cung đích, `source_refs` khớp tên sao trong excerpts (tái dùng logic hiện có).
- **Query RAG** (`horoscope_rag_bridge.generate_horoscope_queries`): topic `van_han` thêm:
  - `"Lưu niên " + can_chi`; `"<sao lưu Tứ Hóa> lưu hạn"` (4 sao); tổng số query của topic ≤ 12.
- **UI** (`horoscope_view.annual_panel` + `horoscope_ui.py`):
  - `annual_panel`: thêm 3 dòng: (1) "Thái Tuế chiếu cung X · Các sao lưu cần lưu ý: A, B, C"; (2) "Lưu Tứ Hóa: X→cung Y · W→cung Z (theo can năm)"; (3) badge mức "Cần lưu ý: nhẹ/vừa/nặng" + hits. Giữ caption `limitations`.
  - `horoscope_ui.py`: selectbox "Phạm vi sao" thêm lựa chọn `"Lưu niên năm {year}"` → filter `f['nhom'] == 'luu_nien'`.

### 4.3 P2 — Prompt chỉ-dữ-kiện + specificity (`horoscope_interpreter.py`)
- Helper mới `prompt_data(features) -> dict`: giữ lại chỉ trường **dữ liệu** (bỏ mọi key chứa `layman`/`meaning_layman`): `thong_tin_co_ban`, `menh_cuc` (chỉ `relation_type, hanh_menh, hanh_cuc, title`), `star_group` (chỉ `code, name, stars`), `dai_han_hien_tai`, `tu_hoa`, `cung_chinh`, `nam_xem`, `luu_nien`, `tam_phuong_tu_chinh_menh` (giữ tên cung, bỏ `cung_data` đầy layman). `build_horoscope_user_prompt` dùng `prompt_data` thay `summary` (dòng ~86).
- **Fallback query** (`horoscope_rag_bridge.retrieve_horoscope_context`): với mỗi query gốc dạng `"<sao> <trạng thái> cung <cung>"`: nếu `search_fts_sqlite(q)` trả rỗng → gọi lại với `q_relaxed` (rớt cụm `" cung <cung>"`, giữ sao + trạng thái); hit được ghi `hit["matched_query"] = q_relaxed`. Chỉ nới 1 tầng, chỉ với query có ≥3 phần, giới hạn tổng query trong topic.
- `top_k_per_topic`: payload UI = 4 (schema hiện cho phép 1–10, không cần đổi).
- **Specificity** (TC-14): `check_specificity(reading, features, context) -> str | None` như spec; trong `interpret_horoscope`: fail → retry 1 lần (bổ sung chỉ dẫn vào user prompt); vẫn fail → `_generation["specificity_low"] = True`. UI: caption 1 dòng "Bài tổng hợp dựa trên ít dữ kiện riêng của lá số; xem mục Phân tích sao để đối chiếu" khi `specificity_low` (không đổi layout).

### 4.4 P3 — Cache + giảm tải (`horoscope_cache.py` MỚI + `horoscope_service.py`)
- Model `HoroscopeCache` trong `backend/app/db/models.py` (chuẩn y `QueryCache`): `cache_key` (PK), `payload_hash`, `response_json`, `created_at`, `last_hit_at`, `hit_count`; đăng ký bảng trong `init_db`/`create_all` như các bảng khác.
- `cache_key = SHA256(json.dumps({birth_info, target_year, provider, model, context_hash}, sort_keys=True))`; `context_hash = SHA256(chuỗi chunk_id theo thứ tự)` (chỉ tính khi có context).
- `reading_events`: **sau** retrieval (đã có `context`), **trước** `interpret_horoscope`: lookup cache → hit: dựng report từ JSON, `meta["cached"]=True`, yield `'result'` luôn (vẫn yield `'prepared'` trước để UI render lá số + nguồn). Miss: chạy LLM như hiện; **chỉ lưu cache khi `actual_provider=="gemini"` và không lỗi** (chuẩn y QueryCache: không lưu lỗi/timeout).
- `config.py`: default `KMS_HOROSCOPE_MAX_TOKENS` → `"2500"` (vẫn đọc env; cập nhật `.env.example`).
- `format_context_for_prompt`: excerpt mỗi nguồn ≤300 ký tự (UI citation giữ ≤500 — 2 hằng số tách riêng).
- **Không** thêm nút "hủy" (MVP): stream heartbeat 1s + timeout 45s + fallback mock như hiện tại đã đủ minh bạch.

### 4.5 Quy ước chung (mọi phase)
- Type hints đầy đủ, docstring tiếng Việt; comment tối giản; không refactor code không liên quan.
- Mọi hằng số quy tắc (offset, bảng Tứ Hóa) ghi chú nguồn `vendor/lasotuvi/App.py:<dòng>` trong code.
- Giữ nguyên hành vi KMS RAG (không đụng `rag.py`, `retriever.py`, `/chat/ask`).
- `git status` hiện có nhiều file chưa tracked (horoscope, `backend/app/db/`) — **không commit** trong quá trình làm; chỉ sửa code + test.

---

## 5. Lệnh xác minh & Tiêu chí hoàn thành (Verification)

- **Môi trường:** workspace `D:\Ki7\KMS_Tu_Vi`, Python 3.12 global (`python -m pytest`; chưa có `.venv`), `data/processed/kms.db` sẵn.
- **Chạy theo phase:**
  ```powershell
  python -m pytest tests/test_horoscope_facts_schema.py -v        # P0
  python -m pytest tests/test_horoscope_annual.py -v             # P1
  python -m pytest tests/test_horoscope_specificity.py -v        # P2
  python -m pytest tests/test_horoscope_cache.py -v              # P3
  python -m pytest tests/test_horoscope_frontend.py -v           # TC-19, 20
  ```
- **Hồi quy toàn cục (bắt buộc trước khi báo hoàn thành):**
  ```powershell
  python -m pytest tests/ -q
  ```
- **Tiêu chuẩn hoàn thành (Definition of Done):**
  - [x] 20 TC đều PASS; baseline KeyError (TC-04) xanh.
  - [x] Toàn bộ `pytest tests/ -q` PASS (không regression KMS RAG: `test_cache.py`, `test_two_way_scope.py` vẫn xanh).
  - [x] Chạy tay UI (theo `RUN_HOROSCOPE.md`): đổi năm + bấm Tạo lại → panel "Năm …" và bảng sao đổi thật (Thái Tuế, lưu Tứ Hóa, tiểu hạn); cùng input lần 2 chạy tức thì (cache); chế độ mock hiển thị đầy đủ bảng sao + cờ "cần lưu ý" không cần AI. *(Đã kiểm bằng AppTest TC-19/TC-20 + smoke backend; kiểm thị giác trên trình duyệt nên chạy lại khi nghiệm thu.)*
  - [x] `ACTIVE_TEST_PLAN.md` chuyển `PASSED` kèm thời gian chạy test cuối.

### Kết quả thực thi (2026-11-01)

| File test | Kết quả |
|---|---|
| `tests/test_horoscope_facts_schema.py` (P0) | 4 passed |
| `tests/test_horoscope_annual.py` (P1) | 7 passed |
| `tests/test_horoscope_specificity.py` (P2) | 4 passed |
| `tests/test_horoscope_cache.py` (P3, gồm index-version) | 5 passed |
| `tests/test_horoscope_frontend.py` (TC-19, TC-20, TC-21) | 8 passed |
| **Toàn bộ `tests/`** | **34 passed** |

TC-22 (bổ sung sau code review 01/11): đổi `index_version` (hash `index_manifest.json`) làm `compute_key` trả khóa khác, nên re-index sách tự vô hiệu cache Horoscope thay vì phải xóa tay.

TC-21 (bổ sung từ vòng code review 01/11): bộ lọc "Lưu niên năm X" và sao đã chọn được reset về mặc định khi báo cáo mới (khác năm) được tạo, tránh giá trị widget cũ nằm ngoài danh sách option mới.

Thay đổi so với plan gốc khi triển khai:
- Bỏ `st.form` ở sidebar: `target_year` nay là widget thường, đổi năm rerun ngay và hiện banner "báo cáo là của năm cũ" (đúng TC-19; khắc phục bẫy UX F3c). Nút "Tạo bản luận giải" đổi từ `form_submit_button` sang `st.button`.
- Cache chỉ lưu bài Gemini thành công, bỏ qua `specificity_low`; khóa cache dùng năm hiệu lực nên `target_year=None` dùng chung cache với năm hiện tại.
- Test cache patch `GEMINI_API_KEY` để không phụ thuộc `.env` của máy chạy.
- **Ngoài tầm kiểm thử tự động (nghiệm thu thủ công, không block hoàn thành):**
  - Chất lượng văn phong Gemini thật (thuộc giai đoạn 6 kế hoạch phát triển chung).
  - An lưu tinh bổ sung ngoài vòng Tuê + lưu Tứ Hóa (giai đoạn sau).

---

## T1 — Độ tin cậy dữ liệu giờ sinh (`input_confidence` A–D)

- **Ngày:** 2026-11-03
- **Trạng thái:** **PASSED**
- **Nguồn kế hoạch:** `C:\Users\Admin\.opencode\plan\kms-tuvi-knowledge-governance-adopt-plan.md` (T1).
- **Mục tiêu:** người xem khai mức chắc chắn của giờ sinh; mức C/D chỉ cho kết luận cấu trúc, cấm kết luận thời điểm/sự kiện, và mọi phần giới hạn phải nêu rõ dữ liệu giờ sinh chưa chắc chắn.

### Thay đổi chính

| File | Nội dung |
|---|---|
| `backend/app/schemas/horoscope.py` | Thêm `input_confidence` (A–D), `gio_sinh_source` (document/memory/estimate/unknown), `gio_sinh_error_phut` (≥0) cho cả request luận giải và hỏi nhanh; default A/memory/None để tương thích API cũ. |
| `backend/app/services/horoscope_confidence.py` **(MỚI)** | Nhãn A–D, chính sách C/D, phát hiện kết luận thời điểm/sự kiện, kiểm tra caveat trong `gioi_han`. |
| `backend/app/services/horoscope_features.py` | Truyền 3 field vào `thong_tin_co_ban`. |
| `backend/app/services/horoscope_interpreter.py` | Dòng dữ kiện trong prompt, rule A/B–C/D trong system prompt, `check_input_confidence` trong luồng retry, caveat trong mock reading. |
| `backend/app/services/horoscope_ask.py` | Prompt/rule C/D, kiểm tra câu trả lời Gemini, caveat trong mock answer. |
| `backend/app/services/horoscope_service.py` | Truyền field khi trích xuất features; đưa mức tin cậy vào cache key để không lẫn bài A với C/D. |
| `frontend/horoscope_ui.py`, `frontend/horoscope_ask.py` | 3 input optional, badge cảnh báo C/D, hiển thị mức trong báo cáo, truyền field sang hỏi nhanh. |

### Ma trận test (`tests/test_horoscope_input_confidence.py`)

| # | Ca kiểm thử | Kết quả |
|---|---|---|
| 1 | Schema default A/memory/None + enum + sai số âm bị từ chối | PASSED |
| 2 | Features propagate đúng 3 field | PASSED |
| 3 | Prompt có nhãn mức, sai số, ràng buộc C/D; mức A không có ràng buộc | PASSED |
| 4 | Prompt hỏi nhanh có nhãn mức + caveat | PASSED |
| 5 | `check_input_confidence` chỉ chặn C/D; bắt kết luận thời điểm và caveat thiếu | PASSED |
| 6 | `check_ask_input_confidence` chặn câu trả lời có kết luận thời điểm | PASSED |
| 7 | Mock reading C/D có caveat ở mọi kết luận + vận hạn | PASSED |
| 8 | Mock ask C/D có caveat | PASSED |
| 9 | Retry 1 lần khi bài C/D chứa kết luận thời điểm | PASSED |
| 10 | Cache tách mức A và C (2 lượt gọi LLM, không dùng lại bài A) | PASSED |
| 11 | AppTest: UI gửi đủ 3 field + hiện cảnh báo C/D | PASSED |

### Kết quả chạy

```powershell
python -m pytest tests/test_horoscope_input_confidence.py -v   # 11 passed
python -m pytest tests/ -q                                     # 120 passed in 89.71s
```

### Definition of Done

- [x] Mức C/D không cho kết luận thời điểm/sự kiện; `gioi_han` nêu nguyên văn "dữ liệu giờ sinh chưa chắc chắn (mức C/D)".
- [x] Mức A/B giữ nguyên hành vi cũ; default A nên client cũ không cần đổi payload.
- [x] Cache không trộn bài của các mức tin cậy khác nhau.
- [x] UI gửi/nhận đủ 3 field và cảnh báo C/D.
- [x] Không thêm phần trăm tin cậy (để dành T2 với `muc_tin_cay` 4 bậc).
