from dataclasses import dataclass
from datetime import datetime, date as dt_date
from typing import List, Optional

# ---------- Models ----------
@dataclass
class Transaction:
    id: int
    type: str
    amount: float
    description: str
    timestamp: datetime

    # ✅ neu: optionale Felder, damit create_transaction sie annehmen kann
    category: str = ""
    student: str = ""
    date: Optional[dt_date] = None


@dataclass
class Balance:
    current_total: float = 0.0


# ---------- interne Storage ----------
_transactions: List[Transaction] = []
_balance = Balance()
_next_id: int = 1


# ---------- intern ----------
def _normalize_type(t: str) -> str:
    t = t.lower()
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


def _reset_storage() -> None:
    """Reset für Test-Isolation / frische DB."""
    global _transactions, _balance, _next_id
    _transactions = []
    _balance = Balance()
    _next_id = 1


# ---------- API ----------
def connect(seed: bool = True) -> None:
    """
    Initialisiert die In-Memory DB.
    - seed=True: legt Beispiel-Transaktionen an (für manuelles Demo-Run)
    - seed=False: startet leer (für Unit-Tests)
    """
    global _transactions, _next_id

    if _transactions:
        return  # schon initialisiert

    if not seed:
        _recalc_and_store_balance()
        return

    now = datetime.now()
    _transactions.extend([
        Transaction(1, "einzahlung", 50.0, "Startgeld", now),
        Transaction(2, "ausgabe", 12.5, "Kreide", now),
        Transaction(3, "einzahlung", 20.0, "Spende Max", now),
    ])
    _next_id = 4
    _recalc_and_store_balance()


def disconnect() -> None:
    _reset_storage()


def create_transaction(
    type_: str,
    amount: float,
    description: str = "",
    timestamp: Optional[datetime] = None,
    # ✅ neu: diese kwargs erwartet dein Backend an manchen Stellen
    category: str = "",
    student: str = "",
    date_: Optional[dt_date] = None,
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
        category=category,
        student=student,
        date=date_,
    )

    _transactions.append(tx)
    _next_id += 1
    _recalc_and_store_balance()
    return tx


def get_all_transactions() -> List[Transaction]:
    return list(_transactions)


def get_balance() -> Balance:
    return _balance


# ---------- Adapter für Tests (DummyDB) ----------
class DummyDB:
    """
    Minimale OO-Hülle um die funktionale In-Memory-DB.
    Wird von den Tests erwartet: from myapp.adapters.db_memory import DummyDB
    """

    def __init__(self) -> None:
        _reset_storage()
        connect(seed=False)

    def add_transaction(self, amount: float, description: str) -> None:
        create_transaction(
            type_="einzahlung",
            amount=amount,
            description=description,
        )

    def get_balance(self) -> float:
        return get_balance().current_total
