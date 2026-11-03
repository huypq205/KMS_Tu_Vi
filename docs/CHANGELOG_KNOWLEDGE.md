# Changelog tri thức KMS Tử Vi

## 2026-11-03 — T1 review: giới hạn C/D được chặn sau retry

- Trước → sau: retry vẫn có thể trả kết luận thời điểm với specificity_low →
  từ chối bài không tuân thủ C/D, dùng fallback có giới hạn hoặc lỗi rõ ràng.
- Bổ sung `loai_ket_luan` (cau_truc/thoi_diem) cho luận điểm/kết luận, schema,
  mock, fixture và UI cùng đợt; C/D chỉ được cấu trúc. Cache schema 3 → 4.
- Review/test tái hiện trước sửa; hồi quy: 2091 passed, 351 known T4 xfailed.

## 2026-11-03 — T3: merge và review loại chứng cứ

- Trước → sau: facts chưa có loại → từ điển 10 loại, `kind`, luận điểm có
  `loi_chung_cu` và `phan_chung`; UI hiển thị dấu hiệu thuận/nghịch.
- Merge nhánh `feature/t3-evidence-labels` (aaa0951) cùng T7 trên main.
- Review sửa việc nhận thêm nhãn nghiệm lý không có trong fact dẫn và chuẩn hóa
  Tị/Tỵ khi xác định giáp cung. Suy luận có nhãn riêng, không giả làm nghiệm lý.
- Kết luận bị ảnh hưởng: luận điểm của mọi bài đọc mới; cache schema được nâng
  bởi T3 để bài cũ thiếu trường tự miss. Không nhập tri thức canonical mới.
- Kiểm chứng sau review: 2089 passed, 351 known T4 xfailed (62.37s).

## 2026-11-03 — T7: cổng import tri thức v1.0

- **Trước → sau:** import canonical chưa có gate → validator CSV/Excel độc lập
  và `import_excel.py --gate`, kiểm tra >=1 yếu tố nguồn+trang / trường phái /
  ví dụ kiểm chứng cho ID mới. Thêm mapping `Source_Type`, `School`, `Validation_Example`.
- **Lý do:** chặn bản ghi thiếu căn cứ và tách giả thuyết diễn đàn/video khỏi RAG.
- **Quy tắc nguồn D:** bắt buộc nháp + `HYPOTHESIS_NEEDS_VALIDATION`, tier 9;
  có hiệu lực cả khi không bật `--gate`. Chunker loại giả thuyết dù bị gán nhầm
  tier hoặc bật nhầm tier 9 trong cấu hình.
- **Phạm vi ảnh hưởng:** nguồn FORUM/VIDEO dùng Book_Code NPL/BD/DAU không còn
  nhận tier của sách; import sai bị từ chối trước khi thay dữ liệu. Bản ghi đủ
  căn cứ B/C có thể lưu khi chưa có trang PDF, chưa tự động đủ điều kiện index.
  Registry nguồn D không ghi đè tên và định danh của sách đã có khi dùng chung mã.
- **Canonical:** không thêm tri thức thật, không đổi nội dung ba sách, không migrate
  DB production; bổ sung metadata và quy trình duyệt.
- **Nguồn/quy trình:** repo `duandigi/tu-vi-dau-so-research` MIT tại commit
  `91f8a06f1bca2fb271791785937265ea78d7f858`; triển khai ngưỡng >=1 theo plan T7.
- **Chi tiết và giới hạn:** [KNOWLEDGE_GATE.md](KNOWLEDGE_GATE.md).

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
