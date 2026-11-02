# T4 — Kiểm tra chéo an sao

Ngày thực hiện: 2026-11-03. Phạm vi: T4 của kế hoạch governance.

## Nguồn và giới hạn

Nguồn tham khảo là [computation.md](https://github.com/hung-ngm/tu-vi-dau-so/blob/d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7/tu-vi-dau-so/skills/tu-vi-dau-so/references/computation.md),
commit `d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7`, blob
`28ffd19e28919c5a2b3eb98d146326bb22f07985`. Không tải nguồn khi chạy test.
Không nhập nội dung tham khảo vào RAG hoặc kho canonical.

Fixture `tests/fixtures/an_sao_vectors.json` chứa các kỳ vọng tĩnh. Các mốc tra tay
từ nguồn được triển khai bằng phép đếm cung để ghi ra JSON; quá trình tạo
`expected` không import vendor hoặc dùng output của vendor. `discrepancies.observed`
được ghi riêng sau lần kiểm tra thất bại đầu tiên, chỉ cho các nhóm đã xác định.
Không có logic tái tạo kỳ vọng hoặc tự chấp nhận sai khác khi chạy test.

Các mốc kiểm tra vị trí Tử Vi ngày 1: Thủy → Sửu; Mộc → Thìn; Kim → Dậu
(nguồn còn ghi phương án Hợi); Thổ → Ngọ; Hỏa → Dần. Kim và Hỏa có nhãn
bất đồng rõ ràng. Với Thủy, bổ sung ngày 2 và ngày 4 theo bảng chi tiết §5,
giữ nguyên bất đồng ngày 4. Không tự sửa bảng tham khảo theo kết quả vendor.

Sáu vector ngày 2/Hỏa không có kỳ vọng tuyệt đối cho các chính tinh vì §5 không
cung cấp đủ dữ liệu. Chúng vẫn kiểm tra tương quan hai chòm và các sao phụ/hạn.
Hạn chế này được lưu bằng `absolute_principal_reference=not_specified_by_reference`.

Tất cả đầu vào là âm lịch, múi giờ KMS hiện hành UTC+7, để kiểm tra an sao độc lập
với chuyển đổi lịch. Bộ này không xác minh lịch nhuận, đổi ngày tại 23 giờ hoặc
độ chính xác chuyển đổi dương/âm; không coi các phần đó đã được kiểm thử ở T4.

## Độ phủ

44 vector gồm:

- 24 tổ hợp: mỗi tháng 1–12 × giờ Tý/Hợi.
- 12 năm 1984–1995: đủ 10 Can và 12 Chi.
- 6 mốc Giáp cách nhau 10 năm: đủ 6 Tuần; dùng tháng 12, giờ Hợi, ngày chẵn.
- 2 vector Thủy nhị cục ngày 2/4 để kiểm tra bảng ngày chẵn.

Bộ kiểm tra phủ 5 Cục, âm/dương nam/nữ, hai chòm 14 chính tinh, Tả/Hữu,
Xương/Khúc, Không/Kiếp, Tứ Hóa, Khôi/Việt, Lộc/Kình/Đà, Hỏa/Linh, Thiên Mã,
Hồng Loan/Thiên Hỉ, Tuần/Triệt, Mệnh/Thân, khởi tuổi và chiều đại hạn,
cùng 12 cung tiểu hạn liên tiếp tính từ năm sinh.

Có 1.784 phép đối chiếu trường dữ liệu; 12/44 vector khớp toàn bộ các kỳ vọng
được nêu. Con số này chỉ mô tả kết quả kiểm tra tài liệu, không phải mức tin cậy
hay độ chính xác của luận đoán Tử Vi.

## Sai khác đã ghi nhận

| Nhóm | Số trường khác | Số vector liên quan | Nội dung |
|---|---:|---:|---|
| T4-TUVI | 322 | 18 | Mốc Tử Vi và sai khác lan theo hai chòm/hóa tinh; §5 có mâu thuẫn hoặc phương án chưa rõ |
| T4-KHOIVIET | 8 | 4 | Thứ tự Khôi/Việt của Đinh, Mậu, Canh, Nhâm |
| T4-HOALINH | 18 | 18 | Chiều đếm giờ trong §13 so với quy tắc âm dương/giới tính của vendor |
| T4-TUHOA | 3 | 2 | Can Canh: Khoa/Kỵ; can Nhâm: Khoa; bàn giao T5 |

Tổng 351 trường khác, không tương đương 351 lỗi độc lập.
Ví dụ:

- `month-01-hour-01`: Tử Vi nguồn Dần, quan sát Dậu (Hỏa lục cục, ngày 1).
- `water-day-04`: Tử Vi nguồn Thìn, quan sát Mão.
- `year-1987`: Khôi nguồn Hợi, quan sát Dậu; Việt nguồn Dậu, quan sát Hợi.
- `year-1990`: Hóa Khoa nguồn Hợi, quan sát Sửu; Hóa Kỵ nguồn Sửu, quan sát Hợi.
- `year-1992`: Hóa Khoa theo Tả Phụ ở Thìn trong nguồn; vendor theo Thiên Phủ ở Tị.

Chi tiết từng phép so sánh, giá trị nguồn và quan sát được lưu trong fixture.
Hồ sơ xử lý: [T4_AN_SAO_DISCREPANCIES.md](issues/T4_AN_SAO_DISCREPANCIES.md).
Đã đăng [GitHub issue #1](https://github.com/huypq205/KMS_Tu_Vi/issues/1)
sau khi người dùng xác nhận cho phép công bố kết quả T4.

Đã tìm trong kho SQLite nhưng chưa có bảng/trang đủ bằng chứng để phân xử.
KMS book vẫn có ưu tiên cao hơn repo tham khảo; chưa kết luận vendor sai.
Không thay đổi code vendor, backend, UI hoặc bảng Tứ Hóa trong T4.

## Cách đọc kết quả test

```powershell
.venv\Scripts\python.exe -m pytest tests/test_lasotuvi_crosscheck.py -v
.venv\Scripts\python.exe -m pytest tests/ -q
```

- Đối chiếu khớp nguồn: `PASSED`.
- Bất đồng đã ghi hồ sơ: `XFAIL` với `strict=True`, không bỏ qua cả vector.
- Mỗi bất đồng có một test riêng yêu cầu quan sát hiện tại giữ đúng bản ghi.
  Nếu xuất hiện một vị trí khác mới, test này thất bại dù test đối chiếu còn XFAIL.
- Nếu code bắt đầu khớp nguồn, strict XPASS buộc review và xóa/cập nhật nhãn bất đồng.
- Kiểm tra độ phủ, sự xuất hiện duy nhất của 14 chính tinh và tương quan hai chòm
  luôn chạy bình thường; không đánh dấu xfail các kiểm tra này.

Kết quả T4: **1.873 passed, 351 xfailed**, không có failure hay skip.
Hồi quy toàn bộ: **2.004 passed, 351 xfailed trong 83,31 giây**.
Trong 1.873 test pass có 351 test bảo vệ quan sát đã ghi; không diễn giải tất cả
1.873 test pass thành 1.873 bằng chứng khớp độc lập với tài liệu tham khảo.

Trạng thái nghiệm thu T4: **PASSED với bất đồng đã document và có issue**, theo
nhánh nghiệm thu cho phép trong plan. Issue vẫn OPEN để đối chiếu các bất đồng
với sách KMS. Phần hiệu chuẩn trường phái Tứ Hóa thuộc T5.
