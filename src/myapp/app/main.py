import sys
from pathlib import Path
import argparse
from datetime import datetime



# Adjust sys.path for direct execution
if __package__ is None:

    p = Path(__file__).resolve()
    src_dir = None
    for parent in p.parents:
        if (parent / "myapp").is_dir():
            src_dir = parent
            break
    if src_dir is None:
        for parent in p.parents:
            if parent.name == "src":
                src_dir = parent
                break
    if src_dir is None:
        try:
            src_dir = p.parents[2]
        except Exception:
            src_dir = p.parent
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

# imports after path adjustment
from myapp.adapters import db  # <- neue "Datenbank"-Schnittstelle


def main() -> None:
    parser = argparse.ArgumentParser(description="Klassenkassa CLI")
    parser.add_argument("--batch", nargs="*", help="Nicht-interaktiver Modus: list|add|balance|save", default=None)
    parser.add_argument("--type", help="Typ für add (einzahlung|ausgabe)")
    parser.add_argument("--amount", help="Betrag für add", type=float)
    parser.add_argument("--desc", help="Beschreibung für add", default="")
    args = parser.parse_args()

    # Memory-"Datenbank" verbinden
    db.connect()

    try:
        # ---------- Batch-Modus ----------
        if args.batch is not None:
            cmd = args.batch[0] if len(args.batch) > 0 else "list"

            if cmd == "list":
                for t in db.get_all_transactions():
                    print(f"{t.id}: {t.type} {t.amount:.2f}€ — {t.description} — {t.timestamp}")
                return

            if cmd == "add":
                ttype = args.type
                if ttype not in ("einzahlung", "ausgabe"):
                    print("Ungültiger Typ für --type. Verwende 'einzahlung' oder 'ausgabe'.")
                    return
                if args.amount is None:
                    print("Bitte --amount angeben.")
                    return

                db.create_transaction(
                    type_=ttype,
                    amount=args.amount,
                    description=args.desc,
                    timestamp=datetime.now(),
                )
                print("Transaktion hinzugefügt.")
                return

            if cmd == "balance":
                bal = db.get_balance()
                print(f"Aktueller Kontostand: {bal.current_total:.2f}€")
                return

            if cmd == "save":
                # In der reinen Memory-DB gibt es nichts dauerhaft zu speichern.
                print("Hinweis: Memory-Datenbank speichert nicht dauerhaft. Es gibt nichts zu speichern.")
                return

        # ---------- Interaktives Menü ----------
        while True:
            print("\nKlassenkassa — Menü")
            print("1) Transaktionen auflisten")
            print("2) Transaktion hinzufügen")
            print("3) Kontostand anzeigen")
            print("4) Speichern und beenden")
            choice = input("Auswahl: ").strip()

            if choice == "1":
                for t in db.get_all_transactions():
                    print(f"{t.id}: {t.type} {t.amount:.2f}€ — {t.description} — {t.timestamp}")

            elif choice == "2":
                ttype = input("Typ (einzahlung/ausgabe): ").strip()
                if ttype not in ("einzahlung", "ausgabe"):
                    print("Ungültiger Typ. Verwende 'einzahlung' oder 'ausgabe'.")
                    continue
                try:
                    amt = float(input("Betrag: ").strip())
                except ValueError:
                    print("Ungültiger Betrag.")
                    continue
                desc = input("Beschreibung: ").strip()

                db.create_transaction(
                    type_=ttype,
                    amount=amt,
                    description=desc,
                    timestamp=datetime.now(),
                )
                print("Transaktion hinzugefügt.")

            elif choice == "3":
                bal = db.get_balance()
                print(f"Aktueller Kontostand: {bal.current_total:.2f}€")

            elif choice == "4":
                # "Speichern" ergibt bei Memory-DB nur symbolisch Sinn
                print("Gespeichert (Memory-DB speichert nur im RAM). Tschüss.")
                break
            else:
                print("Bitte wähle eine Zahl von 1 bis 4.")
    finally:
        db.disconnect()


if __name__ == "__main__":
    try:
        from myapp.gui.main import run as run_gui
        run_gui()
    except Exception as e:
        print("GUI konnte nicht gestartet werden:", e)
