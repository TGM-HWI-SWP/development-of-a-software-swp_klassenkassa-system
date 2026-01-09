from __future__ import annotations

import os
from datetime import date as dt_date, datetime as dt
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import gradio as gr
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

TX_HEADERS: List[str] = ["id", "typ", "betrag", "beschreibung", "zeitstempel", "kategorie", "schüler", "datum"]

JsonDict = Dict[str, Any]
JsonList = List[JsonDict]


def _safe_get_json(url: str, default: Any) -> Any:
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default


def _normalize_tx(t: JsonDict) -> JsonDict:
    return {
        "id": t.get("id"),
        "typ": t.get("type"),
        "betrag": t.get("amount"),
        "beschreibung": t.get("description", "") or "",
        "zeitstempel": t.get("timestamp", "") or "",
        "kategorie": t.get("category", "") or "",
        "schüler": t.get("student", "") or "",
        "datum": t.get("date", "") or "",
    }


def _tx_rows(txs: JsonList) -> List[List[Any]]:
    return [[_normalize_tx(t).get(h) for h in TX_HEADERS] for t in txs]


def refresh_all(filter_text: str = "") -> Tuple[List[List[Any]], str]:
    txs = cast(JsonList, _safe_get_json(f"{BACKEND_URL}/transactions", default=[]))
    bal = cast(JsonDict, _safe_get_json(f"{BACKEND_URL}/balance", default={"current_total": 0}))

    if filter_text:
        ft = filter_text.strip().lower()

        def match(t: JsonDict) -> bool:
            n = _normalize_tx(t)
            blob = " ".join(str(n.get(k, "")) for k in TX_HEADERS).lower()
            return ft in blob

        txs = [t for t in txs if match(t)]

    rows = _tx_rows(txs)
    balance_str = f'{float(bal.get("current_total", 0)):.2f} €'
    return rows, balance_str


def _normalize_date_str(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return dt_date.today().isoformat()
    try:
        dt.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        raise gr.Error("Datum muss im Format YYYY-MM-DD sein (z.B. 2025-12-28).")


def add_transaction(
    t_type: str,
    amount: Union[int, float, None],
    category: str,
    student: str,
    desc: str,
    tx_date_str: str,
) -> Tuple[List[List[Any]], str]:
    payload: JsonDict = {
        "type": t_type,
        "amount": float(amount or 0),
        "description": desc or "",
        "category": category or "",
        "student": student or "",
        "date": _normalize_date_str(tx_date_str),
    }
    try:
        requests.post(f"{BACKEND_URL}/transactions", json=payload, timeout=10).raise_for_status()
    except Exception as e:
        raise gr.Error(f"Transaktion konnte nicht gespeichert werden: {e}")
    return refresh_all("")


def delete_selected_transaction(tx_table_data: List[List[Any]], selected_tx_idx: Optional[int]) -> Tuple[List[List[Any]], str, None]:
    if selected_tx_idx is None:
        raise gr.Error("Bitte zuerst eine Transaktion anklicken.")
    if selected_tx_idx < 0 or selected_tx_idx >= len(tx_table_data):
        raise gr.Error("Ungültige Auswahl.")

    tx_id = tx_table_data[selected_tx_idx][0]
    if not tx_id:
        raise gr.Error("Ungültige ID.")

    try:
        requests.delete(f"{BACKEND_URL}/transactions/{tx_id}", timeout=10).raise_for_status()
    except Exception as e:
        raise gr.Error(f"Löschen fehlgeschlagen: {e}")

    rows, bal = refresh_all("")
    return rows, bal, None


def refresh_savings_with_ids() -> List[List[str]]:
    goals = cast(JsonList, _safe_get_json(f"{BACKEND_URL}/savings-goals?limit=3", default=[]))
    rows: List[List[str]] = [[str(g["id"]), str(g["name"]), f'{float(g["amount"]):.2f} €'] for g in goals]
    while len(rows) < 3:
        rows.append(["", "", ""])
    return rows


def add_saving_goal(name: str, amount: Union[int, float, None]) -> List[List[str]]:
    name = (name or "").strip()
    if not name:
        return refresh_savings_with_ids()

    payload: JsonDict = {"name": name, "amount": float(amount or 0)}
    try:
        r = requests.post(f"{BACKEND_URL}/savings-goals", json=payload, timeout=10)
        if r.status_code >= 400:
            detail = r.json().get("detail", "Unbekannter Fehler")
            raise RuntimeError(detail)
    except Exception as e:
        raise gr.Error(f"Sparziel konnte nicht gespeichert werden: {e}")

    return refresh_savings_with_ids()


def delete_selected_saving_goal(table_data: List[List[Any]], selected_goal_idx: Optional[int]) -> Tuple[List[List[str]], None]:
    if selected_goal_idx is None:
        raise gr.Error("Bitte zuerst ein Sparziel anklicken.")
    if selected_goal_idx < 0 or selected_goal_idx >= len(table_data):
        raise gr.Error("Ungültige Auswahl.")

    goal_id = table_data[selected_goal_idx][0]
    if not goal_id:
        raise gr.Error("Diese Zeile kann nicht gelöscht werden.")

    try:
        requests.delete(f"{BACKEND_URL}/savings-goals/{goal_id}", timeout=10).raise_for_status()
    except Exception as e:
        raise gr.Error(f"Sparziel konnte nicht gelöscht werden: {e}")

    return refresh_savings_with_ids(), None


def refresh_students() -> List[List[str]]:
    students = cast(JsonList, _safe_get_json(f"{BACKEND_URL}/students", default=[]))
    return [[str(s["id"]), str(s["name"])] for s in students]


def add_student(name: str) -> List[List[str]]:
    name = (name or "").strip()
    if not name:
        return refresh_students()
    try:
        r = requests.post(f"{BACKEND_URL}/students", json={"name": name}, timeout=10)
        if r.status_code >= 400:
            detail = r.json().get("detail", "Unbekannter Fehler")
            raise RuntimeError(detail)
    except Exception as e:
        raise gr.Error(f"Schüler konnte nicht gespeichert werden: {e}")
    return refresh_students()


def on_tx_select(evt: gr.SelectData) -> int:
    if isinstance(evt.index, (tuple, list)):
        return int(evt.index[0])
    return int(evt.index)


def on_goal_select(evt: gr.SelectData) -> int:
    if isinstance(evt.index, (tuple, list)):
        return int(evt.index[0])
    return int(evt.index)


# ---------------- UI ----------------
with gr.Blocks(title="Klassenkassa – Verwaltungsoberfläche") as demo:
    gr.Markdown("# Klassenkassa – Verwaltung")

    selected_tx_idx = gr.State(None)
    selected_goal_idx = gr.State(None)

    with gr.Row():
        with gr.Column(scale=2):
            balance_big = gr.Textbox(label="Aktueller Kontostand", value="0.00 €", interactive=False)
        with gr.Column(scale=1):
            gr.Checkbox(label="Automatisch speichern", value=True)
            gr.Markdown("👤 Administrator")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## Sparziele (max. 3)")

            savings_table = gr.Dataframe(
                headers=["", "Sparziel", "Betrag"],
                value=refresh_savings_with_ids(),
                interactive=False,
                row_count=3,
                row_limits=(3, 3),
                column_count=3,
                column_limits=(3, 3),
            )

            savings_table.select(on_goal_select, inputs=None, outputs=selected_goal_idx)

            with gr.Row():
                btn_delete_goal = gr.Button("🗑️ Sparziel löschen", variant="stop")

            with gr.Accordion("➕ Neues Sparziel", open=False):
                goal_name = gr.Textbox(label="Bezeichnung")
                goal_amount = gr.Number(label="Betrag", value=0)
                btn_add_goal = gr.Button("Sparziel hinzufügen")

            btn_add_goal.click(add_saving_goal, inputs=[goal_name, goal_amount], outputs=[savings_table])
            btn_delete_goal.click(
                delete_selected_saving_goal,
                inputs=[savings_table, selected_goal_idx],
                outputs=[savings_table, selected_goal_idx],
            )

        with gr.Column(scale=3):
            gr.Markdown("## Statistik")
            gr.Textbox(label="Diagramm / Information", value="Hier erscheint später ein Diagramm.", interactive=False)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## Klasse & Schüler")
            gr.Textbox(label="Klasse", value="Klasse 5A")
            gr.Textbox(label="Klassenvorstand / Name", value="")

            gr.Markdown("### Schülerliste")
            students_table = gr.Dataframe(
                headers=["ID", "Name"],
                value=refresh_students(),
                interactive=False,
                row_count=10,
                row_limits=(1, 50),
                column_count=2,
                column_limits=(2, 2),
            )

            with gr.Accordion("➕ Neuer Schüler", open=False):
                student_name = gr.Textbox(label="Name")
                btn_add_student = gr.Button("Schüler hinzufügen")
                btn_add_student.click(add_student, inputs=[student_name], outputs=[students_table])

        with gr.Column(scale=3):
            gr.Markdown("## Neue Transaktion")
            tx_amount = gr.Number(label="*Betrag", value=0)
            tx_type = gr.Dropdown(["einzahlung", "ausgabe"], value="einzahlung", label="*Transaktionstyp")
            tx_category = gr.Textbox(label="*Kategorie", placeholder="z. B. Ausflug, Material, Spende")
            tx_student = gr.Textbox(label="Schüler")
            tx_desc = gr.Textbox(label="Beschreibung", lines=3)
            tx_date = gr.Textbox(label="Datum (YYYY-MM-DD)", value=str(dt_date.today()))
            gr.Markdown("*Mit \\* markierte Felder sind Pflichtfelder!*")

            with gr.Row():
                btn_add_tx = gr.Button("Transaktion hinzufügen", variant="primary")
                btn_refresh = gr.Button("Aktualisieren")

    gr.Markdown("## Transaktionen")
    with gr.Row():
        tx_filter = gr.Textbox(label="Filter", placeholder="Suche nach Datum, Name, Betrag, Kategorie, Schüler …")
        btn_apply_filter = gr.Button("Filter anwenden")

    tx_table = gr.Dataframe(
        headers=TX_HEADERS,
        interactive=False,
        row_count=15,
        row_limits=(1, 200),
        column_count=len(TX_HEADERS),
        column_limits=(len(TX_HEADERS), len(TX_HEADERS)),
    )

    tx_table.select(on_tx_select, inputs=None, outputs=selected_tx_idx)

    with gr.Row():
        btn_delete_tx = gr.Button("🗑️ Transaktion löschen", variant="stop")

    btn_refresh.click(refresh_all, inputs=[tx_filter], outputs=[tx_table, balance_big])
    btn_apply_filter.click(refresh_all, inputs=[tx_filter], outputs=[tx_table, balance_big])
    btn_add_tx.click(
        add_transaction,
        inputs=[tx_type, tx_amount, tx_category, tx_student, tx_desc, tx_date],
        outputs=[tx_table, balance_big],
    )
    btn_delete_tx.click(
        delete_selected_transaction,
        inputs=[tx_table, selected_tx_idx],
        outputs=[tx_table, balance_big, selected_tx_idx],
    )

    demo.load(refresh_all, inputs=[tx_filter], outputs=[tx_table, balance_big])
    demo.load(refresh_savings_with_ids, outputs=[savings_table])
    demo.load(refresh_students, outputs=[students_table])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
