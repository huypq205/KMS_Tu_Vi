# KẾ HOẠCH IMPLEMENT — Áp dụng pattern quản trị tri thức từ 2 repo Tử Vi vào KMS_Tu_Vi

**Phiên bản:** v1.0 (draft) — 2026
**Trạng thái:** DRAFT — chờ chuyển sang agent implement
**Người lập:** Claude (QA/Test Architect) theo AGENTS.md

## 0. Đầu vào và nguồn tham khảo

| Nguồn | Vai trò | License | Xử lý nội dung |
|---|---|---|---|
| `duandigi/tu-vi-dau-so-research` (repo 1) | **Tầng quản trị**: quy trình, chứng cứ, phản chứng, nghiệm lý, cổng chất lượng, skill packaging | MIT | Áp dụng pattern; khi trích dẫn phải ghi nguồn |
| `hung-ngm/tu-vi-dau-so` (repo 2) | **Tầng nguyên liệu**: bảng an sao (computation.md), nghĩa sao, cách cục | Không có (chỉ "personal/educational") | **CHỈ tham khảo nội bộ. Không copy nguyên văn vào KMS.** Mọi nội dung đưa vào KMS phải qua cổng gate (T7) và gắn nguồn |
| KMS hiện tại | Mã nguồn sự thật (source of truth) | nội bộ | PDF 3 sách + `REPO_*.csv` + `kms.db` là canonical; LLM không tạo tri thức mới |

### Hiện trạng đã xác minh (KHÔNG làm lại)
- Prompt interpreter đã có: cấm tuyệt đối, "không phán tính cách từ 1 sao", bắt buộc `gioi_han` + `fact_ids` + `source_refs`, "chưa đủ căn cứ từ nguồn đã lấy".
- `check_specificity`: tối thiểu 3 fact + đúng năm xem; retry 1 lần (anti-Barnum).
- `trust_tier` (1/2/3/9) config-driven + `verification_status` + REVIEW_QUEUE.
- `KnowledgeItem.version`, `Release_Status`, `Author_Stances`, `Conflict_Status` (REPO_KNOWLEDGE).
- Nguyên tắc plan §0: "giữ ba tiếng nói", "không bịa trang", "LLM không tạo tri thức canonical".
- `vendor/lasotuvi` (doanguyen, 2016) làm an sao; `horoscope_features.py` đóng gói features.

## 1. Nguyên tắc bất biến khi implement
1. Mọi kết luận trả người dùng: **không ngôn ngữ định mệnh tuyệt đối** (ngày chết, bệnh nặng, ly hôn, phá sản, "thắt cổ", "chết đuối"…). Nội dung repo 2 chứa các câu này → bắt buộc chuyển dạng "cổ thư ghi: … (theo [sách])" hoặc bỏ.
2. Không percentage trong kết luận (chưa có thống kê nghiệm lý đủ mẫu).
3. Không hòa trộn quan điểm giữa các sách (giữ 3 tiếng nói).
4. TDD theo AGENTS.md: test trước → code → chạy `pytest` → hồi quy toàn bộ.
5. Mọi thay đổi schema response phải cập nhật UI + test fixture (`tests/horoscope_support.py`) cùng đợt.

## 2. Các task theo đợt

### ĐỢT 1 — P0 (minh bạch hóa câu trả lời) — ước 2–4 ngày

#### T1. Độ tin cậy dữ liệu đầu vào (`input_confidence` A–D)
**Tham khảo:** repo 1 `case.schema.json` (`input_confidence`, `source_of_time`, `estimated_error_minutes`).

- `backend/app/schemas/horoscope.py` — thêm vào `HoroscopeRequest` và `HoroscopeAskRequest`:
  - `input_confidence: Literal["A","B","C","D"] = "A"` — A: giờ rõ, không sát ranh; B: sai số nhỏ; C: sát ranh giờ/nhớ gần đúng; D: thiếu dữ liệu cốt lõi.
  - `gio_sinh_source: Literal["document","memory","estimate","unknown"] = "memory"`
  - `gio_sinh_error_phut: int | None = None` (≥0)
- `horoscope_features.py`: propagate 3 field vào `thong_tin_co_ban` (kiểm tra `build_horoscope_user_prompt` giữ nguyên các key hiện có trong `PROMPT_KEYS`).
- `HOROSCOPE_SYSTEM_PROMPT` (interpreter): rule — khi C/D: chỉ được kết luận loại *cấu trúc*, cấm loại *thời điểm/sự kiện*; `gioi_han` phải nêu "dữ liệu giờ sinh chưa chắc chắn (mức C/D)".
- UI Streamlit (form input horoscope): 3 trường optional + badge cảnh báo khi C/D.

**Test (new `tests/test_horoscope_input_confidence.py`):**
1. Schema: default A; enum chấp nhận đúng; `gio_sinh_error_phut` âm → validation fail.
2. Prompt: features C → prompt chứa nhãn mức C; features D → prompt chứa cấm kết luận thời điểm.
3. Response validation: reading loại thời điểm với input C/D → bị trả về (bắt buộc đi cùng T2/T3 về `loai_ket_luan`).
4. UI render warning (nối suite `test_horoscope_frontend.py`).

**DoD:** user đánh D → không thấy kết luận "giai đoạn/năm X sẽ…" nào trong bài; `gioi_han` nêu rõ.

#### T2. Mức tin cậy 4 bậc per kết luận (cấm %)
**Tham khảo:** repo 1 `conclusion.confidence` (very_strong/strong/medium/weak) + SOURCE_POLICY §6.

- `horoscope_interpreter.response_schema()`: thêm cho mỗi item `luan_diem` và `ket_luan`:
  - `muc_tin_cay: Literal["rat_manh","manh","trung_binh","yieu"]` (required).
- Prompt: định nghĩa 4 mức (rất mạnh ≥3 nguồn/tầng độc lập không phản chứng lớn; mạnh 2–3 tầng, phản chứng đã giải thích; trung bình thiếu điều kiện hoặc phụ thuộc một sách; yếu 1 dấu hiệu hoặc đầu vào yếu) + câu lệnh "không viết phần trăm độ tin cậy".
- Validate trong interpreter (nơi `check_specificity` đang hoạt động): `muc_tin_cay` thiếu/không thuộc enum → `invalid_response` (retry 1 lần như hiện hành); regex cấm `\d{1,3}(\.\d+)?%` trong `nhan_dinh`, `giai_thich_thun_viet`, `gioi_han` (trừ ngữ cảnh "chu kỳ 60 năm"-kiểu → whitelist theo context field, đơn giản hóa: cấm trong `nhan_dinh`).
- UI: badge màu theo bậc (yếu = xám, rất mạnh = xanh).

**Test (bổ sung `tests/test_horoscope_specificity.py` + fixture `horoscope_support.py`):**
1. `valid_reading` thêm `muc_tin_cay` hợp lệ → pass.
2. Thiếu `muc_tin_cay` → `invalid_response`, retry (mô phỏng 2 lần gọi LLM).
3. Chứa "85% khả năng" trong `nhan_dinh` → bị reject.
4. `fact_ids` < 2 mà claim `rat_manh` → reject (rule: bậc phải nhất quán với số chứng cứ; `manh` cần ≥3 fact như check_specificity hiện có).

**DoD:** mọi kết luận trả về có nhãn bậc tin cậy; không có %; UI hiển thị badge.

#### T3. Từ điển loại chứng cứ + phản chứng bắt buộc
**Tham khảo:** repo 1 `evidence-types.json` (10 loại) + REASONING_ENGINE §2 (ma trận chứng cứ có `direction: support/counter`).

- File mới `backend/app/core/evidence_types.py`: enum 10 loại + nhãn tiếng Việt:
  `TOA_THU, TAM_HOP, XUNG_CHIEU, GIAP_CUNG, TU_HOA, MENH_CUC, VAN_HAN, NGHIEM_LY, TRUONG_PHAI, SUY_LUAN`.
  (KMS tạm dùng 7 loại gắn được với data: TOA_THU/TAM_HOP/XUNG_CHIEU/GIAP_CUNG từ `tam_phuong_tu_chinh_menh` + palace facts; TU_HOA; MENH_CUC; VAN_HAN từ `nam_xem`/`luu_nien`/`dai_han`; TRUONG_PHAI khi segment trả về chỉ có 1 book_code; SUY_LUAN khi LLM nối mạch mà không có fact_id nào.)
- `horoscope_analysis.build_star_facts`: mỗi fact thêm field `kind` (map từ key features: chính tinh trong cung → TOA_THU; sao tam phương → TAM_HOP; đối cung → XUNG_CHIEU; tứ hóa → TU_HOA; đại hạn/lưu niên → VAN_HAN; mệnh cục → MENH_CUC).
- `response_schema()`: `luan_diem` thêm `loi_chung_cu: list[str]` (enum, min 1 khi có fact_ids) và `phan_chung: str` (required — được phép ghi "không ghi nhận phản chứng trong nguồn đã lấy").
- Prompt: hướng dẫn đặt nhãn + câu lệnh phản chứng bắt buộc.
- UI: 2 cột "dấu hiệu thuận / dấu hiệu nghịch" trong bảng luận điểm.

**Test (new `tests/test_horoscope_evidence_labels.py`):**
1. Mapping kind: features mẫu → facts có `kind` đúng (min 3 trường hợp: toa_thu, tu_hoa, van_han).
2. Reading thiếu `loi_chung_cu` khi có fact → reject.
3. `phan_chung` rỗng → reject (phải có hoặc câu "không ghi nhận…").
4. Label không thuộc enum → reject.

**DoD:** bảng chứng cứ hiển thị được loại + phản chứng cho từng luận điểm.

### ĐỢT 2 — P1 (nền tảng an sao + tri thức cấu trúc) — ước 4–6 ngày

#### T4. Cross-check an sao `lasotuvi` ↔ bảng computation.md (repo 2)
- File mới `tests/test_lasotuvi_crosscheck.py` + fixture `tests/fixtures/an_sao_vectors.json` (~30 vector):
  - Bộ dữ liệu sinh mẫu phủ: tháng 12 × giờ Tý/Hợi, ngày chẵn/lẻ, 5 loại Cục, âm/dương nam nữ, các Can (Tứ Hóa/Khôi Việt/Lộc Tồn–Kình–Đà), các nhóm Chi (Hỏa Linh/Thiên Mã/Hồng Loan/Tiểu hạn), 6 Tuần.
  - **Kỳ vọng viết tay từ bảng computation.md (độc lập, KHÔNG import lasotuvi trong fixture)** — đó là cả ý nghĩa cross-check: hai nguồn độc lập (spec bảng vs code vendor).
  - Chạy `generate_raw_horoscope` (hoặc `lapThienBan` trực tiếp) và assert vị trí sao: Tử Vi–Thiên Phủ + 2 chòm, Tả Phụ/Hữu Bật, Văn Xương/Văn Khúc, Địa Kiếp/Địa Không, Tứ Hóa, Khôi Việt, Lộc Tồn–Kình–Đà, Hỏa Linh, Thiên Mã, Tuần/Triệt, khởi đại hạn (tuổi = số Cục + chiều theo Â/D N/N).
- **Rule ưu tiên khi mismatch:** KMS book (3 PDF qua RAG) là nguồn cao hơn; computation.md chỉ là tài liệu kiểm chứng (không license, 1 trường phái). Mismatch → mở issue, xác minh với book KMS trước khi sửa vector; KHÔNG sửa vendor trực tiếp.

#### T5. Hiệu chuẩn trường phái bảng Tứ Hóa
- Script tạm `scripts/compare_tu_hoa_tables.py`: so bảng Tứ Hóa trong lasotuvi (dò trong `Sao.py`/`ThienBan.py` khi implement) với bảng computation.md (Giáp: Liêm–Phá–Vũ–Dương; Ất: Cơ–Lương–Vi–Nguyệt…).
  - **Khớp** → docs ghi nhận: "KMS dùng bảng an Tứ Hóa theo can năm, trùng [nguồn]; ghi nhãn trường phái trong docs/data_dictionary.md".
  - **Khác** → thêm `configs/tu_hoa_tables.yaml` chứa ≥2 bảng có `school` label; `horoscope_features` đọc bảng theo config (mặc định = bảng hiện hành của vendor để không đổi hành vi); UI + prompt ghi nhãn bảng đang dùng. (Áp dụng rule "không tự hòa giải" repo 1: giữ song song, không gộp.)

**DoD (T4+T5):** ≥30 vector cross-check pass (hoặc mismatch được document + có issue); data_dictionary.md có mục "trường phái an sao KMS đang dùng".

#### T6. Hồ sơ sao (star dossier) — 14 slot theo repo 1, seed theo repo 2
**Tham khảo:** STAR_KNOWLEDGE_BASE.md §2 (schema 14 trường) + `star_meanings.md` (repo 2) làm seed.

- File mới `configs/star_seeds/` (YAML per star, chỉ ~20 sao lớn): copy ý (KHÔNG nguyên văn) từ `star_meanings.md`, mỗi slot gắn `source: "Toàn Tập (bản dịch Quách Ngọc Bội)"`, `status: seed_unverified`, và các biểu định mệnh đã bị lọc (gọi "cổ thư ghi …" hoặc bỏ). Đây là input duy nhất từ repo 2 vào KMS → phải qua T7 gate.
- Service mới `backend/app/services/star_dossier.py`:
  - Input: tên sao (normalize không dấu).
  - Nguồn A (canonical): `knowledge_items` theo `subject`/`taxonomy_code` chứa sao (dùng cùng query builder của `horoscope_rag_bridge.search_fts_sqlite`), kèm evidence (trang, book, part) → slot: bản chất, thuận, lệch, theo cung, tứ hóa, khác biệt sách (lấy `Conflict_Status`/`Author_Stances`), trích dẫn sách.
  - Nguồn B (seed): slot còn thiếu nguồn A → hiển thị từ `configs/star_seeds/` với nhãn "tham khảo, chưa đối chiếu sách KMS".
  - Slot `case_notes` (nghiệm lý) = rỗng, đặt chỗ cho T8.
  - `tin_cay` suy từ `trust_tier` của các record nguồn A (tier 1 → "đã đối chiếu NPL"…).
- API: `GET /api/stars/{ten_sao}/dossier` (FastAPI) + trang Streamlit "Hồ sơ sao".
- Rule: slot nào không có data cả A lẫn B → "chưa có trong kho tri thức hiện tại", không fill.

**Test (new `tests/test_star_dossier.py`):**
1. Sao có SPO trong db (VD: Vũ Khúc/Ngọ hoặc sao xuất hiện trong fixtures corpus) → slot + citation (book/part/page) đầy đủ.
2. Sao không có record → toàn slot "chưa có".
3. Slot seed luôn kèm nhãn `seed_unverified`; không seed bao giờ ghi đè slot có nguồn A.
4. API 404 với tên sao không hợp lệ.

#### T7. Cổng 3-yếu-tố khi thêm tri thức (quy trình + gate import)
**Tham khảo:** STAR_KNOWLEDGE_BASE §6 + CONTRIBUTING + `research_rule.yml` (repo 1).

- File mới `scripts/validate_knowledge_import.py`: kiểm tra bản ghi REPO_*.csv / import Excel:
  - Mỗi `knowledge` MỚI phải có ≥1: (a) evidence trỏ source+trang, (b) nhãn trường phái/`Author_Stances` rõ, (c) ví dụ/ca kiểm chứng.
  - Nguồn loại D (diễn đàn/video — mở cột `Source_Type=FORUM/VIDEO` trong REPO_SOURCE) → bắt buộc `Release_Status=DRAFT_NOT_RELEASED` + `Review_Flag=HYPOTHESIS_NEEDS_VALIDATION`; không được index vào RAG (tier 9).
- Tài liệu `docs/KNOWLEDGE_GATE.md`: rule 3-yếu-tố + mẫu đề xuất (template markdown kiểu `research_rule.yml`: tên quy tắc / nguồn+ấn bản / điều kiện+phản chứng / ví dụ kiểm thử) + quy tắc thêm "không ngôn ngữ định mệnh tuyệt đối".
- Nối vào `scripts/import_excel.py` (flag `--gate`) và CI `.github/workflows/test.yml` (chạy gate trên `tuvi_import/*.csv` hiện có — mong đợi pass; fixtures fail mẫu trong test).

**Test (new `tests/test_knowledge_gate.py`):** fixture csv hợp lệ pass; thiếu 3 yếu tố fail; nguồn D mà Release=LOCKED fail.

### ĐỢT 3 — P2 (nghiệm lý + vận năm + skill) — ước 3–5 ngày, chọn lọc

#### T8. Kho ca nghiệm lý khóa dự đoán
**Tham khảo:** CASE_VALIDATION_PROTOCOL.md + `validation` block của case.schema.json.

- `db/models.py`: 3 bảng —
  - `validation_cases` (case_id pattern `TV-\d{4}-\d{3}`, chart_snapshot JSON, input_confidence, created_at)
  - `predictions` (case_id, noi_dung, khoa_thoi_gian, muc_tin_cay, chung_cu_ids, locked_at; **locked → chỉ đọc; thay đổi = thêm row mới kèm `supersedes` + lý do**)
  - `events` (case_id, year, category ∈ 8 giá trị repo 1, mo_ta, prediction_result ∈ {clear_match, partial_match, no_match, not_verifiable}, revealed_at)
- Service: không sửa prediction đã locked (raise); ghi cả kết quả sai; thống kê khớp chỉ render khi ≥30 ca (giao diện "chưa đủ mẫu").
- UI: trang "Nhật ký nghiệm lý" ẩn danh.
- Phạm vi: tách biệt hoàn toàn với luồng horoscope chính (không ép user nào).

**Test:** lock/immutable, versioning, enum, gate thống kê (29 ca → ẩn, 30 ca → hiện).

#### T9. Template báo cáo vận năm (Mẫu D repo 1)
- Nâng `horoscope_annual.py` + `van_han_hien_tai`: thêm `bang_kich_hoat` (mỗi row: chủ đề, 4 tầng [lá số gốc / đại hạn / lưu niên / lưu nguyệt], phản chứng, mức tin cậy theo T2), so năm trước–sau (target_year ± 1), mục "việc chưa đủ căn cứ".
- Prompt: giữ cấu trúc Mẫu D, cấm % và tuyệt đối (theo T1–T3).
**Test:** cấu trúc response; năm biên (target_year = 1900/2100).

#### T10. Skill `tu-vi-kms` (KMS làm data source)
- Thư mục mới `skills/tu-vi-kms/`: `SKILL.md` (<500 dòng, frontmatter + trigger theo kiểu repo 2: 14 tên sao, "lập lá số khi có ngày giờ sinh", thuật ngữ), modes: ASK / STAR_DOSSIER / CROSSCHECK / ANNUAL; rule "không tự an sao — gọi API KMS"; bảng "đọc references nào khi nào" (progressive disclosure).
- `references/` = trỏ tới docs KMS (KNOWLEDGE_GATE, data_dictionary, evidence dictionary).
- Script `scripts/validate_skill.py` (đích: frontmatter, tên, link nội bộ, <500 dòng) chạy trong CI — viết lại từ repo 1 (MIT, được phép, ghi nguồn).
- License skill: MIT, ghi rõ nội dung KMS là nguồn.

#### T11. Changelog tri thức (cross-cutting, làm cùng các đợt)
- `docs/CHANGELOG_KNOWLEDGE.md`: mỗi lần đổi schema/prompt/bảng an sao → mục: phiên bản cũ → mới, dữ kiện mới, lý do, kết luận bị ảnh hưởng (rule WORKSPACE_ARCHITECTURE §"Quản lý phiên bản" repo 1).

## 3. Ma trận test (tổng) — vai QA theo AGENTS.md

| Task | File test | Số case | Loại |
|---|---|---|---|
| T1 | `test_horoscope_input_confidence.py` (mới) | 4 | schema / prompt / validation / UI |
| T2 | `test_horoscope_specificity.py` (bổ sung) | 4 | enum / retry / cấm % / bậc–chứng cứ nhất quán |
| T3 | `test_horoscope_evidence_labels.py` (mới) | 4 | mapping kind / bắt buộc / enum / UI |
| T4 | `test_lasotuvi_crosscheck.py` + fixtures (mới) | ≥30 | cross-check an sao |
| T5 | `scripts/compare_tu_hoa_tables.py` + docs | 2–4 | quyết định config |
| T6 | `test_star_dossier.py` (mới) | 4 | canonical / seed / nhãn / 404 |
| T7 | `test_knowledge_gate.py` (mới) | 3 | pass / fail / nguồn D |
| T8 | `test_validation_cases.py` (mới) | 5 | lock / version / enum / gate thống kê |
| T9 | `test_horoscope_annual.py` (bổ sung) | 3 | cấu trúc / năm biên |
| T10 | `test_skill_structure.py` (mới) | 3 | validate_skill |
| Hồi quy | `pytest tests/` toàn bộ | — | mỗi đợt phải 100% green |

**Milestone nghiệm thu:**
- Đợt 1: user thấy `muc_tin_cay` + `phan_chung` + badge input confidence trong 1 câu hỏi horoscope thật (mô phỏng LLM qua `tests/horoscope_support.py`).
- Đợt 2: `pytest tests/test_lasotuvi_crosscheck.py` green + docs ghi trường phái; trang hồ sơ sao chạy được cho ≥2 sao thật có SPO.
- Đợt 3 (nếu chọn): ca nghiệm lý đầu tiên được lock và chấm điểm.

## 4. Lệnh chạy chuẩn (cho agent implement)
```
pytest tests/test_<task>.py -v        # sau mỗi task
pytest tests/                        # hồi quy cuối đợt
python scripts/validate_knowledge_import.py tuvi_import/   # từ T7
python scripts/compare_tu_hoa_tables.py                    # từ T5
```
Cập nhật `tests/plans/ACTIVE_TEST_PLAN.md` (trạng thái PASSED) theo quy trình AGENTS.md sau mỗi task.

## 5. Rủi ro & biện pháp

| Rủi ro | Mức | Biện pháp |
|---|---|---|
| Repo 2 không license, sai/trừu tượng hóa so với book KMS | Cao | Chỉ là tài liệu kiểm chứng + seed; rule T5 "book KMS > computation.md"; không copy nguyên văn |
| Vendor lasotuvi bug không biết | Cao | T4 là gate: mismatch → issue, không sửa vendor, bọc bằng adapter nếu cần |
| Prompt dài hơn → vượt context/token LLM | Trung bình | Giữ field mới ngắn (1–2 câu rule); đo số token user prompt trước/sau (log) |
| UI Streamlit thêm field làm form dài | Thấp | Group "Độ tin cậy dữ liệu" có thể thu gọn (collapsed) |
| Seed sao tràn vào câu trả lời như kiến thức KMS | Trung bình | Tắt seed bằng config; UI luôn nhãn "tham khảo, chưa đối chiếu" |

## 6. Thứ tự & phụ thuộc
```
T1 → T2 → T3 (đợt 1, tuần tự, cùng chạm interpreter)
T4 → T5 → T6 → T7 (đợt 2; T4/T5 độc lập song song được với T1–T3 ở mức thiết kế, nhưng test an sao nên xong trước T6 vì dossier hiển thị facts sao)
T8, T9, T10, T11 (đợt 3, độc lập nhau)
```
Mỗi task commit tách biệt; đổi schema response phải atomic (backend + UI + fixture cùng commit).

## 7. Các việc KHÔNG làm
- Không sửa code trong `vendor/lasotuvi/` trực tiếp.
- Không import nguyên văn computation.md / star_meanings.md / cách cục (không license).
- Không thêm % tin cậy, không thêm khẳng định tuyệt đối vào prompt hay UI.
- Không gộp nội dung 3 sách khi hiển thị (giữ nguyên rule "3 tiếng nói").
