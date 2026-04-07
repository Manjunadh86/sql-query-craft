"""
Grading logic for the SQL Query Craft environment.

Computes a reward in [0.0, 1.0] with rich partial-credit signals:
  - SQL validity          (0.10)
  - Correct tables used   (0.10)
  - Column count match    (0.10)
  - Column names match    (0.15)
  - Row count match       (0.10)
  - Data values match     (0.45)

Destructive queries receive a -0.20 penalty (clamped to 0).
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from .tasks import TaskDefinition

WEIGHT_VALID_SQL = 0.10
WEIGHT_CORRECT_TABLES = 0.10
WEIGHT_COLUMN_COUNT = 0.10
WEIGHT_COLUMN_NAMES = 0.15
WEIGHT_ROW_COUNT = 0.10
WEIGHT_DATA_MATCH = 0.45
PENALTY_DESTRUCTIVE = 0.20


def _normalize_value(val: Any) -> str:
    """Normalize a value for comparison (case-insensitive, trimmed, rounded floats)."""
    if val is None:
        return "null"
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val).strip().lower()


def _normalize_column(name: str) -> str:
    return name.strip().lower()


def _extract_tables(query: str) -> set:
    """Extract table names referenced in a SQL query."""
    upper = query.upper()
    tables = set()
    for match in re.finditer(r'\bFROM\s+(\w+)', upper):
        tables.add(match.group(1).lower())
    for match in re.finditer(r'\bJOIN\s+(\w+)', upper):
        tables.add(match.group(1).lower())
    return tables


def _check_destructive(query: str) -> bool:
    upper = query.upper().strip()
    destructive_keywords = ["DROP ", "TRUNCATE ", "ALTER ", "DELETE ", "INSERT ", "UPDATE "]
    for kw in destructive_keywords:
        if kw in upper and not upper.startswith("SELECT"):
            return True
    return False


def grade_query(
    conn: sqlite3.Connection,
    task: TaskDefinition,
    student_query: str,
) -> Tuple[float, Dict[str, float]]:
    """
    Grade a student SQL query against the task's expected answer.

    Returns:
        (total_reward, breakdown_dict) where total_reward is in [0.0, 1.0]
    """
    breakdown: Dict[str, float] = {
        "valid_sql": 0.0,
        "correct_tables": 0.0,
        "column_count": 0.0,
        "column_names": 0.0,
        "row_count": 0.0,
        "data_match": 0.0,
        "penalty": 0.0,
    }

    if not student_query or not student_query.strip():
        return 0.01, breakdown

    if _check_destructive(student_query):
        breakdown["penalty"] = -PENALTY_DESTRUCTIVE
        return 0.01, breakdown

    # Execute student query
    try:
        cur_s = conn.cursor()
        cur_s.execute(student_query.strip().rstrip(";"))
        student_cols = [desc[0] for desc in cur_s.description] if cur_s.description else []
        student_rows = cur_s.fetchall()
    except Exception:
        return 0.01, breakdown

    breakdown["valid_sql"] = WEIGHT_VALID_SQL

    # Check tables used
    student_tables = _extract_tables(student_query)
    expected_tables = {t.lower() for t in task.expected_tables}
    if expected_tables and student_tables:
        table_overlap = len(student_tables & expected_tables) / len(expected_tables)
        breakdown["correct_tables"] = WEIGHT_CORRECT_TABLES * table_overlap

    # Execute expected query to get ground truth
    try:
        cur_e = conn.cursor()
        cur_e.execute(task.expected_query.strip().rstrip(";"))
        expected_cols = [desc[0] for desc in cur_e.description] if cur_e.description else []
        expected_rows = cur_e.fetchall()
    except Exception:
        partial = max(sum(breakdown.values()), 0.01)
        return min(partial, 0.99), breakdown

    # Column count match
    if len(student_cols) == len(expected_cols):
        breakdown["column_count"] = WEIGHT_COLUMN_COUNT
    elif student_cols:
        ratio = min(len(student_cols), len(expected_cols)) / max(len(student_cols), len(expected_cols))
        breakdown["column_count"] = WEIGHT_COLUMN_COUNT * ratio * 0.5

    # Column names match
    norm_student_cols = [_normalize_column(c) for c in student_cols]
    norm_expected_cols = [_normalize_column(c) for c in expected_cols]

    if norm_student_cols == norm_expected_cols:
        breakdown["column_names"] = WEIGHT_COLUMN_NAMES
    elif set(norm_student_cols) == set(norm_expected_cols):
        breakdown["column_names"] = WEIGHT_COLUMN_NAMES * 0.8
    elif norm_expected_cols:
        matching = sum(1 for c in norm_expected_cols if c in norm_student_cols)
        breakdown["column_names"] = WEIGHT_COLUMN_NAMES * (matching / len(norm_expected_cols)) * 0.6

    # Row count match
    if len(student_rows) == len(expected_rows):
        breakdown["row_count"] = WEIGHT_ROW_COUNT
    elif expected_rows:
        ratio = 1.0 - abs(len(student_rows) - len(expected_rows)) / max(len(expected_rows), 1)
        breakdown["row_count"] = WEIGHT_ROW_COUNT * max(ratio, 0.0) * 0.5

    # Data value comparison
    if expected_rows and student_rows:
        # Normalize all values for comparison
        norm_expected = [
            tuple(_normalize_value(v) for v in row) for row in expected_rows
        ]
        norm_student = [
            tuple(_normalize_value(v) for v in row) for row in student_rows
        ]

        # First try exact ordered match
        if norm_student == norm_expected:
            breakdown["data_match"] = WEIGHT_DATA_MATCH
        else:
            # Try unordered match (set of rows)
            expected_set = set(norm_expected)
            student_set = set(norm_student)
            if expected_set == student_set:
                breakdown["data_match"] = WEIGHT_DATA_MATCH * 0.9
            else:
                # Partial row matching
                matched = len(expected_set & student_set)
                total = len(expected_set)
                if total > 0:
                    match_ratio = matched / total
                    # Also check column-level matching for partial credit
                    if match_ratio == 0 and len(norm_student) > 0 and len(norm_expected) > 0:
                        col_match = _column_value_similarity(
                            norm_student, norm_expected, norm_student_cols, norm_expected_cols
                        )
                        breakdown["data_match"] = WEIGHT_DATA_MATCH * col_match * 0.3
                    else:
                        breakdown["data_match"] = WEIGHT_DATA_MATCH * match_ratio * 0.7

    total = max(sum(breakdown.values()), 0.0)
    total = min(total, 1.0)
    # Clamp to open interval (0, 1) — strictly between 0 and 1 per OpenEnv spec
    total = max(total, 0.01)
    total = min(total, 0.99)
    return total, breakdown


def _column_value_similarity(
    student_rows: List[tuple],
    expected_rows: List[tuple],
    student_cols: List[str],
    expected_cols: List[str],
) -> float:
    """Compute similarity based on overlapping column values."""
    if not student_rows or not expected_rows:
        return 0.0

    score = 0.0
    matches = 0

    for ec_idx, ec in enumerate(expected_cols):
        if ec in student_cols:
            sc_idx = student_cols.index(ec)
            exp_vals = {row[ec_idx] for row in expected_rows if ec_idx < len(row)}
            stu_vals = {row[sc_idx] for row in student_rows if sc_idx < len(row)}
            if exp_vals:
                overlap = len(exp_vals & stu_vals) / len(exp_vals)
                score += overlap
                matches += 1

    return score / max(matches, 1)
