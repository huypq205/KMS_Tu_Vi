# Nghiệm thu T1–T11 — 2026-11-03

Đã triển khai và review đủ 11 task theo plan. Mỗi task mới hoặc bản sửa sau review
được commit/push riêng vào `origin/main`; giữ nguyên công việc T1/T2 của nhánh
chung và T4/T5 đã hoàn thành. Không force-push hoặc sửa vendor.

## Kết quả theo task

| Task | Kết quả review | Commit / bằng chứng |
|---|---|---|
| T1 | A–D, nguồn/sai số giờ, UI và prompt; C/D bị chặn cả sau retry cuối; `loai_ket_luan` bắt buộc | `bd428c3`, `test_horoscope_input_confidence.py` |
| T2 | Bốn mức, cấm phần trăm; đếm ID khác nhau; mạnh/rất mạnh cần tối thiểu ba fact | `7571bab`, `test_horoscope_conclusion_confidence.py` |
| T3 | Merge head `aaa0951` của feature/t3-evidence-labels; sửa nhãn ngoài chứng cứ và Tị/Tỵ | `5b5d508`, `test_horoscope_evidence_labels.py` |
| T4 | 44 vector độc lập, 1.784 đối chiếu; 351 sai khác được document + issue theo DoD | `4878f5e`, [cross-check](LASOTUVI_CROSSCHECK.md), [issue #1](https://github.com/huypq205/KMS_Tu_Vi/issues/1) |
| T5 | 40 mục/10 Can, ba khác biệt; giữ hai bảng có nguồn, mặc định vendor; không hòa giải tự động | `3bb6c4f`, `test_tu_hoa_tables.py`, [data dictionary](data_dictionary.md) |
| T6 | 14 nhóm, ba tiếng nói, trang thật; 20 seed qua gate, không ghi đè canonical; 8 test | `3c1638b`, [hồ sơ sao](STAR_DOSSIER.md) |
| T7 | Gate CSV/Excel, >=1 căn cứ, quarantine nguồn D; 39 test; workbook thật 10.456 dòng không lỗi | `ab7e636`, `f26eb5b`, [gate](KNOWLEDGE_GATE.md) |
| T8 | Ca ẩn danh/snapshot cố định, khóa và phiên bản, giữ kết quả sai; ngưỡng 30 ca; 11 test | `cd2d2a9`, [nghiệm lý](CASE_VALIDATION.md) |
| T9 | Bảng bốn tầng do server ghép, so năm ±1, việc chưa đủ căn cứ; sửa fallback/nối đại hạn; 10 test | `2cb2453`, [vận năm](ANNUAL_REPORT.md) |
| T10 | Skill API bốn chế độ, 14 sao, MIT; validator/CI; 13 test và hai validator pass | `e051f0b`, [skill](../skills/tu-vi-kms/SKILL.md) |
| T11 | Changelog có trước/sau, nguồn, lý do và phạm vi ảnh hưởng; review tích hợp/CI/DB; bảng nghiệm thu này | [changelog](CHANGELOG_KNOWLEDGE.md), [nhật ký thực thi](GOVERNANCE_EXECUTION.md) |

## Kiểm chứng cuối

```powershell
.venv/Scripts/python.exe -m pytest tests/ -q
# 2135 passed, 351 xfailed in 55.73s
.venv/Scripts/python.exe scripts/validate_skill.py
# PASSED
.venv/Scripts/python.exe scripts/validate_knowledge_import.py tests/fixtures/knowledge_gate/valid/
# PASSED: checked=4, new=4, quarantined=1, errors=0
.venv/Scripts/python.exe scripts/compare_tu_hoa_tables.py
# 40 mục, 3 khác biệt; config lasotuvi khớp vendor
```

Review CI phát hiện ba unit test singleton cũ phụ thuộc gói model tùy chọn trong
môi trường backend nhẹ. Đã sửa bằng factory test cô lập và lazy import model,
thêm test subprocess chặn package để tái hiện; không skip test để làm xanh CI.
Commit `bc497f9`: [GitHub Actions PASSED](https://github.com/huypq205/KMS_Tu_Vi/actions/runs/41567801027).

Đã review API thật bằng TestClient (không gọi LLM bên ngoài): read/ask, hai giả
thiết giờ sinh, dossier và annual. Test nhật ký chạy đầy đủ tạo ca → dự đoán →
khóa → ghi kết quả không khớp trong DB tạm. Đã kiểm tra lỗi/auth, seed toggle,
escaping và trạng thái thiếu dữ liệu. Giao diện T6/T8/T9 được xem trong trình
duyệt ở 1440/768/390px, gồm trạng thái mở hàng bốn tầng; lint/inspector không
FAIL/WARN. Dùng skill design-taste-frontend và skill-creator; chi tiết tại tài
liệu từng task. Không dùng test mô phỏng để tuyên bố đã có ca nghiệm lý thật.

## `tuvi_import/` và dữ liệu canonical

`tuvi_import/` là tên thư mục dự kiến chứa CSV REPO exports, không phải tên của
một file đã có. Nguồn thực tìm thấy là workbook:

`D:/FPT/2026/FA26/KMS301/Project_TuVi/Final/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx`.

Gate kiểm tra toàn bộ như ID mới: 10.456 checked/new, không lỗi. So DB baseline:
10.456 checked, 0 new, không lỗi. Phân bố NPL 2.191 / BD 4.450 / DAU 3.815 khớp
DB. CSV cùng tên 1.559 byte chỉ chứa Indicator/Value/Explanation.

SHA256 workbook: `27901de589ec69959b43a80c3d108b83f5ebbc4c53489795b3301cf31ae72f40`.
SHA khác workbook cũ ghi trong data dictionary; xác nhận khớp ID hiện hành,
không khẳng định hai file Excel giống nhau từng byte. Không import/build index
lại hoặc đưa workbook lên Git.

So sánh DB trước/sau bằng fingerprint từng bảng xác nhận tri thức/evidence/chunk
không đổi. Chỉ cache test và ba bảng nhật ký mới **rỗng** thay đổi. Đã sao lưu
SQLite đầy đủ (kể cả WAL) tại `.pytest_cache/kms-after-governance-tests.db`, dừng
server preview của agent, checkpoint và khôi phục DB tracked. Không đưa cache
test hay dữ liệu người dùng vào commit. Ba bảng nhật ký tự được tạo khi dùng API.

## Giới hạn giữ nguyên khi nghiệm thu

- 351 xfail T4 là sai khác đã biết, strict: thay đổi ngoài kỳ vọng sẽ làm test
  đỏ. Issue #1 còn mở để đối chiếu sách. T4 hoàn thành theo DoD cho phép document
  + issue, không có nghĩa hai nguồn an sao đã trùng hoàn toàn.
- Hai bảng Tứ Hóa có nhãn nguồn riêng; chưa phân xử đúng/sai bằng ba sách KMS.
- Seed chưa thành canonical; metadata Author_Stances vắng trong DB cũ không bị
  tự bịa. Gate cấu trúc không thay review ý nghĩa hay xác minh trang thủ công.
- Chưa an lưu nguyệt; phần tháng khai báo thiếu. Bảng vận năm là dữ kiện để
  đối chiếu, không phải dự đoán sự kiện đã có chứng cứ đủ mạnh.
- Không tạo ca thật giả để đủ 30 mẫu; thống kê thực tế còn đóng nếu chưa đủ mẫu.
  Thời điểm trong nhật ký không chứng minh điều người ghi đã biết ngoài hệ thống.
- Skill nằm trong checkout repo, tham chiếu docs KMS; chưa cài vào cấu hình
  Codex cá nhân. MIT của skill không thay license dữ liệu sách.

Khởi chạy bằng `run_local.bat` hoặc `streamlit run app.py`: điều hướng gồm
Luận giải lá số, Hồ sơ sao và Nhật ký nghiệm lý.
