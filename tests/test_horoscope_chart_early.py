# -*- coding: utf-8 -*-
"""P5 (Plan_Fix_Mai_Anh_v2 §8): Lá số lên đầu trang, danh mục sao dùng chung,

sự kiện sớm chart_ready và responsive 12 cung.
"""
from __future__ import annotations

import json
from unittest.mock import Mock, patch
import pytest

from backend.app.schemas.horoscope import HoroscopeRequest
from backend.app.services.horoscope_features import generate_raw_horoscope
from backend.app.services.star_classification import (
    CHINH_TINH_IDS,
    TU_HOA_IDS,
    CAT_TINH_IDS,
    HUNG_TINH_IDS,
    GROUP_CHINH_TINH,
    GROUP_TU_HOA,
    GROUP_CAT_TINH,
    GROUP_HUNG_TINH,
    GROUP_KHAC,
    classify_star,
    partition_palace_stars,
)
from frontend.laso_renderer import luoi_html, danh_sach_html, render_laso


def _sample_request():
    return HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock")


def test_p5_tc01_all_vendor_stars_classified_into_disjoint_groups():
    """P5.TC-01: Toàn bộ sao trong vendor catalog phải được phân loại vào đúng 1

    trong 5 nhóm; các nhóm là rời nhau, không giao nhau.
    """
    assert len(CHINH_TINH_IDS) == 14
    assert len(TU_HOA_IDS) == 4
    # Không giao nhau giữa các tập ID
    assert CHINH_TINH_IDS.isdisjoint(TU_HOA_IDS)
    assert CHINH_TINH_IDS.isdisjoint(CAT_TINH_IDS)
    assert CHINH_TINH_IDS.isdisjoint(HUNG_TINH_IDS)
    assert TU_HOA_IDS.isdisjoint(CAT_TINH_IDS)
    assert TU_HOA_IDS.isdisjoint(HUNG_TINH_IDS)
    assert CAT_TINH_IDS.isdisjoint(HUNG_TINH_IDS)


def test_p5_tc02_tu_hoa_and_chinh_tinh_have_distinct_identities():
    """P5.TC-02: Tứ Hóa và chính tinh giữ nhận diện riêng; không ép vào cát tinh

    hay hung tinh (P5 §8.2).
    """
    # 4 Hóa tinh
    for sid in (92, 93, 94, 95):
        grp = classify_star({"saoID": sid, "saoTen": "Test"})
        assert grp == GROUP_TU_HOA, f"Star ID {sid} phải thuộc nhóm tu_hoa, không được là {grp}"

    # 14 Chính tinh
    for sid in range(1, 15):
        grp = classify_star({"saoID": sid, "saoTen": "Chính", "saoLoai": 1})
        assert grp == GROUP_CHINH_TINH


def test_p5_tc03_partition_palace_stars_preserves_every_single_star():
    """P5.TC-03: Đủ 12 cung, không mất hoặc nhân đôi sao khi phân nhóm (P5 §8.4).

    Tổng số sao hiển thị trong mỗi cung đúng bằng tổng số sao đầu vào.
    """
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    cungs = raw["thap_ni_cung"]
    assert len(cungs) == 12

    for cung in cungs:
        saos = cung.get("saos", [])
        part = partition_palace_stars(saos)
        # Tổng số sao sau khi phân nhóm phải đúng bằng số sao ban đầu
        total_partitioned = (
            len(part[GROUP_CHINH_TINH])
            + len(part[GROUP_TU_HOA])
            + len(part[GROUP_CAT_TINH])
            + len(part[GROUP_HUNG_TINH])
            + len(part[GROUP_KHAC])
        )
        assert total_partitioned == len(saos), (
            f"Cung {cung.get('ten_cung')}: đầu vào {len(saos)} sao, "
            f"phân nhóm được {total_partitioned} sao (bị mất hoặc nhân đôi)"
        )


def test_p5_tc04_tuan_triet_and_luu_nien_stars_rendered_distinctly():
    """P5.TC-04: Thể hiện riêng Tuần, Triệt, Tứ Hóa và dấu hiệu sao lưu niên (P5 §8.2)."""
    cell = {
        "cung_so": 1,
        "chuan_ten": "Tý",
        "hanh_cung": "Thủy",
        "ten_cung": "Mệnh",
        "co_thanh": False,
        "tu_dai_han": 25,
        "tuan_trung": True,
        "triet_lo": True,
        "saos": [
            {"saoID": 1, "saoTen": "Tử Vi", "saoLoai": 1, "saoDacTinh": "V"},
            {"saoID": 94, "saoTen": "Hóa Lộc", "saoLoai": 3},
            {"saoID": 57, "saoTen": "Văn Xương", "saoLoai": 6},
            {"saoID": 51, "saoTen": "Đà La", "saoLoai": 11},
        ],
    }
    luu_nien_saos = [
        {"sao": "Thái Tuế", "dia_chi": "Tý", "vai_tro": ["Mệnh"], "loai": "hung"}
    ]
    html = luoi_html([cell], luu_nien_by_cung={1: luu_nien_saos})

    # Tuần & Triệt có nhãn/badge riêng
    assert "Tuần" in html
    assert "Triệt" in html
    # Tứ hóa có nhận diện riêng
    assert "Hóa Lộc" in html
    # Chính tinh có đắc tính
    assert "Tử Vi" in html
    assert "V" in html
    # Sao lưu niên có dấu hiệu phân biệt
    assert "Thái Tuế" in html


def test_p5_tc05_reading_events_yields_chart_ready_early():
    """P5.TC-05: Sự kiện sớm chart_ready được phát ngay sau khi tính lá số,

    trước khi gọi RAG retrieval hoặc LLM interpretation (P5 §8.2).
    """
    from backend.app.services.horoscope_service import reading_events

    req = _sample_request()
    events = list(reading_events(req))
    event_types = [e.get("event") for e in events]

    assert "chart_ready" in event_types, "reading_events phải phát sự kiện chart_ready"
    idx_chart = event_types.index("chart_ready")
    idx_result = event_types.index("result")
    assert idx_chart < idx_result, "chart_ready phải được phát trước result"

    # chart_ready mang đủ dữ liệu để vẽ lá số
    chart_evt = events[idx_chart]
    assert "report" in chart_evt
    rep = chart_evt["report"]
    assert len(rep["la_so"]["thap_ni_cung"]) == 12
    assert "thong_tin_co_ban" in rep
    assert "palaces" in rep
    assert "annual" in rep


def test_p5_tc06_renderer_supports_grid_and_list_mode_for_responsive():
    """P5.TC-06: Renderer hỗ trợ cả 2 chế độ: lưới 4x4 (desktop) và danh sách (phone)

    với đầy đủ 12 cung (P5 §8.3).
    """
    raw = generate_raw_horoscope(15, 8, 1995, 5, 1, True)
    cungs = raw["thap_ni_cung"]

    grid_out = render_laso(cungs, che_do="luoi")
    assert 'class="grid"' in grid_out or 'class="horoscope-grid"' in grid_out
    for c in cungs:
        assert c["chuan_ten"] in grid_out

    list_out = render_laso(cungs, che_do="danh_sach")
    assert 'class="danh-sach"' in list_out or 'class="horoscope-list"' in list_out
    for c in cungs:
        assert c["chuan_ten"] in list_out


def test_p5_tc07_chart_intact_when_ai_fails_or_times_out():
    """P5.TC-07: AI chậm hoặc lỗi, người dùng vẫn xem được lá số hoàn chỉnh (P5 §8.4)."""
    from backend.app.services.horoscope_service import reading_events

    req = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="auto")
    with patch("backend.app.services.horoscope_service.interpret_horoscope") as mock_interp:
        # Giả lập interpret_horoscope raise exception hoặc fallback
        mock_interp.side_effect = Exception("AI Timeout")
        events = list(reading_events(req))

    event_types = [e.get("event") for e in events]
    assert "chart_ready" in event_types, "chart_ready vẫn phải phát thành công dù AI lỗi sau đó"
    chart_event = next(e for e in events if e.get("event") == "chart_ready")
    assert len(chart_event["report"]["la_so"]["thap_ni_cung"]) == 12


def test_p5_tc08_consistent_chart_across_three_reading_modes():
    """P5.TC-08: Cùng đầu vào -> cùng vị trí sao ở cả 3 mức đọc (P5 §8.4)."""
    from backend.app.services.horoscope_service import read_horoscope

    req_du_lieu = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock", reading_mode="du_lieu")
    req_giai_thich = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock", reading_mode="giai_thich")
    req_chuyen_sau = HoroscopeRequest(ngay=15, thang=8, nam=1995, chi_gio=5, provider="mock", reading_mode="chuyen_sau")

    rep1 = read_horoscope(req_du_lieu)
    rep2 = read_horoscope(req_giai_thich)
    rep3 = read_horoscope(req_chuyen_sau)

    saos1 = [c["saos"] for c in rep1["la_so"]["thap_ni_cung"]]
    saos2 = [c["saos"] for c in rep2["la_so"]["thap_ni_cung"]]
    saos3 = [c["saos"] for c in rep3["la_so"]["thap_ni_cung"]]

    assert saos1 == saos2 == saos3, "Vị trí sao phải đồng nhất tuyệt đối ở cả 3 mức đọc"


def test_p5_tc09_xss_escaping_and_heavy_palace_render():
    """P5.TC-09: Kiểm tra an toàn XSS và khả năng hiển thị ở cung có nhiều sao."""
    many_saos = [
        {"saoID": 1, "saoTen": "<script>alert(1)</script>", "saoLoai": 1, "saoDacTinh": "M"},
        {"saoID": 92, "saoTen": "Hóa Khoa", "saoLoai": 5},
        {"saoID": 57, "saoTen": "Văn Xương", "saoLoai": 6},
        {"saoID": 58, "saoTen": "Văn Khúc", "saoLoai": 6},
        {"saoID": 51, "saoTen": "Đà La", "saoLoai": 11},
        {"saoID": 52, "saoTen": "Kình Dương", "saoLoai": 11},
        {"saoID": 39, "saoTen": "Tràng Sinh", "saoLoai": 5},
        {"saoID": 28, "saoTen": "Lực Sĩ", "saoLoai": 2},
    ]
    cell = {
        "cung_so": 1,
        "chuan_ten": "Tý",
        "hanh_cung": "Thủy",
        "ten_cung": "Mệnh",
        "saos": many_saos,
    }
    out = luoi_html([cell])
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "alert" in out


def test_p5_tc10_ui_renders_chart_at_top_and_supports_view_mode_toggle():
    """P5.TC-10: UI hiển thị lá số 12 cung ở đầu trang, toggle được chế độ lưới / danh sách."""
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    from unittest.mock import Mock, patch
    from tests.horoscope_support import make_request
    from backend.app.main import horoscope_read
    import json

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    payload = horoscope_read(make_request(provider="mock"))
    payload["ho_ten"] = "Nguyễn An"
    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "chart_ready", "report": payload}),
        json.dumps({"event": "prepared", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response):
        app.sidebar.button[0].click().run()

    assert not app.exception
    assert app.toggle(key="show_chart").value is True
    assert app.radio(key="chart_view_mode").value == "Lưới 12 cung"
    app.radio(key="chart_view_mode").set_value("Đọc từng cung").run()
    assert not app.exception
    html = " ".join(item.value for item in app.markdown)
    assert "danh-sach" in html


def test_p5_tc11_ui_shows_chart_on_chart_ready_stream_event():
    """P5.TC-11: Khi nhận chart_ready trong stream, UI cập nhật preview hiển thị lá số."""
    from streamlit.testing.v1 import AppTest
    from pathlib import Path
    from unittest.mock import Mock, patch
    from tests.horoscope_support import make_request
    from backend.app.main import horoscope_read
    import json

    app = AppTest.from_file(Path(__file__).resolve().parents[1] / "frontend/horoscope_ui.py", default_timeout=20).run()
    payload = horoscope_read(make_request(provider="mock"))
    response = Mock()
    response.iter_lines.return_value = iter([
        json.dumps({"event": "chart_ready", "report": payload}),
        json.dumps({"event": "result", "report": payload}),
    ])
    with patch("requests.post", return_value=response):
        app.sidebar.button[0].click().run()

    assert not app.exception
    assert any("horoscope-chart" in item.value for item in app.markdown)

