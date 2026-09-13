"""
tests/test_executor.py

Tests the read-only DB lock and query timeout actually work, with real
assertions -- not just print statements. No API key needed.
"""
import pytest
from executor import execute_readonly, ExecutionError, QueryTimeout

DB_PATH = "olist_real.db"


def test_normal_query_executes_correctly():
    columns, rows = execute_readonly(DB_PATH, "SELECT COUNT(*) FROM orders")
    assert rows[0][0] == 99441


def test_write_is_blocked_at_connection_level():
    with pytest.raises(ExecutionError):
        execute_readonly(DB_PATH, "DELETE FROM orders")


def test_slow_query_is_interrupted_by_timeout():
    slow_sql = "SELECT COUNT(*) FROM order_items a, order_items b"
    with pytest.raises(QueryTimeout):
        execute_readonly(DB_PATH, slow_sql, timeout_seconds=2)
