from __future__ import annotations

from datetime import date as Date, datetime
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple, cast

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import myapp.adapters as adapters

app = FastAPI(title="Klassenkassa Backend")

MAX_SAVING_GOALS = 3


class BalanceLike(Protocol):
    current_total: float


class DBPort(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...

    def get_all_transactions(self) -> Sequence[Any]: ...

    def create_transaction(
        self,
        type_: str,
        amount: float,
        description: str = "",
        timestamp: Optional[datetime] = None,
        category: str = "",
        student: str = "",
        date_: Optional[Date] = None,
    ) -> Any: ...

    def delete_transaction(self, tx_id: int) -> bool: ...
    def get_balance(self) -> BalanceLike: ...

    def get_savings_goals(self, limit: int = 3) -> List[Dict[str, Any]]: ...
    def create_savings_goal(self, name: str, amount: float, created_at: datetime) -> Dict[str, Any]: ...
    def delete_savings_goal(self, goal_id: int) -> bool: ...

    def get_students(self) -> List[Dict[str, Any]]: ...
    def create_student(self, name: str, created_at: datetime) -> Dict[str, Any]: ...
    def delete_student(self, student_id: int) -> bool: ...


# ✅ Fix: module -> Any -> cast(DBPort)
db_any: Any = adapters.db
db: DBPort = cast(DBPort, db_any)


class TxIn(BaseModel):
    type: str
    amount: float
    description: str = ""
    category: str = ""
    student: str = ""
    date: Date = Field(default_factory=Date.today)


class TxOut(BaseModel):
    id: int
    type: str
    amount: float
    description: str
    timestamp: str
    category: str = ""
    student: str = ""
    date: str = ""


class SavingGoalIn(BaseModel):
    name: str = Field(..., min_length=1)
    amount: float = 0.0


class SavingGoalOut(BaseModel):
    id: int
    name: str
    amount: float
    created_at: str


class StudentIn(BaseModel):
    name: str = Field(..., min_length=1)


class StudentOut(BaseModel):
    id: int
    name: str
    created_at: str


@app.on_event("startup")
def _startup() -> None:
    db.connect()


@app.on_event("shutdown")
def _shutdown() -> None:
    try:
        db.disconnect()
    except Exception:
        pass


@app.get("/transactions", response_model=List[TxOut])
def list_transactions() -> List[TxOut]:
    txs = db.get_all_transactions()
    out: List[TxOut] = []

    for t in txs:
        t_date = getattr(t, "date", None)
        out.append(
            TxOut(
                id=int(getattr(t, "id")),
                type=str(getattr(t, "type")),
                amount=float(getattr(t, "amount")),
                description=str(getattr(t, "description", "") or ""),
                timestamp=getattr(t, "timestamp").isoformat(),
                category=str(getattr(t, "category", "") or ""),
                student=str(getattr(t, "student", "") or ""),
                date=t_date.isoformat() if t_date else "",
            )
        )
    return out


@app.post("/transactions", response_model=TxOut)
def add_transaction(tx: TxIn) -> TxOut:
    try:
        created = db.create_transaction(
            type_=tx.type,
            amount=tx.amount,
            description=tx.description,
            timestamp=datetime.now(),
            category=tx.category,
            student=tx.student,
            date_=tx.date,
        )

        created_date = getattr(created, "date", None)
        return TxOut(
            id=int(getattr(created, "id")),
            type=str(getattr(created, "type")),
            amount=float(getattr(created, "amount")),
            description=str(getattr(created, "description", "") or ""),
            timestamp=getattr(created, "timestamp").isoformat(),
            category=str(getattr(created, "category", "") or ""),
            student=str(getattr(created, "student", "") or ""),
            date=created_date.isoformat() if created_date else "",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: int) -> Dict[str, bool]:
    ok = db.delete_transaction(tx_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Transaktion nicht gefunden")
    return {"ok": True}


@app.get("/balance")
def get_balance() -> Dict[str, float]:
    b = db.get_balance()
    return {"current_total": float(b.current_total)}


@app.get("/savings-goals", response_model=List[SavingGoalOut])
def list_savings_goals(limit: int = MAX_SAVING_GOALS) -> List[SavingGoalOut]:
    goals = db.get_savings_goals(limit=limit)
    return [
        SavingGoalOut(id=int(g["id"]), name=str(g["name"]), amount=float(g["amount"]), created_at=str(g["created_at"]))
        for g in goals
    ]


@app.post("/savings-goals", response_model=SavingGoalOut)
def add_savings_goal(goal: SavingGoalIn) -> SavingGoalOut:
    try:
        created = db.create_savings_goal(name=goal.name, amount=goal.amount, created_at=datetime.now())
        return SavingGoalOut(
            id=int(created["id"]),
            name=str(created["name"]),
            amount=float(created["amount"]),
            created_at=str(created["created_at"]),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/savings-goals/{goal_id}")
def delete_savings_goal(goal_id: int) -> Dict[str, bool]:
    ok = db.delete_savings_goal(goal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sparziel nicht gefunden")
    return {"ok": True}


@app.get("/students", response_model=List[StudentOut])
def list_students() -> List[StudentOut]:
    students = db.get_students()
    return [StudentOut(id=int(s["id"]), name=str(s["name"]), created_at=str(s["created_at"])) for s in students]


@app.post("/students", response_model=StudentOut)
def add_student(s: StudentIn) -> StudentOut:
    try:
        created = db.create_student(name=s.name, created_at=datetime.now())
        return StudentOut(id=int(created["id"]), name=str(created["name"]), created_at=str(created["created_at"]))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/students/{student_id}")
def delete_student(student_id: int) -> Dict[str, bool]:
    ok = db.delete_student(student_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Schüler nicht gefunden")
    return {"ok": True}


@app.get("/stats/daily")
def stats_daily(days: int = 30) -> List[Dict[str, Any]]:
    return []
