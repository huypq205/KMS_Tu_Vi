# Changelog tri thức KMS Tử Vi

## 2026-11-03 — T5: bảng Tứ Hóa có cấu hình và nguồn riêng

- **Phiên bản trước → sau:** bảng vendor hardcode trong adapter → cấu hình
  `tu_hoa_tables.yaml` schema v1; metadata `tu_hoa_table` bổ sung vào dữ kiện.
- **Dữ kiện mới:** so đủ 40 mục/10 Can, ghi nhận 3 khác biệt: Canh Khoa/Kỵ,
  Nhâm Khoa. Hai bảng giữ riêng với nhãn nguồn; mặc định `lasotuvi`.
- **Lý do:** hỗ trợ nhiều bảng tham khảo có nguồn rõ ràng, tránh hòa trộn trường phái.
- **Phạm vi ảnh hưởng:** nếu chọn `hung_ngm_reference`, đổi vị trí hóa tinh gốc
  của năm sinh Canh/Nhâm và lưu hóa của năm xem Canh/Nhâm; cập nhật facts, prompt,
  bảng hiển thị và cache đồng bộ. Mặc định giữ vị trí an sao của vendor.
- **Nguồn:** chú thích Tứ Hóa trong `vendor/lasotuvi/App.py`; §10 `computation.md`
  của `hung-ngm/tu-vi-dau-so` tại commit `d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7`.
- **Giới hạn:** chưa xác nhận bảng nào bằng ba sách KMS; nguồn tham khảo chưa
  trở thành canonical. Các bất đồng khác của T4 vẫn theo
  [issue #1](https://github.com/huypq205/KMS_Tu_Vi/issues/1).
- **Chi tiết:** [trường phái an sao KMS đang dùng](data_dictionary.md#trường-phái-an-sao-kms-đang-dùng).
