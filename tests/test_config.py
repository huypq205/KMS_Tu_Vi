# -*- coding: utf-8 -*-
"""Test suite cho backend.app.core.config và hàm _load_env().
Tuân thủ quy trình TDD trong GEMINI.md.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import pytest
from backend.app.core.config import _load_env


class TestConfigEnvironmentLoading:
    """Kiểm thử cơ chế nạp biến môi trường từ .env và hành vi cờ KMS_PRESERVE_SYSTEM_ENV."""

    def test_tc01_load_env_overwrites_existing_environ(self, tmp_path: Path):
        """TC-CFG-01: Mặc định giá trị trong .env phải ghi đè trực tiếp lên os.environ."""
        # Chuẩn bị biến môi trường giả lập (đang có sẵn từ hệ thống)
        os.environ["KMS_TEST_KEY_OVERWRITE"] = "system_default_value"
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

        test_env = tmp_path / ".env"
        test_env.write_text("KMS_TEST_KEY_OVERWRITE=dotenv_new_value\n", encoding="utf-8")

        try:
            _load_env(test_env)
            assert os.environ["KMS_TEST_KEY_OVERWRITE"] == "dotenv_new_value"
        finally:
            os.environ.pop("KMS_TEST_KEY_OVERWRITE", None)

    def test_tc02_load_env_preserves_system_env_when_flag_active(self, tmp_path: Path):
        """TC-CFG-02: Khi có KMS_PRESERVE_SYSTEM_ENV=1, giữ nguyên giá trị hệ thống."""
        os.environ["KMS_TEST_KEY_PRESERVED"] = "system_protected_value"
        os.environ["KMS_PRESERVE_SYSTEM_ENV"] = "1"

        test_env = tmp_path / ".env"
        test_env.write_text(
            "KMS_TEST_KEY_PRESERVED=dotenv_should_be_ignored\n"
            "KMS_TEST_KEY_NEW=only_in_dotenv\n",
            encoding="utf-8"
        )

        try:
            _load_env(test_env)
            # Biến đã có từ trước không bị ghi đè
            assert os.environ["KMS_TEST_KEY_PRESERVED"] == "system_protected_value"
            # Biến mới chưa có vẫn được nạp
            assert os.environ["KMS_TEST_KEY_NEW"] == "only_in_dotenv"
        finally:
            os.environ.pop("KMS_TEST_KEY_PRESERVED", None)
            os.environ.pop("KMS_TEST_KEY_NEW", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_tc03_load_env_file_not_found_safe(self, tmp_path: Path):
        """TC-CFG-03: Không văng lỗi khi file .env không tồn tại."""
        non_existent = tmp_path / "missing.env"
        assert not non_existent.exists()
        # Không được ném exception
        _load_env(non_existent)

    def test_tc04_load_env_parses_quotes_and_comments(self, tmp_path: Path):
        """TC-CFG-04: Xử lý đúng comment, nháy kép, nháy đơn, khoảng trắng và dòng trống."""
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
        test_env = tmp_path / ".env"
        content = (
            "# Dòng chú thích\n"
            "\n"
            "KMS_TEST_QUOTED_DOUBLE=\"hello world\"\n"
            "KMS_TEST_QUOTED_SINGLE='single phrase'\n"
            "KMS_TEST_SPACES  =  spaced_value  \n"
            "KMS_TEST_EMPTY=\n"
        )
        test_env.write_text(content, encoding="utf-8")

        try:
            _load_env(test_env)
            assert os.environ["KMS_TEST_QUOTED_DOUBLE"] == "hello world"
            assert os.environ["KMS_TEST_QUOTED_SINGLE"] == "single phrase"
            assert os.environ["KMS_TEST_SPACES"] == "spaced_value"
            assert os.environ["KMS_TEST_EMPTY"] == ""
        finally:
            for k in ("KMS_TEST_QUOTED_DOUBLE", "KMS_TEST_QUOTED_SINGLE", "KMS_TEST_SPACES", "KMS_TEST_EMPTY"):
                os.environ.pop(k, None)

    def test_tc05_load_env_flag_defined_inside_env_file(self, tmp_path: Path):
        """TC-CFG-05: Khi cờ KMS_PRESERVE_SYSTEM_ENV=1 nằm ngay trong file .env."""
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
        os.environ["KMS_TEST_FLAG_IN_FILE"] = "original_env"

        test_env = tmp_path / ".env"
        content = (
            "KMS_PRESERVE_SYSTEM_ENV=1\n"
            "KMS_TEST_FLAG_IN_FILE=should_not_overwrite\n"
        )
        test_env.write_text(content, encoding="utf-8")

        try:
            _load_env(test_env)
            assert os.environ["KMS_TEST_FLAG_IN_FILE"] == "original_env"
        finally:
            os.environ.pop("KMS_TEST_FLAG_IN_FILE", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
