# -*- coding: utf-8 -*-
"""Adversarial stress tests for Windows environment variable isolation and KMS_PRESERVE_SYSTEM_ENV.
Executed by Challenger 2 for Milestone 1.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import winreg
from pathlib import Path

import pytest
from backend.app.core.config import _load_env, PRESERVE_SYSTEM_ENV


class TestWindowsRegistryEmpirical:
    """Kiểm tra trực tiếp các khoá Registry cấp User và Machine trên Windows."""

    def test_reg_01_user_registry_gemini_and_google_keys_absent(self):
        """Xác nhận GEMINI_API_KEY và GOOGLE_API_KEY hoàn toàn không tồn tại trong HKCU:\\Environment."""
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            for target_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                with pytest.raises(FileNotFoundError, match="The system cannot find the file specified"):
                    winreg.QueryValueEx(key, target_var)

    def test_reg_02_machine_registry_gemini_and_google_keys_absent(self):
        """Xác nhận GEMINI_API_KEY và GOOGLE_API_KEY không tồn tại trong HKLM (Machine level)."""
        reg_path = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
            for target_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                with pytest.raises(FileNotFoundError, match="The system cannot find the file specified"):
                    winreg.QueryValueEx(key, target_var)


class TestKmsPreserveSystemEnvSwitching:
    """Stress-test cơ chế chuyển mạch KMS_PRESERVE_SYSTEM_ENV."""

    @pytest.mark.parametrize("flag_value", ["1", "true", "True", "TRUE", "yes", "Yes", "YES", " 1 "])
    def test_preserve_truthy_values(self, tmp_path: Path, flag_value: str):
        """Các giá trị truthy của KMS_PRESERVE_SYSTEM_ENV phải bảo vệ giá trị hệ thống."""
        os.environ["KMS_STRESS_TARGET"] = "system_kept"
        os.environ["KMS_PRESERVE_SYSTEM_ENV"] = flag_value
        test_env = tmp_path / ".env"
        test_env.write_text("KMS_STRESS_TARGET=from_dotenv\nKMS_STRESS_NEW=from_dotenv_new\n", encoding="utf-8")

        try:
            _load_env(test_env)
            assert os.environ["KMS_STRESS_TARGET"] == "system_kept"
            assert os.environ["KMS_STRESS_NEW"] == "from_dotenv_new"
        finally:
            os.environ.pop("KMS_STRESS_TARGET", None)
            os.environ.pop("KMS_STRESS_NEW", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    @pytest.mark.parametrize("flag_value", ["0", "false", "False", "FALSE", "no", "NO", "none", "2", "random", ""])
    def test_preserve_falsy_or_invalid_values(self, tmp_path: Path, flag_value: str):
        """Các giá trị falsy hoặc không hợp lệ phải mặc định ghi đè (không bảo vệ)."""
        os.environ["KMS_STRESS_TARGET"] = "system_should_be_overwritten"
        os.environ["KMS_PRESERVE_SYSTEM_ENV"] = flag_value
        test_env = tmp_path / ".env"
        test_env.write_text("KMS_STRESS_TARGET=from_dotenv_wins\n", encoding="utf-8")

        try:
            _load_env(test_env)
            assert os.environ["KMS_STRESS_TARGET"] == "from_dotenv_wins"
        finally:
            os.environ.pop("KMS_STRESS_TARGET", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_dynamic_toggling(self, tmp_path: Path):
        """Kiểm tra việc chuyển mạch qua lại giữa 0, 1 và unset trong cùng một session."""
        test_env = tmp_path / ".env"
        test_env.write_text("KMS_TOGGLE_VAR=dotenv_value\n", encoding="utf-8")

        # Bước 1: Unset flag -> dotenv ghi đè
        os.environ["KMS_TOGGLE_VAR"] = "step1_sys"
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)
        _load_env(test_env)
        assert os.environ["KMS_TOGGLE_VAR"] == "dotenv_value"

        # Bước 2: Bật flag = 1 -> system được bảo vệ
        os.environ["KMS_TOGGLE_VAR"] = "step2_sys"
        os.environ["KMS_PRESERVE_SYSTEM_ENV"] = "1"
        _load_env(test_env)
        assert os.environ["KMS_TOGGLE_VAR"] == "step2_sys"

        # Bước 3: Đổi flag = 0 -> dotenv lại ghi đè
        os.environ["KMS_TOGGLE_VAR"] = "step3_sys"
        os.environ["KMS_PRESERVE_SYSTEM_ENV"] = "0"
        _load_env(test_env)
        assert os.environ["KMS_TOGGLE_VAR"] == "dotenv_value"

        # Bước 4: Đổi flag = "true" -> system được bảo vệ
        os.environ["KMS_TOGGLE_VAR"] = "step4_sys"
        os.environ["KMS_PRESERVE_SYSTEM_ENV"] = "true"
        _load_env(test_env)
        assert os.environ["KMS_TOGGLE_VAR"] == "step4_sys"

        # Dọn dẹp
        os.environ.pop("KMS_TOGGLE_VAR", None)
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_flag_in_env_file_variations(self, tmp_path: Path):
        """Kiểm tra flag KMS_PRESERVE_SYSTEM_ENV được định nghĩa bên trong file .env."""
        os.environ["KMS_FILE_FLAG_TARGET"] = "system_original"
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

        test_env = tmp_path / ".env"
        test_env.write_text(
            '# Comment line with KMS_PRESERVE_SYSTEM_ENV=0\n'
            'KMS_PRESERVE_SYSTEM_ENV="true"\n'
            'KMS_FILE_FLAG_TARGET=dotenv_should_not_overwrite\n',
            encoding="utf-8"
        )

        try:
            _load_env(test_env)
            assert os.environ["KMS_FILE_FLAG_TARGET"] == "system_original"
        finally:
            os.environ.pop("KMS_FILE_FLAG_TARGET", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

    def test_comment_with_preserve_flag_not_activated(self, tmp_path: Path):
        """Dòng chú thích chứa KMS_PRESERVE_SYSTEM_ENV=1 không được kích hoạt chế độ preserve."""
        os.environ["KMS_COMMENT_TARGET"] = "system_original"
        os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)

        test_env = tmp_path / ".env"
        test_env.write_text(
            '# KMS_PRESERVE_SYSTEM_ENV=1\n'
            'KMS_COMMENT_TARGET=dotenv_must_overwrite\n',
            encoding="utf-8"
        )

        try:
            _load_env(test_env)
            # Vì dòng flag chỉ là comment, nó KHÔNG được kích hoạt preserve -> dotenv ghi đè!
            assert os.environ["KMS_COMMENT_TARGET"] == "dotenv_must_overwrite"
        finally:
            os.environ.pop("KMS_COMMENT_TARGET", None)
            os.environ.pop("KMS_PRESERVE_SYSTEM_ENV", None)


class TestRealProcessIsolationSubprocess:
    """Kiểm thử thực thi độc lập qua Subprocess mới."""

    def test_fresh_subprocess_default_overrides(self):
        """Khởi chạy process python mới với biến môi trường kế thừa, kiểm tra .env ghi đè."""
        script = (
            "import os; from backend.app.core.config import GEMINI_API_KEY; "
            "from pathlib import Path; "
            "dotenv_key = ''; "
            "[dotenv_key := line.split('=', 1)[1].strip() for line in Path('.env').read_text(encoding='utf-8').splitlines() if line.startswith('GEMINI_API_KEY=')]; "
            "print('GEMINI_MATCH:', GEMINI_API_KEY == dotenv_key)"
        )
        env = os.environ.copy()
        # Đặt một giá trị rác trong process cha
        env["GEMINI_API_KEY"] = "LEGACY_JUNK_PROCESS_KEY"
        env.pop("KMS_PRESERVE_SYSTEM_ENV", None)

        proc = subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        assert "GEMINI_MATCH: True" in proc.stdout

    def test_fresh_subprocess_with_preserve_flag_active(self):
        """Khởi chạy process python mới với KMS_PRESERVE_SYSTEM_ENV=1, kiểm tra system env được giữ nguyên."""
        script = (
            "import os; from backend.app.core.config import GEMINI_API_KEY, PRESERVE_SYSTEM_ENV; "
            "print('PRESERVE:', PRESERVE_SYSTEM_ENV); "
            "print('GEMINI_PRESERVED:', GEMINI_API_KEY == 'LEGACY_JUNK_PROCESS_KEY')"
        )
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = "LEGACY_JUNK_PROCESS_KEY"
        env["KMS_PRESERVE_SYSTEM_ENV"] = "1"

        proc = subprocess.run(
            [sys.executable, "-c", script],
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        assert "PRESERVE: True" in proc.stdout
        assert "GEMINI_PRESERVED: True" in proc.stdout
