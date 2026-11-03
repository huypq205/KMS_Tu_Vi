# Tử Vi Đẩu Số - Skill cho Claude Code

Skill Claude Code để xem và luận giải **Tử Vi Đẩu Số** — hệ thống mệnh lý học cổ truyền phương Đông do Trần Đoàn (Hi Di) Lão Tổ sáng lập.

## Tổng quan

Skill này cho phép Claude thực hiện:
- Lập lá số từ ngày giờ sinh
- An sao vào 12 cung theo đúng quy tắc truyền thống
- Luận giải lá số theo các nguyên tắc Tử Vi cổ điển
- Phân tích vận hạn theo thời gian (đại hạn, tiểu hạn, lưu niên)

Dựa trên bộ sách tham khảo **"Tử Vi Đẩu Số Toàn Tập"** (Thập Bát Phi Tinh), bản dịch Quách Ngọc Bội.

## Cấu trúc thư mục

```
tu-vi-dau-so/
└── skills/
    └── tu-vi-dau-so/
        ├── SKILL.md                          # Định nghĩa skill chính
        └── references/
            ├── computation.md                # Thuật toán an sao & bảng tra cứu
            ├── star_meanings.md              # Ý nghĩa 14 chính tinh và phụ tinh
            └── cach_cuc_luan_giai.md         # Các cách cục phú quý/bần tiện
```

## Cách sử dụng

Skill tự động kích hoạt khi người dùng hỏi về:
- Tử vi, đẩu số, lá số, xem mệnh, xem số
- Bất kỳ sao nào trong 14 chính tinh (Tử Vi, Thiên Cơ, Thái Dương, Vũ Khúc, v.v.)
- Đọc vận theo ngày tháng năm giờ sinh
- Đại hạn, tiểu hạn, lưu niên
- Tứ Hóa (Hóa Lộc, Hóa Quyền, Hóa Khoa, Hóa Kị)

### Thông tin cần thiết để lập lá số

| Thông tin | Ghi chú |
|-----------|---------|
| **Năm sinh** | Can Chi (VD: Giáp Tý, Ất Sửu...) |
| **Tháng sinh** | Âm lịch |
| **Ngày sinh** | Âm lịch |
| **Giờ sinh** | Một trong 12 địa chi (Tý, Sửu, Dần...) |
| **Giới tính** | Ảnh hưởng chiều đi của đại hạn |

> Nếu người dùng cung cấp ngày dương lịch, Claude sẽ tự quy đổi sang âm lịch.

## Các khái niệm cốt lõi

### Hệ thống sao

| Nhóm | Nội dung |
|------|---------|
| **14 Chính tinh** | 7 sao Bắc Đẩu + 7 sao Nam Đẩu |
| **Lục Cát tinh** | Tả Phụ, Hữu Bật, Văn Xương, Văn Khúc, Thiên Khôi, Thiên Việt |
| **Tứ Sát tinh** | Kình Dương, Đà La, Hỏa Tinh, Linh Tinh |
| **Tứ Hóa** | Hóa Lộc (tài lộc), Hóa Quyền (quyền lực), Hóa Khoa (danh tiếng), Hóa Kị (trở ngại) |
| **Không Vong** | Địa Kiếp, Địa Không |

### 12 Cung

Mệnh · Huynh Đệ · Thê Thiếp · Tử Tức · Tài Bạch · Tật Ách · Thiên Di · Nô Bộc · Quan Lộc · Điền Trạch · Phúc Đức · Phụ Mẫu

### Nguyên tắc luận giải

- **Tam Yếu**: Mệnh – Thân – Hạn
- **Ngũ Hành Cục**: Kim Tứ (4), Mộc Tam (3), Thủy Nhị (2), Hỏa Lục (6), Thổ Ngũ (5)
- **Miếu Vượng / Hãm Địa**: Mức độ mạnh yếu của sao theo cung tọa thủ
- **Tam Phương Tứ Chính**: Luận một cung phải kết hợp tam hợp + đối xung
- **Đại Hạn**: Vận trình 10 năm, khởi từ cung Mệnh theo số Cục

## Cài đặt

Đặt thư mục `skills/` vào project Claude Code hoặc thư mục skills của người dùng, sau đó cấu hình trong `.claude/settings.json`:

```json
{
  "skillPaths": ["./tu-vi-dau-so/skills"]
}
```

## Lưu ý

Tử Vi Đẩu Số mang tính tham khảo. Luận giải luôn được trình bày theo hướng tích cực, nhân văn, khuyến khích hướng thiện — không phán đoán tuyệt đối hay gây lo lắng cho người dùng.
