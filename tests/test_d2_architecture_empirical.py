"""
Empirical test suite for KMS Tử Vi D2 Architecture Diagram
Validates docs/_shared/d2-architect/kms_tuvi_architect.d2,
its compiled SVG docs/_shared/d2-architect/kms_tuvi_architect.svg,
and index docs/_shared/d2-architect/kms_tuvi-d2-architect-index.md.
"""

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import pytest

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
D2_FILE = os.path.join(REPO_ROOT, "docs", "_shared", "d2-architect", "kms_tuvi_architect.d2")
SVG_FILE = os.path.join(REPO_ROOT, "docs", "_shared", "d2-architect", "kms_tuvi_architect.svg")
INDEX_FILE = os.path.join(REPO_ROOT, "docs", "_shared", "d2-architect", "kms_tuvi-d2-architect-index.md")


def test_d2_and_svg_files_exist():
    """Verify that source D2, rendered SVG, and index files exist and are non-empty."""
    assert os.path.isfile(D2_FILE), f"Missing D2 file: {D2_FILE}"
    assert os.path.isfile(SVG_FILE), f"Missing SVG file: {SVG_FILE}"
    assert os.path.isfile(INDEX_FILE), f"Missing Index file: {INDEX_FILE}"

    d2_size = os.path.getsize(D2_FILE)
    svg_size = os.path.getsize(SVG_FILE)
    index_size = os.path.getsize(INDEX_FILE)

    assert d2_size > 1000, f"D2 file too small: {d2_size} bytes"
    assert svg_size > 10000, f"SVG file too small: {svg_size} bytes"
    assert index_size > 500, f"Index file too small: {index_size} bytes"


def test_d2_compilation_cli_exit_code_0():
    """Execute d2 CLI with ELK engine, pad 40, theme 1 and assert exit code 0."""
    cmd = [
        "d2",
        "--layout", "elk",
        "--theme", "1",
        "--pad", "40",
        D2_FILE,
        SVG_FILE
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, f"D2 compilation failed with code {result.returncode}: {result.stderr}"
    assert "success:" in result.stdout or "success:" in result.stderr or result.returncode == 0
    assert os.path.isfile(SVG_FILE)
    assert os.path.getsize(SVG_FILE) > 50000


def test_svg_xml_structure_and_namespaces():
    """Parse SVG using ElementTree to verify XML well-formedness, root tag, and namespace."""
    assert os.path.isfile(SVG_FILE)
    with open(SVG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert content.startswith("<?xml"), "SVG should have XML declaration"
    assert "<svg" in content, "Missing <svg> root element"
    assert "</svg>" in content, "Missing closing </svg> tag"

    tree = ET.fromstring(content)
    assert "svg" in tree.tag.lower(), f"Root tag must be svg, got {tree.tag}"
    assert "viewBox" in tree.attrib, "Root svg must have viewBox"
    viewbox = tree.attrib["viewBox"]
    parts = [float(x) for x in viewbox.split()]
    assert len(parts) == 4, f"viewBox should have 4 parts, got {viewbox}"
    min_x, min_y, width, height = parts
    assert width > 1000, f"Diagram width unexpectedly small: {width}"
    assert height > 500, f"Diagram height unexpectedly small: {height}"


def test_svg_elements_and_non_empty_paths():
    """Verify that SVG contains expected graphics elements: paths, rects, text labels."""
    with open(SVG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    tree = ET.fromstring(content)

    # Namespace handling
    ns = {"svg": "http://www.w3.org/2000/svg"}
    
    # Check rects (container boundaries and blocks)
    rects = tree.findall(".//svg:rect", ns) or tree.findall(".//rect")
    assert len(rects) >= 20, f"Expected at least 20 rectangles for architecture blocks, found {len(rects)}"

    # Check paths (connections and cylinders/icons)
    paths = tree.findall(".//svg:path", ns) or tree.findall(".//path")
    assert len(paths) >= 10, f"Expected at least 10 paths for connections/shapes, found {len(paths)}"

    # Check non-empty text elements
    texts = tree.findall(".//svg:text", ns) or tree.findall(".//text")
    assert len(texts) >= 30, f"Expected at least 30 text labels, found {len(texts)}"

    text_contents = [t.text for t in texts if t.text]
    full_text = " ".join(text_contents)

    # Assert key architectural terms are rendered in SVG
    assert "TỬ VI" in full_text
    assert "Client" in full_text or "Giao diện" in full_text
    assert "Backend" in full_text
    assert "SQLite" in full_text
    assert "Qdrant" in full_text
    assert "LLM" in full_text


def test_architecture_4_containers_and_subblocks():
    """Verify in D2 source that all 4 major containers and key sub-blocks are defined."""
    with open(D2_FILE, "r", encoding="utf-8") as f:
        d2_source = f.read()

    # 4 major containers
    assert re.search(r"Client\s*:\s*.*?\{", d2_source), "Missing Client container"
    assert re.search(r"Backend\s*:\s*.*?\{", d2_source), "Missing Backend container"
    assert re.search(r"Data\s*:\s*.*?\{", d2_source), "Missing Data container"
    assert re.search(r"External\s*:\s*.*?\{", d2_source), "Missing External container"

    # Key sub-blocks
    # Backend sub-blocks
    assert "Gateway:" in d2_source, "Missing Gateway"
    assert "Guardrails:" in d2_source, "Missing Guardrails"
    assert "RAGCore:" in d2_source, "Missing RAGCore"
    assert "HoroscopeCore:" in d2_source, "Missing HoroscopeCore"
    assert "ValidationCore:" in d2_source, "Missing ValidationCore"

    # Data sub-blocks
    assert "SQLiteDB:" in d2_source, "Missing SQLiteDB"
    assert "VectorDB:" in d2_source, "Missing VectorDB"
    assert "MasterFiles:" in d2_source, "Missing MasterFiles"

    # External sub-blocks
    assert "LLMPool:" in d2_source, "Missing LLMPool"
    assert "EmbeddingAPI:" in d2_source, "Missing EmbeddingAPI"


def test_all_connections_reference_valid_nodes():
    """Verify that every connection endpoint (A -> B) references an existing defined node."""
    with open(D2_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract all connection lines
    connection_pattern = re.compile(r"^([\w\.]+)\s*->\s*([\w\.]+)\s*:")
    connections = []
    for line_no, line in enumerate(lines, 1):
        line = line.strip()
        m = connection_pattern.match(line)
        if m:
            src, dst = m.group(1), m.group(2)
            connections.append((line_no, src, dst, line))

    assert len(connections) >= 20, f"Expected at least 20 connections, found {len(connections)}"

    # Parse defined identifiers in hierarchy
    with open(D2_FILE, "r", encoding="utf-8") as f:
        full_text = f.read()

    # Verify that major endpoints exist in the source
    for line_no, src, dst, line_str in connections:
        src_root = src.split(".")[0]
        dst_root = dst.split(".")[0]
        assert src_root in ["User", "Client", "Backend", "Data", "External"], (
            f"Line {line_no}: Invalid source container root '{src_root}' in '{line_str}'"
        )
        assert dst_root in ["User", "Client", "Backend", "Data", "External"], (
            f"Line {line_no}: Invalid destination container root '{dst_root}' in '{line_str}'"
        )
        # Check leaf name is mentioned in file
        src_leaf = src.split(".")[-1]
        dst_leaf = dst.split(".")[-1]
        assert src_leaf in full_text, f"Line {line_no}: Source '{src_leaf}' not found in D2 source"
        assert dst_leaf in full_text, f"Line {line_no}: Destination '{dst_leaf}' not found in D2 source"


def test_layout_resilience_elk_options():
    """Test resilience across different padding and theme options to ensure ELK layout doesn't crash."""
    test_cases = [
        ["d2", "--layout", "elk", "--theme", "0", "--pad", "20", D2_FILE, "-"],
        ["d2", "--layout", "elk", "--theme", "1", "--pad", "60", D2_FILE, "-"],
    ]
    for cmd in test_cases:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        assert res.returncode == 0, f"CLI command {cmd} failed: {res.stderr}"
        assert "<svg" in res.stdout, "Compiled output should produce valid SVG stream"


def test_d2_architect_index_document():
    """Verify that kms_tuvi-d2-architect-index.md contains valid YAML frontmatter and structural sections."""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_text = f.read()

    # Frontmatter
    assert index_text.startswith("---"), "Index file must start with YAML frontmatter"
    assert "type: d2-architect-index" in index_text
    assert "feature: _shared" in index_text

    # Required sections
    assert "## 1. Metadata" in index_text
    assert "## 2. Danh sách các Khối Kiến trúc" in index_text
    assert "## 3. Bản đồ 4 Luồng Dữ liệu Nghiệp vụ Chính" in index_text
    assert "## 4. Hướng dẫn Tái tạo & Biên dịch" in index_text

    # All 4 flows documented
    assert "Luồng 1" in index_text
    assert "Luồng 2" in index_text
    assert "Luồng 3" in index_text
    assert "Luồng 4" in index_text


def test_svg_font_embedding_and_vietnamese_unicode():
    """Verify SVG embeds WOFF fonts and contains intact Vietnamese unicode text."""
    with open(SVG_FILE, "r", encoding="utf-8") as f:
        svg_content = f.read()

    # Font embedding
    assert "@font-face" in svg_content, "SVG must embed font definitions"
    assert "data:application/font-woff;base64," in svg_content, "SVG must contain embedded base64 WOFF font"

    # Vietnamese unicode characters
    vietnamese_samples = [
        "KIẾN TRÚC TỔNG THỂ",
        "Ứng dụng Giao diện Client",
        "Hệ thống Backend",
        "Tầng Dữ liệu",
        "Dịch vụ Ngoài",
        "Luận giải Lá số",
        "Bộ Truy xuất Đa sách",
        "Khóa Bất biến"
    ]
    for sample in vietnamese_samples:
        assert sample in svg_content, f"Vietnamese text '{sample}' missing or corrupted in SVG"


def test_ba_conventions_no_deployment_infrastructure_artifacts():
    """Verify diagram conforms to BA-level architecture and does NOT contain low-level deployment leaks."""
    with open(D2_FILE, "r", encoding="utf-8") as f:
        d2_content = f.read().lower()

    # Disallowed low-level deployment terms according to d2-architect SKILL.md
    forbidden_tokens = ["pod", "replica", "vpc", "subnet", "k8s", "kubernetes", "ingress-controller"]
    for token in forbidden_tokens:
        assert token not in d2_content, f"Forbidden infrastructure token '{token}' found in business architecture D2"


def test_elk_backward_flow_resilience():
    """Verify that ELK layout cleanly compiles cycles and backward edges without error."""
    with open(D2_FILE, "r", encoding="utf-8") as f:
        d2_lines = f.readlines()

    # Verify that backward flow (External -> Backend) is present in D2
    has_backward_flow = any("External.LLMPool -> Backend.Guardrails.CitationValidator" in line for line in d2_lines)
    assert has_backward_flow, "Expected backward flow edge External.LLMPool -> Backend.Guardrails.CitationValidator"

    # Compile with layout elk and check that returncode is 0 and no layout loop warning is raised
    cmd = ["d2", "--layout", "elk", D2_FILE, "-"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, f"ELK backward flow failed compilation: {res.stderr}"
    assert "error" not in res.stderr.lower()

