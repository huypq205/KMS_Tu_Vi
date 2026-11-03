# -*- coding: utf-8 -*-
"""Test Suite cho Giai đoạn 3: Prompt Engineering & Bộ Luận Giải Cho Người Mới (Horoscope AI Interpreter).
Tuân thủ quy trình TDD trong GEMINI.md.
"""
from __future__ import annotations

import json
import sys
import unittest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.services.horoscope_features import (
    generate_raw_horoscope,
    extract_horoscope_features,
)
from backend.app.services.horoscope_rag_bridge import (
    retrieve_horoscope_context,
    format_context_for_prompt,
)
from backend.app.services.horoscope_interpreter import (
    HOROSCOPE_SYSTEM_PROMPT,
    HoroscopeGenerationError,
    build_horoscope_user_prompt,
    parse_reading_response,
    generate_mock_reading,
    interpret_horoscope,
    validate_reading,
)
from backend.app.services.horoscope_analysis import build_star_facts
from tests.horoscope_support import valid_reading


class TestHoroscopeInterpreter(unittest.TestCase):
    """Bộ kiểm thử unit test cho Horoscope Interpreter."""

    def setUp(self):
        raw = generate_raw_horoscope(nn=15, tt=8, nnnn=1995, chi_gio=5, gioi_tinh=1, duong_lich=True)
        self.features = extract_horoscope_features(raw, target_year=2026)
        context = retrieve_horoscope_context(self.features, top_k_per_topic=1)
        self.context_raw = context
        self.formatted_context = format_context_for_prompt(context)

    def test_tc01_system_prompt_rules(self):
        """TC-INT-01: Kiểm tra các quy tắc đạo đức và phiên dịch trong System Prompt."""
        self.assertIn("xu cát tị hung", HOROSCOPE_SYSTEM_PROMPT.lower())
        self.assertIn("json", HOROSCOPE_SYSTEM_PROMPT.lower())
        self.assertIn("đời thường", HOROSCOPE_SYSTEM_PROMPT.lower())
        self.assertIn("không phán", HOROSCOPE_SYSTEM_PROMPT.lower())

    def test_tc02_build_horoscope_user_prompt(self):
        """TC-INT-02: Kiểm tra hàm xây dựng User Prompt đầy đủ thông tin lá số và RAG context."""
        prompt = build_horoscope_user_prompt(self.features, self.formatted_context)
        self.assertIn("THÔNG TIN LÁ SỐ", prompt)
        self.assertIn("Ất Hợi", prompt)
        self.assertIn("SƠN ĐẦU HỎA", prompt)
        self.assertIn("NGỮ CẢNH TRI THỨC TỪ SÁCH KINH ĐIỂN", prompt)
        self.assertIn("YÊU CẦU ĐẦU RA JSON", prompt)

    def test_tc03_parse_reading_response(self):
        """TC-INT-03: Kiểm tra parse JSON sạch và JSON trong markdown codeblock."""
        valid_json = {
            "tieu_de": "Luận giải mẫu",
            "tong_quan": {"ban_sac": "Tự tin, quyết đoán"},
            "su_nghiep": {"phong_cach_lam_viec": "Chủ động"},
            "tai_chinh": {"tu_duy_tien_bac": "Cẩn trọng"},
            "tinh_cam": {"xu_huong_tinh_cam": "Chân thành"},
            "van_han_hien_tai": {"giai_doan": "24-33 tuổi"},
            "loi_khuyen_hanh_dong": ["Học hỏi", "Tập trung"],
        }

        # Case 1: Pure JSON string
        raw_str = json.dumps(valid_json, ensure_ascii=False)
        parsed1 = parse_reading_response(raw_str)
        self.assertEqual(parsed1["tieu_de"], "Luận giải mẫu")

        # Case 2: Markdown code fence ```json ... ```
        fence_str = f"Đây là bài luận giải:\n```json\n{raw_str}\n```\nChúc bạn thành công!"
        parsed2 = parse_reading_response(fence_str)
        self.assertEqual(parsed2["tieu_de"], "Luận giải mẫu")
        self.assertEqual(len(parsed2["loi_khuyen_hanh_dong"]), 2)

    def test_tc04_generate_mock_reading(self):
        """TC-INT-04: Kiểm tra sinh bài luận mẫu offline (fallback) có đủ 6 phần cấu trúc."""
        reading = generate_mock_reading(self.features)

        self.assertIn("tong_quan", reading)
        self.assertIn("su_nghiep", reading)
        self.assertIn("tai_chinh", reading)
        self.assertIn("tinh_cam", reading)
        self.assertIn("van_han_hien_tai", reading)
        self.assertIn("loi_khuyen_hanh_dong", reading)

        # Kiểm tra nội dung bám sát đặc trưng
        self.assertTrue(len(reading["loi_khuyen_hanh_dong"]) >= 3)
        self.assertIn("Sát - Phá - Tham", reading["tong_quan"]["ban_sac"])

    def test_tc06_mock_reading_contains_ket_luan(self):
        """TC-INT-06: Mock reading có mục ket_luan đủ trường, dẫn chứng không bịa."""
        context = self.context_raw
        facts = build_star_facts(self.features, context)
        reading = generate_mock_reading(self.features, context)

        self.assertIn("ket_luan", reading)
        points = reading["ket_luan"]
        self.assertIsInstance(points, list)
        self.assertTrue(1 <= len(points) <= 4, msg=f"ket_luan cần 1–4 mục, hiện {len(points)}")

        citation_ids = {c["ref_id"] for c in context.get("reference_list", [])}
        fact_map = {f["fact_id"]: f for f in facts}
        for point in points:
            self.assertIsInstance(point, dict)
            for key in ("nhan_dinh", "giai_thich_thun_viet", "gioi_han", "fact_ids", "source_refs"):
                self.assertIn(key, point)
            self.assertTrue(point["nhan_dinh"].strip())
            self.assertTrue(point["giai_thich_thun_viet"].strip())
            self.assertTrue(point["gioi_han"].strip())
            self.assertIsInstance(point["fact_ids"], list)
            self.assertIsInstance(point["source_refs"], list)
            for fid in point["fact_ids"]:
                self.assertIn(fid, fact_map, msg=f"fact_id '{fid}' không tồn tại trong DỮ KIỆN")
            for ref in point["source_refs"]:
                self.assertIn(ref, citation_ids, msg=f"source_ref {ref} không nằm trong nguồn đã lấy")

    def test_tc07_validate_reading_ket_luan(self):
        """TC-INT-07: validate_reading chấp nhận ket_luan hợp lệ, bắt dẫn chứng bịa."""
        context = self.context_raw
        facts = build_star_facts(self.features, context)
        usable = [f for f in facts if f.get("source_refs")]
        self.assertTrue(usable, "Cần ít nhất 1 fact có source_refs để kiểm tra ket_luan")
        f0 = usable[0]

        reading = valid_reading(facts, "2026 Bính Ngọ", fact_count=2)
        reading["ket_luan"] = [{
            "loai_ket_luan": "cau_truc",
            "nhan_dinh": f"Sao {f0['sao']} tại {f0['cung']} cần cân nhắc theo nguồn đã trích.",
            "giai_thich_thun_viet": "Giải nghĩa thuần Việt cho vị thế của sao này trong cung.",
            "gioi_han": "Chưa xác minh toàn bộ điều kiện tổ hợp sao.",
            "fact_ids": [f0["fact_id"]],
            "source_refs": list(f0["source_refs"]),
        }]
        validate_reading(reading, facts, context)  # Hợp lệ, không raise

        bad = valid_reading(facts, "2026 Bính Ngọ", fact_count=2)
        bad["ket_luan"] = [{
            "loai_ket_luan": "cau_truc",
            "nhan_dinh": "Nhận định bịa.",
            "giai_thich_thun_viet": "Giải thích bịa.",
            "gioi_han": "Giới hạn bịa.",
            "fact_ids": ["khong_ton_tai"],
            "source_refs": [9999],
        }]
        with self.assertRaises(HoroscopeGenerationError):
            validate_reading(bad, facts, context)


    def test_tc05_interpret_horoscope_e2e(self):
        """TC-INT-05: Kiểm tra hàm điều phối interpret_horoscope hoạt động mượt mà."""
        # Chạy với provider mock để đảm bảo test offline luôn chạy nhanh và ổn định
        result = interpret_horoscope(self.features, self.formatted_context, provider="mock")
        self.assertIsInstance(result, dict)
        self.assertIn("tieu_de", result)
        self.assertIn("tong_quan", result)
        self.assertIn("su_nghiep", result)
        self.assertIn("loi_khuyen_hanh_dong", result)


if __name__ == "__main__":
    unittest.main()

