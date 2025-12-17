from __future__ import annotations

import os
from datetime import datetime, date
from typing import List, Optional

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection

from myapp.models import Transaction, Balance


# -----------------------------------------------------------------------------
# Config (Docker: nutze Service-Name "mongo" statt localhost)
# -----------------------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB", "klassenkassa")

COL_TX = "transactions"
COL_BAL = "balance"


_client: MongoClient | None = None
_db = None
_tx: Collection | None = None
_bal: Collection | None = None


def connect() -> None:
    global _client, _db, _tx, _bal

    _client = MongoClient(MONGO_URI)
    _db = _client[DB_NAME]
    _tx = _db[COL_TX]
    _bal = _db[COL_BAL]

    # fortlaufende int-ID (unique)
    _tx.create_index([("id", ASCENDING)], unique=True)

    # Balance-Dokument sicherstellen
    _bal.update_one(
        {"_id": "balance"},
        {"$setOnInsert": {"current_total": 0.0}},
        upsert=True,
    )


def disconnect() -> None:
    global _client, _db, _tx, _bal
    if _client:
        _client.close()
    _client = None
    _db = None
    _tx = None
    _bal = None


def _require() -> tuple[Collection, Collection]:
    if _tx is None or _bal is None:
        raise RuntimeError("MongoDB not connected. Call db.connect() first.")
    return _tx, _bal


def _tx_to_model(d: dict) -> Transaction:
    # timestamp: in DB ist es iso string, daher hier wieder datetime machen
    ts = d.get("timestamp")
    ts_dt = datetime.fromisoformat(ts) if isinstance(ts, str) else ts

    # Optional: date (YYYY-MM-DD) wieder in date umwandeln, falls vorhanden
    dt_val = d.get("date")
    if isinstance(dt_val, str) and dt_val:
        try:
            dt_val = date.fromisoformat(dt_val)
        except ValueError:
            dt_val = None

    return Transaction(
        id=int(d["id"]),
        type=str(d["type"]),
        amount=float(d["amount"]),
        description=str(d.get("description", "")),
        timestamp=ts_dt,
        # Falls dein Transaction-Model diese Felder (noch) nicht hat, dann entferne sie.
        # Wenn sie existieren: super, dann werden sie mitgefüllt.
        category=str(d.get("category", "")),
        student=str(d.get("student", "")),
        date=dt_val,
    )


def _recalculate_balance(tx: Collection, bal: Collection) -> float:
    income = tx.aggregate(
        [
            {"$match": {"type": "einzahlung"}},
            {"$group": {"_id": None, "sum": {"$sum": "$amount"}}},
        ]
    )
    expense = tx.aggregate(
        [
            {"$match": {"type": "ausgabe"}},
            {"$group": {"_id": None, "sum": {"$sum": "$amount"}}},
        ]
    )

    income_sum = 0.0
    expense_sum = 0.0
    for x in income:
        income_sum = float(x["sum"])
    for x in expense:
        expense_sum = float(x["sum"])

    total = income_sum - expense_sum
    bal.update_one({"_id": "balance"}, {"$set": {"current_total": total}}, upsert=True)
    return total


def _next_id(tx: Collection) -> int:
    last = tx.find_one({}, sort=[("id", -1)])
    return 1 if not last else int(last["id"]) + 1


# -------------------- CRUD: Transactions --------------------

def get_all_transactions() -> List[Transaction]:
    tx, _ = _require()
    docs = tx.find({}).sort("id", ASCENDING)
    return [_tx_to_model(d) for d in docs]


def get_transaction_by_id(tx_id: int) -> Optional[Transaction]:
    tx, _ = _require()
    d = tx.find_one({"id": int(tx_id)})
    return _tx_to_model(d) if d else None


def create_transaction(
    type_: str,
    amount: float,
    description: str = "",
    timestamp: datetime | None = None,
    *,
    category: str = "",
    student: str = "",
    date_: date | None = None,
) -> Transaction:
    tx, bal = _require()

    if type_ not in ("einzahlung", "ausgabe"):
        raise ValueError("type_ must be 'einzahlung' or 'ausgabe'")

    if timestamp is None:
        timestamp = datetime.now()

    if date_ is None:
        date_ = date.today()

    # Minus verhindern
    current_total = get_balance().current_total
    new_total = current_total + float(amount) if type_ == "einzahlung" else current_total - float(amount)
    if new_total < 0:
        raise ValueError("Diese Transaktion würde den Kontostand ins Minus bringen.")

    new_id = _next_id(tx)
    doc = {
        "id": new_id,
        "type": type_,
        "amount": float(amount),
        "description": str(description),
        "timestamp": timestamp.isoformat(),
        "category": str(category),
        "student": str(student),
        "date": date_.isoformat(),  # YYYY-MM-DD
    }
    tx.insert_one(doc)
    _recalculate_balance(tx, bal)
    return get_transaction_by_id(new_id)  # type: ignore


def update_transaction(
    tx_id: int,
    *,
    type_: str | None = None,
    amount: float | None = None,
    description: str | None = None,
    timestamp: datetime | None = None,
    category: str | None = None,
    student: str | None = None,
    date_: date | None = None,
) -> Optional[Transaction]:
    tx, bal = _require()
    existing = get_transaction_by_id(tx_id)
    if existing is None:
        return None

    new_type = existing.type if type_ is None else type_
    new_amount = existing.amount if amount is None else float(amount)
    new_desc = existing.description if description is None else str(description)
    new_ts = existing.timestamp if timestamp is None else timestamp

    # Wenn dein Transaction Model category/student/date hat:
    new_cat = getattr(existing, "category", "") if category is None else category
    new_student = getattr(existing, "student", "") if student is None else student
    new_date = getattr(existing, "date", None) if date_ is None else date_

    if new_type not in ("einzahlung", "ausgabe"):
        raise ValueError("type_ must be 'einzahlung' or 'ausgabe'")

    update_doc = {
        "type": new_type,
        "amount": new_amount,
        "description": new_desc,
        "timestamp": new_ts.isoformat(),
        "category": str(new_cat or ""),
        "student": str(new_student or ""),
        "date": new_date.isoformat() if new_date else "",
    }

    tx.update_one({"id": int(tx_id)}, {"$set": update_doc})

    total = _recalculate_balance(tx, bal)
    if total < 0:
        raise ValueError("Update würde den Kontostand ins Minus bringen.")

    return get_transaction_by_id(tx_id)


def delete_transaction(tx_id: int) -> bool:
    tx, bal = _require()
    res = tx.delete_one({"id": int(tx_id)})
    if res.deleted_count:
        _recalculate_balance(tx, bal)
        return True
    return False


# -------------------- Balance --------------------

def get_balance() -> Balance:
    _, bal = _require()
    d = bal.find_one({"_id": "balance"})
    if not d:
        return Balance(current_total=0.0)
    return Balance(current_total=float(d.get("current_total", 0.0)))
