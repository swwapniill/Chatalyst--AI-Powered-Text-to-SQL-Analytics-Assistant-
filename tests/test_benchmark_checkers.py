"""
tests/test_benchmark_checkers.py

Wraps verify_benchmark_checkers.py's logic in real pytest assertions: each
of the 25 benchmark questions' check() function must correctly validate its
own pre-verified ground-truth SQL result. A benchmark with buggy grading
logic is worse than no benchmark -- this is what stops that from shipping
silently. No API key needed; runs the ground-truth SQL directly, not the LLM.
"""
import sqlite3
import pytest
from benchmark import BENCHMARK
from verify_benchmark_checkers import GROUND_TRUTH_SQL

DB_PATH = "olist_real.db"


@pytest.fixture(scope="module")
def conn():
    connection = sqlite3.connect(DB_PATH)
    yield connection
    connection.close()


@pytest.mark.parametrize("item", BENCHMARK, ids=lambda item: f"q{item['id']}_{item['difficulty']}")
def test_checker_validates_its_own_ground_truth(conn, item):
    cur = conn.cursor()
    sql = GROUND_TRUTH_SQL[item["id"]]
    cur.execute(sql)
    rows = cur.fetchall()
    assert item["check"](None, rows), (
        f"Checker for question #{item['id']} ({item['question']!r}) "
        f"rejected its own verified ground truth: {rows}"
    )
