from __future__ import annotations

import os
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from myapp.models import Balance, Transaction

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
DB_NAME = os.getenv("MONGO_DB", "klassenkassa")

COL_TX = "transactions"
COL_BAL = "balance"
COL_GOALS = "savings_goals"
COL_STUDENTS = "students"

MAX_SAVING_GOALS = 3

Doc = Dict[str, Any]

_client: Optional[MongoClient[Doc]] = None
_db: Optional[Database[Doc]] = None
_tx: Optional[Collection[Doc]] = None
_bal: Optional[Collection[Doc]] = None
_goals: Optional[Collection[Doc]] = None
_students: Optional[Collection[Doc]] = None


def connect() -> None:
    global _client, _db, _tx, _bal, _goals, _students

    _client = MongoClient[Doc](MONGO_URI)
    _db = _client[DB_NAME]

    _tx = _db[COL_TX]
    _bal = _db[COL_BAL]
    _goals = _db[COL_GOALS]
    _students = _db[COL_STUDENTS]

    _tx.create_index([("id", ASCENDING)], unique=True)
    _goals.create_index([("id", ASCENDING)], unique=True)
    _students.create_index([("id", ASCENDING)], unique=True)
    _students.create_index([("name", ASCENDING)], unique=True)

    _bal.update_one(
        {"_id": "balance"},
        {"$setOnInsert": {"current_total": 0.0}},
        upsert=True,
    )


def disconnect() -> None:
    global _client, _db, _tx, _bal, _goals, _students
    if _client is not None:
        _client.close()
    _client = None
    _db = None
    _tx = None
    _bal = None
    _goals = None
    _students = None


def _require_tx_bal() -> Tuple[Collection[Doc], Collection[Doc]]:
    if _tx is None or _bal is None:
        raise RuntimeError("MongoDB not connected. Call db.connect() first.")
    return _tx, _bal


def _require_goals() -> Collection[Doc]:
    if _goals is None:
        raise RuntimeError("MongoDB not connected (goals). Call db.connect() first.")
    return _goals


def _require_students() -> Collection[Doc]:
    if _students is None:
        raise RuntimeError("MongoDB not connected (students). Call db.connect() first.")
    return _students


def _next_id_for(col: Collection[Doc]) -> int:
    last = col.find_one({}, sort=[("id", -1)])
    return 1 if not last else int(last.get("id", 0)) + 1


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.now()
    return datetime.now()


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            return date.fromisoformat(s)
        except ValueError:
            return None
    return None


def _tx_to_model(d: Doc) -> Transaction:
    return Transaction(
        id=int(d.get("id", 0)),
        type=str(d.get("type", "einzahlung")),
        amount=float(d.get("amount", 0.0)),
        description=str(d.get("description", "") or ""),
        timestamp=_parse_timestamp(d.get("timestamp")),
        category=str(d.get("category", "") or ""),
        student=str(d.get("student", "") or ""),
        date=_parse_date(d.get("date")),
    )


def _recalculate_balance(tx: Collection[Doc], bal: Collection[Doc]) -> float:
    income = tx.aggregate(
        [{"$match": {"type": "einzahlung"}}, {"$group": {"_id": None, "sum": {"$sum": "$amount"}}}]
    )
    expense = tx.aggregate(
        [{"$match": {"type": "ausgabe"}}, {"$group": {"_id": None, "sum": {"$sum": "$amount"}}}]
    )

    income_sum = 0.0
    expense_sum = 0.0

    for x in income:
        # x ist Doc-ähnlich
        if isinstance(x, dict):
            income_sum = float(x.get("sum", 0.0))
    for x in expense:
        if isinstance(x, dict):
            expense_sum = float(x.get("sum", 0.0))

    total = income_sum - expense_sum
    bal.update_one({"_id": "balance"}, {"$set": {"current_total": total}}, upsert=True)
    return total


# -------------------- CRUD: Transactions --------------------

def get_all_transactions() -> List[Transaction]:
    tx, _ = _require_tx_bal()
    docs = tx.find({}).sort("id", ASCENDING)
    return [_tx_to_model(d) for d in docs]


def get_transaction_by_id(tx_id: int) -> Optional[Transaction]:
    tx, _ = _require_tx_bal()
    d = tx.find_one({"id": int(tx_id)})
    return _tx_to_model(d) if d else None


def get_balance() -> Balance:
    _, bal = _require_tx_bal()
    d = bal.find_one({"_id": "balance"})
    if not d:
        return Balance(current_total=0.0)
    return Balance(current_total=float(d.get("current_total", 0.0)))


def create_transaction(
    type_: str,
    amount: float,
    description: str = "",
    timestamp: Optional[datetime] = None,
    category: str = "",
    student: str = "",
    date_: Optional[date] = None,
) -> Transaction:
    tx, bal = _require_tx_bal()

    if type_ not in ("einzahlung", "ausgabe"):
        raise ValueError("type_ must be 'einzahlung' or 'ausgabe'")

    if timestamp is None:
        timestamp = datetime.now()

    if date_ is None:
        date_ = date.today()

    current_total = get_balance().current_total
    new_total = current_total + float(amount) if type_ == "einzahlung" else current_total - float(amount)
    if new_total < 0:
        raise ValueError("Diese Transaktion würde den Kontostand ins Minus bringen.")

    new_id = _next_id_for(tx)
    doc: Doc = {
        "id": new_id,
        "type": type_,
        "amount": float(amount),
        "description": str(description),
        "timestamp": timestamp.isoformat(),
        "category": str(category),
        "student": str(student),
        "date": date_.isoformat(),
    }

    tx.insert_one(doc)
    _recalculate_balance(tx, bal)

    created = tx.find_one({"id": new_id})
    if not created:
        raise RuntimeError("Insert failed: transaction not found after insert.")
    return _tx_to_model(created)


def delete_transaction(tx_id: int) -> bool:
    tx, bal = _require_tx_bal()
    res = tx.delete_one({"id": int(tx_id)})
    if int(res.deleted_count) > 0:
        _recalculate_balance(tx, bal)
        return True
    return False


# -------------------- Savings Goals --------------------

def count_savings_goals() -> int:
    goals = _require_goals()
    return int(goals.count_documents({}))


def get_savings_goals(limit: int = MAX_SAVING_GOALS) -> List[Dict[str, Any]]:
    goals = _require_goals()
    docs = goals.find({}).sort("id", -1).limit(int(limit))
    return [
        {"id": int(d.get("id", 0)), "name": str(d.get("name", "")), "amount": float(d.get("amount", 0.0)), "created_at": str(d.get("created_at", ""))}
        for d in docs
    ]


def create_savings_goal(name: str, amount: float, created_at: Optional[datetime] = None) -> Dict[str, Any]:
    goals = _require_goals()
    name = (name or "").strip()
    if not name:
        raise ValueError("Name darf nicht leer sein.")
    if count_savings_goals() >= MAX_SAVING_GOALS:
        raise ValueError(f"Maximal {MAX_SAVING_GOALS} Sparziele erlaubt.")
    if created_at is None:
        created_at = datetime.now()

    new_id = _next_id_for(goals)
    doc: Dict[str, Any] = {"id": new_id, "name": name, "amount": float(amount or 0.0), "created_at": created_at.isoformat()}
    goals.insert_one(doc)  # Doc passt zu Collection[Doc]
    return doc


def delete_savings_goal(goal_id: int) -> bool:
    goals = _require_goals()
    res = goals.delete_one({"id": int(goal_id)})
    return bool(res.deleted_count)


# -------------------- Students --------------------

def get_students() -> List[Dict[str, Any]]:
    students = _require_students()
    docs = students.find({}).sort("id", ASCENDING)
    return [{"id": int(d.get("id", 0)), "name": str(d.get("name", "")), "created_at": str(d.get("created_at", ""))} for d in docs]


def create_student(name: str, created_at: Optional[datetime] = None) -> Dict[str, Any]:
    students = _require_students()
    name = (name or "").strip()
    if not name:
        raise ValueError("Name darf nicht leer sein.")
    if created_at is None:
        created_at = datetime.now()

    new_id = _next_id_for(students)
    doc: Dict[str, Any] = {"id": new_id, "name": name, "created_at": created_at.isoformat()}
    students.insert_one(doc)
    return doc


def delete_student(student_id: int) -> bool:
    students = _require_students()
    res = students.delete_one({"id": int(student_id)})
    return bool(res.deleted_count)
