# T8 — Nhật ký nghiệm lý khóa dự đoán

Mở `streamlit run app.py` → **Nhật ký nghiệm lý**. Luồng này tự nguyện và độc lập
với luồng luận lá số. Không tạo ca hay dự đoán tự động khi người dùng xem horoscope.

1. Tạo mã `TV-YYYY-NNN`. Dùng bản chụp ẩn danh từ bài đọc hiện tại hoặc mở bản
   chụp JSON đã xuất. Chỉ lưu 12 cung, tên sao, fact_id/tóm tắt và ID bảng Tứ Hóa;
   không lưu tên, ngày giờ sinh, địa chỉ hay email. Ghi chú tự nhập cũng phải ẩn danh.
2. Nhập nhận định có điều kiện, năm/khoảng năm, mức tin cậy, fact_id và phản chứng.
   Mức mạnh/rất mạnh cần ba fact_id khác nhau; C/D chỉ được cấu trúc.
3. Lưu nháp rồi khóa bằng hành động riêng. Thời điểm khóa do server ghi.
4. Chỉ sau khi khóa mới đối chiếu sự kiện. Chọn một trong `clear_match`,
   `partial_match`, `no_match`, `not_verifiable`; không bỏ kết quả sai.
5. Sửa nhận định đã khóa bằng phiên bản mới kèm `supersedes` và lý do. Không
   chấm phiên bản mới cho năm đã tiết lộ trước thời điểm khóa phiên bản đó.

## Dữ liệu và API

Ba bảng cộng thêm: `validation_cases`, `predictions`, `events`. `create_all`
tạo bảng khi mở API nhật ký lần đầu, không thay các bảng tri thức. SQLite triggers
chặn UPDATE/DELETE của prediction đã khóa, snapshot ca và kết quả đối chiếu.
Đây là dấu vết trong ứng dụng, không phải sổ chống can thiệp bởi quản trị DB.

Các endpoint dưới `/api/v1/validation` (tuân thủ X-API-Key khi được cấu hình):

| Phương thức/đường dẫn | Chức năng |
|---|---|
| POST `/cases` | tạo ca, snapshot bất biến |
| GET `/cases/{case_id}` | đọc đầy đủ các phiên bản/kết quả |
| POST `/cases/{case_id}/predictions` | tạo dự đoán nháp |
| POST `/predictions/{id}/lock` | khóa dự đoán |
| POST `/predictions/{id}/revisions` | phiên bản mới và lý do |
| POST `/cases/{case_id}/events` | lưu đối chiếu bất biến |
| GET `/statistics` | tình trạng mẫu và số lượt theo kết quả |

Schema từ chối trường ngoài danh sách, kể cả `locked_at`/`revealed_at` do client
cung cấp. Các nhóm sự kiện: career, finance, marriage, children, family, health,
relocation, other. Một prediction chỉ có một kết quả; không có endpoint xóa ca sai.
Chưa có hệ thống tài khoản riêng: sử dụng API key/quyền truy cập dịch vụ hiện hữu.

## Thống kê và review

Chỉ khi có **30 ca khác nhau đã đối chiếu** mới trả số lượt theo bốn kết quả.
29 ca hoặc 30 ca trống vẫn ẩn tổng hợp. Một ca nhiều nhận định không tăng số ca.
Không tính phần trăm hoặc coi dữ liệu tự ghi nhận là xác suất dự báo. Dấu thời gian
chỉ cho biết thứ tự ghi trong hệ thống, không chứng minh sự kiện chưa được biết ngoài hệ thống.

Review: test freeze cả bằng SQL trực tiếp, revision, cross-case, enum, server
timestamps, C/D, fact_id, kết quả sai, ngưỡng 29/30 và API/UI. Các ca test nằm trong
DB tạm; không bịa ca thật để mở khóa thống kê. Browser review 1440/768/390px không
tràn ngang/FAIL; giữ cùng hướng giao diện T6. Câu hỏi chính: nhận định nào đã khóa,
khi nào được đối chiếu và kết quả là gì? Tabs tách từng bước để giảm số trường cùng lúc.

Nguồn quy trình: [CASE_VALIDATION_PROTOCOL](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/references/CASE_VALIDATION_PROTOCOL.md),
[case.schema.json](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/assets/schemas/case.schema.json).
