from fastapi import FastAPI, HTTPException
from datetime import datetime, date as Date
from pydantic import BaseModel, Field
from typing import List
from myapp.adapters import db

app = FastAPI(title="Klassenkassa Backend")


# -----------------------
# Models
# -----------------------
class TxIn(BaseModel):
    type: str
    amount: float
    description: str = ""
    category: str = ""
    student: str = ""
    date: Date = Field(default_factory=Date.today)


class TxOut(BaseModel):
    id: str
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
    id: str
    name: str
    amount: float
    created_at: str


class StudentIn(BaseModel):
    name: str = Field(..., min_length=1)


class StudentOut(BaseModel):
    id: str
    name: str
    created_at: str


# -----------------------
# Lifecycle
# -----------------------
@app.on_event("startup")
def _startup():
    db.connect()


@app.on_event("shutdown")
def _shutdown():
    try:
        db.disconnect()
    except Exception:
        pass


# -----------------------
# Transactions
# -----------------------
@app.get("/transactions", response_model=List[TxOut])
def list_transactions():
    txs = db.get_all_transactions()
    out = []
    for t in txs:
        t_date = getattr(t, "date", None)
        out.append(
            {
                "id": t.id,
                "type": t.type,
                "amount": t.amount,
                "description": getattr(t, "description", "") or "",
                "timestamp": t.timestamp.isoformat(),
                "category": getattr(t, "category", "") or "",
                "student": getattr(t, "student", "") or "",
                "date": t_date.isoformat() if t_date else "",
            }
        )
    return out


@app.post("/transactions", response_model=TxOut)
def add_transaction(tx: TxIn):
    try:
        tx_date = tx.date or Date.today()
        created = db.create_transaction(
            type_=tx.type,
            amount=tx.amount,
            description=tx.description,
            timestamp=datetime.now(),
            category=tx.category,
            student=tx.student,
            date_=tx_date,
        )

        created_date = getattr(created, "date", None)
        return {
            "id": created.id,
            "type": created.type,
            "amount": created.amount,
            "description": getattr(created, "description", "") or "",
            "timestamp": created.timestamp.isoformat(),
            "category": getattr(created, "category", "") or "",
            "student": getattr(created, "student", "") or "",
            "date": created_date.isoformat() if created_date else "",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
# Balance
# -----------------------
@app.get("/balance")
def get_balance():
    b = db.get_balance()
    return {"current_total": b.current_total}


# -----------------------
# Savings Goals
# -----------------------
@app.get("/savings-goals", response_model=List[SavingGoalOut])
def list_savings_goals(limit: int = 3):
    goals = db.get_savings_goals(limit=limit)
    return [
        {
            "id": g.id,
            "name": g.name,
            "amount": g.amount,
            "created_at": g.created_at.isoformat(),
        }
        for g in goals
    ]


@app.post("/savings-goals", response_model=SavingGoalOut)
def add_savings_goal(goal: SavingGoalIn):
    try:
        created = db.create_savings_goal(
            name=goal.name, amount=goal.amount, created_at=datetime.now()
        )
        return {
            "id": created.id,
            "name": created.name,
            "amount": created.amount,
            "created_at": created.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
# Students
# -----------------------
@app.get("/students", response_model=List[StudentOut])
def list_students():
    students = db.get_students()
    return [
        {
            "id": s.id,
            "name": s.name,
            "created_at": s.created_at.isoformat(),
        }
        for s in students
    ]


@app.post("/students", response_model=StudentOut)
def add_student(s: StudentIn):
    try:
        created = db.create_student(name=s.name, created_at=datetime.now())
        return {
            "id": created.id,
            "name": created.name,
            "created_at": created.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
# Optional: Stats fürs Chart
# -----------------------
@app.get("/stats/daily")
def stats_daily(days: int = 30):
    """
    Gibt z.B. [{"date":"2025-12-01","income":10,"expense":5,"net":5}, ...]
    """
    return db.get_daily_stats(days=days)
