from typing import List, Tuple
from datetime import datetime

from myapp.models import Transaction, Balance

TYPE_MAP_INCOMING = {"income": "einzahlung", "expense": "ausgabe"}

# --- In-Memory-"Datenbank" ---
_transactions: List[Transaction] = []
_balance: Balance = Balance(current_total=0.0)
_next_id: int = 1


def _parse_transaction(obj) -> Transaction:
    """Wird aktuell nicht mehr für JSON gebraucht, kann aber für spätere Imports nützlich sein."""
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


def _recalculate_internal() -> None:
    """Aktualisiert den globalen Kontostand basierend auf _transactions."""
    _balance.current_total = calculate_balance(_transactions)


# -------------------------------------------------
# Öffentliche API – gleiche Signaturen wie vorher
# -------------------------------------------------

def load_from_json(path: str) -> Tuple[List[Transaction], Balance]:
    """
    Früher: JSON von 'path' laden.
    Jetzt: liefert einfach den aktuellen In-Memory-Stand zurück.
    'path' wird ignoriert, bleibt aber im Interface.
    """
    # Kopie der Liste zurückgeben, damit externe Änderungen nicht unsere interne Liste zerschießen
    return list(_transactions), Balance(current_total=_balance.current_total)


def save_to_json(path: str, transactions: List[Transaction], balance: Balance) -> None:
    """
    Früher: JSON nach 'path' speichern.
    Jetzt: keine Datei mehr. Wir übernehmen nur den Stand in die In-Memory-DB.
    """
    global _transactions, _balance, _next_id

    # internen Zustand aus den übergebenen Daten aktualisieren
    _transactions = list(transactions)
    _balance = Balance(current_total=float(balance.current_total))

    # nächstes ID ermitteln
    if _transactions:
        _next_id = max(t.id for t in _transactions) + 1
    else:
        _next_id = 1

    # Keine Datei schreiben – Memory-DB hat keine Persistenz


def calculate_balance(transactions: List[Transaction]) -> float:
    total = 0.0
    for t in transactions:
        if t.type == "einzahlung":
            total += t.amount
        else:
            total -= t.amount
    return total


def add_transaction(transactions: List[Transaction], t: Transaction) -> None:
    """
    Fügt eine Transaktion sowohl zur übergebenen Liste als auch zur internen In-Memory-DB hinzu.
    """
    global _next_id

    # Falls die Transaktion keine sinnvolle ID hat, eine neue vergeben
    if t.id is None or t.id == 0:
        t.id = _next_id
        _next_id += 1
    else:
        # sicherstellen, dass _next_id hinterher nicht kollidiert
        _next_id = max(_next_id, t.id + 1)

    # zur externen Liste hinzufügen (für Kompatibilität mit bestehendem Code)
    transactions.append(t)

    # auch in unserer "Datenbank" speichern
    _transactions.append(t)
    _recalculate_internal()
