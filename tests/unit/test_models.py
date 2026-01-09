from myapp.models import Transaction
from pydantic import ValidationError


def test_transaction_valid():
    t = Transaction(amount=10.0, description="Einzahlung")
    assert t.amount == 10.0


def test_transaction_invalid_amount():
    try:
        Transaction(amount="abc", description="Fehler")  # type: ignore[arg-type]
        assert False
    except ValidationError:
        assert True
