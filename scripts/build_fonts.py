"""Script to subset IBM Plex Sans fonts for KMS Tu Vi frontend.

Converts TTF fonts to woff2 with a compact charset covering:
- ASCII basic (32-126)
- Full Vietnamese accents (precomposed uppercase & lowercase, including Đ/đ/Ð)
- Typography punctuation and symbols
- Math/UI symbols and units

Target: Total base64 payload size of plex-400.woff2 + plex-600.woff2 <= 70 KB.
"""

from __future__ import annotations

import base64
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT_DIR = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT_DIR / "frontend" / "assets" / "fonts"

LATIN_BASIC = [chr(i) for i in range(32, 127)]
VN_LOWERCASE = (
    "aáàảãạăắằẳẵặâấầẩẫậ"
    "eéèẻẽẹêếềểễệ"
    "iíìỉĩị"
    "oóòỏõọôốồổỗộơớờởỡợ"
    "uúùủũụưứừửữự"
    "yýỳỷỹỵ"
    "đ"
)
VN_UPPERCASE = VN_LOWERCASE.upper() + "Ð"
PUNCTUATION_AND_SYMBOLS = "–—‘’“”„…•·°±×÷©®™→←↑↓↔✓✕%‰#@§☯★☆⚠≤≥✦\u00A0"

FULL_CHARSET = set(
    LATIN_BASIC
    + list(VN_LOWERCASE)
    + list(VN_UPPERCASE)
    + list(PUNCTUATION_AND_SYMBOLS)
)


def build_subset_font(
    input_ttf: Path,
    output_woff2: Path,
    charset: set[str],
) -> tuple[int, int]:
    """Subsets a TTF font and writes it out as woff2.

    Returns:
        (raw_bytes_len, base64_bytes_len)
    """
    font = TTFont(str(input_ttf))

    opts = subset.Options()
    opts.flavor = "woff2"
    opts.hinting = False
    opts.drop_tables += ["GPOS", "STAT", "gasp", "fpgm", "prep", "cvt "]
    opts.layout_features = ["ccmp", "liga", "locl"]

    sub = subset.Subsetter(options=opts)
    cmap = font.getBestCmap()
    unicodes = [ord(char) for char in charset if ord(char) in cmap]
    sub.populate(unicodes=unicodes)
    sub.subset(font)

    output_woff2.parent.mkdir(parents=True, exist_ok=True)
    font.save(str(output_woff2))

    raw_bytes = output_woff2.read_bytes()
    b64_bytes = base64.b64encode(raw_bytes)

    return len(raw_bytes), len(b64_bytes)


def build_all_fonts() -> dict[str, dict[str, int]]:
    """Builds plex-400.woff2 and plex-600.woff2."""
    weights = [400, 600]
    results: dict[str, dict[str, int]] = {}
    total_b64 = 0

    print("Subsetting IBM Plex Sans fonts for KMS Tu Vi...")
    for weight in weights:
        input_ttf = FONTS_DIR / f"IBMPlexSans-{weight}.ttf"
        output_woff2 = FONTS_DIR / f"plex-{weight}.woff2"

        if not input_ttf.exists():
            raise FileNotFoundError(f"Source font file not found: {input_ttf}")

        raw_len, b64_len = build_subset_font(input_ttf, output_woff2, FULL_CHARSET)
        results[f"plex-{weight}"] = {"raw": raw_len, "base64": b64_len}
        total_b64 += b64_len

        print(
            f"  - Weight {weight}: raw={raw_len:,} bytes, "
            f"base64={b64_len:,} bytes ({b64_len / 1024:.2f} KB) -> {output_woff2.name}"
        )

    print(
        f"Total base64 font payload: {total_b64:,} bytes "
        f"({total_b64 / 1024:.2f} KB) - Target: <= 71,680 bytes (70 KB)"
    )
    if total_b64 > 70 * 1024:
        raise ValueError(
            f"Font payload exceeds 70 KB: {total_b64 / 1024:.2f} KB > 70 KB"
        )
    print("SUCCESS: Font payload within budget!")
    return results


if __name__ == "__main__":
    build_all_fonts()
