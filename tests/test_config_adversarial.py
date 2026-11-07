# -*- coding: utf-8 -*-
"""Adversarial stress and oracle verification suite for backend.app.core.config._load_env.
Written by Challenger 1 for Milestone 1.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
import pytest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.app.core.config import _load_env


class TestConfigAdversarial:
    """Stress harness and edge-case probes for _load_env."""

    def test_adv01_multiple_equals_in_value(self, tmp_path: Path):
        """Probe 1: Giá trị chứa nhiều dấu '=' (ví dụ connection string, query params)."""
        env_file = tmp_path / ".env"
        conn_str = "postgresql://user:pass@localhost:5432/kms?sslmode=require&target_session_attrs=read-write"
        env_file.write_text(f"KMS_CONN_STR={conn_str}\nKMS_RAW_EQ=a=b=c=d=e\n", encoding="utf-8")

        try:
            _load_env(env_file)
            assert os.environ.get("KMS_CONN_STR") == conn_str
            assert os.environ.get("KMS_RAW_EQ") == "a=b=c=d=e"
        finally:
            os.environ.pop("KMS_CONN_STR", None)
            os.environ.pop("KMS_RAW_EQ", None)

    def test_adv02_quotes_and_nested_quotes(self, tmp_path: Path):
        """Probe 2: Các loại ngoặc kép, ngoặc đơn, lồng nhau, rỗng."""
        env_file = tmp_path / ".env"
        content = (
            'KMS_Q1="hello world"\n'
            "KMS_Q2='single quoted'\n"
            'KMS_Q3="nested \'single\' inside"\n'
            'KMS_Q4=\'nested "double" inside\'\n'
            'KMS_Q5=""\n'
            "KMS_Q6=''\n"
            'KMS_Q7="""triple"""\n'
        )
        env_file.write_text(content, encoding="utf-8")

        keys = ["KMS_Q1", "KMS_Q2", "KMS_Q3", "KMS_Q4", "KMS_Q5", "KMS_Q6", "KMS_Q7"]
        try:
            _load_env(env_file)
            assert os.environ.get("KMS_Q1") == "hello world"
            assert os.environ.get("KMS_Q2") == "single quoted"
            assert os.environ.get("KMS_Q3") == "nested 'single' inside"
            assert os.environ.get("KMS_Q4") == 'nested "double" inside'
            assert os.environ.get("KMS_Q5") == ""
            assert os.environ.get("KMS_Q6") == ""
            assert os.environ.get("KMS_Q7") == "triple"
        finally:
            for k in keys:
                os.environ.pop(k, None)

    def test_adv03_line_endings_and_spacing(self, tmp_path: Path):
        """Probe 3: Line endings hỗn hợp (CRLF Windows, LF Unix), khoảng trắng và dòng trống."""
        env_file = tmp_path / ".env"
        # Ghi byte trực tiếp để mô phỏng chính xác CRLF và LF
        data = (
            b"\r\n"
            b"   \r\n"
            b"# Comment with CRLF\r\n"
            b"  # Indented comment\r\n"
            b"KMS_CRLF = val_crlf  \r\n"
            b"KMS_LF=val_lf\n"
            b"   KMS_SPACES   =   val_spaces   \r\n"
            b"\n\r\n"
        )
        env_file.write_bytes(data)

        keys = ["KMS_CRLF", "KMS_LF", "KMS_SPACES"]
        try:
            _load_env(env_file)
            assert os.environ.get("KMS_CRLF") == "val_crlf"
            assert os.environ.get("KMS_LF") == "val_lf"
            assert os.environ.get("KMS_SPACES") == "val_spaces"
        finally:
            for k in keys:
                os.environ.pop(k, None)

    def test_adv04_special_characters_and_unicode(self, tmp_path: Path):
        """Probe 4: Ký tự tiếng Việt có dấu, emoji, ký tự đặc biệt."""
        env_file = tmp_path / ".env"
        content = (
            'KMS_VN="Tử Vi Đẩu Số 2026 - Giáp Thìn - Thiên Cơ Hóa Kỵ"\n'
            'KMS_EMOJI="🔮✨🪐"\n'
            'KMS_ZH="紫微斗数命盘"\n'
            "KMS_SPECIAL=\"!@#$%^&*()_+{}[]:;<>?,./~`\"\n"
        )
        env_file.write_text(content, encoding="utf-8")

        keys = ["KMS_VN", "KMS_EMOJI", "KMS_ZH", "KMS_SPECIAL"]
        try:
            _load_env(env_file)
            assert os.environ.get("KMS_VN") == "Tử Vi Đẩu Số 2026 - Giáp Thìn - Thiên Cơ Hóa Kỵ"
            assert os.environ.get("KMS_EMOJI") == "🔮✨🪐"
            assert os.environ.get("KMS_ZH") == "紫微斗数命盘"
            assert os.environ.get("KMS_SPECIAL") == "!@#$%^&*()_+{}[]:;<>?,./~`"
        finally:
            for k in keys:
                os.environ.pop(k, None)

    def test_adv05_preserve_flag_with_spaces_around_equal(self, tmp_path: Path):
        """Probe 5: KMS_PRESERVE_SYSTEM_ENV có khoảng trắng xung quanh dấu '=' trong file .env."""
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
        os.environ["KMS_SYS_TARGET"] = "original_system_value"

        env_file = tmp_path / ".env"
        # Viết dạng có khoảng trắng: "KMS_PRESERVE_SYSTEM_ENV = 1"
        content = (
            "KMS_PRESERVE_SYSTEM_ENV = 1\n"
            "KMS_SYS_TARGET=should_be_preserved\n"
        )
        env_file.write_text(content, encoding="utf-8")

        try:
            _load_env(env_file)
            # Nếu regex hoặc startswith quá cứng nhắc ("KMS_PRESERVE_SYSTEM_ENV="),
            # dòng có khoảng trắng "KMS_PRESERVE_SYSTEM_ENV = 1" sẽ bị bỏ qua ở pass 1,
            # dẫn đến overwrite giá trị hệ thống!
            assert os.environ.get("KMS_SYS_TARGET") == "original_system_value", (
                f"Expected original_system_value to be preserved, but got {os.environ.get('KMS_SYS_TARGET')}"
            )
        finally:
            os.environ.pop("KMS_SYS_TARGET", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_adv06_utf8_bom_handling(self, tmp_path: Path):
        """Probe 6: File .env có UTF-8 BOM byte order mark (phổ biến trên Windows)."""
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
        os.environ["KMS_BOM_PROTECT"] = "system_val"

        env_file = tmp_path / ".env"
        # Ghi file bắt đầu bằng BOM UTF-8: \xef\xbb\xbf
        bom_content = "\ufeffKMS_PRESERVE_SYSTEM_ENV=1\nKMS_BOM_PROTECT=overwritten?\nKMS_BOM_KEY=success\n"
        env_file.write_text(bom_content, encoding="utf-8")

        try:
            _load_env(env_file)
            # Kiểm tra xem BOM có làm hỏng key đầu tiên hoặc startswith hay không
            assert os.environ.get("KMS_BOM_PROTECT") == "system_val", (
                f"BOM caused KMS_PRESERVE_SYSTEM_ENV to be missed! Got {os.environ.get('KMS_BOM_PROTECT')}"
            )
            assert os.environ.get("KMS_BOM_KEY") == "success"
        finally:
            os.environ.pop("KMS_BOM_PROTECT", None)
            os.environ.pop("KMS_BOM_KEY", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
            # Dọn dẹp key nếu bị nhiễm BOM
            os.environ.pop("\ufeffKMS_PRESERVE_SYSTEM_ENV", None)

    def test_adv07_empty_key_and_malformed_lines(self, tmp_path: Path):
        """Probe 7: Dòng dị dạng: không có key ('=val'), không có dấu '=', dòng chỉ có dấu '='."""
        env_file = tmp_path / ".env"
        content = (
            "JUST_A_STRING_NO_EQUALS\n"
            "===\n"
            "=orphan_value\n"
            "VALID_AFTER=ok\n"
        )
        env_file.write_text(content, encoding="utf-8")

        try:
            # Không được văng unhandled crash
            _load_env(env_file)
            assert os.environ.get("VALID_AFTER") == "ok"
        finally:
            os.environ.pop("VALID_AFTER", None)
            os.environ.pop("", None)
            os.environ.pop("=", None)

    def test_adv08_stress_large_file(self, tmp_path: Path):
        """Probe 8: Stress test tải lượng lớn: 1,000 biến trong file .env."""
        env_file = tmp_path / ".env"
        lines = [f"KMS_STRESS_KEY_{i}=val_{i}" for i in range(1000)]
        env_file.write_text("\n".join(lines), encoding="utf-8")

        start = time.perf_counter()
        _load_env(env_file)
        elapsed = time.perf_counter() - start

        try:
            assert elapsed < 1.0, f"Loading 1,000 env vars took too long: {elapsed:.2f}s"
            assert os.environ.get("KMS_STRESS_KEY_0") == "val_0"
            assert os.environ.get("KMS_STRESS_KEY_999") == "val_999"
        finally:
            for i in range(1000):
                os.environ.pop(f"KMS_STRESS_KEY_{i}", None)

    def test_adv09_preservation_flags_various_formats(self, tmp_path: Path):
        """Probe 9: Đánh giá tất cả các biến thể giá trị cờ: 1, true, yes, TRUE, YES, True."""
        for truthy in ["1", "true", "yes", "TRUE", "YES", "True", '"1"', "'true'"]:
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
            os.environ["KMS_TARGET"] = "keep_me"

            env_file = tmp_path / f".env_{truthy.strip('\"\'')}"
            env_file.write_text(f"KMS_PRESERVE_SYSTEM_ENV={truthy}\nKMS_TARGET=overwrite_me\n", encoding="utf-8")

            try:
                _load_env(env_file)
                assert os.environ.get("KMS_TARGET") == "keep_me", f"Failed to preserve with flag value: {truthy}"
            finally:
                os.environ.pop("KMS_TARGET", None)
                os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_adv10_falsy_preservation_flags(self, tmp_path: Path):
        """Probe 10: Đánh giá các biến thể falsy: 0, false, no, FALSE, NO, chuỗi rỗng -> PHẢI ghi đè."""
        for falsy in ["0", "false", "no", "FALSE", "NO", ""]:
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
            os.environ["KMS_TARGET"] = "initial"

            env_file = tmp_path / f".env_{falsy}"
            env_file.write_text(f"KMS_PRESERVE_SYSTEM_ENV={falsy}\nKMS_TARGET=overwritten\n", encoding="utf-8")

            try:
                _load_env(env_file)
                assert os.environ.get("KMS_TARGET") == "overwritten", f"Failed to overwrite with falsy flag: {falsy}"
            finally:
                os.environ.pop("KMS_TARGET", None)
                os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_adv11_inline_comments_behavior(self, tmp_path: Path):
        """Probe 11: Kiểm tra hành vi đối với comment cuối dòng (inline comments)."""
        env_file = tmp_path / ".env"
        # Kiểm tra xem _load_env giữ nguyên hay cắt bỏ inline comment
        content = "INLINE_UNQUOTED=my_val # inline note\nINLINE_QUOTED=\"my_val # inside quotes\"\n"
        env_file.write_text(content, encoding="utf-8")

        try:
            _load_env(env_file)
            val1 = os.environ.get("INLINE_UNQUOTED")
            val2 = os.environ.get("INLINE_QUOTED")
            assert val2 == "my_val # inside quotes"
        finally:
            os.environ.pop("INLINE_UNQUOTED", None)
            os.environ.pop("INLINE_QUOTED", None)

    def test_adv12_directory_path_handling(self, tmp_path: Path):
        """Probe 12: Truyền đường dẫn là một thư mục thay vì file (trường hợp mount volume docker nhầm)."""
        # Không được ném PermissionError unhandled crash
        try:
            _load_env(tmp_path)
        except PermissionError:
            pytest.fail("Unhandled PermissionError when directory path is provided to _load_env")

