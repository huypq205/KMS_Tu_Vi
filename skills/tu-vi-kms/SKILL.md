---
name: tu-vi-kms
description: Tra cứu Tử Vi qua API KMS khi cần lập lá số có ngày giờ sinh, hỏi theo sách, đối chiếu nguồn hoặc vận năm; gồm Tử Vi, Thiên Cơ, Thái Dương, Vũ Khúc, Thiên Đồng, Liêm Trinh, Thiên Phủ, Thái Âm, Tham Lang, Cự Môn, Thiên Tướng, Thiên Lương, Thất Sát, Phá Quân và các thuật ngữ Mệnh–Cục, tam phương, Tứ Hóa, đại hạn. Dùng KMS làm nguồn dữ kiện và chứng cứ.
license: MIT
metadata:
  version: "1.0"
---

# Tử Vi KMS

Dùng dịch vụ KMS để lấy lá số, hồ sơ sao và nguồn sách. Không tự an sao, đổi
âm dương lịch, suy giờ sinh hoặc tính vận hạn bằng trí nhớ. Không có API thì
nêu rõ chưa có dữ kiện, dừng kết luận chuyên môn phụ thuộc dữ kiện đó.

## Chọn chế độ và tài liệu

| Chế độ | Khi dùng | Đọc khi cần |
|---|---|---|
| ASK | Hỏi một chủ đề; hoặc lập lá số rồi hỏi khi có đủ ngày giờ | [API](references/api.md#ask) |
| STAR_DOSSIER | Hỏi về ý nghĩa/điều kiện một sao | [API](references/api.md#star_dossier), [chính sách nguồn](references/knowledge.md) |
| CROSSCHECK | So quan điểm sách, bảng an sao hoặc hai giờ sinh đã cung cấp | [đối chiếu](references/crosscheck.md) |
| ANNUAL | Xem dữ kiện và giới hạn vận một năm | [API](references/api.md#annual), [báo cáo năm](../../docs/ANNUAL_REPORT.md) |

Chỉ đọc tài liệu cho chế độ đang dùng. [Chính sách tri thức](references/knowledge.md)
trỏ về tài liệu KMS hiện hành; không chứa bản sao sách. Cần dịch vụ đang chạy;
base URL mặc định `http://127.0.0.1:8000`, có thể lấy từ `KMS_API_BASE`. Nếu dịch
vụ có key, dùng `KMS_API_KEY` trong header `X-API-Key`, không in/log key.

## Dữ kiện và cách trả lời

- Thiếu ngày/tháng/năm, loại lịch, chi giờ hoặc giới tính để lập lá số thì hỏi
  đúng phần còn thiếu. Không cần tên thật. Hỏi mức chắc chắn giờ sinh A–D thay
  vì mặc định nâng dữ liệu không chắc thành A. C/D chỉ kết luận cấu trúc.
- Giữ `fact_id`, nguồn sách và trang dẫn cạnh nhận định. Giữ riêng NPL/DAU/BD;
  ghi rõ điều kiện khớp/chưa khớp, không gộp các sách thành một tiếng nói.
- Chỉ dùng bốn bậc rất mạnh/mạnh/trung bình/yếu do KMS trả. Không đổi thành phần
  trăm, không dùng số fact để tự nâng độ tin cậy hay biến bảng dữ kiện thành dự báo.
- Dẫn phản chứng khi có; không có trong nguồn lấy thì ghi đúng giới hạn đó.
  Phần nối mạch của người viết phải mang nhãn suy luận, không giả làm nghiệm lý.
- `seed_unverified` là tham khảo chưa đối chiếu, không thành nguồn canonical.
  Mặc định không bật seed; chỉ bật khi người dùng muốn lớp tham khảo này.
- Không khẳng định định mệnh, ngày chết, bệnh nặng, ly hôn hay phá sản cho người
  xem. Trích cổ thư có nội dung đó phải đặt trong ngữ cảnh nguồn hoặc bỏ.
- 401: báo cần key hợp lệ. 404 sao: kiểm tra tên; 422: sửa input. 503/network:
  báo chưa lấy được dữ kiện. Không tạo dữ liệu/citation thay cho lỗi; không lặp
  lại hàng loạt yêu cầu hoặc gọi LLM tốn phí để thay một tra cứu dữ kiện đơn giản.

Skill chỉ dùng các API đọc/tính dữ kiện trong tài liệu. Việc ghi ca nghiệm lý,
import tri thức, commit/push hoặc đăng issue phải theo yêu cầu riêng của người dùng.

Mã và hướng dẫn skill theo [MIT](LICENSE); license không cấp lại quyền cho
nội dung ba sách KMS hoặc nội dung repo tham khảo không có license.
