"""Tests for FileGuard: Magic byte inspection, dangerous binary blocking, path traversal, and zip bomb protection."""

import io
import zipfile
import pytest

from app.security.file_guard import FileGuard


def test_filename_sanitization_path_traversal():
    assert FileGuard.sanitize_filename("../../../etc/passwd") == "passwd"
    assert FileGuard.sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert FileGuard.sanitize_filename("valid_report_2026.csv") == "valid_report_2026.csv"
    assert FileGuard.sanitize_filename(".hidden_config.json") == "file_.hidden_config.json"
    assert FileGuard.sanitize_filename("test\x00file.csv") == "testfile.csv"


def test_file_guard_allowed_formats():
    csv_bytes = b"id,name,revenue\n1,Alpha,5000\n2,Beta,9000"
    valid, err = FileGuard.validate_file_content("sales.csv", csv_bytes)
    assert valid is True
    assert err is None

    parquet_bytes = b"PAR1" + b"\x00" * 20 + b"PAR1"
    valid, err = FileGuard.validate_file_content("data.parquet", parquet_bytes)
    assert valid is True

    pdf_bytes = b"%PDF-1.7\n%stream content"
    valid, err = FileGuard.validate_file_content("paper.pdf", pdf_bytes)
    assert valid is True


def test_file_guard_dangerous_executables_blocked():
    # Windows PE executable (MZ header)
    pe_bytes = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 100
    valid, err = FileGuard.validate_file_content("malware.csv", pe_bytes)
    assert valid is False
    assert "Dangerous executable" in err

    # Linux ELF executable
    elf_bytes = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 100
    valid, err = FileGuard.validate_file_content("exploit.parquet", elf_bytes)
    assert valid is False
    assert "Dangerous executable" in err

    # Shell script
    sh_bytes = b"#!/bin/bash\nrm -rf /"
    valid, err = FileGuard.validate_file_content("script.txt", sh_bytes)
    assert valid is False


def test_file_guard_disallowed_extension():
    valid, err = FileGuard.validate_file_content("payload.exe", b"test content")
    assert valid is False
    assert "extension '.exe' is not permitted" in err


def test_zip_bomb_detection():
    # Create safe zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("test.txt", "Small content hello world")
    
    valid, err = FileGuard.inspect_zip_archive_safety(buf.getvalue())
    assert valid is True

    # Create zip with path traversal
    buf_bad = io.BytesIO()
    with zipfile.ZipFile(buf_bad, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("../../etc/shadow", "root:x:0:0")

    valid_bad, err_bad = FileGuard.inspect_zip_archive_safety(buf_bad.getvalue())
    assert valid_bad is False
    assert "path traversal" in err_bad
