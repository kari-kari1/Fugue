"""验证iteration表迁移的测试"""
import pytest
from sqlalchemy import create_engine, inspect
from app.core.config import settings


def test_iterations_table_exists():
    """验证iterations表存在"""
    engine = create_engine(settings.DATABASE_URL_SYNC)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert 'iterations' in tables


def test_iterations_table_columns():
    """验证iterations表的列"""
    engine = create_engine(settings.DATABASE_URL_SYNC)
    inspector = inspect(engine)
    columns = {col['name'] for col in inspector.get_columns('iterations')}

    required_columns = {
        'id', 'execution_id', 'iteration_number', 'feedback', 'mode', 'status',
        'original_task_snapshot', 'previous_output', 'refined_output',
        'tokens_used', 'cost_usd', 'error_message', 'created_at', 'updated_at', 'completed_at'
    }
    assert required_columns.issubset(columns)


def test_iterations_table_primary_key():
    """验证iterations表主键"""
    engine = create_engine(settings.DATABASE_URL_SYNC)
    inspector = inspect(engine)
    pk = inspector.get_pk_constraint('iterations')
    assert pk is not None
    assert pk['constrained_columns'] == ['id']


def test_iterations_table_foreign_keys():
    """验证iterations表外键"""
    engine = create_engine(settings.DATABASE_URL_SYNC)
    inspector = inspect(engine)
    fks = inspector.get_foreign_keys('iterations')
    assert len(fks) == 1
    fk = fks[0]
    assert fk['constrained_columns'] == ['execution_id']
    assert fk['referred_table'] == 'executions'
    assert fk['referred_columns'] == ['id']
