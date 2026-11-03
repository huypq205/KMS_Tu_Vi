# TEST PLAN: Horoscope — Khắc phục 4 điểm feedback giảng viên + baseline facts schema

> Review P1 (Plan_Fix_Mai_Anh_v2): PASSED; hợp đồng ba mức đọc — thêm
> `reading_mode` (tách khỏi provider) vào request + meta, `CACHE_SCHEMA_VERSION`
> 6→7 (thêm chiều mức đọc vào key), adapter 6 nhóm cho báo cáo cũ (trường thiếu
> hiển thị là thiếu, không suy đoán). Review code P1: sửa item hỏng giữ cấu trúc
> lồng nhau + meta đường lỗi đủ trường hợp đồng. Hồi quy: 2163 passed /
> 351 known T4 xfailed.
> T2/T3/T9 (governance) không bị thay thế hay khép lại bởi gói này.
>
> Review P2 (Plan_Fix_Mai_Anh_v2): PASSED; kiểm kê 30 quy tắc cách cục (21 quý + 9 phá)
> thành `configs/cach_cuc_catalog.yaml` (4 trạng thái + sẵn sàng thực thi + 8 ứng viên
> bản đầu + 4 rule nhạy cảm bị chặn); loader/validator với bất biến duyệt nguồn, không
> tự duyệt (reviewer_role='chua_chi_dinh'). Hồi quy: 2175 passed / 351 known T4 xfailed.
>
> Review P2b (Plan_Fix_Mai_Anh_v2): PASSED; tách quan hệ cung thành module dùng chung
> `palace_relations` (đồng cung / xung chiếu / 2 tam hợp / 2 giáp, cung neo nêu rõ, chuẩn
> hóa tên chi-cung không đoán khi mơ hồ, đọc miếu/vượng từ `saoDacTinh`, thiếu trả
> "thieu"); `get_tam_phuong_tu_chinh` và `_palace_evidence_kind` giữ nguyên hành vi.
> Không đổi bảng trạng thái sao / bảng Tứ Hóa. Hồi quy: 2196 passed / 351 known T4 xfailed.
>
> Review P2+P2b (2026-11-03): PASSED; sửa 3 chỗ "Tị"→"Tỵ" trong text catalog, harden
> validator P2 (cờ boolean dạng string bị chặn; bất biến I3/I5 + thiếu trường được kiểm
> chứng *chặn thật* qua P2.TC-10…13), `CHI_ORDER` re-export từ `palace_relations`
> (một nguồn sự thật địa chi), thêm P2b.TC-09c (nhãn tiếng Việt 5 trạng thái sao).
> Hồi quy: 2202 passed / 351 known T4 xfailed. T2/T3/T9 (governance) không bị thay thế hay
> khép lại bởi gói này.
>
> Review P3 (Plan_Fix_Mai_Anh_v2): PASSED; bộ nhận diện cách cục chạy bằng code trên dữ kiện
> lá số (`cach_cuc_detector`), đúng 8 quy tắc bản đầu, phân biệt khớp đủ / khớp một phần /
> không khớp / chưa thể đánh giá, liên kết `fact_id`, báo dữ kiện dùng chung, ghi điều kiện
> thuận/nghịch; AI bị chặn dẫn `rule_ids` ngoài kết quả nhận diện. Quy tắc vẫn giữ
> `chi_tham_khao` (không tự duyệt). Hồi quy: 2225 passed / 351 known T4 xfailed.
> T2/T3/T9 (governance) không bị thay thế hay khép lại bởi gói này.

> Review T1 sau merge T3: PASSED. Chặn cứng kết luận thời điểm C/D kể cả sau
> retry; thêm loai_ket_luan vào schema/mock/fixture/UI, cache v4. Hồi quy review:
> 2091 passed, 351 known T4 xfailed. Ghi chú cũ về trả specificity_low cho vi phạm
> C/D bên dưới là lịch sử, đã được sửa bởi review này.

> Review T2: PASSED; chỉ đếm fact_id khác nhau. Ngưỡng hiện hành rất mạnh/mạnh
> >=3, trung bình >=1, yếu >=0; thay ngưỡng mạnh 2 của triển khai ban đầu cho đúng
> plan. Cache v5, hồi quy 2092 passed / 351 known T4 xfailed.

> Review T7 dữ liệu thật: PASSED trên workbook Final/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx:
> 10456 bản ghi kiểm tra như mới không lỗi; cùng 10456 ID có trong kms.db. CSV
> cùng tên là bảng Indicator/Value/Explanation, không phải thư mục tuvi_import.

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

### Ghi chú giới hạn (chuyển tiếp T2/T3)

- Nếu Gemini sau retry vẫn chứa kết luận thời điểm ở mức C/D, bài được trả về với cờ `specificity_low=True` (chưa chặn cứng). Plan gốc để việc chặn cứng cho T2/T3 (`loai_ket_luan`); cache không lưu bài `specificity_low`.

---

## T2 — Bậc tin cậy per kết luận (`muc_tin_cay`), cấm phần trăm

- **Ngày:** 2026-11-03
- **Trạng thái:** **PASSED**
- **Nguồn kế hoạch:** `C:\Users\Admin\.opencode\plan\kms-tuvi-knowledge-governance-adopt-plan.md` (T2).
- **Mục tiêu:** mỗi `luan_diem`/`ket_luan` trả về có nhãn bậc tin cậy; bậc phải khớp số chứng cứ; không dùng phần trăm tin cậy.

### Thay đổi chính

| File | Nội dung |
|---|---|
| `backend/app/services/horoscope_interpreter.py` | `response_schema()` thêm `muc_tin_cay` (enum, required) cho `luan_diem`/`ket_luan`; prompt định nghĩa 4 bậc + cấm %; `check_conclusion_confidence` kiểm tra enum, số fact_id tối thiểu và %; retry 1 lần, sau retry vẫn sai → `invalid_response`; mock gắn nhãn |
| `backend/app/services/horoscope_cache.py` | `CACHE_SCHEMA_VERSION = 2` trong khóa cache để bài cũ thiếu `muc_tin_cay` tự miss |
| `frontend/horoscope_view.py`, `frontend/horoscope_ui.py`, `frontend/assets/horoscope.css` | `confidence_badge` + badge màu 4 bậc ở phần Kết luận và Lập luận |
| `tests/horoscope_support.py`, `tests/test_horoscope_feedback.py` | Fixture/mẫu cũ thêm `muc_tin_cay` để không vỡ hồi quy |

### Quy tắc đã chốt

- Enum: `rat_manh`, `manh`, `trung_binh`, `yeu`. Plan gốc ghi `yieu` (lỗi chính tả) → triển khai dùng `yeu`.
- Số `fact_id` tối thiểu: `rat_manh` 3, `manh` 2, `trung_binh` 1, `yeu` 0.
- Cấm mẫu phần trăm (`85%`, `85 %`, `12,5%`) trong mọi chuỗi của bài đọc.
- Thiếu/sai nhãn → retry 1 lần kèm chỉ dẫn; sau retry vẫn sai → `invalid_response` (model fallback hoặc mock), không trả bài thiếu nhãn.

### Ma trận test (`tests/test_horoscope_conclusion_confidence.py`)

| # | Ca kiểm thử | Kết quả |
|---|---|---|
| 1 | Schema bắt buộc `muc_tin_cay` + enum 4 bậc | PASSED |
| 2 | Prompt định nghĩa 4 bậc và cấm phần trăm | PASSED |
| 3 | `valid_reading` có nhãn hợp lệ → pass | PASSED |
| 4 | Thiếu nhãn hoặc nhãn lạ → reject | PASSED |
| 5 | `rat_manh` với 1 fact_id → reject; đủ 3 → pass | PASSED |
| 6 | `85%`, `85 %`, `12,5%` trong `nhan_dinh` → reject | PASSED |
| 7 | Thiếu nhãn → retry 1 lần, lần 2 hợp lệ → nhận bài Gemini | PASSED |
| 8 | Thiếu nhãn cả 2 lần → mock fallback `invalid_response`, không trả bài thiếu nhãn | PASSED |
| 9 | Mock reading gắn nhãn cho mọi kết luận | PASSED |
| 10 | `confidence_badge` map đúng 4 bậc + nhãn lạ về trung tính | PASSED |
| 11 | AppTest: báo cáo mock hiển thị badge "Tin cậy:" | PASSED |

### Kết quả chạy

```powershell
python -m pytest tests/test_horoscope_conclusion_confidence.py -v   # 11 passed
python -m pytest tests/ -q                                          # 131 passed in 78.99s
```

### Definition of Done

- [x] Mọi kết luận trả về (Gemini lẫn mock) có nhãn bậc tin cậy.
- [x] Không có phần trăm tin cậy trong bài đọc.
- [x] UI hiển thị badge màu theo bậc (rất mạnh = xanh, yếu = xám).
- [x] Cache cũ tự miss nhờ `CACHE_SCHEMA_VERSION`.
- [x] Hồi quy toàn bộ 131 test xanh.

---

## T3 — Từ điển loại chứng cứ + phản chứng bắt buộc

- **Ngày:** 2026-11-03
- **Trạng thái:** **PASSED**
- **Nguồn kế hoạch:** `C:\Users\Admin\.opencode\plan\kms-tuvi-knowledge-governance-adopt-plan.md` (T3).
- **Mục tiêu:** mỗi fact sao/cung có `kind` thuộc 10 loại chứng cứ; mỗi `luan_diem` có `loi_chung_cu` khớp `kind` của fact đã dẫn và `phan_chung` bắt buộc.

### Thay đổi chính

| File | Nội dung |
|---|---|
| `backend/app/core/evidence_types.py` (mới) | Enum 10 loại chứng cứ + nhãn tiếng Việt + câu chuẩn `NO_COUNTER_EVIDENCE` |
| `backend/app/services/horoscope_analysis.py` | Mỗi fact thêm `kind`: tọa thủ/tam hợp/xung chiếu/giáp cung theo vị trí so với Mệnh; tứ hóa gốc và lưu tứ hóa → `tu_hoa`; vòng Thái Tuế lưu niên → `van_han` |
| `backend/app/services/horoscope_interpreter.py` | Schema `luan_diem` thêm `loi_chung_cu` (enum, `minItems: 1`) và `phan_chung` (required); prompt giải thích 10 loại; `check_evidence_labels`; retry 1 lần rồi hard-reject; mock có `luan_diem` gắn nhãn |
| `backend/app/services/horoscope_cache.py` | `CACHE_SCHEMA_VERSION = 3` để bài cache cũ thiếu trường T3 tự miss |
| `frontend/horoscope_view.py`, `frontend/horoscope_ui.py`, `frontend/assets/horoscope.css` | `evidence_table` 3 cột (luận điểm, dấu hiệu thuận, dấu hiệu nghịch) + chip loại chứng cứ |
| `tests/horoscope_support.py`, `tests/test_horoscope_feedback.py`, `tests/test_horoscope_facts_schema.py` | Fixture/mẫu cũ thêm `loi_chung_cu`, `phan_chung`; schema fact yêu cầu `kind` |

### Quy tắc đã chốt

- 10 loại: `toa_thu`, `tam_hop`, `xung_chieu`, `giap_cung`, `tu_hoa`, `menh_cuc`, `van_han`, `nghiem_ly`, `truong_phai`, `suy_luan`.
- `loi_chung_cu` phải khớp ít nhất một `kind` của `fact_id` đã dẫn; `suy_luan` được phép đi kèm nhưng không thay thế loại chứng cứ thật.
- `phan_chung` bắt buộc không rỗng; nếu nguồn không có phản chứng thì ghi nguyên văn "Không ghi nhận phản chứng trong nguồn đã lấy."
- Thiếu/sai nhãn hoặc phản chứng rỗng → retry 1 lần; sau retry vẫn lỗi → `invalid_response` (model fallback hoặc mock), không trả bài thiếu nhãn.
- `MENH_CUC`, `NGHIEM_LY`, `TRUONG_PHAI`, `SUY_LUAN` là nhãn ngữ cảnh dành cho bước sau (hồ sơ sao/nghiệm lý/trường phái); hiện chỉ fact sao/cung được gắn `kind`.

### Ma trận test (`tests/test_horoscope_evidence_labels.py`)

| # | Ca kiểm thử | Kết quả |
|---|---|---|
| 1 | Từ điển đủ 10 loại, nhãn không rỗng | PASSED |
| 2 | Fact có `kind` đúng quan hệ cung với Mệnh (tọa thủ/tam hợp/xung chiếu/giáp cung) | PASSED |
| 3 | Tứ hóa gốc + lưu tứ hóa → `tu_hoa`; vòng Thái Tuế → `van_han` | PASSED |
| 4 | Schema bắt buộc `loi_chung_cu` (enum, min 1) và `phan_chung` | PASSED |
| 5 | Prompt hệ thống định nghĩa đủ 10 loại và câu phản chứng chuẩn | PASSED |
| 6 | Bài đọc hợp lệ có nhãn/phản chứng → pass | PASSED |
| 7 | Thiếu hoặc rỗng `loi_chung_cu` khi có fact → reject | PASSED |
| 8 | Nhãn ngoài enum → reject | PASSED |
| 9 | Nhãn không khớp `kind` của fact_id → reject; thêm `suy_luan` hợp lệ → pass | PASSED |
| 10 | `phan_chung` rỗng → reject; câu chuẩn → pass | PASSED |
| 11 | Thiếu nhãn → retry 1 lần kèm chỉ dẫn, lần 2 hợp lệ → nhận bài Gemini | PASSED |
| 12 | Phản chứng rỗng cả 2 lần → mock fallback `invalid_response` | PASSED |
| 13 | Mock reading có `luan_diem` gắn nhãn + phản chứng | PASSED |
| 14 | `evidence_table` có 2 cột dấu hiệu, chip loại chứng cứ, escape HTML | PASSED |
| 15 | AppTest: báo cáo mock hiển thị bảng "Dấu hiệu thuận/nghịch" | PASSED |

### Kết quả chạy

```powershell
python -m pytest tests/test_horoscope_evidence_labels.py -v   # 15 passed
python -m pytest tests/ -q                                    # 146 passed in 63.48s
```

### Definition of Done

- [x] 10 loại chứng cứ có nhãn tiếng Việt dùng chung backend/UI.
- [x] Mỗi fact sao/cung có `kind` và mỗi luận điểm có `loi_chung_cu` khớp fact.
- [x] `phan_chung` bắt buộc; có câu chuẩn khi nguồn không có phản chứng.
- [x] UI hiển thị bảng luận điểm với dấu hiệu thuận/nghịch.
- [x] Cache cũ tự miss nhờ `CACHE_SCHEMA_VERSION = 3`.
- [x] Hồi quy toàn bộ 146 test xanh.

### Khác biệt so với plan

- Plan chỉ yêu cầu label thuộc enum; bản triển khai kiểm tra thêm **label phải khớp `kind` của fact đã dẫn** để tránh gắn nhãn chứng cứ sai.
- Plan gợi ý `phan_chung` được phép ghi câu "không ghi nhận…"; bản triển khai bắt buộc chuỗi không rỗng và dùng câu chuẩn trong prompt/mock, nhưng vẫn chấp nhận phản chứng cụ thể khác.
- UI dùng bảng **3 cột** (luận điểm + 2 cột dấu hiệu) thay vì chỉ 2 cột, để giữ nhận định/giới hạn đi kèm.
- Mock reading từ T2 có `luan_diem` rỗng; T3 bổ sung 3 luận điểm dữ kiện (mỗi loại chứng cứ một mục) để bảng hiển thị được cả khi offline.
- Chưa sinh fact `kind=menh_cuc`; nhãn này để dành cho hồ sơ sao/nghiệm lý ở T6/T8.

---

## Governance T4 — Cross-check an sao (2026-11-03)

- **Trạng thái kiểm thử: PASSED** — có bất đồng nguồn được ghi nhận bằng strict XFAIL.
- **Trạng thái nghiệm thu T4: PASSED** — bất đồng đã document và có
  [GitHub issue #1](https://github.com/huypq205/KMS_Tu_Vi/issues/1).
  Các bất đồng chưa được phân xử bằng bảng/trang sách KMS.
- Phạm vi độc lập với T1/T2: chỉ bổ sung test, fixture và tài liệu;
  không thay đổi backend, UI, vendor hoặc bảng Tứ Hóa.
- Nguồn: `hung-ngm/tu-vi-dau-so`, commit
  `d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7`, `references/computation.md`.
- Fixture tĩnh: `tests/fixtures/an_sao_vectors.json`, **44 vector**, kỳ vọng
  từ các mốc tra độc lập, không sinh từ output vendor. Phủ 12 tháng × giờ Tý/Hợi,
  5 Cục, âm/dương nam/nữ, 10 Can, 12 Chi, ngày chẵn/lẻ, 6 Tuần và các nhóm sao T4.
- Nguồn không mô tả đủ vị trí tuyệt đối cho 6 vector ngày 2/Hỏa:
  vẫn kiểm tra hai chòm tương đối, sao phụ và hạn; ghi rõ giới hạn trong fixture.
- 351 trường khác thuộc 4 nhóm: Tử Vi và sai khác lan truyền (322),
  Khôi/Việt (8), Hỏa/Linh (18), Tứ Hóa (3). Mỗi trường có test quan sát riêng
  để không che regression mới. Không sửa kỳ vọng chỉ để làm test xanh.

```powershell
.venv\Scripts\python.exe -m pytest tests/test_lasotuvi_crosscheck.py -v
# 1873 passed, 351 xfailed in 4.07s
.venv\Scripts\python.exe -m pytest tests/ -q
# 2004 passed, 351 xfailed in 83.31s
```

Chi tiết: [báo cáo T4](../../docs/LASOTUVI_CROSSCHECK.md) và
[hồ sơ bất đồng](../../docs/issues/T4_AN_SAO_DISCREPANCIES.md).
GitHub issue đã đăng sau khi người dùng xác nhận cho phép công bố kết quả T4
lên `huypq205/KMS_Tu_Vi`. Hiệu chuẩn bảng Tứ Hóa thuộc T5.

---

## Governance T5 — Hiệu chuẩn bảng Tứ Hóa (2026-11-03)

- **Trạng thái: PASSED.**
- Đã đối chiếu đủ 40 mục/10 Can bằng AST từ vendor. Config mặc định khớp vendor;
  nguồn tham khảo cố định theo commit như T4. Có đúng 3 khác biệt:
  Canh Hóa Khoa (Thiên Đồng / Thái Âm), Canh Hóa Kỵ (Thái Âm / Thiên Đồng),
  Nhâm Hóa Khoa (Thiên Phủ / Tả Phụ).
- Hai bảng tách riêng trong `configs/tu_hoa_tables.yaml`, có `school`, `source`,
  `verification_status`; mặc định `lasotuvi`. Chọn bảng qua `KMS_TU_HOA_TABLE`.
- Adapter cập nhật đồng bộ hóa tinh gốc, lưu niên, facts, prompt và nhãn UI;
  hỗ trợ cách viết Tả phù/Tả Phụ. Không sửa file vendor hoặc tự gộp hai bảng.
- Metadata ID/signature tách cache theo bảng và nội dung cấu hình.
- Schema dữ kiện bổ sung được cập nhật cùng fixture chung và UI;
  không thay đổi schema JSON bài luận T1/T2.
- T4 ghim bảng vendor để không phụ thuộc cấu hình bảng của ứng dụng.
- Chưa phân xử bất đồng bằng sách KMS; issue #1 vẫn OPEN. T5 hoàn tất nhánh
  cấu hình nhiều bảng mà plan yêu cầu khi phát hiện khác biệt.

### Kiểm chứng

`tests/test_tu_hoa_tables.py`: **29 ca pass** trong lần hồi quy toàn bộ, gồm
10 Can đối chiếu vendor, 3 khác biệt chính xác, lựa chọn bảng cho lá số gốc/lưu niên,
facts/prompt/UI, bảo toàn snapshot, cache tách bảng, kiểm tra cấu hình lỗi,
escaping nhãn và chạy CLI từ thư mục khác.

```powershell
.venv\Scripts\python.exe scripts/compare_tu_hoa_tables.py
# 40 mục / 10 Can; 3 khác biệt; Config lasotuvi khớp vendor: True
.venv\Scripts\python.exe -m pytest tests/ -q
# 2033 passed, 351 xfailed in 92.75s
```

351 xfail là các bất đồng T4 đã được ghi nhận, không phải failure mới của T5.
Tài liệu sử dụng: [data dictionary](../../docs/data_dictionary.md#trường-phái-an-sao-kms-đang-dùng).
Lịch sử thay đổi: [CHANGELOG_KNOWLEDGE.md](../../docs/CHANGELOG_KNOWLEDGE.md).

---

## Governance T7 — Cổng kiểm duyệt nhập tri thức (2026-11-03)

- **Trạng thái: PASSED** — kiểm thử, tích hợp và review workbook thực tế:
  10.456 checked, 0 errors; đối chiếu baseline 0 new IDs. Xem cập nhật T11 bên dưới.
- Validator read-only: `scripts/validate_knowledge_import.py`; nhận CSV export
  `REPO_*` và workbook canonical, có `--json` để chỉ rõ file/sheet, dòng, ID, mã lỗi.
- Knowledge mới phải có >=1: nguồn+trang hợp lệ; trường phái/Author_Stances;
  ví dụ/ca kiểm chứng. ID cũ được nhận diện qua DB baseline mở read-only.
- Nguồn FORUM/VIDEO bắt buộc `DRAFT_NOT_RELEASED` và token
  `HYPOTHESIS_NEEDS_VALIDATION`, ép tier 9 trước rule theo sách; hiệu lực cả khi
  không bật gate tùy chọn. Chunker loại giả thuyết và tier 9 dù cấu hình sai.
- `import_excel.py --gate` kiểm tra trước init/ghi DB và kiểm tra lại trước khi
  thay knowledge/evidence/chunk; lỗi không làm mất dữ liệu hiện có.
- Metadata Source_Type, School, Validation_Example được đọc qua mapping.
  Bản ghi đủ căn cứ B/C có thể lưu khi chưa có trang; gate pass không tự đủ điều
  kiện index. Không thêm cột hay migrate DB production.
- CI chạy fixture bắt buộc và test âm tính; chạy CSV thực tế nếu có
  `tuvi_import/`, báo SKIPPED rõ ràng nếu vắng mặt. Thư mục có nhưng rỗng là lỗi.
- Tài liệu và mẫu đề xuất: [KNOWLEDGE_GATE.md](../../docs/KNOWLEDGE_GATE.md).
  Quy tắc nội dung không định mệnh tuyệt đối, không bịa nguồn/trang và giữ riêng
  quan điểm sách vẫn cần review thủ công, không coi gate là xác minh ngữ nghĩa.

### Kiểm chứng

39 test bao phủ: ba yếu tố OR; placeholder/thiếu căn cứ; trang sai; liên kết
source/evidence/redirect; nguồn D có release LOCKED; source D trộn nguồn sách;
quarantine kể cả khi tắt gate; tier/index không bị override; CSV/Excel/CLI;
preflight không init DB khi lỗi; bảo toàn knowledge/chunk; bản ghi chưa có trang;
nguồn video không ghi đè tên/định danh sách đã có khi dùng chung Book_Code.

```powershell
.venv\Scripts\python.exe scripts/validate_knowledge_import.py tests/fixtures/knowledge_gate/valid/
# PASSED; checked=4; new=4; quarantined=1; errors=0
.venv\Scripts\python.exe -m pytest tests/test_knowledge_gate.py -v
# 39 passed in 2.67s
.venv\Scripts\python.exe -m pytest tests/ -q
# 2072 passed, 351 xfailed in 49.73s
```

Trong lần triển khai ban đầu, `tuvi_import/` và workbook chưa có trong workspace.
Review sau đó tìm thấy workbook ở thư mục Final và kiểm tra read-only đủ 10.456
bản ghi; không lỗi, 0 ID mới so DB. Không import/build index lại; test tích hợp
dùng DB tạm. CSV cùng tên là bảng chỉ số, không phải REPO exports.

## Governance T6 — Hồ sơ sao (2026-11-03)

**PASSED**: 8 test riêng; hồi quy 2100 passed / 351 known T4 xfailed.
Review API alias/auth/503/404, 14 nhóm, nguồn sách tách biệt, trang dẫn thật,
20 seed qua gate, ưu tiên canonical và cấu hình tắt seed phía server.
Review UI thực tế 1440/768/390px và trạng thái Streamlit.
Chi tiết: [STAR_DOSSIER.md](../../docs/STAR_DOSSIER.md).

## Governance T8 — Nhật ký nghiệm lý (2026-11-03)

**PASSED**: 11 test riêng, hồi quy 2111 passed / 351 known T4 xfailed.
Review SQL freeze (prediction/snapshot/events), revision có lý do, enum, C/D,
chứng cứ, thời điểm server, cross-case và chống chấm phiên bản sau tiết lộ.
29 ca đã chấm và 30 ca trống chưa mở thống kê; 30 ca đã chấm mới mở số lượt.
Browser review ba kích thước không FAIL/WARN. Test dùng DB tạm.
Chi tiết: [CASE_VALIDATION.md](../../docs/CASE_VALIDATION.md).

## Governance T9 — Báo cáo vận năm (2026-11-03)

**PASSED**: 10 test riêng. Hồi quy đến T9: 2121 passed / 351 known T4 xfailed.
Lệnh hồi quy dùng `--ignore=tests/test_skill_validation.py` cho test T10 đang
triển khai, không bỏ test T1–T9. Review bốn tầng, dữ kiện server, năm ±1,
1900/2100, C/D, ID bịa, tháng thiếu, bảng Tứ Hóa, escaping và API.
Sửa thiếu năm fallback và khóa nối địa chi đại hạn sau review; cache v6.
Ảnh đóng/mở ba kích thước, lint/inspector không FAIL/WARN.
Chi tiết: [ANNUAL_REPORT.md](../../docs/ANNUAL_REPORT.md).

## Governance T10 — Skill KMS (2026-11-03)

**PASSED**: 13 test riêng; hồi quy 2134 passed / 351 known T4 xfailed.
`scripts/validate_skill.py` và quick_validate của skill-creator đều pass.
Review frontmatter, tên, thiếu/trùng key, <500 dòng, link/anchor, traversal;
review API thật cho ASK, dossier, annual và hai giờ sinh (provider mock, C/D).
CI bổ sung bước validate skill. Gói [tu-vi-kms](../../skills/tu-vi-kms/SKILL.md)
giữ tại repo, dùng tham chiếu tới docs KMS; chưa cài vào thư mục skill cá nhân.

## Governance T11 — Review và nghiệm thu toàn bộ (2026-11-03)

**PASSED**: hồi quy cuối `pytest tests/ -q`: **2135 passed, 351 known T4 xfailed**
(55.73s). Không ignore task nào trong lần cuối. Hai gate, script so bảng và
review UI/API/DB hoàn tất. T4 đáp ứng DoD document + issue, chưa phân xử bằng sách.

CI phát hiện ba test singleton cũ phụ thuộc model không cài trong backend nhẹ.
Đã tái hiện bằng subprocess chặn package, sửa lazy import/factory test cô lập,
6 test singleton pass; không skip chúng. [CI bc497f9 đã xanh](https://github.com/huypq205/KMS_Tu_Vi/actions/runs/41567801027).

Changelog/plan được cập nhật; workbook thật pass gate và khớp ID corpus. DB chỉ
thay cache test/bảng nhật ký rỗng, đã backup và khôi phục, không commit dữ liệu.
[Bảng nghiệm thu và giới hạn](../../docs/GOVERNANCE_ACCEPTANCE.md).

## Skill local — computation và star_meanings (2026-11-03)

**PASSED — phạm vi tích hợp tham khảo.** Chưa xử lý các khoảng trống T2/T3/T9.

- computation local có Git blob trùng fixture T4; không có engine thực thi và
  thiếu bảng nhất quán. Không thay bộ an sao hiện tại. Chạy lại cross-check:
  1873 passed / 351 known xfailed, so 40 mục Tứ Hóa vẫn ba khác biệt.
- 11 test mới cho loader/reference/nguồn, nhóm/alias, lỗi file/tắt, lọc nội dung,
  context, cache snapshot, UI, mock/Gemini provenance và an sao không đổi.
- Hồi quy: **2146 passed / 351 known T4 xfailed** (48.85s).
- Review giao diện desktop/tablet/mobile, không FAIL; một WARN khoảng trống
  desktop hiện hữu, chưa làm đợt redesign. Không gọi Gemini thật trong test.
- Tài liệu người dùng thêm giữ local; server khác phải cung cấp file hoặc cấu
  hình đường dẫn. Test CI dùng fixture, không cần công bố nguyên văn tài liệu.

Chi tiết: [LOCAL_TUVI_SKILL_INTEGRATION.md](../../docs/LOCAL_TUVI_SKILL_INTEGRATION.md).

## Plan_Fix_Mai_Anh_v2 P1 — Hợp đồng dữ liệu ba mức đọc (2026-11-03)

**Trạng thái:** **PASSED** — 17 test riêng `tests/test_horoscope_contract.py` (kèm 3 test review-fix TC-10…12: item hỏng giữ cấu trúc lồng nhau, meta đường lỗi đủ trường hợp đồng, chốt `GROUPS_REQUIRED_BY_MODE`); hồi quy toàn cục: **2163 passed / 351 known T4 xfailed** (68.11s, `-m "not heavy"`).

**Review code P1 (2026-11-03):** sửa 2 điểm — `adapt_point` cho item không phải dict trước đó trả cấu trúc phẳng (consumer truy trường lồng nhau gặp TypeError); meta của báo cáo lỗi (`provider=gemini` thiếu khóa) thiếu `reading_mode`/`contract_version` → đã chốt cả 3 đường ok/cached/error. Không đổi: `HoroscopeAskRequest` (phạm vi P6), `dieu_kien.thun` map từ `loi_chung_cu` là xấp xỉ adapter P1, P3/P6 thay bằng điều kiện có cấu trúc.

**Nguồn plan:** `Plan_Fix_Mai_Anh_v2.md` (P1 §3) — tách `reading_mode` khỏi `provider`, hợp đồng nhận định 6 nhóm, adapter báo cáo cũ, chiều cache mới.

### Thay đổi chính

| File | Thay đổi |
|---|---|
| `backend/app/schemas/horoscope_contract.py` | **MỚI**: `ReadingMode` (du_lieu/giai_thich/chuyen_sau), `CONTRACT_VERSION=1`, `MISSING="thieu"`, `adapt_point`/`adapt_reading`/`sample_response`; mapping 6 nhóm cho cả hai cấu trúc `luan_diem` và `ket_luan` (giai_thich_thun_viet thuộc ket_luan) |
| `backend/app/schemas/horoscope.py` | `HoroscopeRequest.reading_mode` (mặc định `chuyen_sau`, giữ hành vi hiện hành); field mới, tương thích ngược với client cũ |
| `backend/app/services/horoscope_cache.py` | `CACHE_SCHEMA_VERSION` 6→7; `compute_key` nhận chiều `reading_mode` (trị số cũ không truyền vẫn hoạt động, mặc định `chuyen_sau`) |
| `backend/app/services/horoscope_service.py` | `meta` thêm `reading_mode` + `contract_version`; cache key truyền `req.reading_mode` |
| `tests/test_horoscope_contract.py` | **MỚI**: P1.TC-01…09 |

### Ma trận test

- **P1.TC-01** (Unit): `reading_mode` mặc định + 3 giá trị hợp lệ; giá trị lạ bị `ValidationError`; `reading_mode` độc lập với `provider`.
- **P1.TC-02** (Unit): cache key khác nhau theo `reading_mode`; cùng mức → cùng key; `CACHE_SCHEMA_VERSION == 7`.
- **P1.TC-03** (Integration): `read_horoscope(provider="mock", reading_mode="du_lieu")` (fallback không gọi AI) trả `meta.reading_mode` + `meta.contract_version`, `cached=False`, `actual_provider="mock"`.
- **P1.TC-04** (Unit): adapter mục `luan_diem` — trường thiếu (`giai_thich`, `rule_ids`, `chu_de`, `chua_kiem_tra`) là `MISSING`, không suy đoán; `loi_chung_cu`→dieu_kien.thun, `phan_chung`→dieu_kien.nghich.
- **P1.TC-05** (Unit): adapter mục `ket_luan` — `giai_thich_thun_viet` map đúng; `source_refs=[]` giữ `[]` (đã kiểm tra, không trích dẫn), khác `MISSING`.
- **P1.TC-06** (Unit): `du_lieu` chỉ lấy khối `luan_diem`; `giai_thich`/`chuyen_sau` lấy cả hai; mode lạ → `ValueError`.
- **P1.TC-07** (Unit): báo cáo cũ rất cũ (thiếu cả trường T2/T3) vẫn qua adapter, nhóm thiếu đều là `MISSING`.
- **P1.TC-08** (Unit): bài fallback có `_generation` (mock, timeout) không làm adapter rơi KeyError.
- **P1.TC-09** (Unit): response mẫu 3 mức — `sample_response` giữ report gốc nguyên vẹn + khối `contract` đúng số item theo mức.
- **P1.TC-10** (Unit, review-fix): item không phải dict vẫn trả đúng cấu trúc lồng nhau, mọi lá `MISSING` (không TypeError khi truy `can_cu.rule_ids`).
- **P1.TC-11** (Integration, review-fix): báo cáo lỗi (`provider=gemini` thiếu khóa, không fallback) — `meta` vẫn mang `reading_mode` + `contract_version`.
- **P1.TC-12** (Unit, review-fix): chốt hình dạng `GROUPS_REQUIRED_BY_MODE` (du_lieu không cần nhóm giai_thich).

### Ghi chú ranh giới

- P1 chỉ chốt **hợp đồng + tương thích + ca kiểm thử**; hành vi pipeline ba mức (prompt, ngân sách token, fallback nội dung) thuộc P6.
- `rule_ids` hiện luôn `MISSING` — P3 (nhận diện cách cục) sẽ điền; UI (P7) hiển thị "chưa có quy tắc".
- Cache bump v7 làm toàn bộ cache cũ tự miss một lần (đúng thiết kế, không sửa data).

## Plan_Fix_Mai_Anh_v2 P2 — Kiểm kê và duyệt nguồn cách cục (2026-11-03)

**Trạng thái:** **PASSED** — 17 test riêng `tests/test_cach_cuc_catalog.py`; hồi quy toàn cục: **2175 passed / 351 known T4 xfailed** (63.52s, `-m "not heavy"`).

**Nguồn plan:** `Plan_Fix_Mai_Anh_v2.md` (P2 §4) — danh mục quy tắc có trạng thái và người duyệt; không tự duyệt; nội dung nhạy cảm bị chặn; file nguồn thiếu phải nhận diện đúng.

### Thay đổi chính

| File | Thay đổi |
|---|---|
| `configs/cach_cuc_catalog.yaml` | **MỚI**: kiểm kê 30 quy tắc (21 quý cách + 9 phá cách, section 1–2 của nguồn) + khai báo 8 section ngoài phạm vi (3–10) với nhãn nội dung nhạy cảm |
| `backend/app/services/cach_cuc_catalog.py` | **MỚI**: loader + validator (bất biến I1–I5), `filter_rules`, `batch_candidates`, `catalog_signature` |
| `tests/test_cach_cuc_catalog.py` | **MỚI**: P2.TC-01…09 |

### Ma trận test

- **P2.TC-01** (Unit): đủ 30 quy tắc (21 quý + 9 phá), id duy nhất, `reviewer_role='chua_chi_dinh'` nên không rule nào `duyet_dung`, mọi `nguoi_duyet` là null.
- **P2.TC-02** (Unit): trạng thái hợp lệ; rule nhạy cảm (4 quy tắc luận tử vong) không vượt `chi_tham_khao`/`can_doi_chieu` khi chưa duyệt.
- **P2.TC-03** (Unit): bất biến "sẵn sàng thực thi" — `san_sang_thuc_thi=true` ⟺ `diem_mo_ho=[]` + đủ 3 ca (đúng/sai/thiếu).
- **P2.TC-04** (Unit): đúng 8 ứng viên bản đầu cho P3, đủ rõ và không nhạy cảm.
- **P2.TC-05** (Unit): 8 section 3–10 được khai báo; section 4 (yểu chiết) và 8 (phẩm hạnh/giới) mang nhãn nhạy cảm; không rule nào trùng section.
- **P2.TC-06** (Unit): `filter_rules` theo nhom/trạng thái/sẵn sàng; `get_rule` raise KeyError cho id lạ.
- **P2.TC-07** (Unit): `catalog_signature` ổn định theo nội dung (P6 dùng cho cache key, truy ngược nguồn).
- **P2.TC-08** (Unit): validator chặn trạng thái sai, id trùng, **tự duyệt khi reviewer chưa chỉ định**, `duyet_dung` thiếu người duyệt + mốc.
- **P2.TC-09** (Unit): file nguồn không tồn tại → `CatalogError` rõ (không chạy im lặng).
- **P2.TC-10** (Unit, thêm ở review 2026-11-03): I3 kiểm chứng *chặn thật* — rule nhạy cảm gán `chua_ho_tro` (bên ngoài tham khảo/đối chiếu) raise; ngược lại `noi_dung_da_duyet=true` thì I3 không chặn.
- **P2.TC-11** (Unit, thêm ở review): I5 kiểm chứng trần — đẩy bản đầu lên 9 ứng viên raise `CatalogError`.
- **P2.TC-12** (Unit, thêm ở review): thiếu trường bắt buộc của rule (vd. xóa `ca_kiem_thu`) raise `CatalogError`.
- **P2.TC-13** (Unit, thêm ở review): cờ boolean trong YAML viết dạng string (`noi_dung_nhay_cam: "false"`) bị chặn — không ngầm coi chuỗi "false" là `True`/`False` sai nghĩa.

### Phân công & nhãn (P2 §4.2)

- Kiểm kê, chuẩn hóa, test: AI/engineer (báo cáo này).
- Người duyệt chuyên môn: **chưa chỉ định** (`reviewer_role: 'chua_chi_dinh'`) — khi chỉ định, sửa field này trong YAML rồi mới gán `duyet_dung` (có `nguoi_duyet` + `ngay_duyet`).
- Bạn: chốt phạm vi đưa vào sản phẩm.

### Kiểm kê nội bộ (số liệu cho quyết định phạm vi)

- 30 quy tắc: 16 đủ rõ (`san_sang_thuc_thi=true`), 14 còn điểm mơ hồ/mâu thuẫn (`can_doi_chieu`).
- 4 quy tắc nội dung nhạy cảm (tử vong/tuổi thọ): Linh Xương Đà Vũ, Cự Hỏa Kình Dương, Mã đầu đới kiếm, Mệnh vô chính diệu — bị chặn khỏi bản đầu.
- Bản đầu P3: 8 quy tắc ứng viên (`ung_vien_ban_dau`), đúng trần plan ("khoảng 5–8").

## Plan_Fix_Mai_Anh_v2 P2b — Chuẩn hóa quan hệ cung (2026-11-03)

**Trạng thái:** **PASSED** — 22 test riêng `tests/test_palace_relations.py`; hồi quy toàn cục: **2196 passed / 351 known T4 xfailed** (94.22s, `-m "not heavy"`).

**Nguồn plan:** `Plan_Fix_Mai_Anh_v2.md` (P2b §5) — tách quan hệ cung thành module dùng chung; đồng cung, 2 tam hợp, đối cung/xung chiếu, 2 giáp; cung neo nêu rõ; chuẩn hóa tên/mã cung; đọc miếu/vượng/đắc/bình/hãm từ `saoDacTinh`, thiếu trả "thiếu"; test đủ 12 cung, đặc biệt vòng qua Tý/Hợi.

### Thay đổi chính

| File | Thay đổi |
|---|---|
| `backend/app/services/palace_relations.py` | **MỚI**: phép tính quan hệ cung trên `cung_so` 1..12 (1 = Tý … 12 = Hợi); `doi_cung`, `tam_hop`, `giap_cung`, `tam_phuong`, `quan_he`, `cac_cung_lien_quan`; chuẩn hóa `CHI_NAMES` + mã cung (`normalize_palace_role`, `palace_so_by_role`, `resolve_anchor`); `evidence_kind`; `dac_tinh_in_palace` đọc `saoDacTinh`/`dac_tinh` |
| `backend/app/services/horoscope_features.py` | `get_tam_phuong_tu_chinh` **ủy thác** cho `palace_relations.tam_phuong`, giữ nguyên khóa `chinh_cung`/`doi_cung`/`tam_hop`/`all_cung_sos` và thứ tự cung |
| `backend/app/services/horoscope_analysis.py` | `_palace_evidence_kind` **ủy thác** cho `palace_relations.evidence_kind`; bỏ so sánh chuỗi có dấu `"Tị"/"Tỵ"` (nay chuẩn hóa tên chi), giữ nguyên kết quả đầu ra |
| `tests/test_palace_relations.py` | **MỚI**: P2b.TC-01…11 |

### API chính (P3/P5 dùng lại)

- `quan_he(a, b) -> "dong_cung" | "tam_hop" | "xung_chieu" | "giap_cung" | "khong"` — mã trùng `rule["quan_he"]` của danh mục P2 (P3 so khớp trực tiếp).
- `tam_phuong(cung_so)` — 4 cung Tam phương Tứ chính, kèm `giap_cung` (không có trong kết quả cũ).
- `resolve_anchor(palaces, "Mệnh" | "Quan Lộc" | "Tý" | cung_so)` — cung neo được nêu rõ, raise `ValueError` nếu không xác định (không mặc định về Mệnh).
- `dac_tinh_in_palace(palace, "Tử Vi") -> "mieu"|"vuong"|"dac"|"binh"|"ham"|MISSING` — chỉ đọc, không suy.
- `MISSING = "thieu"` của hợp đồng P1 dùng chung khi thiếu dữ liệu.

### Ma trận test

- **P2b.TC-01** (Unit): `doi_cung` đủ 12 cung, đối xứng (2 lần trả về gốc), không tự trỏ; wrap Tý(1)↔Ngọ(7), Tỵ(6)↔Hợi(12).
- **P2b.TC-02** (Unit): `tam_hop` tạo đúng 4 nhóm rời nhau phủ kín 12 cung; quan hệ 2 chiều giữa 3 cung trong nhóm; Hợi(12) → Mão(4), Mùi(8).
- **P2b.TC-03** (Unit): `giap_cung` đủ 12 cung; `giap_cung(1) == (12, 2)`, `giap_cung(12) == (11, 1)`; quan hệ giáp đối xứng; không trùng chính nó/đối cung.
- **P2b.TC-04** (Unit): `quan_he` đối xứng toàn ma trận 12×12; mỗi cung đúng `{dong_cung:1, xung_chieu:1, tam_hop:2, giap_cung:2, khong:6}`; mã quan hệ dùng được với `RELATIONSHIPS` của P2.
- **P2b.TC-05** (Unit): `tam_phuong` trả 4 cung duy nhất, `all_cung_sos` đúng thứ tự `[chính, đối, +4, +8]`; wrap Hợi → `[12, 6, 4, 8]`; `get_tam_phuong_tu_chinh` giữ nguyên shape, nhận cả list lẫn map, cung thiếu trả `{}`.
- **P2b.TC-06** (Unit): chuẩn hóa tên chi — đúng 12 tên, `"Tị"→"Tỵ"` (biến thể cũ), khác hoa/thường và bỏ dấu khi không mơ hồ; `"ty"` mơ hồ Tý/Tỵ → `None` (không đoán); tên cung `"Quan Lộc"` → mã `quan_loc`; `resolve_anchor` nhận số cung/tên chi/tên cung và raise khi thiếu.
- **P2b.TC-07** (Unit): `evidence_kind` đủ 12×12 khớp `quan_he`; `"Tị"`/`"Tỵ"` cho cùng kết quả giáp cung; tên mơ hồ/không hợp lệ → `toa_thu`; `_palace_evidence_kind` giữ kết quả cũ.
- **P2b.TC-08** (Unit): `cac_cung_lien_quan` phân nhóm đủ 12 cung, không trùng, không sót.
- **P2b.TC-09** (Unit): đọc đúng 5 mã `M/V/Đ/B/H` từ `saoDacTinh`; khớp tên sao không phân biệt hoa/thường/dấu; đọc được cả dạng `describe_palace` (`chinh_tinh[].dac_tinh`).
- **P2b.TC-09c** (Unit, thêm ở review): nhận cả nhãn tiếng Việt của 5 trạng thái sao (`Miếu`/`VƯỢNG`/`ĐẮC`/`bình`/`hãm` → mã chuẩn); nhãn không tồn tại (vd. "Đa") vẫn là `MISSING`.
- **P2b.TC-09b** (Unit): thiếu cung/sao/`saoDacTinh`/mã lạ → `MISSING`; sao không nằm trong cung → `MISSING` (không lấy từ cung khác).
- **P2b.TC-10** (Unit): `dac_tinh_in_palace` không sửa dữ liệu gốc; module chỉ có đúng 5 mã vendor, không thêm bảng miếu/vượng mới.
- **P2b.TC-11** (Unit): `cung_so` 0, 13, -1, 12.5, "1", None, True/False đều raise `ValueError` (kể cả qua `get_tam_phuong_tu_chinh`).

### Review P2 + P2b (2026-11-03, sau khi commit `a202b7a` + `371558e`)

Kiểm tra chéo hai gói, phát hiện và sửa:

| # | Phát hiện | Gói | Xử lý |
|---|---|---|---|
| R1 | 3 chỗ text tự do trong YAML ghi "Tị" thay vì "Tỵ" (validator chỉ kiểm trường `chi` có cấu trúc nên không bắt) | P2 | Sửa 3 dòng thành "Tỵ" cho nhất quán |
| R2 | Bất biến I3 (nhạy cảm chưa duyệt) và I5 (trần 8 ứng viên) chỉ được kiểm chứng bằng dữ liệu hiện có, chưa có test kiểm chứng validator *thật sự chặn* | P2 | Thêm P2.TC-10…13: rule nhạy cảm vượt trần trạng thái raise; `noi_dung_da_duyet=true` thì I3 không chặn; 9 ứng viên raise; thiếu `ca_kiem_thu` raise; cờ boolean dạng string ("false") raise |
| R3 | `horoscope_analysis.CHI_ORDER` là bản sao của chuỗi chi trong `palace_relations` (2 nguồn sự thật) | P2b | `CHI_ORDER = CHI_NAMES` re-export từ `palace_relations`; test import sẵn có không đổi |
| R4 | Biến cục bộ đặt tên `quan_he` trong `get_tam_phuong_tu_chinh` dễ nhầm với mã quan hệ P2 | P2b | Đổi tên thành `tptc` |
| R5 | (đã loại) nghi ngờ nhãn "Đắc" fold thành "da" → MISSING; probe theo codepoint xác nhận nhãn trong module là "Đắc" (U+0110+U+1EAF) fold đúng "dac" | P2b | Không cần sửa; ghi test P2b.TC-09c để đóng băng hành vi |

Ngoài phạm vi gói này (chỉ ghi nhận, không sửa):
- `horoscope_features.py:219` — title "Mệnh Cục Tị Hòa" (nghi ngờ chính tả nội dung "Tị" vs "Hòa" chuẩn; thuộc duyệt nội dung T9/plan, cần chủ nội dung chốt từ ngữ).
- Frontend vẫn giữ phép tính quan hệ riêng (`frontend/laso_renderer.py`…) — gom về `palace_relations` khi làm P5/P7.
- `catalog_signature` chỉ chứa `version/source_file/rules`: đúng thiết kế (P3/P6 phụ thuộc nội dung rules; đổi `reviewer_role` thuần túy không đổi kết quả P3 nên cache vẫn hợp lệ).

### Ranh giới & ghi chú

- **Không** đổi bảng trạng thái sao (`Sao.anDacTinh`) hay bảng Tứ Hóa (`configs/tu_hoa_tables.yaml`, `tu_hoa_tables.py`) — đúng P2b §5.3.
- `cung_so` là nguồn chuẩn duy nhất; tên chi/cung chỉ dùng để nhập liệu và hiển thị, luôn chuẩn hóa trước khi so sánh.
- `"ty"` không dấu là mơ hồ giữa Tý (1) và Tỵ (6) → trả `None`; muốn chỉ định phải viết có dấu.
- `quan_he` trả `"khong"` khi hai cung không liên hệ; `"khong"` không nằm trong danh mục quy tắc P2 (quy tắc chỉ dùng 4 quan hệ).
- P3 sẽ dùng `quan_he`/`resolve_anchor`/`dac_tinh_in_palace`; P5 dùng cùng module để vẽ/đánh dấu quan hệ cung.

## Plan_Fix_Mai_Anh_v2 P3 — Nhận diện cách cục (2026-11-03)

**Trạng thái:** **PASSED** — 23 test riêng `tests/test_cach_cuc_detector.py`; hồi quy toàn cục: **2225 passed / 351 known T4 xfailed** (80.63s, `-m "not heavy"`).

**Nguồn plan:** `Plan_Fix_Mai_Anh_v2.md` (P3 §6) — nhận diện cách cục **bằng code trên dữ kiện lá số**, độc lập AI: đối chiếu sao/cung/quan hệ P2b/tầng thời gian, gắn kết quả với `fact_id`, ghi **đạt / không đạt / chưa kiểm tra được**, phát hiện dữ kiện bị nhiều quy tắc dùng, ghi điều kiện thuận/nghịch. Bản đầu chạy đúng 8 quy tắc `ung_vien_ban_dau` của P2.

### Thay đổi chính

| File | Thay đổi |
|---|---|
| `backend/app/services/cach_cuc_detector.py` | **MỚI**: `detect_cach_cuc` (8 quy tắc bản đầu), dựng chỉ mục sao theo cung + chỉ mục `fact_id`, đối chiếu điều kiện cấu trúc (sao/cung/quan hệ/chi) và bổ sung (trạng thái sao), xếp 4 kết quả, ghi `fact_reuse`, `check_rule_ids` chặn AI tự thêm cách cục |
| `backend/app/services/cach_cuc_catalog.py` | Thêm `DAC_TINH_STATES`; chuẩn hóa/kiểm `trang_thai_sao` (mapping tên sao → `mieu/vuong/dac/binh/ham`, sao phải thuộc quy tắc) |
| `configs/cach_cuc_catalog.yaml` | Thêm `trang_thai_sao` cho 3 quy tắc có yêu cầu "miếu" trong văn bản nguồn (Thất Sát, Vũ Khúc, Kình Dương/Hỏa Tinh); **không** đổi bảng miếu vượng/Tứ Hóa |
| `backend/app/services/horoscope_interpreter.py` | `generate_mock_reading` chạy nhận diện và thêm khối `cach_cuc`; `luan_diem`/`ket_luan` mang `rule_ids` + `dieu_kien_chua_kiem_tra`; prompt có khối cách cục đã nhận diện và lệnh cấm tự thêm; schema/mock points thêm 2 trường; `interpret_horoscope` chạy `check_rule_ids` và retry/fallback như các kiểm tra khác |
| `tests/test_cach_cuc_detector.py` | **MỚI**: P3.TC-01…21b |

### Bốn kết quả nhận diện (P3 §6.2)

| Mã | Nghĩa | Cách xếp |
|---|---|---|
| `khop_du` | Khớp đủ | Mọi điều kiện bắt buộc đạt; điều kiện bổ sung (nếu có) cũng đạt |
| `khop_mot_phan` | Khớp một phần | Cấu trúc (sao/cung/quan hệ/chi) đạt, nhưng điều kiện bổ sung không đạt |
| `khong_khop` | Không khớp | Có ít nhất một điều kiện cấu trúc không đạt (kể cả thiếu sao) |
| `chua_the_danh_gia` | Chưa thể đánh giá | Thiếu dữ kiện: chưa đủ 12 cung, chưa an sao, thiếu trạng thái sao, hoặc quy tắc ngoài tầng lá số gốc |

Điều kiện con ghi `dat` / `khong_dat` / `chua_kiem_tra` (kèm lý do), không gộp "thiếu dữ liệu" với "không đạt".

### API chính

- `detect_cach_cuc(features, catalog=None, rules=None, facts=None, context=None)` → `{phien_ban, catalog_signature, tong_so_quy_tac, tom_tat, rules, fact_reuse, canh_bao}`. Không truyền `rules` thì chạy `batch_candidates(catalog)`.
- `check_rule_ids(reading, detection)` → `None` nếu hợp lệ, chuỗi lý do nếu AI dẫn `rule_id` không có trong kết quả hoặc quy tắc `khong_khop`/`chua_the_danh_gia`. `rule_ids` vắng/None/`MISSING` (báo cáo cũ) được bỏ qua.
- Hằng số: `OUTCOME_*`, `OUTCOMES`, `CONDITION_DAT/KHONG_DAT/UNKNOWN`, `DETECTION_CAVEAT`.

### Hành vi trên fixture thật

`make_features(2026)` (lá số 15/8/1995): **0 khớp đủ, 0 khớp một phần, 8 không khớp, 0 chưa thể đánh giá** — đúng kỳ vọng vì lá số này không có Tử Phủ đồng cung tại Dần/Thân, Thái Âm tại Tý, Tham Vũ tại Sửu/Mùi, v.v. Dữ kiện `fact_id` `10` (Vũ Khúc tại Dần) được báo dùng chung bởi `quy-tham-vo-dong-hanh` và `quy-vu-khuc-mieu-vien`. Lá số rỗng (không an sao) trả cả 8 quy tắc `chua_the_danh_gia`, không đoán.

### Ma trận test

- **P3.TC-01** (Unit): đúng 8 quy tắc `ung_vien_ban_dau`, đúng thứ tự danh mục; mọi kết quả giữ `trang_thai_noi_dung == "chi_tham_khao"` (không tự duyệt); `tom_tat` cộng đúng 8; có `catalog_signature`.
- **P3.TC-02** (Positive): Tử Vi + Thiên Phủ đồng cung tại Dần → `khop_du`; điều kiện `quan_he`/`chi` đạt; `fact_ids` đúng 2 fact của Tử Vi/Thiên Phủ tại Dần.
- **P3.TC-03** (Negative): chỉ có Tử Vi → `khong_khop`; điều kiện `sao:Thiên Phủ` là `khong_dat`; vẫn giữ `fact_id` của Tử Vi.
- **P3.TC-04** (Near-miss): Tử Phủ đồng cung tại Tý → `khong_khop`; `quan_he` đạt nhưng `chi` không đạt, `gia_tri_thuc_te == "Tý"`.
- **P3.TC-05** (Near-miss): Tử Vi tại Dần, Thiên Phủ tại Ngọ → `khong_khop`; điều kiện `quan_he` ghi `quan_he_thuc_te == "tam_hop"`.
- **P3.TC-06** (Positive): Lộc Tồn tại Tý + Thiên Mã tại Thìn (tam hợp) → `khop_du`.
- **P3.TC-07** (Thiếu dữ liệu): Thất Sát tại Dần nhưng `dac_tinh == "—"` → `chua_the_danh_gia`; `trang_thai_sao` là `chua_kiem_tra`, giá trị `MISSING`; `dieu_kien_chua_kiem_tra` không rỗng.
- **P3.TC-08** (Partial): Thất Sát tại Dần, trạng thái Hãm → `khop_mot_phan`; `chi` đạt, `trang_thai_sao` không đạt.
- **P3.TC-09** (Positive): Thất Sát tại Dần, trạng thái Miếu → `khop_du`.
- **P3.TC-10** (Ranh giới): sao lưu niên Thất Sát tại Dần **không** thoả quy tắc `la_so_goc` → `khong_khop`; `fact_id` lưu niên không nằm trong kết quả.
- **P3.TC-11** (Ranh giới): quy tắc `tang_thoi_gian == "luu_nien"` → `chua_the_danh_gia`, lý do nêu "tầng thời gian" (P3 bản đầu chỉ nhận diện lá số gốc).
- **P3.TC-12** (Positive): Hóa Khoa/Tý + Hóa Quyền/Thìn + Hóa Lộc/Thân (tam phương) → `khop_du`.
- **P3.TC-13** (Negative): chỉ 2/3 Tứ Hóa → `khong_khop`, điều kiện `sao:Hóa Lộc` không đạt.
- **P3.TC-14** (Điều kiện thuận): Thiên Cơ + Cự Môn đồng cung tại Mão với can tuổi không thuộc `can_tuoi` vẫn `khop_du`; `can_tuoi` nằm ở `dieu_kien_thuan` và ghi `khong_dat`/`dat` tương ứng — không chặn kết quả.
- **P3.TC-15** (Dữ kiện dùng chung): Tham Lang + Vũ Khúc tại Sửu → Tham Vũ `khop_du`, Vũ Khúc miếu viên `khong_khop`; `fact_reuse` báo đúng `fact_id` của Vũ Khúc dùng bởi cả 2 quy tắc.
- **P3.TC-16** (Thiếu dữ liệu): không an sao → cả 8 quy tắc `chua_the_danh_gia`, đều có `dieu_kien_chua_kiem_tra`.
- **P3.TC-17** (Thiếu dữ liệu): chỉ 11 cung → cả 8 quy tắc `chua_the_danh_gia`.
- **P3.TC-18** (Hợp đồng): `check_rule_ids` nhận `rule_id` đã nhận diện; bỏ qua `MISSING`/mục cũ; chặn `rule_id` bịa.
- **P3.TC-18b** (Hợp đồng): chặn `rule_id` có trong danh mục nhưng kết quả `khong_khop`.
- **P3.TC-19** (Tích hợp): `generate_mock_reading` có khối `cach_cuc`, `ket_luan` mang `rule_ids` + `dieu_kien_chua_kiem_tra`; adapter P1 giữ nguyên `rule_ids` trong `can_cu`.
- **P3.TC-20** (Prompt): prompt nêu tên + `rule_id` cách cục đã nhận diện và lệnh "không tự thêm".
- **P3.TC-21** (Validator): `trang_thai_sao` với giá trị lạ (`"sai"`) → `CatalogError`.
- **P3.TC-21b** (Validator): `trang_thai_sao` nêu sao ngoài danh sách `sao` của quy tắc → `CatalogError`.

### Ranh giới & ghi chú

- **Không** đổi bảng trạng thái sao hay bảng Tứ Hóa; P3 chỉ đọc `saoDacTinh`/`dac_tinh` qua `palace_relations.dac_tinh_in_palace`.
- **Không tự duyệt**: kết quả giữ nguyên `trang_thai` của quy tắc (`chi_tham_khao`); `reviewer_role` vẫn `chua_chi_dinh`.
- Quy tắc `la_so_goc` chỉ đọc sao gốc; sao lưu niên không bao giờ thoả quy tắc gốc (TC-10).
- AI không được thêm cách cục: `rule_ids` chỉ hợp lệ khi có trong kết quả code và quy tắc `khop_du`/`khop_mot_phan`; prompt nêu rõ, validator chặn + retry.
- `can_tuoi` là **điều kiện thuận** (lấy từ mục `ho_tro` nguồn), không phải điều kiện bắt buộc; `ho_tro`/`pha_cach` dạng văn bản ghi `chua_kiem_tra`, không tự diễn giải.
- `cung_muc_tieu` chưa được dùng để neo; chỉ `cung_neo` xác định cung neo, không có neo thì tìm nhóm cung theo quan hệ.
- Ngoài phạm vi (chỉ ghi nhận): title `horoscope_features.py:219` "Mệnh Cục Tị Hòa" (nội dung); frontend vẫn tự tính quan hệ cung — gom về `palace_relations` khi làm P5/P7.
