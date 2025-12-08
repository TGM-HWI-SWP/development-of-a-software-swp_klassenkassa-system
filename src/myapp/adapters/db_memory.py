from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from myapp.models import Transaction, Balance

# Mapping wie bisher
TYPE_MAP_INCOMING = {"income": "einzahlung", "expense": "ausgabe"}


# ---------- In-Memory "Datenbank" ----------

_transactions: List[Transaction] = []
_balance: Balance = Balance(current_total=0.0)
_next_id: int = 1


# ---------- Verbindungs-API (Dummy) ----------

def connect() -> None:
    """Dummy-Connect, nur fürs Interface."""
    print("[MEMORY-DB] connected (in RAM)")


def disconnect() -> None:
    """Dummy-Disconnect, nur fürs Interface."""
    print("[MEMORY-DB] disconnected")


# ---------- Hilfsfunktionen intern ----------

def _normalize_type(t_type: str) -> str:
    """Mappt 'income'/'expense' auf 'einzahlung'/'ausgabe'."""
    return TYPE_MAP_INCOMING.get(t_type, t_type)


def calculate_balance(transactions: List[Transaction]) -> float:
    """Berechnet den Kontostand aus einer Transaktionsliste."""
    total = 0.0
    for t in transactions:
        if t.type == "einzahlung":
            total += t.amount
        else:
            total -= t.amount
    return total


def _recalc_and_store_balance() -> None:
    """Aktualisiert _balance.current_total basierend auf _transactions."""
    _balance.current_total = calculate_balance(_transactions)


# ---------- Öffentliche DB-Funktionen ----------

def get_all_transactions() -> List[Transaction]:
    """Alle Transaktionen der In-Memory-DB."""
    return list(_transactions)


def get_transaction_by_id(tx_id: int) -> Optional[Transaction]:
    for t in _transactions:
        if t.id == tx_id:
            return t
    return None


def create_transaction(
    type_: str,
    amount: float,
    description: str = "",
    timestamp: datetime | str | None = None,
    *,
    id_: int | None = None,
) -> Transaction:
    """Neue Transaktion anlegen und in die Memory-DB schreiben."""
    global _next_id

    norm_type = _normalize_type(type_)

    # Timestamp normalisieren
    if timestamp is None:
        ts = datetime.now()
    elif isinstance(timestamp, str):
        ts = datetime.fromisoformat(timestamp)
    else:
        ts = timestamp

    # ID vergeben (falls nicht vorgegeben)
    if id_ is None:
        id_ = _next_id
        _next_id += 1

    tx = Transaction(
        id=int(id_),
        type=norm_type,
        amount=float(amount),
        description=str(description),
        timestamp=ts,
    )
    _transactions.append(tx)
    _recalc_and_store_balance()
    return tx


def update_transaction(
    tx_id: int,
    *,
    type_: str | None = None,
    amount: float | None = None,
    description: str | None = None,
    timestamp: datetime | str | None = None,
) -> Optional[Transaction]:
    """Vorhandene Transaktion ändern."""
    tx = get_transaction_by_id(tx_id)
    if tx is None:
        return None

    if type_ is not None:
        tx.type = _normalize_type(type_)
    if amount is not None:
        tx.amount = float(amount)
    if description is not None:
        tx.description = str(description)
    if timestamp is not None:
        if isinstance(timestamp, str):
            tx.timestamp = datetime.fromisoformat(timestamp)
        else:
            tx.timestamp = timestamp

    _recalc_and_store_balance()
    return tx


def delete_transaction(tx_id: int) -> bool:
    """Transaktion löschen."""
    global _transactions
    before = len(_transactions)
    _transactions = [t for t in _transactions if t.id != tx_id]
    deleted = len(_transactions) < before
    if deleted:
        _recalc_and_store_balance()
    return deleted


def get_balance() -> Balance:
    """Aktuellen Balance-Stand zurückgeben."""
    # zur Sicherheit immer auf Basis der aktuellen Liste
    _recalc_and_store_balance()
    return _balance
