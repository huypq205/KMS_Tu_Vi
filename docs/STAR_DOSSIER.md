# T6 — Hồ sơ sao theo nguồn

API: `GET /api/v1/stars/{ten_sao}/dossier?include_seeds=false`.
Alias theo plan: `/api/stars/{ten_sao}/dossier`; cả hai đều tuân thủ X-API-Key
khi bật cấu hình bảo vệ. Tên sao không hợp lệ trả 404; lỗi kho/seed trả 503.

Mở `streamlit run app.py`, chọn **Hồ sơ sao**. `run_local.bat` đã dùng entrypoint
điều hướng này. Tra cứu bằng tên có/không dấu; URL có thể truyền `?star=Vũ Khúc`.
Không có lời gọi LLM hay thao tác ghi tri thức trong luồng hồ sơ.

## 14 mục

`core_function`, `yin_yang_five_element`, `favorable_expression`,
`unfavorable_expression`, `strength_by_branch`, `by_palace`,
`supportive_combinations`, `challenging_combinations`, `transformation_behavior`,
`with_tuan_triet`, `with_sat_tinh`, `school_differences`, `case_notes`,
`source_citations`. Đây là 14 nhóm hiển thị rút từ schema hồ sơ sao của repo 1,
không phải tuyên bố schema gốc chỉ có đúng 14 trường.

## Ưu tiên nguồn

- Nguồn A: bản ghi KI đủ tier 1/2/3, không là giả thuyết, có trang dẫn thật.
  Dùng cùng tìm kiếm FTS với horoscope, kết hợp subject/taxonomy của knowledge.
  Mỗi entry giữ knowledge_id, book_code, điều kiện, trust_tier và trang/phần.
- Phân mục bằng metadata điều kiện/predicate; không phân loại được thì giữ ở
  view từng sách. Không suy diễn để lấp mục thiếu. Mỗi sách tối đa 30 bản ghi
  trong kết quả; việc có nhiều bản ghi hơn không tự tăng độ tin cậy.
- `school_differences` giữ riêng tiếng nói từng sách; không tự khẳng định chúng
  mâu thuẫn. Dùng Conflict_Status và Author_Stances nếu metadata được lưu; DB cũ
  chưa có cột author_stance thì hiện chưa có metadata, không bịa tác giả/lập trường.
- Nguồn B: 20 YAML seed được diễn giải ngắn từ repo 2, luôn `seed_unverified`,
  ghi nguồn gián tiếp và URL commit. Chỉ lấp mục chưa có nguồn A. Không vào RAG.
- Nguồn gốc gán cho seed là Toàn Tập (bản dịch Quách Ngọc Bội) theo plan/repo
  tham khảo, chưa được đối chiếu độc lập với bản sách; không có số trang giả.
- T7 được chạy trên mỗi seed trước khi sử dụng. Tri thức seed chưa thành canonical.
- Người dùng phải chủ động bật tham khảo. Đặt `KMS_STAR_SEEDS_ENABLED=0` để tắt
  trên server, kể cả khi request yêu cầu. Mặc định API không kèm seed.
- Mục không có dữ liệu giữ thông báo `chưa có trong kho tri thức hiện tại`;
  `case_notes` để rỗng làm chỗ cho kho nghiệm lý T8, không tạo ca minh họa giả.

## Review

Đã kiểm tra riêng hai sao Vũ Khúc và Cự Môn trong corpus thật: có bản ghi và trang
dẫn. Test dùng thêm corpus tạm để kiểm tra không hòa trộn sách, seed không ghi đè,
14 mục trống, enum tên sao, alias API/auth, lỗi DB và trạng thái UI.

Nguồn thiết kế quy trình: [repo 1 STAR_KNOWLEDGE_BASE](https://github.com/duandigi/tu-vi-dau-so-research/blob/91f8a06f1bca2fb271791785937265ea78d7f858/references/STAR_KNOWLEDGE_BASE.md).
Nguồn seed: [repo 2 star_meanings](https://github.com/hung-ngm/tu-vi-dau-so/blob/d0238e9ee9f1a8a1603f5ff1328b18bf6e4635b7/tu-vi-dau-so/skills/tu-vi-dau-so/references/star_meanings.md).
Không sao chép nguyên văn các đoạn luận; đã bỏ khẳng định định mệnh, bệnh tật,
tuổi thọ, số con và đánh giá phẩm chất cá nhân trong lớp seed.

### Review giao diện

Áp dụng skill design-taste-frontend, hướng `achromatic-ledger`, seed 82576219;
giữ IBM Plex Sans và palette KMS. Đổi một lần từ icon rail sang mặt phẳng mở
để giữ điều hướng Streamlit có nhãn. Câu hỏi chính của trang: nguồn nào ghi gì
về sao này? Vì vậy tab đầu hiển thị từng sách và trang dẫn trước các nhóm nghĩa.
Trên tablet/điện thoại các sách xếp dọc; trích dẫn có màu chữ đầy đủ, trang dẫn
màu phụ. Đã xem ảnh thật ở 1440/768/390px, kiểm tra không tràn ngang và trạng
thái trống/lỗi bằng Streamlit AppTest. Lint và inspector không có FAIL/WARN.

Kiểm thử T6: 8 passed; hồi quy: 2100 passed, 351 xfailed đã ghi nhận ở T4.
