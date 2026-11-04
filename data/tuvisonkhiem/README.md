# Thư Viện Tử Vi Sơn Khiêm (Data Archive)

Nguồn dữ liệu: [Thư viện Tử Vi Sơn Khiêm](https://tuvisonkhiem.vn/thu-vien/)  
Ngày cào: 2026-11-04 17:55:00  
Tổng số bài viết: 292

## Phân bổ dữ liệu
- **Thư viện sao (`tv_sao`):** 96 sao (chính tinh, phụ tinh, vòng Thái Tuế, vòng Bác Sĩ, Tứ Hóa, cách an sao, tính chất đắc hãm và khi vào 12 cung)
- **Từ điển thuật ngữ (`tv_thuat_ngu`):** 97 mục (các khái niệm cung, tam hợp, xung chiếu, tứ hóa, phi tinh...)
- **Cách cục Tử Vi (`tv_cach_cuc`):** 53 cách cục (các cách cục đắc cách, phá cách, tinh-vị, giáp cung...)
- **Thư viện sách (`tv_sach`):** 46 đầu sách cổ thư và tài liệu chuyên sâu

## Cấu trúc thư mục
```
data/tuvisonkhiem/
├── raw_json/
│   ├── tv_sao.json
│   ├── tv_thuat_ngu.json
│   ├── tv_cach_cuc.json
│   ├── tv_sach.json
│   └── taxonomies.json
├── markdown/
│   ├── sao/            # 96 file markdown
│   ├── thuat-ngu/      # 97 file markdown
│   ├── cach-cuc/       # 53 file markdown
│   └── sach/           # 46 file markdown
├── tuvisonkhiem_master.json # Toàn bộ 292 bài kèm metadata và markdown
└── README.md
```
