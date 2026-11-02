# T4 — Các khác biệt an sao cần đối chiếu sách KMS

Trạng thái: OPEN — chờ đối chiếu sách KMS.
GitHub issue: [#1 — Các bất đồng an sao](https://github.com/huypq205/KMS_Tu_Vi/issues/1),
đã đăng sau khi người dùng xác nhận cho phép công bố kết quả T4.

Nguồn tham khảo: [computation.md tại commit d0238e9](https://github.com/hung-ngm/tu-vi-dau-so/blob/d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7/tu-vi-dau-so/skills/tu-vi-dau-so/references/computation.md).
Đây là tài liệu kiểm chứng, không phải nguồn canonical của KMS.

## T4-TUVI

§5 chưa cung cấp bảng ngày đầy đủ cho tất cả Cục; phần mô tả chu kỳ Thủy nhị cục
không nhất quán với bảng chi tiết. Kim tứ cục ngày 1 có hai phương án Dậu/Hợi.
Vector chọn Dậu theo phương án nêu trước, giữ nguyên nhãn bất đồng và chưa xác nhận.
Hỏa lục cục ngày 1: tài liệu ghi Dần, vendor trả Dậu.
Ví dụ âm lịch 01/01/1984, giờ Tý, nam có Hỏa lục cục và Tử Vi tại Dậu.
Vị trí các sao hai chòm và hóa tinh có thể khác theo vị trí gốc này.

Không nội suy vị trí tuyệt đối cho ngày/Cục mà tài liệu không mô tả đủ.
Những vector đó vẫn kiểm tra tương quan hai chòm, sao phụ, Cục và hạn.

## T4-KHOIVIET

§11 và vendor khác thứ tự Khôi/Việt ở các can Đinh, Mậu, Canh, Nhâm.
Cần xác minh trường phái và bảng trong sách KMS trước khi sửa kỳ vọng.

## T4-HOALINH

§13 dùng chiều thuận cho cả Hỏa và Linh theo giờ; vendor áp dụng chiều theo
âm dương năm sinh và giới tính. Giờ Tý có thể trùng vì chưa dịch khỏi cung khởi.

## T4-TUHOA

§10 khác vendor ở can Canh (Hóa Khoa/Hóa Kỵ) và can Nhâm (Hóa Khoa).
Đây là dữ liệu bàn giao T5; T4 không thay đổi bảng đang dùng.

## Kiểm tra nguồn canonical

Đã tìm read-only trong `data/processed/kms.db` qua `chunks_fts` với nhóm từ:
`an sao`, `tu vi AND thuy`, `khoi AND viet`, `hoa tinh AND linh`,
`canh AND hoa khoa`. Các hit đọc ban đầu chủ yếu là luận nghĩa, chưa đủ xác minh
bảng an sao. Ví dụ `ck-KN-000479` (NPL, trang PDF 127) nói cần kiểm tra dữ kiện và
vị trí sao; đó không phải bảng quyết định các bất đồng trên. Chưa xác nhận bằng PDF gốc.

## Điều kiện giải quyết

- Ghi đúng sách, phần và trang của bằng chứng cho từng khác biệt.
- Giữ riêng các trường phái nếu có bất đồng.
- Không sửa trực tiếp `vendor/lasotuvi/` và không sửa kỳ vọng chỉ để test xanh.
- Cập nhật fixture và bản ghi quan sát khi có quyết định được chứng minh.
- Chuyển xử lý bảng Tứ Hóa sang T5.

Các giá trị tham khảo và quan sát cụ thể cho từng vector nằm trong
`tests/fixtures/an_sao_vectors.json`. `discrepancies` chỉ là quan sát hành vi hiện tại,
không được dùng làm kỳ vọng từ nguồn tham khảo.
