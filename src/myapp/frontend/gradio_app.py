import os
import requests
import gradio as gr
from datetime import date as dt_date

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

def _safe_get_json(url, default):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return default

# -----------------------
# Transaktionen
TX_HEADERS = ["id", "typ", "betrag", "beschreibung", "zeitstempel", "kategorie", "schüler", "datum"]

def _normalize_tx(t):
    return {
        "id": t.get("id"),
        "typ": t.get("type"),
        "betrag": t.get("amount"),
        "beschreibung": t.get("description", ""),
        "zeitstempel": t.get("timestamp", ""),
        "kategorie": t.get("category", ""),
        "schüler": t.get("student", ""),
        "datum": t.get("date", ""),
    }

def _tx_rows(txs):
    return [[_normalize_tx(t)[h] for h in TX_HEADERS] for t in txs]

def refresh_all(filter_text=""):
    txs = _safe_get_json(f"{BACKEND_URL}/transactions", default=[])
    bal = _safe_get_json(f"{BACKEND_URL}/balance", default={"current_total": 0})

    if filter_text:
        ft = filter_text.strip().lower()

        def match(t):
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
        return ""
    # akzeptiert YYYY-MM-DD; alles andere wird trotzdem als String gesendet,
    # das Backend entscheidet, wie damit umgegangen wird
    return s

def add_transaction(t_type, amount, category, student, desc, tx_date_str):
    payload = {
        "type": t_type,
        "amount": float(amount or 0),
        "description": desc or "",
        "category": category or "",
        "student": student or "",
        "date": _normalize_date_str(tx_date_str),
    }
    requests.post(f"{BACKEND_URL}/transactions", json=payload, timeout=10).raise_for_status()
    return refresh_all("")

# -----------------------
# Sparziele (lokal)
SAVINGS = [
    {"name": "neues Ziel", "amount": 0.0},
    {"name": "Klassenfahrt", "amount": 200.0},
    {"name": "Eis", "amount": 50.0},
]

def list_savings():
    top = SAVINGS[:3]
    return [[s["name"], f'{float(s["amount"]):.2f} €'] for s in top]

def add_saving_goal(name, amount):
    name = (name or "").strip()
    if not name:
        return list_savings()
    SAVINGS.insert(0, {"name": name, "amount": float(amount or 0)})
    return list_savings()

# -----------------------
# UI
with gr.Blocks(title="Klassenkassa – Verwaltungsoberfläche") as demo:
    gr.Markdown("# Klassenkassa – Verwaltung")

    with gr.Row():
        with gr.Column(scale=2):
            balance_big = gr.Textbox(label="Aktueller Kontostand", value="0.00 €", interactive=False)
        with gr.Column(scale=1):
            autosave = gr.Checkbox(label="Automatisch speichern", value=True)
            gr.Markdown("👤 Administrator")

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## Sparziele (max. 3)")
            savings_table = gr.Dataframe(
                headers=["Sparziel", "Betrag"],
                value=list_savings(),
                interactive=False,
                row_count=(3, "fixed"),
                col_count=(2, "fixed"),
            )
            with gr.Accordion("➕ Neues Sparziel", open=False):
                goal_name = gr.Textbox(label="Bezeichnung")
                goal_amount = gr.Number(label="Betrag", value=0)
                btn_add_goal = gr.Button("Sparziel hinzufügen")
                btn_add_goal.click(add_saving_goal, inputs=[goal_name, goal_amount], outputs=[savings_table])

        with gr.Column(scale=3):
            gr.Markdown("## Statistik")
            gr.Markdown("*(Platzhalter für Diagramme, z. B. Kontostand-Verlauf)*")
            gr.Textbox(label="Diagramm / Information", value="Hier erscheint später ein Diagramm.", interactive=False)

    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## Klasse & Schüler")
            class_name = gr.Textbox(label="Klasse", value="Klasse 5A")
            teacher_name = gr.Textbox(label="Klassenvorstand / Name", value="")

            gr.Markdown("### Schülerliste")
            students_table = gr.Dataframe(
                headers=["ID", "Name"],
                value=[[1, "Schüler A"], [2, "Schüler B"], [3, "..."]],
                interactive=False,
                row_count=(5, "dynamic"),
                col_count=(2, "fixed"),
            )

        with gr.Column(scale=3):
            gr.Markdown("## Neue Transaktion")
            tx_amount = gr.Number(label="*Betrag", value=0)
            tx_type = gr.Dropdown(["einzahlung", "ausgabe"], value="einzahlung", label="*Transaktionstyp")
            tx_category = gr.Textbox(label="*Kategorie", placeholder="z. B. Ausflug, Material, Spende")
            tx_student = gr.Textbox(label="Schüler")
            tx_desc = gr.Textbox(label="Beschreibung", lines=3)
            tx_date = gr.Textbox(label="Datum (YYYY-MM-DD)", value=str(dt_date.today()))
            gr.Markdown(
        "*Mit \\* markierte Felder sind Pflichtfelder!*"
            )
            with gr.Row():
                btn_add_tx = gr.Button("Transaktion hinzufügen", variant="primary")
                btn_refresh = gr.Button("Aktualisieren")

    gr.Markdown("## Transaktionen")
    with gr.Row():
        tx_filter = gr.Textbox(
            label="Filter",
            placeholder="Suche nach Datum, Name, Betrag, Kategorie, Schüler …"
        )
        btn_apply_filter = gr.Button("Filter anwenden")

    tx_table = gr.Dataframe(
        headers=TX_HEADERS,
        interactive=False,
        row_count=(15, "dynamic")
    )

    btn_refresh.click(refresh_all, inputs=[tx_filter], outputs=[tx_table, balance_big])
    btn_apply_filter.click(refresh_all, inputs=[tx_filter], outputs=[tx_table, balance_big])
    btn_add_tx.click(
        add_transaction,
        inputs=[tx_type, tx_amount, tx_category, tx_student, tx_desc, tx_date],
        outputs=[tx_table, balance_big]
    )

    demo.load(refresh_all, inputs=[tx_filter], outputs=[tx_table, balance_big])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
