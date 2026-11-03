# T9 — Bảng kích hoạt vận năm

Phần **Vận trình** của bài đọc có thêm `bang_kich_hoat`, `so_sanh_nam` và
`viec_chua_du_can_cu`. Bảng ba chủ đề (sự nghiệp/tài chính/tình cảm) giữ bốn tầng:
lá số gốc, đại hạn, lưu niên và lưu nguyệt. Mỗi tầng ghi nội dung và fact_id;
mỗi hàng có phản chứng/giới hạn, loại cấu trúc và mức tin cậy.

## Nguồn dữ kiện

KMS ghép bảng từ dữ kiện server sau khi tạo phần lời luận; LLM không được điền
tầng còn thiếu. Schema trả người dùng gồm bảng; schema gửi Gemini chỉ yêu cầu
phần lời luận để tránh tốn token lặp lại dữ kiện. `validate_reading` kiểm tra
đầy đủ hợp đồng cuối cùng. Mock có cùng cấu trúc; cache schema 5 → 6.

- Lá số gốc: sao gốc trong các cung liên quan từng chủ đề.
- Đại hạn: khoảng tuổi/cung hạn hiện tại; các fact dẫn là **sao gốc tại cung
  hạn**, không giả làm lưu tinh đại hạn.
- Lưu niên: vòng Thái Tuế và lưu Tứ Hóa theo năm và bảng Tứ Hóa đã chọn.
- Lưu nguyệt: trạng thái `missing`, không có fact_id, thông báo chưa an lưu nguyệt.
- Mức bảng hiện tại là `yeu`: bảng chỉ là dữ kiện để đối chiếu, chưa đủ điều
  kiện sách và phản chứng để nâng thành kết luận mạnh. Không đếm các tầng có
  cùng sao như các chứng cứ độc lập. Các kết luận của lời luận vẫn theo T2.
- C/D: bảng giữ cấu trúc, ghi giới hạn giờ sinh; không kết luận sự kiện/thời điểm.

So năm trước/năm xem/năm sau được tính riêng từ lá số gốc, giữ cùng bảng Tứ Hóa.
Không tính 1899/2101 khi năm xem là 1900/2100; trả `out_of_range` và để Can Chi
rỗng. Không có năm hoặc dữ kiện gốc thì trả `missing`, không tự bịa năm.
Tiểu hạn là cung theo ánh xạ vendor; không gọi sao gốc ở đó là lưu tinh.

API dữ kiện độc lập: `POST /api/v1/horoscope/annual`, body theo HoroscopeRequest.
Trả `annual_report`, `facts`, input_confidence và trạng thái chưa truy xuất sách;
không gọi LLM. Muốn bài luận có nguồn dùng `/api/v1/horoscope/read` như trước.
Năm xem ở cả read/ask/annual được giới hạn 1900–2100 khi được cung cấp.

## Review

10 test riêng bao phủ schema bốn tầng, ID bịa/sai tầng, C/D, tháng thiếu, bảng
Tứ Hóa, so năm, biên, API 422, escaping và fallback thiếu năm. Hồi quy riêng
interpreter/cache/specificity đã pass. Kiểm tra bám năm chỉ đọc phần lời luận,
không để năm trong bảng server giúp một bài chung chung vượt kiểm tra. Review
ảnh phát hiện khóa nối đại hạn dùng địa chi thay vì tên lĩnh vực; đã sửa nối
đúng `dia_chi` và thêm test tái hiện, không để tầng có dữ kiện bị báo thiếu.

Giữ cùng hướng giao diện T6: các hàng mở chi tiết thay cho bảng bảy cột trên
điện thoại. Đã xem ảnh trạng thái đóng/mở 1440/768/390px; không tràn ngang,
không FAIL/WARN từ lint/inspector. Dữ liệu preview là fixture an sao được ghi nhãn,
không phải ca người dùng thật. Câu hỏi chính: chủ đề có dữ kiện ở tầng nào và
điều gì vẫn chưa đủ căn cứ?

Nguồn cấu trúc: [OUTPUT_CONTRACT — Mẫu D](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/references/OUTPUT_CONTRACT.md).
Mẫu gốc có ba tầng; tầng lưu nguyệt được thêm theo plan KMS và luôn khai báo thiếu.
