# Thư mục audit phục vụ cập nhật báo cáo (05/11/2026)

Thư mục này chứa bằng chứng và script kiểm kê dùng để cập nhật
`docs/REPORT_KMS_TU_VI.md` / `.docx` lên phiên bản 2.0. **Không phải mã nguồn
sản phẩm**, không được import bởi backend/frontend.

| Tệp | Mục đích |
|---|---|
| `db_stats.py` | Đếm bảng/số dòng `data/processed/kms.db` ở chế độ **chỉ đọc**; phân bố trust tier, release/validation status, import runs |
| `spot_check.py` | Đối chiếu số liệu đầu mục: 30 quy tắc cách cục, 2 bảng Tứ Hóa, 10 loại chứng cứ, 14 slot / 108 sao / 20 seed, 34 sao tham khảo, danh sách bảng DB |
| `list_routes.py` | Liệt kê route FastAPI thực tế (dùng `app.openapi()`) |
| `verify_docx.py` | Kiểm tra cấu trúc DOCX sau khi build: heading, bảng, marker markdown sót lại, sự hiện diện của số liệu chính |
| `find_stray.py` | Kiểm tra đoạn văn bản chứa ký tự backtick, '#' hoặc khối code trong DOCX để rà soát lỗi định dạng |
| `code_inventory.md` | Bản kiểm kê tầng backend (endpoint, service, config, YAML, delta so với báo cáo v1) |
| `fe_tests_docs_inventory.md` | Bản kiểm kê frontend, test, script, tài liệu, skill, delta so với báo cáo v1 |
| `REPORT_KMS_TU_VI_v1_2026-11-01.md` / `.docx` | Bản sao báo cáo v1.0 (01/11/2026) để đối chiếu/khôi phục |

Cách chạy (từ gốc repo, Python 3.12):

```powershell
python docs/_report_audit/db_stats.py
python docs/_report_audit/spot_check.py
python docs/_report_audit/list_routes.py
python docs/build_report_docx.py        # sinh lại DOCX từ Markdown
python docs/_report_audit/verify_docx.py
python docs/_report_audit/find_stray.py
```

Lưu ý: số liệu là **ảnh chụp** tại thời điểm 05/11/2026; DB được mở read-only
nên các script không làm thay đổi tri thức.
