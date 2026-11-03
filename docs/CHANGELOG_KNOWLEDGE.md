# Changelog tri thức KMS Tử Vi

## 2026-11-03 — T9: báo cáo năm bốn tầng, cache v6

- Trước → sau: vận trình chỉ có bốn đoạn lời → thêm bảng ba chủ đề với lá số
  gốc/đại hạn/lưu niên/lưu nguyệt, phản chứng và mức tin cậy; so năm ±1 và mục
  chưa đủ căn cứ. Dữ kiện được ghép phía server, không lấy bảng do LLM bịa.
- Lưu nguyệt luôn thiếu; bảng giữ mức yếu/chỉ cấu trúc. So năm giữ bảng Tứ Hóa
  đã chọn, không an 1899/2101; request năm ngoài 1900–2100 bị từ chối.
- Cache schema 5 → 6; mock, schema, prompt, validator và UI đồng bộ. Không nhập
  tri thức mới. Năm trong bảng không thay được yêu cầu lời luận bám năm xem.
- Review sửa fallback thiếu năm và nối đại hạn bằng địa chi; thêm test tái hiện.
  10 test T9 passed; hồi quy phạm vi đến T9: 2121 passed / 351 known T4 xfailed.
- Chi tiết, nguồn Mẫu D và giới hạn: [ANNUAL_REPORT.md](ANNUAL_REPORT.md).

## 2026-11-03 — T8: nghiệm lý có khóa và lịch sử bất biến

- Trước → sau: chưa có kho nghiệm lý → ba bảng bổ sung, API và trang nhật ký
  ẩn danh độc lập. Snapshot, dự đoán đã khóa và kết quả được bảo vệ bằng trigger.
- Thay đổi nhận định tạo row mới kèm lý do; giữ kết quả sai, ngăn đối chiếu
  phiên bản khóa sau khi đã biết sự kiện cùng ca/năm. Không đổi dữ liệu an sao.
- Đầu vào C/D không được lách nhãn cấu trúc để ghi khẳng định thời điểm.
- Thống kê số lượt chỉ mở từ 30 ca đã đối chiếu, không dùng phần trăm.
  Không tạo ca thật giả để đạt ngưỡng. API/UI kế thừa bảo vệ key hiện hữu.
- Review 11 test riêng và ảnh ba kích thước; hồi quy 2111 passed / 351 known
  T4 xfailed. Nguồn và giới hạn: [CASE_VALIDATION.md](CASE_VALIDATION.md).

## 2026-11-03 — T6: hồ sơ sao có nguồn và seed tách biệt

- Trước → sau: chỉ tra cứu qua bài luận → API và UI hồ sơ 14 nhóm, giữ riêng
  NPL/DAU/BD với knowledge_id và trang dẫn. Mục thiếu được công khai.
- 20 YAML diễn giải ý từ repo 2, luôn seed_unverified, qua T7 gate, chỉ lấp nhóm
  thiếu và chỉ xuất hiện khi người dùng bật. Không nhập seed vào canonical/RAG.
- Ảnh hưởng: thêm luồng đọc độc lập, không thay bài luận hay bảng an sao.
- Review API, ưu tiên nguồn, nhãn, lỗi và UI ba kích thước; 8 test riêng passed,
  hồi quy 2100 passed / 351 known T4 xfailed. Xem STAR_DOSSIER.md.

## 2026-11-03 — T7 review trên workbook thật

- Xác định workbook trong thư mục Final; CSV cùng tên chỉ chứa chỉ số tổng hợp,
  không phải bộ REPO exports. Gate kiểm tra 10456 bản ghi như mới: không lỗi.
- Đối chiếu DB baseline: 10456 checked, 0 new, 0 errors; đủ ba sách hiện hành.
  Không import/build lại DB; không đưa workbook lên Git.

## 2026-11-03 — T2 review: số fact độc lập theo ID

- Trước → sau: đếm độ dài danh sách (có thể lặp ID) → đếm fact_id khác nhau.
- Mức mạnh cần >=3 fact theo plan T2; rất mạnh >=3, trung bình >=1, yếu >=0.
  Cache schema 4 → 5 để không trả lại bài theo ngưỡng cũ.
- Review có test tái hiện lặp ID và hai fact cho mức mạnh; hồi quy 2092 passed,
  351 known T4 xfailed. Các bậc không phải tỷ lệ xác suất nghiệm lý.

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
