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
    return ""


EVIDENCE_LABELS = {
    "toa_thu": "Tọa thủ", "tam_hop": "Tam hợp", "xung_chieu": "Xung chiếu",
    "giap_cung": "Giáp cung", "tu_hoa": "Tứ hóa", "menh_cuc": "Mệnh – Cục",
    "van_han": "Vận hạn", "nghiem_ly": "Nghiệm lý", "truong_phai": "Trường phái",
    "suy_luan": "Suy luận",
}


def evidence_label(value) -> str:
    return EVIDENCE_LABELS.get(str(value or ""), "Chưa rõ loại")


def evidence_table(points, fact_map=None) -> str:
    """Bảng luận điểm 3 cột: luận điểm · dấu hiệu thuận · dấu hiệu nghịch."""
    fact_map = fact_map or {}
    rows = []
    for point in points or []:
        chips = "".join(
            f'<span class="evidence-chip">{text(evidence_label(label))}</span>'
            for label in point.get("loi_chung_cu") or []
        ) or '<span class="muted">—</span>'
        facts = [
            f"{fact_map[i]['sao']} tại {fact_map[i]['cung']}"
            for i in (point.get("fact_ids") or []) if i in fact_map
        ]
        refs = ", ".join(f"[{r}]" for r in (point.get("source_refs") or []))
        support = chips
        if facts:
            support += '<p class="evidence-facts">' + text("; ".join(facts)) + '</p>'
        if refs:
            support += '<p class="evidence-facts">Nguồn: ' + text(refs) + '</p>'
        counter = text(point.get("phan_chung") or "—")
        rows.append(
            '<tr>'
            f'<td>{confidence_badge(point.get("muc_tin_cay"))}'
            f'<p class="muted">Loại: {text({"cau_truc": "Cấu trúc", "thoi_diem": "Thời điểm"}.get(point.get("loai_ket_luan"), "Chưa phân loại"))}</p>'
            f'<p>{text(point.get("nhan_dinh"))}</p>'
            f'<p class="muted">Điều kiện / giới hạn: {text(point.get("gioi_han"))}</p></td>'
            f'<td>{support}</td>'
            f'<td>{counter}</td>'
            '</tr>'
        )
    return ('<table class="evidence-table"><thead><tr>'
            '<th>Luận điểm</th><th>Dấu hiệu thuận</th><th>Dấu hiệu nghịch</th>'
            '</tr></thead><tbody>' + "".join(rows) + '</tbody></table>')


def topic_panel(key: str, value: dict) -> str:
    if not isinstance(value, dict) or not value:
        return panel(TOPICS[key], '<p class="muted">Chưa có luận giải cho chủ đề này.</p>')
    body = "".join(f'<div class="reading-field"><h3>{label}</h3>{content(value.get(field))}</div>'
                   for field, label in FIELDS[key].items())
    if key=='van_han_hien_tai' and value.get('bang_kich_hoat'):
        body+=annual_activation_panel(value)
    return panel(TOPICS[key], body)


def annual_activation_panel(value: dict) -> str:
    body='<h3>Bảng kích hoạt bốn tầng</h3><p class="muted">Dữ kiện theo năm âm lịch; chưa phải kết luận sự kiện.</p>'
    for row in value.get('bang_kich_hoat',[]):
        layers=''
        for key,label in [('la_so_goc','Lá số gốc'),('dai_han','Đại hạn'),('luu_nien','Lưu niên'),('luu_nguyet','Lưu nguyệt')]:
            layer=row.get(key,{})
            layers+=f'<dt>{label}</dt><dd>{text(layer.get("noi_dung"))}<p class="muted">Fact: {text(", ".join(layer.get("fact_ids",[])) or "Chưa có")}</p></dd>'
        body+=f'<details class="annual-activation"><summary>{text(row.get("chu_de"))} · {confidence_badge(row.get("muc_tin_cay"))}</summary><dl>{layers}</dl><p>Phản chứng / giới hạn: {text(row.get("phan_chung"))}</p></details>'
    body+='<h3>So sánh năm trước / năm xem / năm sau</h3>'
    for year in value.get('so_sanh_nam',[]):
        body+=f'<details class="annual-activation"><summary>{text(year.get("year"))} · {text(year.get("can_chi") or "Ngoài phạm vi")}</summary><p>Đại hạn: {text(year.get("dai_han"))}</p><p>Tiểu hạn: {text(year.get("tieu_han"))}</p>{content(year.get("luu_tu_hoa"))}<p class="muted">{text(year.get("gioi_han"))}</p></details>'
    return body+'<h3>Chưa đủ căn cứ để kết luận</h3>'+content(value.get('viec_chua_du_can_cu'))


def palace_preview() -> str:
    """A labelled diagram, not a made-up chart or a sample personal reading."""
    labels = {(0, 0): "Tỵ", (0, 1): "Ngọ", (0, 2): "Mùi", (0, 3): "Thân",
              (1, 0): "Thìn", (1, 3): "Dậu", (2, 0): "Mão", (2, 3): "Tuất",
              (3, 0): "Dần", (3, 1): "Sửu", (3, 2): "Tý", (3, 3): "Hợi"}
    cells = "".join(f'<span class="map-cell" style="grid-area:{r+1}/{c+1}">{name}</span>' for (r, c), name in labels.items())
    return f'<div class="palace-preview" aria-label="Sơ đồ minh họa mười hai địa chi">{cells}<div class="map-center"><strong>12 cung</strong><span>Một bản đồ để chiêm nghiệm</span></div></div>'


def tu_hoa_table_caption(info: dict | None) -> str:
    if not info or not info.get('school'):
        return ''
    return f"Bảng Tứ Hóa: {info['school']}."


def annual_panel(annual: dict, luu_nien: dict | None = None) -> str:
    p = annual.get('tieu_han') or {}
    stars = ', '.join(f"{s['ten']} ({s['dac_tinh']})" for s in p.get('chinh_tinh', [])) or 'Vô chính diệu'
    risks = ', '.join(s['ten'] for s in p.get('risk_stars', [])) or 'Chưa có trong danh mục hiện tại'
    body = [
        f"<p>Tiểu hạn tại <strong>{text(p.get('ten'))} · {text(p.get('chuan_ten'))}</strong> · {text(annual.get('tuoi_am'))} tuổi âm.</p>"
        f"<p>Chính tinh gốc: {text(stars)}.<br>Nhóm cần lưu ý: {text(risks)}.</p>"
    ]
    if luu_nien:
        caption = tu_hoa_table_caption(luu_nien.get('tu_hoa_table'))
        if caption:
            body.append(f"<p class='muted'>{text(caption)}</p>")
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
        if can_luu_y:
            level = can_luu_y.get('level_label') or {
                'nhan': 'Thấp', 'vua': 'Vừa', 'nang': 'Cao', 'chua_du_du_lieu': 'Chưa đủ dữ liệu',
            }.get(can_luu_y.get('level'), '—')
            reason = can_luu_y.get('level_reason') or ''
            body.append(
                (f"<p class='muted'>{text(reason)}</p>" if reason else "")

            )
            roles = {'menh': 'Mệnh', 'than': 'Thân', 'dai_han': 'Đại hạn', 'tieu_han': 'Tiểu hạn'}
            rows = []
            for signal in can_luu_y.get('signals') or []:
                signal_roles = signal.get('vai_tro') or (
                    [signal.get('don_vai')] if signal.get('don_vai') else []
                )
                role_text = ', '.join(roles.get(role, role) for role in signal_roles) or '—'
                why = signal.get('vi_sao') or {}
                rule = why.get('quy_tac') or {}
                topics = ', '.join(why.get('chu_de') or []) or '—'
                missing = ' '.join(why.get('dieu_kien_thieu') or []) or '—'
                rows.append(
                    f"<details class='annual-signal'><summary>{text(signal.get('sao'))} tại "
                    f"{text(signal.get('cung_ten'))} · vai trò: {text(role_text)}</summary>"
                    f"<p>{text(why.get('giai_thich'))}</p>"
                    f"<p class='muted'>Quy tắc: {text(rule.get('id') or '—')} · "
                    f"Chủ đề: {text(topics)}</p>"
                    f"<p class='muted'>Còn thiếu: {text(missing)}</p></details>"
                )
            body.append(''.join(rows) if rows else
                        "<p class='muted'>Không có tín hiệu lưu niên trùng cung trọng tâm.</p>")
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
