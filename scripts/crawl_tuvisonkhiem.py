"""
Script cào và chuẩn hóa toàn bộ dữ liệu từ Thư viện Tử Vi Sơn Khiêm (https://tuvisonkhiem.vn/thu-vien/)
Lưu trữ vào thư mục data/tuvisonkhiem/ dưới dạng:
1. Raw JSON (theo từng endpoint và taxonomy)
2. Clean Markdown (theo từng thư mục sao, thuat-ngu, cach-cuc, sach)
3. Master JSON Index để tích hợp vào RAG / Vector DB / Search engine
"""

import os
import sys
import json
import html
import time
import urllib.request
from pathlib import Path
import html2text

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_API = "https://tuvisonkhiem.vn/wp-json/wp/v2"
OUTPUT_DIR = Path("data/tuvisonkhiem")
RAW_DIR = OUTPUT_DIR / "raw_json"
MD_DIR = OUTPUT_DIR / "markdown"

ENDPOINTS = {
    "tv_sao": {
        "folder": "sao",
        "label": "Thư viện sao",
        "tax_keys": {
            "tv_danh_muc": "danh_muc",
            "tv_nhom": "nhom",
            "tv_an_theo": "an_theo",
            "tv_nhom_tinh_chat": "tinh_chat"
        }
    },
    "tv_thuat_ngu": {
        "folder": "thuat-ngu",
        "label": "Từ điển thuật ngữ",
        "tax_keys": {
            "tv_chu_de": "chu_de"
        }
    },
    "tv_cach_cuc": {
        "folder": "cach-cuc",
        "label": "Cách cục Tử Vi",
        "tax_keys": {
            "tv_nhom_cach": "nhom_cach"
        }
    },
    "tv_sach": {
        "folder": "sach",
        "label": "Thư viện sách",
        "tax_keys": {
            "tv_phai": "phai"
        }
    }
}

TAXONOMIES = [
    "tv_danh_muc",
    "tv_nhom",
    "tv_an_theo",
    "tv_nhom_tinh_chat",
    "tv_chu_de",
    "tv_phai",
    "tv_nhom_cach"
]

def fetch_json(url: str):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_all_items(endpoint: str):
    items = []
    page = 1
    per_page = 100
    while True:
        url = f"{BASE_API}/{endpoint}?per_page={per_page}&page={page}"
        try:
            batch = fetch_json(url)
            if not batch:
                break
            items.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
            time.sleep(0.3)
        except urllib.error.HTTPError as e:
            if e.code == 400: # Exceeded total pages
                break
            raise
    return items

def get_html_converter():
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0
    h.unicode_snob = True
    h.single_line_break = False
    return h

def main():
    print("=== BẮT ĐẦU CÀO THƯ VIỆN TỬ VI SƠN KHIÊM ===")
    
    # Tạo thư mục
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    MD_DIR.mkdir(parents=True, exist_ok=True)
    for conf in ENDPOINTS.values():
        (MD_DIR / conf["folder"]).mkdir(parents=True, exist_ok=True)

    # 1. Cào Taxonomies
    print("\n1. Đang tải bảng phân loại (Taxonomies)...")
    taxonomy_maps = {} # tax_name -> {id: name}
    all_tax_terms = {}
    for tax in TAXONOMIES:
        url = f"{BASE_API}/{tax}?per_page=100"
        try:
            terms = fetch_json(url)
            all_tax_terms[tax] = terms
            taxonomy_maps[tax] = {t["id"]: t["name"] for t in terms}
            print(f" - {tax}: {len(terms)} terms")
        except Exception as e:
            print(f" [Lỗi khi tải taxonomy {tax}]: {e}")
            taxonomy_maps[tax] = {}

    with open(RAW_DIR / "taxonomies.json", "w", encoding="utf-8") as f:
        json.dump(all_tax_terms, f, ensure_ascii=False, indent=2)

    # 2. Cào các Post Type
    converter = get_html_converter()
    master_index = []
    summary_counts = {}

    for ep, conf in ENDPOINTS.items():
        folder_name = conf["folder"]
        label = conf["label"]
        print(f"\n2. Đang tải {label} ({ep})...")
        items = fetch_all_items(ep)
        summary_counts[label] = len(items)
        print(f" -> Đã lấy {len(items)} mục.")

        # Lưu Raw JSON
        with open(RAW_DIR / f"{ep}.json", "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        # Xử lý Markdown & Index
        for item in items:
            item_id = item.get("id")
            slug = item.get("slug")
            raw_title = item.get("title", {}).get("rendered", "")
            title = html.unescape(raw_title).strip()
            link = item.get("link", "")
            date = item.get("date", "")
            modified = item.get("modified", "")
            raw_content = item.get("content", {}).get("rendered", "")

            # Phân giải taxonomy IDs sang label
            tax_labels = {}
            for wp_tax_key, custom_key in conf["tax_keys"].items():
                ids = item.get(wp_tax_key, [])
                if isinstance(ids, list):
                    labels = [taxonomy_maps.get(wp_tax_key, {}).get(i, str(i)) for i in ids]
                    tax_labels[custom_key] = labels

            # Chuyển HTML sang Markdown
            md_content = converter.handle(raw_content).strip()

            # Tạo file markdown với frontmatter
            frontmatter_lines = [
                "---",
                f"id: {item_id}",
                f'title: "{title}"',
                f"slug: {slug}",
                f"category: {label}",
                f"endpoint: {ep}",
                f"link: {link}",
                f"date: {date}",
                f"modified: {modified}"
            ]
            if tax_labels:
                frontmatter_lines.append("taxonomies:")
                for k, v in tax_labels.items():
                    frontmatter_lines.append(f"  {k}: {json.dumps(v, ensure_ascii=False)}")
            frontmatter_lines.append("---\n")

            full_md = "\n".join(frontmatter_lines) + f"# {title}\n\n" + md_content + "\n"

            # Ghi file .md
            file_path = MD_DIR / folder_name / f"{slug}.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_md)

            # Thêm vào master index
            master_index.append({
                "id": item_id,
                "title": title,
                "slug": slug,
                "category": label,
                "endpoint": ep,
                "link": link,
                "date": date,
                "modified": modified,
                "taxonomies": tax_labels,
                "markdown_path": f"markdown/{folder_name}/{slug}.md",
                "content_markdown": md_content,
            })

    # 3. Ghi master index
    print("\n3. Ghi file Master Index...")
    with open(OUTPUT_DIR / "tuvisonkhiem_master.json", "w", encoding="utf-8") as f:
        json.dump(master_index, f, ensure_ascii=False, indent=2)

    # 4. Ghi README tóm tắt dataset
    readme_content = f"""# Thư Viện Tử Vi Sơn Khiêm (Data Archive)

Nguồn dữ liệu: [Thư viện Tử Vi Sơn Khiêm](https://tuvisonkhiem.vn/thu-vien/)  
Ngày cào: {time.strftime('%Y-%m-%d %H:%M:%S')}  
Tổng số bài viết: {len(master_index)}

## Phân bổ dữ liệu
- **Thư viện sao (`tv_sao`):** {summary_counts.get('Thư viện sao', 0)} sao (chính tinh, phụ tinh, vòng Thái Tuế, vòng Bác Sĩ, Tứ Hóa, cách an sao, tính chất đắc hãm và khi vào 12 cung)
- **Từ điển thuật ngữ (`tv_thuat_ngu`):** {summary_counts.get('Từ điển thuật ngữ', 0)} mục (các khái niệm cung, tam hợp, xung chiếu, tứ hóa, phi tinh...)
- **Cách cục Tử Vi (`tv_cach_cuc`):** {summary_counts.get('Cách cục Tử Vi', 0)} cách cục (các cách cục đắc cách, phá cách, tinh-vị, giáp cung...)
- **Thư viện sách (`tv_sach`):** {summary_counts.get('Thư viện sách', 0)} đầu sách cổ thư và tài liệu chuyên sâu

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
"""
    with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    print("\n=== HOÀN TẤT THÀNH CÔNG! ===")
    print(f"Tổng số bài viết: {len(master_index)}")
    for k, v in summary_counts.items():
        print(f" - {k}: {v} bài")
    print(f"Thư mục lưu trữ: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
