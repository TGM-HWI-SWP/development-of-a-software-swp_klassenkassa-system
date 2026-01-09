from myapp.backend.api import Controller
from myapp.adapters.db_memory import DummyDB


def test_add_transaction_updates_balance():
    db = DummyDB()
    controller = Controller(db=db)

    controller.add_transaction(10.0, "Einzahlung")
    assert controller.get_balance() == 10.0
