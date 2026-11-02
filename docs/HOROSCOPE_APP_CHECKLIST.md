# CHECKLIST XÂY DỰNG DỰ ÁN BÓI TOÁN TỬ VI CHO NGƯỜI MỚI (AI HOROSCOPE)

> Cập nhật sau phản hồi giảng viên 31/10/2026: xem [bản sửa dữ liệu, truy xuất, tiểu hạn và vận hành AI](HOROSCOPE_FEEDBACK_FIXES.md). Những mục hoàn thành bên dưới phản ánh các giai đoạn ban đầu; nghiệm thu chất lượng chuyên môn/AI thật vẫn cần thực hiện riêng.

> **Mục tiêu dự án:** Xây dựng ứng dụng Tử Vi thông minh cho người hoàn toàn không có kiến thức chuyên môn, tự động an sao từ ngày giờ sinh, kết hợp tri thức từ 3 cuốn sách kinh điển (NPL, BD, DAU) và AI (Gemini) để đưa ra bài luận giải sâu sắc, tích cực, dễ hiểu theo ngôn ngữ đời thường.
>
> **Quy ước trạng thái:**
> - [x] **ĐÃ HOÀN THÀNH** (Kế thừa từ nền tảng KMS hiện có)
> - [ ] **CHƯA HOÀN THÀNH** (Cần thực hiện tuần tự theo các bước bên dưới)

---

## 📊 BẢNG TIẾN ĐỘ TỔNG QUAN

| Giai đoạn | Nội dung trọng tâm | Trạng thái |
| :--- | :--- | :---: |
| **Giai đoạn 0** | Nền tảng dữ liệu & Thuật toán an sao lõi | **100% ĐÃ XONG** |
| **Giai đoạn 1** | Module bóc tách cấu trúc lá số đa chiều (Feature Extractor) | **100% ĐÃ XONG** |
| **Giai đoạn 2** | Bridge kết nối Lá số ↔ Kho tri thức sách (Smart RAG Bridge) | **100% ĐÃ XONG** |
| **Giai đoạn 3** | Kỹ thuật Prompt luận giải & Phiên dịch ngôn ngữ bình dân (LLM) | **100% ĐÃ XONG** |
| **Giai đoạn 4** | Xây dựng API Service & Endpoint luận giải cá nhân | **100% ĐÃ XONG** |
| **Giai đoạn 5** | Thiết kế Giao diện người dùng thân thiện (Layman UI/UX) | **100% ĐÃ XONG** |
| **Giai đoạn 6** | Kiểm thử luồng, Tối ưu hóa & An toàn nội dung (Safety) | **0% CHƯA LÀM** |

---

## 🛠 DANH MỤC CÔNG VIỆC CHI TIẾT (THỰC HIỆN TUẦN TỰ)

### GIAI ĐOẠN 0: NỀN TẢNG DỮ LIỆU & ENGINE AN SAO (ĐÃ CÓ SẴN)
> Giai đoạn này đã được xây dựng hoàn tất trong codebase hiện tại, bạn không cần làm lại.

- [x] **0.1. Tích hợp Engine An sao 108 sao Tử Vi chuẩn xác**
  - Thư viện `vendor/lasotuvi/`: Hỗ trợ đầy đủ thuật toán Can Chi, Lịch thiên văn Ephemeris (`Lich_EPHEM.py`, `Lich_HND.py`).
  - Đã tính chuẩn: Cung Mệnh/Thân, Cục, Tứ Hóa, Tuần, Triệt, Đại hạn, Tiểu hạn.
- [x] **0.2. Thu thập & Cấu trúc hóa kho dữ liệu 3 cuốn sách Tử Vi kinh điển**
  - Đã hoàn tất 10.456 bản ghi làm sạch từ: Nguyễn Phát Lộc (NPL), Bửu Đình (BD), Đẩu Số Toàn Thư (DAU).
  - Đã đóng gói thành SQLite DB (`data/processed/kms.db`) và file JSONL (`data/processed/TuVi_KMS_3Books_RAG_CHUNKS_v1.0.jsonl`).
- [x] **0.3. Hạ tầng tìm kiếm FTS5 tiếng Việt không dấu**
  - Đã xây dựng `backend/app/services/fts.py` hỗ trợ tìm kiếm siêu tốc, chịu lỗi gõ dấu tiếng Việt.
- [x] **0.4. Khung giao diện nguyên mẫu (Prototype)**
  - Giao diện `frontend/lasoban.py` hiển thị lưới 12 cung truyền thống.
  - Phân tích sơ cấp `frontend/phan_tich.py` liệt kê ý nghĩa cơ bản của từng chính tinh.
- [x] **0.5. Cầu nối gọi mô hình ngôn ngữ lớn (LLM Adapter)**
  - Đã có `backend/app/services/llm_provider.py` hỗ trợ Gemini API và Mock LLM offline.

---

### GIAI ĐOẠN 1: BÓC TÁCH CẤU TRÚC LÁ SỐ ĐA CHIỀU (FEATURE EXTRACTOR)
> **Mục tiêu:** Chuyển dữ liệu vị trí các sao rời rạc thành các cụm thông tin có ý nghĩa luận đoán.

- [x] **1.1. Chuẩn hóa module trích xuất đặc trưng lá số (`backend/app/services/horoscope_features.py`)**
  - [x] Viết hàm tính tương quan Bản Mệnh vs Cục (Ngũ hành sinh/khắc: Mệnh sinh Cục, Cục sinh Mệnh, Mệnh Cục tị hòa, Mệnh khắc Cục, Cục khắc Mệnh).
  - [x] Viết hàm trích xuất bộ ba **Tam phương tứ chính** của Mệnh: Mệnh + Tài Bạch + Quan Lộc + Thiên Di (chiếu Mệnh).
  - [x] Viết hàm nhận diện các bộ chính tinh cốt lõi (Tử Phủ Vũ Tướng, Sát Phá Tham, Cơ Nguyệt Đồng Lương, Cự Nhật, hoặc Mệnh Vô Chính Diệu).
  - [x] Viết hàm phân tích vị trí Đắc - Miếu - Hãm của chính tinh và sự hội tụ của Cát tinh (Xương Khúc, Khôi Việt, Tả Hữu,...) / Sát tinh (Kình Đà, Hỏa Linh, Không Kiếp).
  - [x] Viết hàm xác định vị trí 4 hóa tinh (Hóa Lộc, Hóa Quyền, Hóa Khoa, Hóa Kỵ) đóng tại cung nào kèm lời giải thích layman.
  - [x] Viết hàm xác định Đại hạn 10 năm hiện tại theo tuổi dương/âm lịch và can chi năm xem.

---

### GIAI ĐOẠN 2: SMART RAG BRIDGE (LÁ SỐ ↔ KHO TRI THỨC SÁCH)
> **Mục tiêu:** Tự động sinh query tìm đúng đoạn sách giải thích các cách cục trên lá số để AI có dẫn chứng chính xác.

- [x] **2.1. Viết bộ sinh câu hỏi truy vấn tự động (`backend/app/services/horoscope_rag_bridge.py`)**
  - [x] Sinh query cho Cung Mệnh/Thân: ví dụ "Thất Sát", "Sát Phá Tham", "Mệnh Vô Chính Diệu".
  - [x] Sinh query cho Cung Sự Nghiệp / Quan Lộc: kết hợp chính tinh tại Quan Lộc và Hóa Quyền/Khoa.
  - [x] Sinh query cho Cung Tài Chính / Tài Bạch: kết hợp chính tinh tại Tài Bạch và Hóa Lộc/Lộc Tồn.
  - [x] Sinh query cho Cung Tình Duyên / Phu Thê: kết hợp chính tinh và cát/sát tinh tại Phu Thê.
  - [x] Sinh query cho Vận Hạn: tìm kiếm đại hạn 10 năm theo độ tuổi hiện tại.
- [x] **2.2. Tích hợp truy vấn FTS5 trực tiếp theo nhóm chủ đề**
  - [x] Chạy tìm kiếm FTS5 tốc độ cao trực tiếp trên SQLite (`kms.db`), chuẩn hóa bỏ dấu tiếng Việt NFD/NFC.
  - [x] Gom nhóm ngữ cảnh tri thức theo 5 chủ đề, đánh số trích dẫn [1], [2]... sẵn sàng nạp cho LLM Prompt.

---

### GIAI ĐOẠN 3: PROMPT ENGINEERING & BỘ LUẬN GIẢI CHO NGƯỜI MỚI (AI TRANSLATOR)
> **Mục tiêu:** AI đóng vai trò người phiên dịch tâm lý - chuyển cổ ngữ Tử Vi thành lời khuyên cuộc sống hiện đại.

- [x] **3.1. Soạn thảo System Prompt chuyên biệt cho Luận giải Tử Vi Hiện đại**
  - [x] Thiết lập giọng văn: Thông thái, ấm áp, khách quan, mang tính khai vấn/định hướng (Life coaching), không mê tín dị đoan.
  - [x] Quy tắc chuyển ngữ thuật ngữ chuyên môn:
    * Ví dụ: Không nói cụt lủn *"Cự Môn hãm địa"* → Phải giải thích *"Bạn là người rất sắc sảo trong lời nói và tư duy phản biện, tuy nhiên cần chú ý cách biểu đạt để tránh hiểu lầm trong giao tiếp."*
    * Ví dụ: Không nói *"Gặp Triệt là hỏng"* → Phải giải thích *"Giai đoạn tiền vận (trước 30 tuổi) bạn sẽ trải qua nhiều thử thách trui rèn, sau đó mới bắt đầu gặt hái ổn định."*
  - [x] Quy tắc đạo đức nghiêm ngặt: Tuyệt đối không phán định tai nạn chết người, bệnh hiểm nghèo, ly tán không thể cứu vãn; luôn kèm lời khuyên giải pháp (Xu cát tị hung).
- [x] **3.2. Thiết kế cấu trúc đầu ra JSON chuẩn cho bài luận giải (`HoroscopeReadingResponse`)**
  - [x] `tong_quan`: Điểm mạnh bẩm sinh, điểm mù tính cách, năng lượng cốt lõi.
  - [x] `su_nghiep`: Môi trường làm việc lý tưởng, phong cách lãnh đạo/thực thi, nghề nghiệp tương hợp.
  - [x] `tai_chinh`: Cách kiếm tiền, tư duy tài chính, rủi ro tiền bạc cần phòng tránh.
  - [x] `tinh_cam`: Xu hướng trong tình yêu, đặc điểm người bạn đời phù hợp, bí quyết giữ gìn gia đạo.
  - [x] `van_han_hien_tai`: Trọng tâm đại hạn đang trải qua, cơ hội nên nắm bắt, thách thức cần cẩn trọng.
  - [x] `loi_khuyen_hanh_dong`: 3 việc cụ thể nên làm ngay để cải thiện năng lượng bản thân.
  - [x] Cung cấp bộ sinh mock luận giải thông minh deterministic fallback khi không có API key hoặc chạy offline.

---

### GIAI ĐOẠN 4: XÂY DỰNG API SERVICE TẠI BACKEND
> **Mục tiêu:** Tạo API hoàn chỉnh phục vụ frontend gọi dữ liệu.

- [x] **4.1. Cấu hình phân tách Scope cho API**
  - [x] Giữ nguyên `/chat/ask` cho tra cứu học thuật thuần túy (KMS).
  - [x] Mở endpoint mới: `POST /api/v1/horoscope/read` dành riêng cho bói toán & luận giải cá nhân.
- [x] **4.2. Xây dựng Request Schema (`HoroscopeRequest`)**
  - [x] Nhận: Họ tên, Ngày/Tháng/Năm, Chi giờ sinh (12 khung giờ kèm tên cung + giờ thực tế), Giới tính, Loại lịch (Dương/Âm), top_k, provider (auto/mock/gemini), target_year.
  - [x] T1: nhận `input_confidence` (A–D), `gio_sinh_source` (document/memory/estimate/unknown), `gio_sinh_error_phut` (≥0); default A/memory/None để tương thích client cũ.
  - [x] T2: response `luan_diem`/`ket_luan` có `muc_tin_cay` (rat_manh/manh/trung_binh/yeu); cấm phần trăm tin cậy.
  - [x] Schema: `backend/app/schemas/horoscope.py` — `HoroscopeRequest` (Pydantic v2, validation đầy đủ ge/le), `HoroscopeResponse`.
- [x] **4.3. Pipeline xử lý trọn gói tại Controller**
  - [x] Nhận request → Gọi `generate_raw_horoscope` → `extract_horoscope_features` → `retrieve_horoscope_context` → `interpret_horoscope` → Trả JSON có cấu trúc.
  - [x] Endpoint: `POST /api/v1/horoscope/read` trong `backend/app/main.py`.
  - [x] 10 test cases PASS: `tests/test_horoscope_api.py` (Schema validation + Direct endpoint calls).

---

### GIAI ĐOẠN 5: XÂY DỰNG GIAO DIỆN NGƯỜI MỚI (LAYMAN FRONTEND)
> **Mục tiêu:** Giao diện trực quan, đẹp mắt, người không biết gì cũng đọc và hiểu ngay lập tức.

- [x] **5.1. Tạo trang web luận giải riêng biệt (`frontend/horoscope_ui.py`)**
- [x] **5.2. Thiết kế Form nhập liệu thân thiện**
  - [x] Lựa chọn khung giờ trực quan (kèm gợi ý đồng hồ thực tế: *Tý: 23:00 - 01:00*).
  - [x] Nút chuyển nhanh Dương lịch ↔ Âm lịch (chọn loại lịch nhập; không tự quy đổi ngày).
  - [x] Thẻ chọn chủ đề ưu tiên đọc ngoài phần tổng quan; thay đổi thứ tự báo cáo, không tạo câu hỏi tự do mới.
- [x] **5.3. Thiết kế Báo cáo Kết quả dạng Thẻ Trực Quan (Card Layout)**
  - [x] **Thẻ Header:** Tên, Bản mệnh (Ngũ hành nạp âm kèm dấu màu), Thân cư cung nào, Cục số.
  - [x] **Thẻ Điểm Mạnh & Tính Cách:** Bullet point ngắn gọn từ kết quả API.
  - [x] **Thẻ Công Danh - Sự Nghiệp:** Khuyến nghị công việc, cách làm việc hiệu quả.
  - [x] **Thẻ Tài Chính & Tiền Bạc:** Nội dung từ phần tài chính của API.
  - [x] **Thẻ Tình Duyên & Hạnh Phúc:** Nội dung từ phần tình cảm của API.
  - [x] **Thẻ Vận Trình Hiện Tại:** Giai đoạn và trọng tâm từ API.
- [x] **5.4. Chế độ Chuyển đổi Nâng cao (Toggle Switch)**
  - [x] *"Xem lá số chi tiết 12 cung"*: Tách renderer dùng chung `frontend/laso_renderer.py` từ `lasoban.py`; lưới desktop, danh sách trên điện thoại.
  - [x] *"Xem trích dẫn sách gốc"*: Đúng đoạn 500 ký tự dùng trong prompt, kèm sách/chương/phần/trang thật và nhãn chưa duyệt.

**Nghiệm thu giai đoạn 5:** Taste Skill Framed sheet; font IBM Plex Sans offline.
`pytest tests/`: **70 passed, 1 skipped** (smoke Gemini thật opt-in).
Kiểm tra trình duyệt ở **1440/768/390 px**: không tràn ngang, không lỗi JavaScript;
mock E2E mở đủ 12 cung và 10 nguồn. Giao diện phân biệt AI với mock/fallback.
Xem `docs/RUN_HOROSCOPE.md` và `docs/HOROSCOPE_UI_DESIGN.md`.
Giai đoạn 6 vẫn chưa nghiệm thu.

---

### GIAI ĐOẠN 6: KIỂM THỬ, ĐẠO ĐỨC & KHÓA SẢN PHẨM (SAFETY & LAUNCH)
> **Mục tiêu:** Đảm bảo hệ thống chạy mượt mà, không crash và an toàn về mặt đạo đức/pháp lý.

- [ ] **6.1. Kiểm thử tính toán an sao biên**
  - [ ] Viết test `tests/test_horoscope_edge_cases.py`: Giờ giao ngày (23:00 - 00:00), năm nhuận âm lịch, tháng thiếu.
- [ ] **6.2. Kiểm thử nội dung luận giải (Quality & Safety Testing)**
  - [ ] Thử nghiệm với 10 lá số thuộc các nhóm tính cách khác nhau (Mệnh Vô Chính Diệu, Mệnh Sát Tinh hội tụ, Mệnh Cát Tinh).
  - [ ] Đảm bảo 100% kết quả không có ngôn từ mang tính tiêu cực cực đoan, hoang mang sợ hãi.
- [ ] **6.3. Bổ sung Tuyên bố Miễn trừ Trách nhiệm (Legal Disclaimer)**
  - [ ] Đặt banner rõ ràng ở cuối bài luận: *"Tử Vi là hệ thống văn hóa chiêm tinh truyền thống mang tính chất tham khảo, giúp thấu hiểu bản thân và chiêm nghiệm. Luận giải không mang tính quyết định số phận tuyệt đối và không thay thế các tư vấn y khoa, pháp lý hay tài chính chuyên nghiệp."*
- [ ] **6.4. Đóng gói hướng dẫn khởi chạy nhanh**
  - [ ] Viết file `RUN_HOROSCOPE.md` hướng dẫn chạy 1 lệnh để bật web service cho người dùng trải nghiệm.

---

## 📌 THỨ TỰ BƯỚC THỰC HIỆN TIẾP THEO:

- [x] **Bước 1 (Task 1.1):** ĐÃ HOÀN THÀNH — Module `backend/app/services/horoscope_features.py` đã bóc tách đầy đủ Mệnh-Cục, Tam phương tứ chính, Sát Phá Tham / Cự Nhật / Vô Chính Diệu, Tứ Hóa, Đại hạn (7/7 tests passed).
- [x] **Bước 2 (Giai đoạn 2):** ĐÃ HOÀN THÀNH — Module `backend/app/services/horoscope_rag_bridge.py` tự động sinh query 5 chủ đề và truy vấn FTS5 trực tiếp trong `kms.db` (4/4 tests passed).
- [x] **Bước 3 (Giai đoạn 3):** ĐÃ HOÀN THÀNH — Module `backend/app/services/horoscope_interpreter.py` cung cấp Prompt chuẩn Life Coaching, schema JSON luận giải đầy đủ 6 phần, tích hợp Gemini và mock offline generator (5/5 tests passed).
- [x] **Bước 4 (Giai đoạn 4):** ĐÃ HOÀN THÀNH — Endpoint `POST /api/v1/horoscope/read` trong `backend/app/main.py`, schema Pydantic `backend/app/schemas/horoscope.py`, pipeline đầy đủ an sao→RAG→AI. Cài FastAPI 0.162.0 + uvicorn 0.54 + pydantic 2.14 + sqlalchemy 2.1 trong `.venv`. **10/10 tests PASS** (`tests/test_horoscope_api.py`).
- [x] **Bước 5 (Giai đoạn 5):** Hoàn thành **5.1–5.4** — Streamlit UI, form, báo cáo, 12 cung và nguồn sách. Xem `docs/RUN_HOROSCOPE.md`.

