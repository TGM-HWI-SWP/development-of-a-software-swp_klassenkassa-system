import inspect
from myapp.backend.api import DBPort
from myapp.adapters.db_memory import DummyDB


def test_dummy_db_implements_port():
    for name, member in inspect.getmembers(DBPort, predicate=inspect.isfunction):
        assert hasattr(DummyDB, name), f"Missing DB method: {name}"
