# 🚀 HƯỚNG DẪN KHỞI CHẠY DỰ ÁN KMS TỬ VI (KHI KHÔNG DÙNG IDE)

Tài liệu này hướng dẫn bạn cách khởi chạy và sử dụng dự án **hoàn toàn độc lập** trên máy tính Windows mà không cần mở Antigravity IDE hay VS Code.

Giao diện luận giải mới chạy riêng bằng lệnh dưới đây, cùng với backend đang mở. `run_prototype_ui.bat` phía dưới chỉ mở giao diện lá số truyền thống.

```powershell
.\.venv\Scripts\python.exe -m streamlit run frontend/horoscope_ui.py --server.address 127.0.0.1 --server.port 8502 --server.headless true --browser.gatherUsageStats false
```

Mở `http://127.0.0.1:8502`. Sau khi cập nhật bản sửa, dừng và khởi động lại backend/Streamlit.
Cấu hình model riêng cho bài luận bằng `KMS_HOROSCOPE_MODEL`; xem [hướng dẫn đầy đủ](docs/RUN_HOROSCOPE.md).

---

## ⚡ CÁCH 1: KHỞI CHẠY 1-CLICK (ĐƠN GIẢN NHẤT)

Trong thư mục dự án `D:\FPT\2026\FA26\KMS301\Project_TuVi\KMS\KMS`, đã có sẵn **3 file tiện ích**:

### 1. Nhấp đúp vào `run_backend.bat`
* **Mục đích:** Khởi động Backend API Server (FastAPI).
* **Kết quả:** Cửa sổ dòng lệnh sẽ tự bật lên và **tự động mở trình duyệt** đến địa chỉ:
  👉 **`http://localhost:8000/docs`** (Giao diện Swagger UI trực quan).
* Tại đây bạn có thể nhập ngày giờ sinh vào mục `POST /api/v1/horoscope/read` để nhận kết quả bói toán & luận giải ngay lập tức.

### 2. Nhấp đúp vào `run_test_cli.bat`
* **Mục đích:** Luận giải nhanh qua cửa sổ Terminal tương tác.
* **Kết quả:** Màn hình sẽ hỏi bạn từng thông tin:
  1. Nhập họ tên
  2. Ngày / Tháng / Năm sinh
  3. Chọn giờ sinh (hiển thị danh sách 12 khung giờ chi kèm giờ thực tế)
  4. Chọn giới tính (Nam / Nữ)
  5. Chọn loại lịch (Dương lịch / Âm lịch)
* Hệ thống sẽ tính toán lá số, tìm kiếm 3 cuốn sách kinh điển và in bài luận giải 6 phần ngay trên màn hình.

### 3. Nhấp đúp vào `run_prototype_ui.bat`
* **Mục đích:** Mở giao diện Web Streamlit (Lá số bàn 12 cung truyền thống).
* **Địa chỉ:** `http://localhost:8501`.

---

## 💻 CÁCH 2: CHẠY BẰNG DÒNG LỆNH (POWERSHELL / CMD)

Nếu bạn muốn mở PowerShell hoặc Command Prompt thủ công:

### Bước 1: Mở PowerShell và di chuyển vào thư mục dự án
```powershell
cd D:\FPT\2026\FA26\KMS301\Project_TuVi\KMS\KMS
```

### Bước 2: Thiết lập mã hóa tiếng Việt
```powershell
$env:PYTHONIOENCODING="utf-8"
```

### Bước 3: Chạy chức năng mong muốn

* **Khởi động Backend Server:**
  ```powershell
  .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
  ```
  *(Truy cập `http://localhost:8000/docs`)*

* **Chạy Luận giải tương tác trên Terminal:**
  ```powershell
  .venv\Scripts\python.exe scripts\test_horoscope_cli.py -i
  ```

* **Chạy Luận giải nhanh với tham số truyền sẵn:**
  ```powershell
  .venv\Scripts\python.exe scripts\test_horoscope_cli.py --ho_ten "Nguyễn Văn A" --ngay 15 --thang 8 --nam 1995 --gio 5 --gioi_tinh 1
  ```

* **Chạy toàn bộ 26 Unit Tests để kiểm tra độ ổn định:**
  ```powershell
  .venv\Scripts\python.exe -m unittest discover -s tests -p "test_horoscope*.py" -v
  ```

---

## 🔑 CẤU HÌNH API KEY (NẾU CÓ)

Hệ thống được thiết kế để **chạy offline 100%** bằng mô hình luận giải thông minh deterministic fallback nếu không có mạng hay API key.

Nếu bạn muốn kết nối Google Gemini API:
1. Mở file `.env` tại thư mục gốc dự án.
2. Điền API Key của bạn:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
3. Khi gọi API hoặc CLI, chọn provider là `gemini` hoặc `auto`.

### Bảo mật API khi deploy (Render)
Ba biến tuỳ chọn trong `.env` (mặc định: API mở, rate limit 10 yêu cầu/phút cho `/horoscope*`):

```env
KMS_API_KEY=            # khi đặt: mọi /api/v1/* (trừ /health) bắt buộc header X-API-Key
KMS_RATE_LIMIT_PER_MIN=10   # 0 để tắt
KMS_CORS_ORIGINS=http://localhost:8501,http://localhost:8502
```

Frontend Streamlit tự gửi `X-API-Key` khi `KMS_API_KEY` được đặt (cùng file `.env`), và tự hiển thị cảnh báo khi dev local "im lặng" trỏ vào backend production.

---

## 🛑 CÁCH DỪNG HỆ THỐNG
* Tại cửa sổ dòng lệnh đang chạy server, bạn chỉ cần nhấn tổ hợp phím **`Ctrl + C`** để tắt server một cách an toàn.

