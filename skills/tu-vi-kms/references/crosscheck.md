# CROSSCHECK

- **Giữa sách:** gọi dossier cho sao liên quan. Trình bày theo từng NPL/DAU/BD:
  điều kiện, nhận định của nguồn, trang, điểm khác/chưa có metadata. Không tự
  đặt hai đoạn vào trạng thái mâu thuẫn khi điều kiện khác nhau hoặc còn thiếu.
- **Bảng an sao:** xem [kết quả T4](../../../docs/LASOTUVI_CROSSCHECK.md) và
  [bảng Tứ Hóa](../../../configs/tu_hoa_tables.yaml). Trong checkout KMS có thể
  chạy `python scripts/compare_tu_hoa_tables.py` từ thư mục repo để đọc 40 mục.
  Đây là script đối chiếu bảng đã có, không tự an sao và không sửa vendor.
  Ba khác biệt Tứ Hóa chưa được xác nhận bằng sách KMS; giữ nhãn hai bảng.
  Các sai khác khác theo [issue T4](../../../docs/issues/T4_AN_SAO_DISCREPANCIES.md).
- **Hai giờ sinh:** nếu người dùng cung cấp hai giả thiết, gọi read `provider=mock`
  riêng từng input. So cấu trúc thực trả về, giữ input_confidence C/D nếu không
  chắc. Không chọn giờ chỉ từ mức hợp với lời luận; cần sự kiện ẩn danh đã có.

Không ghi/import điều chỉnh thành canonical từ kết quả đối chiếu. Đề xuất sửa
phải đi qua knowledge gate và review riêng khi người dùng yêu cầu.
