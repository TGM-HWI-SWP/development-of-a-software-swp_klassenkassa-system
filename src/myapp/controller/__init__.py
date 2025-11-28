from typing import List, Tuple
import json
from datetime import datetime
from pathlib import Path

from myapp.models import Transaction, Balance

TYPE_MAP_INCOMING = {"income": "einzahlung", "expense": "ausgabe"}


def _parse_transaction(obj) -> Transaction:
    t_type = obj.get("type")
    if t_type in TYPE_MAP_INCOMING:
        t_type = TYPE_MAP_INCOMING[t_type]
    ts = obj.get("timestamp")
    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts)
    return Transaction(
        id=int(obj["id"]),
        type=t_type,
        amount=float(obj["amount"]),
        description=str(obj.get("description", "")),
        timestamp=ts,
    )


def load_from_json(path: str) -> Tuple[List[Transaction], Balance]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    transactions = [_parse_transaction(t) for t in data.get("transactions", [])]
    bal = data.get("balance", {})
    balance_value = bal.get("current_total")
    if balance_value is None:
        balance_value = calculate_balance(transactions)
    balance = Balance(current_total=float(balance_value))
    return transactions, balance


def save_to_json(path: str, transactions: List[Transaction], balance: Balance) -> None:
    p = Path(path)
    data = {
        "transactions": [
            {
                "id": t.id,
                "type": ("einzahlung" if t.type == "einzahlung" else "ausgabe"),
                "amount": t.amount,
                "description": t.description,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in transactions
        ],
        "balance": {"current_total": balance.current_total},
    }
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def calculate_balance(transactions: List[Transaction]) -> float:
    total = 0.0
    for t in transactions:
        if t.type == "einzahlung":
            total += t.amount
        else:
            total -= t.amount
    return total


def add_transaction(transactions: List[Transaction], t: Transaction) -> None:
    transactions.append(t)
