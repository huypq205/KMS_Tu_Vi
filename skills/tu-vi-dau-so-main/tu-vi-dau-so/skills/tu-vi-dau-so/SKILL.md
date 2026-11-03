---
name: tu-vi-dau-so
description: "Xem và luận giải Tử Vi Đẩu Số (Purple Star Astrology) - hệ thống chiêm tinh học cổ truyền phương Đông. Sử dụng skill này bất cứ khi nào người dùng hỏi về tử vi, lá số tử vi, xem mệnh, luận giải vận hạn, hỏi về các sao trong tử vi, cách cục, đại hạn, tiểu hạn, lưu niên, hoặc bất kỳ chủ đề nào liên quan đến Tử Vi Đẩu Số. Trigger khi người dùng nhắc đến: tử vi, đẩu số, lá số, xem mệnh, cung mệnh, sao tử vi, thiên cơ, thái dương, thái âm, vũ khúc, thiên đồng, liêm trinh, thiên phủ, tham lang, cự môn, thiên tướng, thiên lương, thất sát, phá quân, hóa lộc/quyền/khoa/kị, đại hạn, tiểu hạn, lưu niên, tam hợp, tứ chính, miếu vượng, hãm địa, cách cục, hoặc bất kỳ thuật ngữ tử vi nào khác. Cũng trigger khi người dùng cung cấp ngày tháng năm giờ sinh và muốn xem số."
---

# Tử Vi Đẩu Số - Hệ thống Luận giải

Dựa trên bộ sách "Tử Vi Đẩu Số Toàn Tập" (Thập Bát Phi Tinh), bản dịch Quách Ngọc Bội.

## Tổng quan

Tử Vi Đẩu Số là hệ thống mệnh lý học do Trần Đoàn (Hi Di) Lão Tổ sáng lập, dựa trên vị trí các sao trên bầu trời để suy đoán mệnh vận con người. Chỉ cần 4 yếu tố: **Năm, Tháng, Ngày, Giờ sinh** (âm lịch).

## Quy trình xem Tử Vi

### Bước 1: Thu thập thông tin
Cần biết chính xác: Năm sinh (Can Chi), Tháng sinh (âm lịch), Ngày sinh (âm lịch), Giờ sinh (12 chi), Giới tính (Nam/Nữ). Nếu người dùng cho dương lịch, cần đổi sang âm lịch.

### Bước 2: Lập lá số (An sao)
Đọc file `references/computation.md` để thực hiện từng bước tính toán.

Thứ tự an sao:
1. Xác định Thiên Can, Địa Chi năm sinh → Âm Dương Nam Nữ
2. An Mệnh, An Thân
3. Bài bố 12 cung (Mệnh, Huynh Đệ, Thê Thiếp, Tử Tức, Tài Bạch, Tật Ách, Thiên Di, Nô Bộc, Quan Lộc, Điền Trạch, Phúc Đức, Phụ Mẫu)
4. Định Ngũ Hành Cục (Kim 4, Mộc 3, Thủy 2, Hỏa 6, Thổ 5)
5. An Tử Vi → An 13 sao Bắc Đẩu (nghịch): Tử Vi, Thiên Cơ, (cách 1) Thái Dương, Vũ Khúc, Thiên Đồng, (cách 2) Liêm Trinh
6. An Thiên Phủ → An 13 sao Nam Đẩu (thuận): Thiên Phủ, Thái Âm, Tham Lang, Cự Môn, Thiên Tướng, Thiên Lương, Thất Sát, (cách 3) Phá Quân
7. An Tả Phụ, Hữu Bật (theo tháng sinh)
8. An Văn Xương, Văn Khúc (theo giờ sinh)
9. An Địa Kiếp, Địa Không (theo giờ sinh)
10. An Tứ Hóa: Lộc, Quyền, Khoa, Kị (theo Can năm sinh)
11. An Thiên Khôi, Thiên Việt (theo Can năm sinh)
12. An Lộc Tồn, Kình Dương, Đà La (theo Can năm sinh)
13. An Hỏa Tinh, Linh Tinh (theo Chi năm sinh + giờ)
14. An các sao phụ: Thiên Mã, Hồng Loan, Thiên Hỉ, Thiên Hình, Thiên Diêu, etc.
15. An vòng Tràng Sinh (theo Cục)
16. An vòng Thái Tuế, vòng Bác Sĩ
17. Định Đại Hạn, Tiểu Hạn

### Bước 3: Luận giải
Đọc file `references/star_meanings.md` và `references/cach_cuc_luan_giai.md` để tra cứu ý nghĩa.

## Nguyên tắc Luận giải Cốt lõi

### 1. Tam Yếu: Mệnh - Thân - Hạn
- **Mệnh**: Bản chất, tính cách, tiềm năng bẩm sinh
- **Thân**: Hành động, hướng phát triển thực tế (sau 30 tuổi xem Thân là chính)
- **Hạn**: Vận may rủi theo từng giai đoạn (Đại hạn 10 năm, Tiểu hạn 1 năm, Lưu niên)

**"Mệnh hảo, Thân hảo, Hạn hảo → đáo lão vinh xương. Mệnh suy, Thân suy, Hạn suy → chung thân khất cái."**

### 2. Miếu Vượng vs Hãm Địa
Mỗi sao có cung miếu (mạnh nhất), vượng, đắc địa, bình, hãm (yếu nhất). Sao miếu vượng phát huy tốt, hãm địa thì xấu hoặc bất lực.

### 3. Ngũ Hành Sinh Khắc
- Tương sinh: Kim→Thủy→Mộc→Hỏa→Thổ→Kim
- Tương khắc: Kim→Mộc→Thổ→Thủy→Hỏa→Kim
- Cục khắc Mệnh → xấu; Cục sinh Mệnh → tốt

### 4. Tam Phương Tứ Chính
Luận giải luôn xem **tam hợp** (3 cung cách nhau 4 cung: Dần-Ngọ-Tuất, Tị-Dậu-Sửu, Thân-Tý-Thìn, Hợi-Mão-Mùi) và **đối cung** (xung chiếu). Một cung được đánh giá bởi cả sao tọa thủ VÀ sao tam hợp chiếu + đối xung chiếu.

### 5. Phân loại sao

**14 Chính tinh**: Tử Vi, Thiên Cơ, Thái Dương, Vũ Khúc, Thiên Đồng, Liêm Trinh, Thiên Phủ, Thái Âm, Tham Lang, Cự Môn, Thiên Tướng, Thiên Lương, Thất Sát, Phá Quân

**Lục Cát tinh**: Tả Phụ, Hữu Bật, Văn Xương, Văn Khúc, Thiên Khôi, Thiên Việt

**Tứ Sát tinh**: Kình Dương, Đà La, Hỏa Tinh, Linh Tinh

**Tứ Hóa**: Hóa Lộc (tài lộc), Hóa Quyền (quyền lực), Hóa Khoa (danh tiếng), Hóa Kị (trở ngại)

**Không Vong**: Địa Kiếp, Địa Không (phá hoại, trống rỗng)

### 6. Bảng Tứ Hóa theo Can năm sinh
```
Giáp: Liêm-Lộc, Phá-Quyền, Vũ-Khoa, Dương-Kị
Ất:   Cơ-Lộc,   Lương-Quyền, Vi(Tử Vi)-Khoa, Nguyệt-Kị  
Bính: Đồng-Lộc, Cơ-Quyền,   Xương-Khoa, Liêm-Kị
Đinh: Nguyệt-Lộc, Đồng-Quyền, Cơ-Khoa,  Cự-Kị
Mậu: Tham-Lộc, Nguyệt-Quyền, Bật-Khoa, Cơ-Kị
Kỷ:   Vũ-Lộc,   Tham-Quyền,  Lương-Khoa, Khúc-Kị
Canh: Nhật-Lộc, Vũ-Quyền,    Âm-Khoa,   Đồng-Kị
Tân:  Cự-Lộc,   Dương-Quyền, Khúc-Khoa, Xương-Kị
Nhâm: Lương-Lộc, Tử(Vi)-Quyền, Tả-Khoa,  Vũ-Kị
Quý:  Phá-Lộc,   Cự-Quyền,   Âm-Khoa,   Tham-Kị
```

### 7. Các Cách cục quan trọng (Quý cách)
Đọc chi tiết tại `references/cach_cuc_luan_giai.md`. Một số cách chính:

- **Tử Phủ đồng cung**: Phú quý trọn đời
- **Nhật lệ trung thiên**: Thái Dương cư Ngọ → quyền quý cực cao
- **Nguyệt lãng thiên môn**: Thái Âm cư Hợi → đại phú đại quý  
- **Cơ Nguyệt Đồng Lương**: Hợp làm công chức, lại nhân
- **Tham Vũ đồng hành**: Uy trấn biên cương, võ tướng
- **Cự Nhật đồng cung (Dần)**: Quan phong tam đại
- **Sát Phá Liêm Tham**: Miếu → đứng đầu ba quân; Hãm → hung hiểm
- **Phủ Tướng triều viên**: Thực lộc vạn chung
- **Minh châu xuất hải**: Nguyệt ở Hợi chiếu Mệnh Mùi
- **Khoa Quyền Lộc hội**: Danh dự chiêu chương
- **Giáp Quý/Giáp Lộc/Giáp Quyền/Giáp Khoa**: Cực quý

### 8. Luận 12 Cung

| Cung | Luận về |
|------|---------|
| **Mệnh** | Tính cách, tướng mạo, bản chất con người |
| **Huynh Đệ** | Anh chị em, bạn bè thân |
| **Thê Thiếp** (Phu Thê) | Hôn nhân, vợ/chồng |
| **Tử Tức** | Con cái |
| **Tài Bạch** | Tiền tài, tài chính |
| **Tật Ách** | Sức khỏe, bệnh tật |
| **Thiên Di** | Đi xa, quan hệ xã hội |
| **Nô Bộc** (Giao Hữu) | Bạn bè, cấp dưới, người giúp việc |
| **Quan Lộc** | Sự nghiệp, công danh |
| **Điền Trạch** | Nhà cửa, bất động sản |
| **Phúc Đức** | Phúc phần, tuổi thọ, đời sống tinh thần |
| **Phụ Mẫu** (Tướng Mạo) | Cha mẹ, tướng mạo ngoại hình |

### 9. Luận Đại Hạn (10 năm)
- Khởi từ cung Mệnh, theo số Cục (VD: Kim Tứ Cục → bắt đầu 4 tuổi)
- Dương Nam / Âm Nữ: đi thuận
- Âm Nam / Dương Nữ: đi nghịch  
- Mỗi cung 10 năm. Xem sao tại cung hạn + tam hợp + đối cung

### 10. Luận Lưu Niên
- Theo Chi của năm hiện tại → cung Thái Tuế
- Xem sao tại cung lưu niên + lưu sát + tương tác với đại hạn

## Hướng dẫn Luận giải Chi tiết

### Khi xem tổng quát lá số:
1. Xem **cung Mệnh**: Chính tinh nào? Miếu hay Hãm? Có cát tinh hay sát tinh?
2. Xem **cung Thân**: Ở cung nào? Sao gì?
3. Xem **tam phương tứ chính** của Mệnh
4. Xem **Phúc Đức** (rất quan trọng - "Đệ nhất tiên khán Phúc Đức")
5. Xem **Thiên Di** ("Tái tam tế khảo Thiên Di")
6. Xem từng cung theo nhu cầu (Tài Bạch, Quan Lộc, Phu Thê...)
7. Xem Đại Hạn hiện tại và Lưu Niên

### Nguyên tắc vàng:
- **"Tinh luận miếu vượng tối phạ Không Vong"** - Sao miếu vượng rất sợ Không Vong
- **"Sát lạc Không Vong cánh vô uy lực"** - Sát tinh gặp Không Vong thì hết uy lực
- **"Nhật Nguyệt tối hiềm phản bối"** - Nhật Nguyệt rất ghét lạc hãm
- **"Lộc Mã tối hỉ giao trì"** - Lộc Mã rất mừng gặp nhau
- **"Mệnh vô chính diệu, yểu chiết cô bần"** - Mệnh không chính tinh: nghèo khổ, chết non
- **"Đệ nhất tiên khán Phúc Đức"** - Trước tiên xem Phúc Đức

## Files tham khảo

| File | Nội dung | Khi nào đọc |
|------|----------|-------------|
| `references/computation.md` | Thuật toán an sao, bảng tra cứu Cục, bảng an Tử Vi, Lộc Tồn, Khôi Việt, etc. | Khi cần lập lá số từ ngày sinh |
| `references/star_meanings.md` | Ý nghĩa 14 chính tinh + phụ tinh, tính cách, hình tướng, luận từng cung | Khi cần luận giải chi tiết ý nghĩa sao |
| `references/cach_cuc_luan_giai.md` | Các cách cục phú quý/bần tiện, Cốt Tủy Phú, luận hạn, đắc địa/thất hãm | Khi cần đánh giá cách cục, phú quý/bần tiện |

## Lưu ý quan trọng khi luận giải

1. **Luôn xem tổng thể** - không bao giờ kết luận chỉ dựa trên 1 sao hay 1 cung
2. **Cân nhắc miếu/hãm** - cùng 1 sao nhưng ở cung khác nhau thì ý nghĩa rất khác
3. **Xem tam phương tứ chính** - 1 cung phải xem cả 3 cung tam hợp + đối cung
4. **Phân biệt nam/nữ** - nhiều sao và cách cục luận khác nhau cho nam và nữ
5. **Sinh khắc chế hóa** - không chỉ xem từng sao mà phải xem tương tác ngũ hành
6. **Hạn vận kết hợp** - Mệnh tốt mà Hạn xấu vẫn gặp khó; Mệnh xấu mà Hạn tốt có thể phát
7. **Tránh phán đoán tuyệt đối** - Tử vi chỉ mang tính tham khảo, không quyết định cuộc đời
8. **Nhân văn và đạo đức** - Khi luận giải, luôn giữ thái độ tích cực, nhân văn, khuyến khích hướng thiện

## Cách trình bày khi luận giải cho người dùng

1. Tóm tắt thông tin lá số (cung Mệnh, chính tinh, Cục, Thân ở đâu)
2. Phân tích tính cách và tiềm năng (cung Mệnh)
3. Phân tích các lĩnh vực được hỏi (tài chính, sự nghiệp, tình cảm...)
4. Phân tích vận hạn hiện tại (nếu được hỏi)
5. Tổng kết và lời khuyên tích cực
