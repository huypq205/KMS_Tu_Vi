"""Empirical Challenge Test Suite for DBML & SQL Architecture Documentation.

Tests docs/_shared/dbdiagram/kms_tuvi.dbml and docs/_shared/dbdiagram/kms_tuvi.sql:
- dbml2sql CLI compilation across targets (PostgreSQL, MySQL, MSSQL, Oracle)
- 17-table parity with SQLite kms.db and SQLAlchemy models
- Column-level schema parity
- Foreign key integrity & zero violations on live database
- SQL statement syntax (CREATE TABLE, ALTER TABLE, COMMENT ON)
- Oracle validation with negative test cases
- Documentation compliance (kms_tuvi-dbdiagram-index.md)
"""
from __future__ import annotations

import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure Windows stdout UTF-8 encoding
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
DBML_FILE = REPO_ROOT / "docs" / "_shared" / "dbdiagram" / "kms_tuvi.dbml"
SQL_FILE = REPO_ROOT / "docs" / "_shared" / "dbdiagram" / "kms_tuvi.sql"
INDEX_FILE = REPO_ROOT / "docs" / "_shared" / "dbdiagram" / "kms_tuvi-dbdiagram-index.md"
SQLITE_DB = REPO_ROOT / "data" / "processed" / "kms.db"

EXPECTED_17_TABLES = {
    "books",
    "book_parts",
    "knowledge_items",
    "knowledge_pages",
    "id_redirects",
    "term_aliases",
    "evidences",
    "audit_samples",
    "import_runs",
    "chunks",
    "chunk_members",
    "evaluation_cases",
    "query_cache",
    "horoscope_cache",
    "validation_cases",
    "predictions",
    "events",
}


def get_sqlite_tables_and_columns() -> dict[str, list[str]]:
    """Retrieve all business tables and their columns from SQLite kms.db."""
    assert SQLITE_DB.exists(), f"SQLite database not found at {SQLITE_DB}"
    conn = sqlite3.connect(str(SQLITE_DB))
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '%fts%' ORDER BY name"
    )
    tables = [row[0] for row in cur.fetchall()]
    table_cols: dict[str, list[str]] = {}
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        table_cols[table] = [col[1] for col in cur.fetchall()]
    conn.close()
    return table_cols


def parse_dbml_tables(dbml_content: str) -> dict[str, dict[str, str]]:
    """Parse table names and column definitions from DBML."""
    # Match Table <name> { ... }
    pattern = re.compile(r"Table\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}", re.DOTALL)
    tables: dict[str, dict[str, str]] = {}
    for match in pattern.finditer(dbml_content):
        tname = match.group(1)
        tbody = match.group(2)
        cols: dict[str, str] = {}
        for line in tbody.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("Note:") or line.startswith("indexes"):
                continue
            col_match = re.match(r"^([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_()]+)", line)
            if col_match:
                cname = col_match.group(1)
                ctype = col_match.group(2)
                cols[cname] = ctype
        tables[tname] = cols
    return tables


def parse_sql_tables(sql_content: str) -> dict[str, dict[str, str]]:
    """Parse table names and column definitions from SQL."""
    pattern = re.compile(r'CREATE\s+TABLE\s+"([^"]+)"\s*\((.*?)\);', re.DOTALL)
    tables: dict[str, dict[str, str]] = {}
    for match in pattern.finditer(sql_content):
        tname = match.group(1)
        tbody = match.group(2)
        cols: dict[str, str] = {}
        for line in tbody.strip().split("\n"):
            line = line.strip()
            col_match = re.match(r'^"([^"]+)"\s+([a-zA-Z0-9_()]+)', line)
            if col_match:
                cname = col_match.group(1)
                ctype = col_match.group(2)
                cols[cname] = ctype
        tables[tname] = cols
    return tables


class TestDbmlSqlEmpiricalValidation:
    """Empirical verification test suite for KMS Tử Vi DBML & SQL documentation."""

    def test_dbml2sql_installed(self):
        """Assert dbml2sql CLI tool is installed and accessible."""
        res = subprocess.run("dbml2sql --version", shell=True, capture_output=True, text=True, check=False)
        assert res.returncode == 0
        assert len(res.stdout.strip()) > 0

    def test_dbml2sql_compilation_postgres(self):
        """Empirically compile docs/_shared/dbdiagram/kms_tuvi.dbml with --postgres."""
        assert DBML_FILE.exists(), f"DBML file missing at {DBML_FILE}"
        res = subprocess.run(
            f'dbml2sql "{DBML_FILE}" --postgres',
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
        )
        assert res.returncode == 0, f"dbml2sql failed with code {res.returncode}:\n{res.stderr}"
        stdout = res.stdout
        assert not re.search(r"\bERROR:\s*", stdout), f"dbml2sql reported error in stdout:\n{stdout}"
        assert 'CREATE TABLE "books"' in stdout
        assert 'ALTER TABLE "book_parts" ADD FOREIGN KEY' in stdout
        assert 'COMMENT ON TABLE "books"' in stdout

    def test_dbml2sql_multi_target_stress(self):
        """Stress-test DBML compilation against MySQL, MSSQL, Oracle engines."""
        targets = ["--mysql", "--mssql", "--oracle"]
        for target in targets:
            res = subprocess.run(
                f'dbml2sql "{DBML_FILE}" {target}',
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
            )
            assert res.returncode == 0, f"dbml2sql stress test failed for target {target}:\n{res.stderr}"
            assert not re.search(r"\bERROR:\s*", res.stdout), f"dbml2sql reported error for target {target}:\n{res.stdout}"
            assert len(res.stdout) > 5000, f"Output too short for target {target}"

    def test_negative_oracle_rejects_corrupted_dbml(self):
        """Negative test: confirm dbml2sql detects when DBML has invalid syntax/dangling ref."""
        corrupted_dbml = """
        Table valid_tab {
          id integer [pk]
        }
        Table bad_tab {
          id integer [pk]
          fake_ref integer [ref: > non_existent_table.non_existent_col]
        }
        """
        with tempfile.NamedTemporaryFile("w", suffix=".dbml", delete=False, encoding="utf-8") as tmp:
            tmp.write(corrupted_dbml)
            tmp_path = tmp.name

        try:
            res = subprocess.run(
                f'dbml2sql "{tmp_path}" --postgres',
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                encoding="utf-8",
            )
            # dbml2sql outputs ERROR: in stdout and creates dbml-error.log
            has_error = (
                res.returncode != 0
                or bool(re.search(r"\bERROR:\s*", res.stdout))
                or bool(re.search(r"\bERROR:\s*", res.stderr))
            )
            assert has_error, "dbml2sql unexpectedly succeeded on corrupted DBML"
        finally:
            Path(tmp_path).unlink(missing_ok=True)
            # Clean up dbml-error.log created in repo root
            Path("dbml-error.log").unlink(missing_ok=True)

    def test_table_count_and_identity_parity(self):
        """Assert exact 17 tables match between SQLite kms.db, DBML, and SQL."""
        sqlite_data = get_sqlite_tables_and_columns()
        sqlite_tables = set(sqlite_data.keys())
        assert sqlite_tables == EXPECTED_17_TABLES, f"SQLite tables mismatch: {sqlite_tables ^ EXPECTED_17_TABLES}"

        dbml_content = DBML_FILE.read_text(encoding="utf-8")
        dbml_tables = parse_dbml_tables(dbml_content)
        assert set(dbml_tables.keys()) == EXPECTED_17_TABLES, (
            f"DBML tables mismatch: {set(dbml_tables.keys()) ^ EXPECTED_17_TABLES}"
        )

        sql_content = SQL_FILE.read_text(encoding="utf-8")
        sql_tables = parse_sql_tables(sql_content)
        assert set(sql_tables.keys()) == EXPECTED_17_TABLES, (
            f"SQL tables mismatch: {set(sql_tables.keys()) ^ EXPECTED_17_TABLES}"
        )

    def test_column_parity_with_sqlite(self):
        """Assert 100% column parity between SQLite kms.db and DBML/SQL schemas."""
        sqlite_data = get_sqlite_tables_and_columns()
        sql_content = SQL_FILE.read_text(encoding="utf-8")
        sql_tables = parse_sql_tables(sql_content)

        mismatches = []
        for table in EXPECTED_17_TABLES:
            scols = set(sqlite_data[table])
            qcols = set(sql_tables[table].keys())
            if scols != qcols:
                mismatches.append(f"{table}: SQLite extra={scols - qcols}, SQL extra={qcols - scols}")

        assert not mismatches, f"Column mismatches detected:\n" + "\n".join(mismatches)

    def test_foreign_key_integrity_and_data_compliance(self):
        """Assert all foreign key declarations are valid and zero violations exist on kms.db."""
        dbml_content = DBML_FILE.read_text(encoding="utf-8")
        dbml_tables = parse_dbml_tables(dbml_content)

        # Find all references: field [ref: > target_table.target_col]
        ref_pattern = re.compile(
            r"Table\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}",
            re.DOTALL,
        )
        refs: list[tuple[str, str, str, str]] = []
        for match in ref_pattern.finditer(dbml_content):
            src_table = match.group(1)
            tbody = match.group(2)
            for line in tbody.strip().split("\n"):
                m = re.match(r"^([a-zA-Z0-9_]+)\s+.*?ref:\s*>\s*([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", line.strip())
                if m:
                    src_col = m.group(1)
                    tgt_table = m.group(2)
                    tgt_col = m.group(3)
                    refs.append((src_table, src_col, tgt_table, tgt_col))

        assert len(refs) == 14, f"Expected 14 FK references in DBML, found {len(refs)}"

        # 1. Schema check: target tables and columns must exist in DBML
        for src_tab, src_col, tgt_tab, tgt_col in refs:
            assert tgt_tab in dbml_tables, f"Dangling target table: {tgt_tab} from {src_tab}.{src_col}"
            assert tgt_col in dbml_tables[tgt_tab], (
                f"Dangling target column: {tgt_tab}.{tgt_col} from {src_tab}.{src_col}"
            )
            # Verify data type compatibility
            src_type = dbml_tables[src_tab][src_col]
            tgt_type = dbml_tables[tgt_tab][tgt_col]
            assert src_type == tgt_type, (
                f"FK type mismatch: {src_tab}.{src_col} ({src_type}) -> {tgt_tab}.{tgt_col} ({tgt_type})"
            )

        # 2. Live database check: assert 0 orphan records in SQLite kms.db
        conn = sqlite3.connect(str(SQLITE_DB))
        cur = conn.cursor()
        fk_violations = []
        for src_tab, src_col, tgt_tab, tgt_col in refs:
            query = (
                f"SELECT COUNT(*) FROM {src_tab} "
                f"WHERE {src_col} IS NOT NULL AND {src_col} NOT IN (SELECT {tgt_col} FROM {tgt_tab})"
            )
            cur.execute(query)
            count = cur.fetchone()[0]
            if count > 0:
                fk_violations.append(f"{src_tab}.{src_col} -> {tgt_tab}.{tgt_col}: {count} violations")
        conn.close()

        assert not fk_violations, f"Referential integrity violations in live database:\n" + "\n".join(fk_violations)

    def test_sql_ddl_structure_and_syntax(self):
        """Assert SQL file statements, indices, comments, and constraints."""
        sql_content = SQL_FILE.read_text(encoding="utf-8")

        # 17 CREATE TABLE
        create_tables = re.findall(r'CREATE\s+TABLE\s+"([^"]+)"', sql_content)
        assert len(create_tables) == 17
        assert set(create_tables) == EXPECTED_17_TABLES

        # 2 CREATE UNIQUE INDEX
        indices = re.findall(r'CREATE\s+UNIQUE\s+INDEX\s+"([^"]+)"', sql_content)
        assert len(indices) == 2
        assert set(indices) == {"uq_part", "uq_chunk_member"}

        # 14 ALTER TABLE ADD FOREIGN KEY
        fks = re.findall(r'ALTER\s+TABLE\s+"([^"]+)"\s+ADD\s+FOREIGN\s+KEY', sql_content)
        assert len(fks) == 14

        # 17 COMMENT ON TABLE
        table_comments = re.findall(r'COMMENT\s+ON\s+TABLE\s+"([^"]+)"', sql_content)
        assert len(table_comments) == 17
        assert set(table_comments) == EXPECTED_17_TABLES

        # Extensive COMMENT ON COLUMN
        col_comments = re.findall(r'COMMENT\s+ON\s+COLUMN\s+"([^"]+)"\."([^"]+)"', sql_content)
        assert len(col_comments) > 100, f"Expected >100 column comments, found {len(col_comments)}"

    def test_tablegroups_exhaustiveness(self):
        """Assert TableGroups in DBML cover all 17 tables without omissions or duplicates."""
        dbml_content = DBML_FILE.read_text(encoding="utf-8")
        tg_pattern = re.compile(r"TableGroup\s+([a-zA-Z0-9_]+)\s*\{([^}]+)\}", re.DOTALL)
        tgroups = tg_pattern.findall(dbml_content)

        assert len(tgroups) == 4, f"Expected 4 TableGroups, found {len(tgroups)}"
        grouped_tables: list[str] = []
        for tg_name, tg_body in tgroups:
            tables_in_group = [t.strip() for t in tg_body.strip().split("\n") if t.strip()]
            grouped_tables.extend(tables_in_group)

        # Check no duplicates in groups
        assert len(grouped_tables) == len(set(grouped_tables)), "Duplicate tables found across TableGroups"
        assert set(grouped_tables) == EXPECTED_17_TABLES, (
            f"TableGroups mismatch with expected 17 tables: {set(grouped_tables) ^ EXPECTED_17_TABLES}"
        )

    def test_index_documentation_compliance(self):
        """Assert docs/_shared/dbdiagram/kms_tuvi-dbdiagram-index.md compliance."""
        assert INDEX_FILE.exists(), f"Index file missing at {INDEX_FILE}"
        text = INDEX_FILE.read_text(encoding="utf-8")

        # YAML frontmatter
        assert text.startswith("---")
        assert "type: dbdiagram-index" in text
        assert "kms_tuvi.dbml" in text
        assert "kms_tuvi.sql" in text

        # Matrix contains all 17 tables
        for table in EXPECTED_17_TABLES:
            assert f"`{table}`" in text, f"Table `{table}` missing from index documentation matrix"
