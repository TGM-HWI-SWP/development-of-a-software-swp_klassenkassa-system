from dataclasses import dataclass
from datetime import datetime
from typing import List

# ---------- Models ----------
@dataclass
class Transaction:
    id: int
    type: str
    amount: float
    description: str
    timestamp: datetime


@dataclass
class Balance:
    current_total: float = 0.0


# ---------- interne Storage ----------
_transactions: List[Transaction] = []
_balance = Balance()
_next_id: int = 1


# ---------- intern ----------
def _normalize_type(t: str) -> str:
    if t not in ("einzahlung", "ausgabe"):
        raise ValueError("type must be 'einzahlung' or 'ausgabe'")
    return t


def _calculate_balance(transactions: List[Transaction]) -> float:
    total = 0.0
    for t in transactions:
        if t.type == "einzahlung":
            total += t.amount
        else:
            total -= t.amount
    return total


def _recalc_and_store_balance() -> None:
    _balance.current_total = _calculate_balance(_transactions)


# ---------- API ----------
def connect() -> None:
    global _transactions, _next_id

    if _transactions:
        return  # schon initialisiert

    now = datetime.now()

    _transactions.extend([
        Transaction(1, "einzahlung", 50.0, "Startgeld", now),
        Transaction(2, "ausgabe", 12.5, "Kreide", now),
        Transaction(3, "einzahlung", 20.0, "Spende Max", now),
    ])

    _next_id = 4
    _recalc_and_store_balance()


def disconnect() -> None:
    pass


def create_transaction(
    type_: str,
    amount: float,
    description: str = "",
    timestamp: datetime | None = None,
) -> Transaction:
    global _next_id

    norm_type = _normalize_type(type_)
    ts = timestamp or datetime.now()

    tx = Transaction(
        id=_next_id,
        type=norm_type,
        amount=float(amount),
        description=description,
        timestamp=ts,
    )

    _transactions.append(tx)
    _next_id += 1
    _recalc_and_store_balance()
    return tx


def get_all_transactions() -> List[Transaction]:
    return list(_transactions)


def get_balance() -> Balance:
    return _balance
