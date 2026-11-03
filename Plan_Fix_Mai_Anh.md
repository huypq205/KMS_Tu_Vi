1\. Kiến trúc nội dung sau khi hoàn thành



Luồng xử lý dự kiến:

Thông tin sinh

&#x20;   ↓

Engine lập lá số hiện tại

&#x20;   ↓

Dữ kiện sao – cung – hạn có mã tham chiếu

&#x20;   ↓

Nhận diện tín hiệu và cách cục theo quy tắc

&#x20;   ↓

Bộ căn cứ: điều kiện khớp, điều kiện thiếu, nguồn, giới hạn

&#x20;   ├─ Lá số và dữ kiện

&#x20;   ├─ AI giải thích

&#x20;   └─ AI luận giải chuyên sâu

Cả ba mức dùng cùng một lá số. AI nhận dữ liệu có cấu trúc phía sau trang; không cần đọc hoặc thu thập lại HTML của chính ứng dụng.

Mức đọc	Nội dung chính	Tiêu chí khác biệt

Lá số và dữ kiện	Lá số, vị trí sao, hạn, tín hiệu, điều kiện khớp và lời giải thích theo mẫu	Hoạt động khi không có AI

AI giải thích	Giải nghĩa thuật ngữ, giải thích từng nhận định và liên hệ dữ kiện	Người mới hiểu được “vì sao”

AI luận giải chuyên sâu	Tổng hợp theo chủ đề, cân nhắc thuận/nghịch, phân biệt gốc–hạn, nêu điều kiện thay đổi kết luận	Có lập luận tổng hợp, không chỉ viết dài hơn





2\. P1 — Chốt cấu trúc dữ liệu và bộ ca nghiệm thu



Đây là nền tảng để backend và UI làm việc thống nhất.



Công việc:

\- Ghi nhận cấu trúc response hiện tại và các phần cần tương thích.

\- Bổ sung khái niệm reading\_mode, tách khỏi provider. Mức đọc là lựa chọn của người dùng; provider là bộ xử lý thực sự chạy.

\- Thiết kế một cấu trúc nhận định dùng chung cho cả ba mức.

\- Chuẩn bị bộ lá số kiểm thử cố định và dữ liệu giả lập lỗi AI.

\- Ghi lại giao diện hiện tại để đối chiếu sau khi thay đổi.

Mỗi nhận định cần có tối thiểu:

Thành phần	Ý nghĩa

Nhận định	Người xem cần hiểu điều gì

Dữ kiện	Sao nào, cung nào, gốc hay lưu niên, năm nào

Quy tắc	Điều kiện nào khiến hệ thống tạo nhận định

Lý do liên quan	Vì sao cung/dữ kiện đó liên quan đến chủ đề

Thuận và nghịch	Dấu hiệu hỗ trợ, dấu hiệu hạn chế hoặc mâu thuẫn

Điều kiện thiếu	Những gì hệ thống chưa kiểm tra được

Nguồn	Nguồn hỗ trợ cụ thể cho phần diễn giải

Giới hạn	Phạm vi có thể hiểu từ nhận định





Phải phân biệt hai trạng thái: “đã kiểm tra, không tìm thấy” và “chưa có dữ liệu để kiểm tra”.



Nghiệm thu: chốt được hợp đồng dữ liệu, ví dụ response cho ba mức và bộ ca kiểm thử trước khi mở rộng các thành phần phía sau.



3\. P2 — Chuẩn hóa nguồn ý nghĩa sao và cách cục



Hai file có vai trò khác nhau:

\- star\_meanings.md: giải nghĩa từng sao, nhóm sao và thuật ngữ.

\- cach\_cuc\_luan\_giai.md: điều kiện kết hợp sao–cung, cách cục, nguyên tắc diễn giải theo hạn.

Tôi đề xuất tạo bộ dữ liệu cách cục đã duyệt, có phiên bản, thay vì mỗi lần chạy lại tự diễn dịch Markdown thành quy tắc.



Công việc:

\- Kiểm kê từng mục trong file cách cục.

\- Tách điều kiện nhận diện khỏi lời diễn giải.

\- Chuẩn hóa tên sao, địa chi, quan hệ đồng cung/tam hợp/xung chiếu/giáp cung.

\- Giữ vị trí mục nguồn và dấu vân tay nội dung để truy ngược.

\- Gắn trạng thái: được phép dùng, chỉ tham khảo, cần đối chiếu, chưa hỗ trợ.

\- Ghi rõ phạm vi: lá số gốc, đại hạn hay lưu niên.

Ví dụ, mục có câu “Thái Âm cư Hợi + cát tinh” chưa đủ để tự động hóa nếu chưa xác định rõ:

\- Cát tinh nào được tính?

\- Cần đồng cung hay hội chiếu?

\- Điều kiện có bắt buộc tại Mệnh không?

\- Tuần/Triệt hoặc sát tinh ảnh hưởng như thế nào?

Những phần nguồn viết tắt, mơ hồ hoặc gộp tên sao phải được đưa vào danh sách đối chiếu. Không tự suy diễn để hoàn thiện quy tắc.



Các câu luận về tử vong, tuổi thọ, phẩm hạnh hay phân biệt giới cần được duyệt nội dung trước khi dùng trong sản phẩm. Nguồn này tiếp tục mang nhãn tham khảo chưa đối chiếu KMS; việc xuất hiện trong file không tự biến thành căn cứ đã xác minh.



Phạm vi bản đầu: chọn khoảng 5–8 cách cục có điều kiện đủ rõ và dữ kiện engine đáp ứng được. Ví dụ Tử Phủ đồng cung hoặc Cơ Cự đồng cung là ứng viên để xem xét, chưa mặc định công nhận toàn bộ lời luận đi kèm.



Nghiệm thu: mỗi mục được sử dụng đều có điều kiện rõ, giới hạn rõ và truy ngược được nguồn. File thiếu hoặc chưa được cung cấp trên server phải được nhận diện đúng.



4\. P3 — Xây bộ nhận diện cách cục và điều kiện



Bộ nhận diện chạy bằng code trên dữ kiện lá số, độc lập với AI.



Công việc:

\- Kiểm tra sao, cung, quan hệ và phạm vi thời gian theo từng quy tắc đã duyệt.

\- Liên kết kết quả với các mã dữ kiện đã khớp.

\- Ghi lại điều kiện đạt, không đạt và chưa kiểm tra được.

\- Nhận diện trường hợp một dữ kiện được nhiều quy tắc sử dụng.

\- Ghi nhận điều kiện thuận/nghịch khi có quy tắc và dữ liệu tương ứng.

Kết quả cần phân biệt:

\- Khớp các điều kiện được hỗ trợ.

\- Khớp một phần, còn thiếu điều kiện.

\- Không khớp.

\- Chưa thể đánh giá.

Không được lấy sao lưu niên ghép với sao gốc để công nhận một cách cục gốc, trừ khi chính quy tắc cho phép.



Nghiệm thu bằng các ca dương tính, âm tính và gần đúng: thiếu một sao, sai cung, sai quan hệ, thiếu trạng thái miếu/vượng, trùng tên sao ở hai tầng thời gian. AI không được tự thêm cách cục ngoài kết quả nhận diện.



5\. P4 — Giải thích tín hiệu và xử lý nhãn “nặng”



Đây là gói giải quyết trực tiếp ví dụ bạn phản ánh.



Công việc:

\- Mỗi tín hiệu phải xác định được sao gốc hay sao lưu niên.

\- Giữ cung thực tế và các vai trò của cung thành hai thông tin riêng.

\- Nhóm cùng một tín hiệu vật lý lại; ví dụ một sao ở cung vừa là Mệnh vừa là Thân vẫn giữ hai vai trò, nhưng không mặc định thành hai chứng cứ độc lập.

\- Công khai điều kiện tạo nhãn.

\- Phân biệt mức tập trung tín hiệu với độ chắc chắn của diễn giải.

Tôi đề xuất thay cách hiển thị “nặng” bằng “Mức tập trung tín hiệu cần xem xét”, với câu giải thích ngay bên cạnh. Ngưỡng tính mới cần được chốt bằng test sau khi rà soát trùng lặp; không chỉ đổi chữ rồi giữ nguyên mọi cách đếm.



Ví dụ cách trình bày dự kiến:

Tang Môn lưu niên tại Mệnh

Đây là sao thuộc vòng lưu niên của năm đang xem. Hệ thống đưa vào nhóm cần xem xét vì vị trí của nó trùng cung Mệnh theo quy tắc đang áp dụng. Ý nghĩa truyền thống được giải thích từ nguồn tham khảo đã chọn. Riêng dấu hiệu này chưa đủ để kết luận một sự kiện cụ thể.



Nếu cùng cung còn Liêm Trinh lưu Kỵ, phần giải thích phải nói rõ đó là một dấu hiệu khác, đồng thời nêu chúng cùng thuộc tầng lưu niên; không tự coi là hai tầng xác nhận.



Phần “vì sao” được tạo từ dữ kiện và quy tắc trước, nên chế độ không AI vẫn có nội dung hữu ích.



Nghiệm thu:

\- Truy được nhãn về điều kiện code.

\- Không đếm một tín hiệu thành nhiều chứng cứ độc lập vì trùng vai trò.

\- Nguồn chưa đủ thì ghi đúng phần còn thiếu.

\- Không biến mức kích hoạt thành dự báo chắc chắn về chuyện xấu.

6\. P5 — Đưa lá số 12 cung lên đầu



Dùng lại bộ vẽ hiện tại và nâng cấp cách trình bày.



Công việc:

\- Hiện lá số mặc định ngay sau thông tin sinh và năm xem.

\- Hiện ngay khi tính xong lá số, trước khi chờ truy xuất nguồn và AI.

\- Đặt thông tin sinh, âm/dương lịch, giờ sinh và năm xem ở vị trí dễ đối chiếu.

\- Thống nhất danh mục phân nhóm sao giữa frontend và backend.

\- Giữ chính tinh thành nhóm nổi bật.

\- Chia phụ tinh thành hai cột cát tinh / hung tinh theo danh mục truyền thống.

\- Có vị trí cho sao khác hoặc chưa phân loại.

\- Thể hiện riêng Tuần, Triệt, Tứ Hóa và dấu hiệu sao lưu niên.

Tứ Hóa và chính tinh cần được giữ nhận diện riêng; không ép toàn bộ vào hai nhóm tốt/xấu.



Trên desktop dùng bố cục 12 cung truyền thống. Trên điện thoại có chế độ đọc từng cung rõ chữ và lựa chọn xem toàn đồ phóng lớn; tránh thu nhỏ toàn bộ chữ để ép vừa màn hình.



Nghiệm thu:

\- Đủ 12 cung, không mất hoặc nhân đôi sao khi phân nhóm.

\- Cùng đầu vào cho cùng vị trí sao ở cả ba mức đọc.

\- AI chậm hoặc lỗi vẫn xem được lá số.

\- Kiểm tra thực tế ở 1440, 768 và 390px, gồm cung có nhiều sao.

7\. P6 — Triển khai ba mức đọc và AI chuyên sâu



Gói này có hai phần: điều phối chế độ và chất lượng nội dung.



Về điều phối:

\- UI gửi reading\_mode rõ ràng.

\- Backend trả mức được yêu cầu, mức thực tế đã hoàn thành và lý do fallback nếu có.

\- Chế độ dữ kiện không gọi AI.

\- Đổi mức đọc sử dụng lại lá số đã tính.

\- Cache phân biệt mức đọc, prompt/schema, bộ quy tắc và snapshot nguồn.

\- Lỗi ở mức chuyên sâu vẫn giữ lá số và phần đọc đã có.

Về AI giải thích:

\- Nhận dữ kiện, tín hiệu, kết quả cách cục và các nguồn liên quan.

\- Giải thích thuật ngữ bằng tiếng Việt dễ hiểu.

\- Mỗi nhận định liên kết với căn cứ cụ thể.

\- Giữ nguyên những điều kiện chưa đủ.

Về AI chuyên sâu, mỗi chủ đề cần trả về cấu trúc:

1\. Nhận định chính.

2\. Các dữ kiện dẫn đến nhận định.

3\. Cách chúng liên hệ với nhau.

4\. Điều kiện thuận.

5\. Điều kiện nghịch hoặc giới hạn.

6\. Phần có thể thay đổi theo hạn.

7\. Gợi ý chiêm nghiệm phù hợp.

Backend phải kiểm tra mã dữ kiện, nguồn, cách cục và năm xem mà AI sử dụng. Kiểm tra tự động giúp bắt sai cấu trúc và tham chiếu; chất lượng lập luận vẫn cần review nội dung trên bài AI thật.



Nghiệm thu: cùng một bộ lá số phải cho thấy ba mức khác nhau về giá trị đọc. Bản chuyên sâu đạt khi tổng hợp được quan hệ và điều kiện, không chỉ thêm đoạn văn hoặc thuật ngữ.



8\. P7 — Sắp xếp lại toàn bộ trang



Thứ tự trang theo đúng nhu cầu bạn nêu:

Vị trí	Nội dung hiện mặc định

Đầu trang	Thông tin sinh, năm xem, lá số 12 cung

Tiếp theo	Chọn mức đọc và trạng thái thực chạy

Tổng quan	Những điểm chính, viết ngắn và dễ hiểu

Theo chủ đề	Sự nghiệp, tài chính, tình cảm, vận trình

Vì sao	Giải thích các nhận định và cách cục liên quan

Xem căn cứ	Trích đoạn, bảng dữ kiện, nguồn và chi tiết kỹ thuật





Mỗi nhận định có lời giải thích ngắn tại chỗ; nút “Vì sao?” mở phần đầy đủ. Người đọc không phải xuống cuối trang tự ghép bảng sao với bài luận.



Các phần hiện đang dễ lặp — tổng quan, kết luận, luận điểm, bảng sao, dữ kiện năm — cần được rà lại để mỗi phần có một mục đích rõ. Nội dung sách chỉ hiện trên trang chính khi cần giải thích nhận định; đoạn trích dài nằm trong “Xem căn cứ”.



Giữ Streamlit và phong cách hiện có. Skill giao diện được dùng để kiểm tra thứ bậc nội dung, mật độ chữ, khả năng đọc và trạng thái tương tác.



Nghiệm thu bằng các thao tác thực tế: lập lá số, đổi năm, đổi mức đọc, mở lời giải thích, mở nguồn, hỏi theo chủ đề, thử lại khi lỗi và đọc trên điện thoại.



9\. P8 — Review, kiểm thử và phát hành từng phần



Bộ ca nghiệm thu cần bao gồm:

\- Lá số nhiều sao và Mệnh vô chính diệu.

\- Cung Mệnh trùng cung Thân.

\- Một sao trùng nhiều vai trò.

\- Cách cục đủ điều kiện và chỉ khớp một phần.

\- Dữ kiện thiếu hoặc nguồn diễn giải mâu thuẫn.

\- Giờ sinh không chắc chắn C/D.

\- Không có khóa AI, AI timeout, response sai cấu trúc.

\- Cache của hai mức đọc.

\- Đổi năm trong khi còn báo cáo cũ.

\- Thiếu file nguồn tham khảo trên môi trường triển khai.

Quy trình cho mỗi gói khi triển khai:

1\. Chốt tiêu chí nghiệm thu và viết test cần thiết.

2\. Implement.

3\. Chạy test liên quan.

4\. Review code, dữ liệu và nội dung.

5\. Chạy hồi quy theo quy trình repo trước khi đánh dấu hoàn thành.

6\. Với thay đổi UI, mở trình duyệt và kiểm tra ảnh ở ba kích thước.

7\. Commit và push riêng sau khi đạt kiểm tra.

Test giả lập AI kiểm chứng được luồng xử lý. Muốn nghiệm thu “luận giải sâu hơn” phải review thêm bài do AI thật tạo ra.



10\. Thứ tự triển khai và giới hạn phạm vi

Gói	Phụ thuộc	Khả năng làm song song

P1 — Cấu trúc dữ liệu, ca nghiệm thu	Bắt đầu	Làm trước

P2 — Chuẩn hóa nguồn	Cấu trúc từ P1	Có thể cùng P5

P3 — Nhận diện cách cục	P1, P2	Có thể cùng P4

P4 — Giải thích tín hiệu	P1, rà quy tắc hiện tại	Có thể cùng P3/P5

P5 — Lá số đầu trang	P1	Có thể cùng P2

P6 — Ba mức đọc, AI sâu	P2, P3, P4	Theo sau phần căn cứ

P7 — Tích hợp toàn trang	P4, P5, P6	Chuẩn bị bố cục sớm

P8 — Nghiệm thu tổng thể	Các gói trên	Review xuyên suốt, chốt cuối

