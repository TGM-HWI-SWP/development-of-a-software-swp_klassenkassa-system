from datetime import datetime
from myapp.models import Transaction, Balance

DUMMY_TRANSACTIONS = [
    Transaction(id=1, type="einzahlung", amount=10.0, description="Startkapital", timestamp=datetime.now()),
    Transaction(id=2, type="ausgabe", amount=2.5, description="Kekse", timestamp=datetime.now()),
]

DUMMY_BALANCE = Balance(current_total=7.5)
