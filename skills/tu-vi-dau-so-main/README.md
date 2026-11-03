# Tu Vi Dau So - Tử Vi Đẩu Số Skill

A Claude Code skill for reading and interpreting **Tử Vi Đẩu Số** (Purple Star Astrology / Zi Wei Dou Shu) — a classical East Asian astrology system.

## Overview

This project provides a Claude Code skill that enables Claude to:
- Construct a natal chart (lá số) from a person's birth date/time
- Calculate and place all stars across the 12 palaces
- Interpret the chart according to traditional Tử Vi principles
- Analyze fortune periods (đại hạn, tiểu hạn, lưu niên)

Based on the reference work **"Tử Vi Đẩu Số Toàn Tập"** (Thập Bát Phi Tinh), translated by Quách Ngọc Bội.

## Structure

```
tu-vi-dau-so/
└── skills/
    └── tu-vi-dau-so/
        ├── SKILL.md                          # Main skill definition
        └── references/
            ├── computation.md                # Star placement algorithms & lookup tables
            ├── star_meanings.md              # Meanings of the 14 main stars + auxiliaries
            └── cach_cuc_luan_giai.md         # Fortune/misfortune patterns & interpretations
```

## Usage

This skill is triggered automatically when a user asks about:
- Tử vi, đẩu số, lá số, xem mệnh
- Any of the 14 main stars (Tử Vi, Thiên Cơ, Thái Dương, Vũ Khúc, etc.)
- Birth date/time readings and fortune analysis
- Đại hạn, tiểu hạn, lưu niên (fortune periods)
- Tứ Hóa (Hóa Lộc, Hóa Quyền, Hóa Khoa, Hóa Kị)

### Required Input

To construct a full natal chart, Claude needs:
- **Year of birth** (can chi - 60-year cycle)
- **Month of birth** (lunar calendar)
- **Day of birth** (lunar calendar)
- **Hour of birth** (one of 12 earthly branches)
- **Gender** (affects fortune direction)

Solar calendar dates will be converted to lunar automatically.

## Key Concepts

| Concept | Description |
|---------|-------------|
| **14 Chính tinh** | 14 main stars (7 North Dipper + 7 South Dipper) |
| **Tứ Hóa** | 4 transformations: Lộc (wealth), Quyền (power), Khoa (fame), Kị (obstacles) |
| **Lục Cát tinh** | 6 auspicious auxiliary stars |
| **Tứ Sát tinh** | 4 malefic stars (Kình Dương, Đà La, Hỏa Tinh, Linh Tinh) |
| **Ngũ Hành Cục** | 5 elemental destiny types (Metal-4, Wood-3, Water-2, Fire-6, Earth-5) |
| **Tam phương tứ chính** | Reading a palace together with its trine + opposition |
| **Đại Hạn** | 10-year fortune cycle |
| **Tiểu Hạn / Lưu Niên** | Annual fortune cycle |

## Installation

Place the `skills/` directory in your Claude Code project or user skills directory, then configure it in your `.claude/settings.json`:

```json
{
  "skillPaths": ["./tu-vi-dau-so/skills"]
}
```

## License

For personal and educational use. Interpretations are for reference only and do not determine one's destiny.
