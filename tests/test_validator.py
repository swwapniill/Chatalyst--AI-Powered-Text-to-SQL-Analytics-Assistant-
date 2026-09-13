"""
tests/test_validator.py

These are real pytest assertions -- if the validator regresses, CI actually
fails the build, unlike the original validator.py __main__ block which only
printed PASS/FAIL text and always exited 0 regardless of outcome.

No API key needed -- this only tests the AST parsing/safety logic, not the LLM.
"""
import pytest
from validator import validate_and_prepare, ValidationError
from schema_loader import load_schema

DB_PATH = "olist_real.db"


@pytest.fixture(scope="module")
def schema():
    return load_schema(DB_PATH)


def test_simple_select_passes_and_gets_limit(schema):
    sql = validate_and_prepare("SELECT COUNT(*) FROM orders", schema)
    assert "LIMIT" in sql.upper()


def test_oversized_limit_gets_capped(schema):
    sql = validate_and_prepare("SELECT * FROM orders LIMIT 5000", schema)
    assert "LIMIT 1000" in sql


def test_delete_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("DELETE FROM orders", schema)


def test_drop_table_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("DROP TABLE orders", schema)


def test_update_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("UPDATE orders SET order_status='delivered'", schema)


def test_statement_stacking_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("SELECT * FROM orders; DROP TABLE orders;", schema)


def test_unknown_column_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("SELECT fake_column FROM orders", schema)


def test_unknown_table_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("SELECT * FROM fake_table", schema)


def test_case_insensitive_table_name_passes(schema):
    sql = validate_and_prepare("select * from ORDERS", schema)
    assert sql  # should not raise


def test_cte_is_allowed(schema):
    sql = validate_and_prepare(
        "WITH recent AS (SELECT * FROM orders WHERE order_status='delivered') "
        "SELECT COUNT(*) FROM recent",
        schema,
    )
    assert "recent" in sql.lower()


def test_legitimate_union_is_allowed(schema):
    sql = validate_and_prepare(
        "SELECT order_id FROM orders UNION SELECT order_id FROM order_items", schema
    )
    assert sql


def test_union_cannot_leak_sqlite_master(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare(
            "SELECT * FROM orders UNION SELECT * FROM sqlite_master", schema
        )


def test_pragma_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("PRAGMA table_info(orders)", schema)


def test_attach_database_is_rejected(schema):
    with pytest.raises(ValidationError):
        validate_and_prepare("ATTACH DATABASE 'evil.db' AS evil", schema)
