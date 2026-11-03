"""P4 (Plan_Fix_Mai_Anh_v2): tín hiệu lưu niên và phần "vì sao".

Các bất biến cần khóa:

- một tín hiệu vật lý = **sao + cung + tầng thời gian + năm**; nhiều vai trò
  (Mệnh/Thân/đại hạn/tiểu hạn) nằm trong **một danh sách** trên cùng tín hiệu;
- `count` đếm **tín hiệu đã định danh**, `role_count` đếm vai trò trùng khớp —
  không đếm một tín hiệu thành nhiều chứng cứ độc lập;
- phân mức tách thành hàm riêng, có phiên bản và điều kiện code truy được;
- một tín hiệu đơn tại Mệnh/Thân vẫn giữ mức tập trung cao (hiệu chỉnh #1 của
  plan: gộp trùng không tự động hạ nhãn), nhưng trùng vai trò đại hạn/tiểu hạn
  không còn tự đẩy lên "nang";
- mỗi tín hiệu có `vi_sao` gồm dữ kiện · quy tắc · chủ đề · điều kiện thiếu,
  chạy được không cần AI;
- hai tín hiệu khác nhau cùng cung (vd. Tang Môn + Liêm Trinh lưu Kỵ) phải nói
  rõ là dấu hiệu khác, cùng tầng lưu niên, không phải hai tầng xác nhận;
- thiếu dữ liệu an sao/cung trọng tâm → "chưa đủ dữ liệu", không mặc định "nhẹ".
"""
from __future__ import annotations

from backend.app.services.horoscope_annual import (
    ACTIVATION_RULE_VERSION,
    classify_activation,
    compute_luu_nien,
)
from backend.app.services.palace_relations import CHI_NAMES
from tests.horoscope_support import make_features, make_raw

ROLE_LABELS = {
    "menh": "Mệnh",
    "than": "Thân",
    "dai_han": "Đại hạn",
    "tieu_han": "Tiểu hạn",
}


def _cungs_2026() -> list[dict]:
    return make_raw()["thap_ni_cung"]


def _synthetic_cungs(liem_trinh_cung_so: int) -> list[dict]:
    cungs = []
    for so in range(1, 13):
        cungs.append({
            "cung_so": so,
            "chuan_ten": CHI_NAMES[so - 1],
            "ten_cung": f"Cung {so}",
            "saos": [],
        })
    cungs[liem_trinh_cung_so - 1]["saos"].append(
        {"saoTen": "Liêm Trinh", "saoLoai": 1}
    )
    return cungs


# --- P4.TC-01: một tín hiệu vật lý giữ nhiều vai trò, không nhân bản ----------
def test_tc01_one_physical_signal_keeps_all_roles_once():
    cungs = _cungs_2026()
    tang_mon_so = compute_luu_nien(cungs, 2026)["vong_thai_tue"]["Tang Môn"]["cung_so"]
    ln = compute_luu_nien(
        cungs, 2026,
        cung_menh_so=tang_mon_so,
        cung_than_so=tang_mon_so,
        dai_han_cung_so=tang_mon_so,
        tieu_han_cung_so=tang_mon_so,
    )
    can_luu_y = ln["can_luu_y"]
    tang_mon = [s for s in can_luu_y["signals"] if s["sao"] == "Tang Môn"]
    assert len(tang_mon) == 1
    signal = tang_mon[0]
    assert signal["vai_tro"] == ["menh", "than", "dai_han", "tieu_han"]
    assert signal["so_vai_tro"] == 4
    assert signal["tang_thoi_gian"] == "luu_nien"
    assert signal["nam"] == 2026
    assert signal["can_chi"] == "Bính Ngọ"
    assert signal["tin_hieu_id"].startswith("ln-2026-")
    assert can_luu_y["count"] == 1
    assert can_luu_y["role_count"] == 4
    assert len({s["tin_hieu_id"] for s in can_luu_y["signals"]}) == can_luu_y["count"]


# --- P4.TC-02: trùng vai trò đại hạn/tiểu hạn không tự đẩy mức lên "nang" ----
def test_tc02_role_overlap_in_decade_and_year_does_not_inflate_level():
    cungs = _cungs_2026()
    tang_mon_so = compute_luu_nien(cungs, 2026)["vong_thai_tue"]["Tang Môn"]["cung_so"]
    assert tang_mon_so not in (2, 4)
    ln = compute_luu_nien(
        cungs, 2026,
        cung_menh_so=2,
        cung_than_so=4,
        dai_han_cung_so=tang_mon_so,
        tieu_han_cung_so=tang_mon_so,
    )
    can_luu_y = ln["can_luu_y"]
    assert can_luu_y["count"] == 1
    assert can_luu_y["role_count"] == 2
    assert can_luu_y["level"] == "vua"
    assert can_luu_y["level_label"] == "Vừa"
    assert can_luu_y["level_basis"]["co_menh_than"] is False


# --- P4.TC-03: một tín hiệu tại Mệnh vẫn giữ mức cao (hiệu chỉnh #1) ----------
def test_tc03_single_signal_at_menh_stays_high_concentration():
    result = classify_activation([{"vai_tro": ["menh"]}])
    assert result["level"] == "nang"
    assert result["level_label"] == "Cao"
    assert result["level_basis"]["so_tin_hieu"] == 1
    assert result["level_basis"]["co_menh_than"] is True


# --- P4.TC-04: ngưỡng dựa trên số tín hiệu, không phải số vai trò -------------
def test_tc04_thresholds_use_distinct_signals_not_role_hits():
    empty = classify_activation([])
    assert empty["level"] == "nhan"
    assert empty["level_label"] == "Thấp"

    one_decade = classify_activation([{"vai_tro": ["dai_han"]}])
    assert one_decade["level"] == "vua"

    two_signals = classify_activation([
        {"vai_tro": ["dai_han"]},
        {"vai_tro": ["tieu_han"]},
    ])
    assert two_signals["level"] == "nang"
    assert two_signals["level_basis"]["so_tin_hieu"] == 2
    assert two_signals["level_basis"]["so_vai_tro"] == 2


# --- P4.TC-05: nhãn truy được về điều kiện code + phiên bản quy tắc ----------
def test_tc05_level_is_versioned_and_traceable_to_code_conditions():
    result = classify_activation([{"vai_tro": ["menh", "than"]}])
    assert ACTIVATION_RULE_VERSION == 2
    assert result["level_rule_version"] == 2
    assert result["level_basis"] == {
        "so_tin_hieu": 1,
        "so_vai_tro": 2,
        "co_menh_than": True,
        "nguong": "Có vai trò Mệnh/Thân hoặc từ 2 tín hiệu khác nhau trở lên → Cao; "
                  "1 tín hiệu chỉ ở đại hạn/tiểu hạn → Vừa; 0 tín hiệu → Thấp.",
    }
    assert "quy tắc v2" in result["level_reason"]
    assert "không phải mức độ xấu" in result["level_reason"]


# --- P4.TC-06: mỗi tín hiệu có phần "vì sao" chạy bằng code -----------------
def test_tc06_each_signal_explains_data_rule_topic_and_missing_conditions():
    ln = make_features(2026)["luu_nien"]
    signals = ln["can_luu_y"]["signals"]
    assert signals
    for signal in signals:
        why = signal["vi_sao"]
        assert {"du_kien", "quy_tac", "chu_de", "dieu_kien_thieu", "giai_thich"} <= set(why)
        assert why["du_kien"]["sao"] == signal["sao"]
        assert why["du_kien"]["cung_so"] == signal["cung_so"]
        assert why["du_kien"]["tang_thoi_gian"] == "luu_nien"
        assert why["du_kien"]["nam"] == 2026
        assert why["quy_tac"]["id"].startswith("luu_nien.")
        assert why["quy_tac"]["mo_ta"]
        assert why["chu_de"]
        assert why["dieu_kien_thieu"]
        assert "chưa đủ" in why["giai_thich"].lower()
        assert "không kết luận" in why["giai_thich"].lower() or \
               "chưa đủ để kết luận" in why["giai_thich"].lower()


# --- P4.TC-07: hai tín hiệu khác nhau cùng cung nói rõ không phải hai tầng ----
def test_tc07_two_signals_in_same_palace_are_distinct_not_two_layers():
    # Năm 2026 (Bính Ngọ): Thái Tuế tại Ngọ, Tang Môn +2 tại Thân; can Bính
    # hóa Kỵ Liêm Trinh. Đặt Liêm Trinh tại Thân để hai tín hiệu cùng cung.
    cungs = _synthetic_cungs(liem_trinh_cung_so=9)
    ln = compute_luu_nien(cungs, 2026, dai_han_cung_so=9)
    can_luu_y = ln["can_luu_y"]
    assert can_luu_y["count"] == 2
    assert can_luu_y["role_count"] == 2
    assert {s["sao"] for s in can_luu_y["signals"]} == {"Tang Môn", "Liêm Trinh lưu Kỵ"}
    for signal in can_luu_y["signals"]:
        explanation = signal["vi_sao"]["giai_thich"]
        assert "tín hiệu khác" in explanation
        assert "cùng thuộc tầng lưu niên" in explanation
        assert "không phải hai tầng xác nhận" in explanation
        assert len(signal["vi_sao"]["tin_hieu_cung_cung"]) == 1


# --- P4.TC-08: thiếu dữ liệu an sao/cung trọng tâm -> chưa đủ dữ liệu --------
def test_tc08_missing_chart_data_is_not_reported_as_low_concentration():
    ln = compute_luu_nien([], 2026)
    can_luu_y = ln["can_luu_y"]
    assert can_luu_y["count"] == 0
    assert can_luu_y["level"] == "chua_du_du_lieu"
    assert can_luu_y["level_label"] == "Chưa đủ dữ liệu"
    assert "Thái Tuế" in can_luu_y["level_reason"]
    assert can_luu_y["dieu_kien_thieu"]


def test_tc08b_no_focus_palace_is_explicitly_unknown():
    ln = compute_luu_nien(_cungs_2026(), 2026)
    can_luu_y = ln["can_luu_y"]
    assert can_luu_y["level"] == "chua_du_du_lieu"
    assert any("cung trọng tâm" in reason for reason in can_luu_y["dieu_kien_thieu"])


# --- P4.TC-09: giao diện hiển thị mức tập trung + lời giải thích --------------
def test_tc09_annual_panel_shows_concentration_and_explanation():
    from frontend.horoscope_view import annual_panel

    features = make_features(2026)
    html = annual_panel(features["nam_xem"], features["luu_nien"])
    assert "Mức tập trung tín hiệu cần xem xét" in html
    assert "Mức cần lưu ý: <strong>nặng</strong>" not in html
    assert "Quy tắc:" in html
    assert "vai trò" in html.lower()
    assert "Tang Môn" in html
    assert "Chủ đề:" in html
    assert "Còn thiếu:" in html
    assert "nặng" not in html.lower()
