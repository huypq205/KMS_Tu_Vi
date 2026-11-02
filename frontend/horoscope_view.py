"""Presentation helpers; no Streamlit state, vendor engine or network imports."""
from datetime import date
from html import escape

TOPICS = {
    "su_nghiep": "Sự nghiệp", "tai_chinh": "Tài chính",
    "tinh_cam": "Tình cảm", "van_han_hien_tai": "Vận trình",
}
# Câu hỏi gợi ý cho ô "Hỏi nhanh có đáp · kèm nguồn sách" trong từng tab chủ đề.
ASK_SUGGESTIONS = {
    "su_nghiep": ["Năm nay có cơ hội đổi việc không?", "Nên theo hướng nào?"],
    "tai_chinh": ["Có giàu không?", "Năm nay nên chú ý khoản nào?"],
    "tinh_cam": ["Năm nay có người tìm hiểu không?", "Kiểu người nào hợp với mình?"],
    "van_han_hien_tai": ["Năm nay nên chú ý điều gì?", "Cần chuẩn bị gì cho năm tới?"],
}
# Nhãn mức căn cứ của câu trả lời hỏi nhanh.
ASK_LABELS = {
    "dau_hieu_ro": "Dấu hiệu rõ theo dữ kiện & nguồn",
    "dau_hieu_yeu": "Dấu hiệu yếu · cần cân nhắc",
    "chua_du_can_cu": "Chưa đủ căn cứ từ nguồn đã lấy",
}
BOOKS = {"NPL": "Nguyễn Phát Lộc", "BD": "Tử Vi Ứng Dụng — Bửu Đình", "DAU": "Tử Vi Đẩu Số Toàn Thư"}
HOURS = ["Tý · 23:00–01:00", "Sửu · 01:00–03:00", "Dần · 03:00–05:00", "Mão · 05:00–07:00",
         "Thìn · 07:00–09:00", "Tỵ · 09:00–11:00", "Ngọ · 11:00–13:00", "Mùi · 13:00–15:00",
         "Thân · 15:00–17:00", "Dậu · 17:00–19:00", "Tuất · 19:00–21:00", "Hợi · 21:00–23:00"]
FIELDS = {
    "su_nghiep": {"phong_cach_lam_viec": "Cách làm việc", "moi_truong_phu_hop": "Môi trường phù hợp",
                  "nghe_nghiep_tuong_hop": "Hướng nghề nghiệp", "loi_khuyen_phat_trien": "Gợi ý phát triển"},
    "tai_chinh": {"tu_duy_tien_bac": "Tư duy tiền bạc", "co_hoi_tich_luy": "Cơ hội tích lũy",
                  "rui_ro_can_phong": "Điều cần cân nhắc", "loi_khuyen_quan_ly_tai_chinh": "Gợi ý quản lý"},
    "tinh_cam": {"xu_huong_tinh_cam": "Cách kết nối", "mau_nguoi_tuong_hop": "Sự đồng điệu",
                 "bi_quyet_hoa_hop": "Gợi ý vun đắp"},
    "van_han_hien_tai": {"giai_doan": "Giai đoạn hiện tại", "chu_de_trong_tam": "Trọng tâm",
                          "co_hoi_nen_nam_bat": "Cơ hội học hỏi", "thach_thuc_can_can_trong": "Điều cần chú ý"},
}


def validate_birth_date(day: int, month: int, year: int, solar: bool) -> str | None:
    if solar:
        try:
            birth = date(year, month, day)
        except ValueError:
            return "Ngày sinh không tồn tại trong dương lịch. Hãy kiểm tra ngày, tháng và năm."
        if birth > date.today():
            return "Ngày sinh cần là hôm nay hoặc một ngày trong quá khứ."
    elif day > 30:
        return "Tháng âm lịch chỉ có 29 hoặc 30 ngày. Hãy kiểm tra lại ngày sinh."
    return None


def text(value) -> str:
    return escape(str(value)) if value is not None and value != "" else "—"


def content(value) -> str:
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{text(item)}</li>" for item in value) + "</ul>" if value else '<p class="muted">Chưa có nội dung.</p>'
    return f"<p>{text(value)}</p>"


def panel(title: str, body: str, extra_class: str = "") -> str:
    return f'<section class="reading-panel {extra_class}"><h2>{text(title)}</h2>{body}</section>'


CONFIDENCE_LABELS = {
    "rat_manh": ("Rất mạnh", "conf-rat-manh"),
    "manh": ("Mạnh", "conf-manh"),
    "trung_binh": ("Trung bình", "conf-trung-binh"),
    "yeu": ("Yếu", "conf-yeu"),
}


def confidence_badge(level) -> str:
    """Nhãn bậc tin cậy per kết luận; bậc lạ hiển thị trung tính, không đoán."""
    label, css = CONFIDENCE_LABELS.get(str(level or ""), ("Chưa rõ bậc", "conf-yeu"))
    return f'<span class="conf-badge {css}">Tin cậy: {text(label)}</span>'


def topic_panel(key: str, value: dict) -> str:
    if not isinstance(value, dict) or not value:
        return panel(TOPICS[key], '<p class="muted">Chưa có luận giải cho chủ đề này.</p>')
    body = "".join(f'<div class="reading-field"><h3>{label}</h3>{content(value.get(field))}</div>'
                   for field, label in FIELDS[key].items())
    return panel(TOPICS[key], body)


def palace_preview() -> str:
    """A labelled diagram, not a made-up chart or a sample personal reading."""
    labels = {(0, 0): "Tỵ", (0, 1): "Ngọ", (0, 2): "Mùi", (0, 3): "Thân",
              (1, 0): "Thìn", (1, 3): "Dậu", (2, 0): "Mão", (2, 3): "Tuất",
              (3, 0): "Dần", (3, 1): "Sửu", (3, 2): "Tý", (3, 3): "Hợi"}
    cells = "".join(f'<span class="map-cell" style="grid-area:{r+1}/{c+1}">{name}</span>' for (r, c), name in labels.items())
    return f'<div class="palace-preview" aria-label="Sơ đồ minh họa mười hai địa chi">{cells}<div class="map-center"><strong>12 cung</strong><span>Một bản đồ để chiêm nghiệm</span></div></div>'


def annual_panel(annual: dict, luu_nien: dict | None = None) -> str:
    p = annual.get('tieu_han') or {}
    stars = ', '.join(f"{s['ten']} ({s['dac_tinh']})" for s in p.get('chinh_tinh', [])) or 'Vô chính diệu'
    risks = ', '.join(s['ten'] for s in p.get('risk_stars', [])) or 'Chưa có trong danh mục hiện tại'
    body = [
        f"<p>Tiểu hạn tại <strong>{text(p.get('ten'))} · {text(p.get('chuan_ten'))}</strong> · {text(annual.get('tuoi_am'))} tuổi âm.</p>"
        f"<p>Chính tinh gốc: {text(stars)}.<br>Nhóm cần lưu ý: {text(risks)}.</p>"
    ]
    if luu_nien:
        thai_tue = luu_nien.get('thai_tue') or {}
        vong = luu_nien.get('vong_thai_tue') or {}
        cat = [name for name, entry in vong.items() if entry.get('loai') == 'cat']
        hung = [name for name, entry in vong.items() if entry.get('loai') == 'hung']
        body.append(
            f"<p><strong>Lưu niên {text(luu_nien.get('can_chi'))}</strong>: Thái Tuế tại cung "
            f"{text(thai_tue.get('cung_ten'))} · {text(thai_tue.get('dia_chi'))}.<br>"
            f"Sao cát trong vòng Tuế: {text(', '.join(cat))}.<br>"
            f"Sao cần lưu ý: {text(', '.join(hung))}.</p>"
        )
        hoa = luu_nien.get('luu_tu_hoa') or []
        hoa_text = ' · '.join(
            f"{x.get('ten', '')}: {x.get('ten_sao', '')} → cung {x.get('cung_ten', '')}" for x in hoa
        ) or 'Chưa xác định'
        body.append(f"<p>Lưu Tứ Hóa theo can năm: {text(hoa_text)}.</p>")
        can_luu_y = luu_nien.get('can_luu_y') or {}
        level = {'nhan': 'nhẹ', 'vua': 'vừa', 'nang': 'nặng'}.get(can_luu_y.get('level'), '—')
        roles = {'menh': 'Mệnh', 'than': 'Thân', 'dai_han': 'đại hạn', 'tieu_han': 'tiểu hạn'}
        hits = '; '.join(
            f"{hit.get('sao', '')} tại {hit.get('cung_ten', '')} ({roles.get(hit.get('don_vai'), hit.get('don_vai'))})"
            for hit in can_luu_y.get('hits', [])
        ) or 'không có sao lưu niên trùng cung trọng tâm'
        body.append(f"<p>Mức cần lưu ý: <strong>{text(level)}</strong> · {text(hits)}.</p>")
        body.append(f"<p class='muted'>{text(luu_nien.get('limitations'))}</p>")
    body.append(f"<p class='muted'>{text(annual.get('limitations'))}</p>")
    return panel(f"Năm {annual.get('year', '—')} · {annual.get('can_chi', '')}", ''.join(body))


def star_table(facts: list[dict]) -> str:
    headings = ['Sao', 'Cung · địa chi', 'Trạng thái', 'Phạm vi', 'Tuần / Triệt', 'Nguồn nhắc tên']
    rows = []
    for f in facts:
        cells = [f['sao'], f"{f['cung']} · {f['dia_chi']}", f['dac_tinh'],
                 ', '.join(f['roles']) or 'Lá số gốc',
                 ', '.join(n for key, n in [('tuan', 'Tuần'), ('triet', 'Triệt')] if f[key]) or '—',
                 ', '.join(f'[{r}]' for r in f['source_refs']) or 'Chưa có']
        rows.append('<tr>' + ''.join(f'<td data-label="{text(label)}">{text(value)}</td>' for label, value in zip(headings, cells)) + '</tr>')
    return '<div class="star-table-wrap" tabindex="0" aria-label="Danh sách sao và dữ kiện"><table class="star-table"><thead><tr>' + ''.join(f'<th scope="col">{h}</th>' for h in headings) + '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
