# T7 — Cổng kiểm duyệt tri thức nhập vào KMS

Phiên bản quy tắc: 1.0 — 2026-11-03.

## Điều kiện cho bản ghi mới

Mỗi `Knowledge_ID`/`Canonical_ID` mới phải có **ít nhất một** trong ba yếu tố:

| Yếu tố | Metadata được kiểm tra |
|---|---|
| A — Dẫn nguồn và trang | `Source_IDs` trỏ tới nguồn có trong registry, kèm `PDF_Pages` hợp lệ; hoặc evidence liên kết đúng knowledge/source và có `PDF_Page` dương |
| B — Trường phái hoặc lập trường | `School` hoặc `Author_Stances` có nội dung rõ |
| C — Ví dụ hoặc ca kiểm chứng | `Validation_Example`, `Case_ID` hoặc trường ví dụ tương đương có nội dung |

Đây là phép OR theo yêu cầu T7 của plan, không yêu cầu đồng thời cả ba yếu tố.
Các placeholder rỗng, `N/A`, `UNKNOWN`, `TBD`, `[]`, `{}` hoặc `—` không được tính.

Gate còn kiểm tra ID, nội dung, ID trùng, liên kết nguồn/evidence và redirect.
Trang PDF phải dương; `PDF_Pages` phải parse được toàn bộ chuỗi. Với BD, ghi đúng
phần, ví dụ `P7:36`; evidence cần `Part_Number` và `PDF_Page` riêng.
`Evidence_Count` đơn thuần không được xem là evidence.

Gate chỉ xác nhận điều kiện metadata. Nó không chứng minh nội dung đúng, trang
thật sự khớp PDF, trường phái được xác thực, bản quyền được phép sử dụng hoặc ca
nghiệm lý đã được kiểm chứng. Những việc này vẫn cần review theo nguồn KMS.

## Nguồn D: FORUM và VIDEO

Khai báo `Source_Type=FORUM` hoặc `VIDEO` trong `REPO_SOURCE.csv`/sheet `SOURCES`.
Cũng nhận `Source_Type` tại bản ghi knowledge hoặc evidence. Phân loại áp dụng
nếu **bất kỳ** nguồn liên quan nào thuộc D, kể cả khi có nguồn sách đi cùng.
Khi thiếu liên kết nguồn trực tiếp, nguồn D khai báo cho cùng `Book_Code` cũng
buộc bản ghi phải được xem xét theo chính sách D.

Mọi knowledge dùng nguồn D phải có:

```text
Release_Status = DRAFT_NOT_RELEASED
Review_Flag = HYPOTHESIS_NEEDS_VALIDATION
trust_tier = 9
```

`Review_Flag` có thể có nhiều token phân tách bằng `;`, `,` hoặc `|`, nhưng phải
có đúng token trên. Các giá trị như `NOT_HYPOTHESIS_NEEDS_VALIDATION` không hợp lệ.
Knowledge mới từ D vẫn phải đáp ứng ít nhất một yếu tố A/B/C.

Importer từ chối trạng thái không hợp lệ thay vì tự đổi nhãn thành nháp.
Quy tắc D luôn áp dụng, **kể cả khi không truyền `--gate`**, và cả khi cập nhật
một ID cũ. Tier 9 được ép trước quy tắc theo sách, tránh trường hợp nguồn video
mang `Book_Code=NPL` được nhận tier 1. Bước tạo chunk loại tier 9 và nhãn giả thuyết
kể cả khi cấu hình nhầm bật tier 9 hoặc ai đó gán nhầm tier cho bản ghi.
Registry FORUM/VIDEO cũng không được ghi đè tên và định danh của sách đã có
trong bảng `books` khi dùng chung `Book_Code`.

T7 bổ sung mapping cột `Source_Type`; không thêm cột hoặc migrate DB production.
Loại nguồn nằm trong file nguồn, còn trạng thái nháp, review flag và tier được
lưu trong knowledge để bảo vệ bước index.

## Kiểm tra CSV, không ghi DB

```powershell
python scripts/validate_knowledge_import.py tuvi_import/
python scripts/validate_knowledge_import.py tuvi_import/REPO_KNOWLEDGE.csv --json
```

Tên CSV được nhận:

- Knowledge: `REPO_KNOWLEDGE*.csv`, `CANONICAL_KNOWLEDGE.csv`,
  `CANONICAL_KNOWLEDGE_V1_0.csv`; cũng nhận CSV có header ID/nội dung tương ứng.
- Registry nguồn: `REPO_SOURCE.csv`, `REPO_SOURCES.csv` hoặc `SOURCES.csv`.
- Evidence: `REPO_EVIDENCE.csv` hoặc `EVIDENCE.csv`.
- Redirect: `REPO_ID_REDIRECTS.csv` hoặc `CANONICAL_ID_REDIRECTS.csv`.

Nếu truyền một CSV knowledge riêng, script tự đọc registry/evidence/redirect có
tên trên ở cùng thư mục. Các CSV không phải dữ liệu gate được bỏ qua trong chế độ
thư mục. Input thiếu hoặc không có knowledge nào trả lỗi, không báo pass giả.
CSV dùng UTF-8 hoặc UTF-8 BOM, dấu phẩy và header; ô có dấu phẩy phải đặt trong
dấu ngoặc kép đúng chuẩn CSV. Cột ngoài phạm vi gate không được import vào DB bởi
script này.

Fixture dữ liệu tổng hợp chỉ dùng cho test nằm tại
`tests/fixtures/knowledge_gate/valid/`. Các bản ghi đó không phải tri thức thật,
không được đưa vào kho KMS.

`--json` xuất mã lỗi, knowledge ID, tên file/sheet và số dòng. Exit code 0 là
pass; 1 là lỗi dữ liệu hoặc không đọc được input. Không có lệnh mạng hay LLM.

## Kiểm tra workbook và nối vào import

```powershell
python scripts/validate_knowledge_import.py "duong-dan/workbook.xlsx"
python scripts/import_excel.py --excel "duong-dan/workbook.xlsx" --gate
```

Workbook dùng tên sheet/cột theo `configs/column_mapping.yaml`. `SOURCES` và
sheet knowledge bắt buộc; validator độc lập chấp nhận thiếu evidence/redirect
nếu bản ghi đáp ứng yếu tố B/C hoặc dẫn trang trực tiếp. Luồng importer vẫn dùng
các sheet cấu trúc hiện hành của workbook canonical.

CLI độc lập mặc định kiểm tra mọi ID như bản ghi mới. Với import tăng dần:

```powershell
python scripts/validate_knowledge_import.py tuvi_import/ --existing-db data/processed/kms.db
```

Database baseline được mở read-only. ID đã tồn tại không bị yêu cầu bổ sung A/B/C
lại; các quy tắc nguồn D và lỗi liên kết vẫn được kiểm tra. `import_excel.py
--gate` tự dùng DB hiện hành làm baseline, chạy preflight trước `init_db`, rồi
kiểm tra lại trong luồng import trước khi thay knowledge/evidence/chunk. Nếu gate
thất bại, preflight không khởi tạo hoặc ghi DB; lỗi trong transaction được rollback.

Bản ghi có trường phái/ca kiểm chứng có thể chưa có trang PDF. Importer lưu được
bản ghi có ID, Book_Code và nội dung; việc thiếu PDF không còn khiến bản ghi bị
loại âm thầm. Điều kiện index có evidence vẫn áp dụng; gate pass không tự làm
bản ghi được index hoặc được duyệt phát hành.

## Quy tắc nội dung và review thủ công

- Giữ riêng tiếng nói của ba sách; ghi nguồn và trường phái khi có bất đồng.
- Không bịa trang, điều kiện, phản chứng hoặc ca kiểm chứng để qua gate.
- Không dùng ngôn ngữ định mệnh tuyệt đối, chẩn đoán y khoa hay khẳng định sự kiện
  chắc chắn. Nội dung lịch sử nhạy cảm phải được quy về lời ghi của nguồn và nêu
  giới hạn; bỏ nếu không thể diễn đạt phù hợp.
- LLM chỉ hỗ trợ tìm, tóm tắt hoặc đề xuất review; không tạo tri thức canonical mới.
- Việc lọc ngôn ngữ/đánh giá ý nghĩa chưa được tự động hóa bằng regex trong gate.
  Người review phải kiểm tra phần này trước khi chấp thuận phát hành.

## Mẫu đề xuất quy tắc

```markdown
# Tên quy tắc:

- Knowledge_ID dự kiến:
- Nội dung đề xuất:
- Tác giả / sách / ấn bản:
- Source_ID / Source_Type:
- Phần / chương / trang PDF:
- Trường phái / Author_Stances:
- Điều kiện áp dụng:
- Phản chứng hoặc giới hạn:
- Ví dụ kiểm thử / ca nghiệm lý ẩn danh:
- Kết quả không khớp hoặc chưa xác minh:
- Quan điểm khác trong sách KMS:
- Kết luận hiện có bị ảnh hưởng:
- Release_Status / Review_Flag:
- Người review và bằng chứng đã kiểm tra:
```

Điền đúng dữ kiện có sẵn, để rõ mục chưa biết. Nguồn D luôn giữ nháp và giả thuyết.

## CI và nguồn tham khảo của quy trình

CI luôn chạy gate trên fixture hợp lệ và toàn bộ test âm tính/tích hợp. Khi có
`tuvi_import/`, chạy thêm gate trên CSV thực tế; thư mục tồn tại nhưng rỗng là lỗi.
Nếu thư mục vắng mặt, CI ghi rõ `SKIPPED actual CSV validation`, không coi dữ liệu
thật đã pass. Workspace triển khai T7 hiện chưa có thư mục này hoặc workbook gốc,
nên chỉ có kết quả fixture và test tích hợp; chưa xác nhận kho import thực tế.

Quy trình và mẫu đề xuất được diễn giải cho KMS từ repo MIT
`duandigi/tu-vi-dau-so-research`, commit `91f8a06f1bca2fb271791785937265ea78d7f858`:
[STAR_KNOWLEDGE_BASE §6](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/references/STAR_KNOWLEDGE_BASE.md#6-kiểm-soát-chất-lượng),
[CONTRIBUTING](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/CONTRIBUTING.md),
[research_rule.yml](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/.github/ISSUE_TEMPLATE/research_rule.yml).
Code gate được viết riêng cho schema CSV/Excel của KMS; ngưỡng ít nhất một yếu tố
thực hiện theo T7 trong plan dự án.

## Review dữ liệu thật sau khi tìm lại nguồn

Đã tìm và kiểm tra read-only workbook tại
`D:/FPT/2026/FA26/KMS301/Project_TuVi/Final/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx`
(9.369.217 byte). Chạy validator trên toàn bộ ID như mới: **10.456 checked,
10.456 new, 0 quarantined, 0 errors — PASSED**. Không chạy import hoặc build index.

CSV cùng tên chỉ có 1.559 byte, header `Indicator,Value,Explanation`, là bảng chỉ số
tổng hợp; không phải export knowledge. `tuvi_import/` trong plan là thư mục dự kiến
chứa các CSV `REPO_*`; nó không đồng nhất với CSV chỉ số này. Không cần tạo CSV
trung gian vì validator đã đọc trực tiếp workbook thật. Giữ workbook ngoài Git.

SHA-256 workbook: `27901de589ec69959b43a80c3d108b83f5ebbc4c53489795b3301cf31ae72f40`.
Khi đối chiếu baseline `kms.db`: checked=10.456, new=0, errors=0. Số bản ghi theo
sách khớp DB hiện hành: NPL 2.191, BD 4.450, DAU 3.815. SHA của file workbook
khác SHA workbook từng ghi trong data dictionary; các ID hiện hành khớp, chưa vì
vậy khẳng định hai file Excel giống nhau từng byte.

```powershell
python scripts/validate_knowledge_import.py "D:/FPT/2026/FA26/KMS301/Project_TuVi/Final/TuVi_KMS_3Books_CANONICAL_MASTER_DEDUP_v1.0.xlsx" --json
```
