from datetime import datetime
from pathlib import Path
import json
from typing import Tuple, List

from myapp.models import Transaction, Balance


_FALLBACK_TRANSACTIONS = [
    Transaction(id=1, type="einzahlung", amount=10.0, description="Startkapital", timestamp=datetime.now()),
    Transaction(id=2, type="ausgabe", amount=2.5, description="Kekse", timestamp=datetime.now()),
]


def load_dummy_data() -> Tuple[List[Transaction], Balance]:
    """Lädt `dummydata.json` neben dieser Datei. Fallback auf in-code Daten bei Fehlern."""
    p = Path(__file__).parent / "dummydata.json"
    if p.exists():
        try:
            with p.open("r", encoding="utf-8") as f:
                data = json.load(f)
            transactions = []
            for obj in data.get("transactions", []):
                ts = obj.get("timestamp")
                if isinstance(ts, str):
                    ts = datetime.fromisoformat(ts)
                ttype = obj.get("type")
                if ttype == "income":
                    ttype = "einzahlung"
                elif ttype == "expense":
                    ttype = "ausgabe"
                transactions.append(
                    Transaction(
                        id=int(obj["id"]),
                        type=ttype,
                        amount=float(obj.get("amount", 0.0)),
                        description=str(obj.get("description", "")),
                        timestamp=ts,
                    )
                )
            bal = data.get("balance", {})
            current_total = bal.get("current_total")
            if current_total is None:
                current_total = sum(t.amount if t.type == "einzahlung" else -t.amount for t in transactions)
            return transactions, Balance(current_total=float(current_total))
        except Exception:
            pass
    total = sum(t.amount if t.type == "einzahlung" else -t.amount for t in _FALLBACK_TRANSACTIONS)
    return _FALLBACK_TRANSACTIONS.copy(), Balance(current_total=float(total))


if __name__ == "__main__":
    txs, bal = load_dummy_data()
    print(f"Loaded {len(txs)} transactions, balance={bal.current_total}")
