# KMS API

API đầy đủ: `{base}/docs` hoặc `{base}/openapi.json`. Schema nguồn:
[HoroscopeRequest/AskRequest](../../../backend/app/schemas/horoscope.py).
Dùng HTTP client có sẵn, timeout hữu hạn; không tự dựng endpoint chưa tồn tại.
Ngoài HTTP status, kiểm tra `status`/`detail` trong JSON: một số luồng cũ trả
`status=error` trong HTTP 200. Không trình bày response lỗi như bài luận thành công.

## ASK

- Lập lá số: `POST /api/v1/horoscope/read`. Body ví dụ về **định dạng**:
  `{"ngay":15,"thang":8,"nam":1995,"chi_gio":5,"gioi_tinh":1,"duong_lich":true,"input_confidence":"B","gio_sinh_source":"memory","target_year":2026,"provider":"mock"}`.
  Thay toàn bộ thông tin bằng dữ kiện người dùng đã cung cấp. Không dùng ví dụ
  làm lá số thật. `mock` trả dữ kiện, không gọi AI; `auto` có thể gọi Gemini.
- Hỏi: `POST /api/v1/horoscope/ask`, cùng input sinh và thêm `question`, `topic`.
  Topic: tong_quan, su_nghiep, tai_chinh, tinh_cam, van_han.
  Giữ `input_confidence` và bảng trường phái của luồng KMS, không tự thay bảng.
- Chi giờ: Tý=1, Sửu=2, Dần=3, Mão=4, Thìn=5, Tỵ=6, Ngọ=7, Mùi=8,
  Thân=9, Dậu=10, Tuất=11, Hợi=12. Giới tính: Nam=1, Nữ=2.
- Độ tin cậy: A giờ rõ, B sai số nhỏ, C sát ranh giới/gần đúng, D thiếu giờ
  cốt lõi. Nguồn giờ: document/memory/estimate/unknown; sai số tùy chọn
  `gio_sinh_error_phut` không âm. Nếu D chưa có chi giờ, hỏi giả thiết cần so;
  không tự gán một giờ để có kết quả.
- Giữ dấu hiệu fallback/mock của response; không gọi bản dữ kiện là luận AI.

## STAR_DOSSIER

`GET /api/v1/stars/{ten_sao_url_encoded}/dossier?include_seeds=false`.
Không cần thông tin sinh. Response có 14 slots; giữ mục `missing` là thiếu dữ
liệu. Từng entry có book_code, knowledge_id, trang và điều kiện. Dossier là
kết quả tìm kiếm có giới hạn số bản ghi, không khẳng định phủ hết mọi câu sách.
Tham khảo [hồ sơ sao](../../../docs/STAR_DOSSIER.md).

## ANNUAL

`POST /api/v1/horoscope/annual`, body sinh giống read, yêu cầu `target_year`
1900–2100. Endpoint này chỉ an sao và ghép bảng tất định, không gọi LLM hoặc
truy xuất sách. Response gồm `annual_report`, `facts`, `input_confidence`.

Giải thích theo thứ tự: bối cảnh đại hạn, ba chủ đề, bảng kích hoạt bốn tầng,
điều kiện thuận/nghịch, so năm ±1, việc chưa đủ căn cứ. Bảng là dữ kiện yếu
chờ đối chiếu, không phải cơ hội/rủi ro đã được chứng minh. Muốn phần diễn giải
có nguồn thì gọi read/ask với cùng input theo yêu cầu của người dùng.

Lưu nguyệt hiện `missing`: không tự thêm tháng. 1899/2101 trong so sánh biên
mang `out_of_range`; không tính ngoài phạm vi. Năm là năm âm lịch Can Chi.
