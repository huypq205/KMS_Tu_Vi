# Kiểm tra computation và tích hợp ý nghĩa sao từ skill local

Ngày: 2026-11-03. Phạm vi theo yêu cầu mới: kiểm tra khả năng thay bộ an sao;
dùng star_meanings cho cả tra cứu và ngữ cảnh AI. Chưa xử lý các khoảng trống
T2/T3/T9 được nêu trong lượt review trước, chưa triển khai thiết kế UI mới.

## Kết luận về computation

KMS hiện có API FastAPI nhận input, nhưng phần an sao được tính trong Python:
`generate_raw_horoscope` → `vendor/lasotuvi`. Không gọi API lập lá số bên ngoài.

Thư mục người dùng thêm tại `skills/tu-vi-dau-so-main/` gồm Markdown (SKILL,
computation, star_meanings, cách cục, README), không có engine Python/JS thực thi.
`computation.md` hướng dẫn agent đếm cung/tra bảng; không phải hàm thay thế thư
viện. Việc LLM có thể làm theo hướng dẫn không bảo đảm cùng input cho cùng output.

Git blob của computation local: `28ffd19e28919c5a2b3eb98d146326bb22f07985`,
trùng chính xác nguồn đã dùng trong fixture T4. Chạy lại đối chiếu 44 vector:
**1873 passed, 351 xfailed**. Known mismatch được giữ nguyên, không đổi kỳ vọng
theo vendor để làm xanh test. 351 trường khác không phải 351 lỗi độc lập.

Các điểm không đủ căn cứ thay thế:

- Thủy nhị cục: phần mô tả nói hai ngày tiến một cung, bảng chi tiết lại đi một
  cung mỗi ngày. Ngày 4 nguồn ghi Thìn, vendor cho Mão trong vector đã ghi nhận.
- Kim tứ cục ngày 1 ghi hai phương án Dậu hoặc Hợi.
- Sai khác Khôi/Việt, Hỏa/Linh và ba mục Tứ Hóa đã có trong hồ sơ T4/T5.
- Thiếu bộ chuyển lịch thực thi, bảng ngày đầy đủ/nhất quán cho mọi Cục và toàn
  bộ dữ liệu sao/trạng thái cần cho hợp đồng response hiện tại.

**Quyết định:** giữ engine hiện tại và API hiện tại. Không lấy suy đoán của LLM
để tự lấp bảng thiếu; chưa có engine thay thế đạt điều kiện tương đương. Không
sửa vendor, không đổi trường phái mặc định. Xem [T4](LASOTUVI_CROSSCHECK.md).

## star_meanings đã nối vào đâu

Loader `star_meanings_reference.py` chỉ đọc `references/star_meanings.md`, không
thực thi SKILL.md hoặc nhận các chỉ dẫn trong tài liệu làm lệnh hệ thống.
Đã kiểm tra tài liệu local: đọc được **34 sao**, gồm 14 chính tinh và các nhóm
phụ tinh/Tứ Hóa. Không có mục riêng cho Tuế Phá, Tang Môn hoặc Thái Tuế: không
tự bịa ý nghĩa của chúng từ nguồn này.

- **Hồ sơ sao:** bật “Bổ sung tham khảo chưa đối chiếu sách KMS”, tra cứu lại,
  mở tab “Ý nghĩa và điều kiện” → “Ý nghĩa sao từ skill tham khảo”. Nội dung
  nằm riêng trong `reference_meaning`, không ghi đè 14 slot canonical hoặc seed.
- **Bài luận AI:** cấp tối đa tám mục liên quan các sao thật trong lá số. Ưu
  tiên lưu Kỵ, chính tinh Mệnh và các cung chủ đề; mỗi mục trong prompt tối đa
  600 ký tự để tránh gửi toàn bộ sách. Giữ tên nhóm nếu nguồn viết chung hai sao.
- **Hỏi đáp AI:** chỉ chọn sao trong tập facts liên quan câu hỏi/chủ đề.
- **Chế độ không AI:** vẫn có thể tra tài liệu nhưng không gắn nhãn đã dùng AI.
  Response có `star_meaning_references`; meta `star_meanings_provided_to_ai`
  chỉ bật khi có mục tham khảo và thực chạy bằng Gemini (hoặc trả cache bài đó).

## Ranh giới nguồn

Mỗi mục giữ tên file, nhóm, SHA256, nguồn gián tiếp và `reference_unverified`.
Không gán book_code NPL/DAU/BD, trang PDF hoặc số source_ref giả. Prompt yêu cầu
ghi rõ khi dùng nguồn skill; chỉ hỗ trợ giải nghĩa, không thay chứng cứ để kết
luận về cá nhân hoặc nâng mức tin cậy. Các mục còn được kiểm cấu trúc bằng T7.

Loader bỏ toàn bộ dòng có dấu hiệu định mệnh/nhạy cảm đã nhận diện hoặc chỉ thị
chen trong tài liệu; bỏ phần luận số con, tuổi thọ và hình tướng theo từng cung.
Đây là lọc có giới hạn, không thay review ý nghĩa thủ công. Không nhập tài liệu
này vào knowledge_items, chunks hoặc chỉ mục RAG. Ba sách vẫn giữ riêng tiếng nói.

Đổi nội dung/tắt nguồn làm đổi khóa cache. Trong một lượt đọc, cache dùng đúng
snapshot tham khảo đã cấp cho model, tránh gắn bài cũ vào tài liệu mới.

## Cấu hình và triển khai

```dotenv
KMS_STAR_MEANINGS_ENABLED=1
KMS_STAR_MEANINGS_PATH=
```

Path rỗng dùng file trong thư mục skill người dùng vừa thêm. Có thể đặt đường
dẫn khác đến file `star_meanings.md`. Tắt với `KMS_STAR_MEANINGS_ENABLED=0`.
Hồ sơ sao còn tuân thủ `KMS_STAR_SEEDS_ENABLED` và checkbox tham khảo.

Tài liệu gốc người dùng đưa vào được giữ local, không tự đưa nguyên văn lên
GitHub. Khi chạy trên server khác, cần cung cấp file ở đường dẫn tương ứng hoặc
đặt KMS_STAR_MEANINGS_PATH; nếu vắng/hỏng/tắt thì không thêm ngữ cảnh và các luồng
cũ vẫn chạy. Việc thêm loader không tự cài skill vào cấu hình agent cá nhân.

## Kiểm chứng

11 test mới: parsing/nhãn/nguồn, nhóm và alias, thiếu/tắt/hỏng UTF-8, lọc dòng,
context liên quan/giới hạn, prompt read/ask, cache snapshot, ưu tiên canonical,
UI, provenance và engine không thay đổi. Gemini được mock ở biên transport;
không dùng kết quả mock để tuyên bố chất lượng bài luận Gemini thật đã nghiệm thu.

Hồi quy cuối: **2146 passed, 351 known T4 xfailed** (48.85s). Engine cross-check
riêng: 1873 passed, 351 xfailed. Review trình duyệt ở 1440/768/390px đã mở đúng
tab tham khảo: không tràn ngang hoặc FAIL. Đã sửa font nội dung và viền panel
để giữ cùng kiểu KMS; inspector còn một WARN về khoảng trống desktop của bố cục
một cột hiện hữu. Không mở rộng thành đợt thiết kế lại UI trong thay đổi này.
