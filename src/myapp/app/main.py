import sys
from pathlib import Path

from myapp.models import Transaction, Balance
from datetime import datetime
import argparse
from myapp.controller import (
	load_from_json,
	save_to_json,
	calculate_balance,
	add_transaction,
)

# Wenn die Datei direkt als Skript gestartet wird (z.B. "python main.py"),
# stelle sicher, dass der `src`-Ordner im `sys.path` ist, damit
# `import myapp...` funktioniert.
if __package__ is None:
	src_dir = Path(__file__).resolve().parents[2]
	src_str = str(src_dir)
	if src_str not in sys.path:
		sys.path.insert(0, src_str)


def _get_data_path() -> str:
	return str((Path(__file__).resolve().parents[1] / "dummydata" / "dummydata.json"))


def main() -> None:
	parser = argparse.ArgumentParser(description="Klassenkassa CLI")
	parser.add_argument("--batch", nargs="*", help="Nicht-interaktiver Modus: list|add|balance|save", default=None)
	parser.add_argument("--type", help="Typ für add (einzahlung|ausgabe)")
	parser.add_argument("--amount", help="Betrag für add", type=float)
	parser.add_argument("--desc", help="Beschreibung für add", default="")
	args = parser.parse_args()

	data_path = _get_data_path()
	transactions, balance = load_from_json(data_path)

	# Batch mode: execute given commands and exit
	if args.batch is not None:
		# args.batch can be empty list if --batch provided without values
		cmd = args.batch[0] if len(args.batch) > 0 else "list"
		if cmd == "list":
			for t in transactions:
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
			new_id = max((t.id for t in transactions), default=0) + 1
			t = Transaction(id=new_id, type=ttype, amount=args.amount, description=args.desc, timestamp=datetime.now())
			add_transaction(transactions, t)
			balance.current_total = calculate_balance(transactions)
			print("Transaktion hinzugefügt.")
			return
		if cmd == "balance":
			print(f"Aktueller Kontostand: {balance.current_total:.2f}€")
			return
		if cmd == "save":
			balance.current_total = calculate_balance(transactions)
			save_to_json(data_path, transactions, balance)
			print("Gespeichert.")
			return

	# Interactive mode (unchanged UX)
	while True:
		print("\nKlassenkassa — Menü")
		print("1) Transaktionen auflisten")
		print("2) Transaktion hinzufügen")
		print("3) Kontostand anzeigen")
		print("4) Speichern und beenden")
		choice = input("Auswahl: ").strip()

		if choice == "1":
			for t in transactions:
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
			new_id = max((t.id for t in transactions), default=0) + 1
			t = Transaction(id=new_id, type=ttype, amount=amt, description=desc, timestamp=datetime.now())
			add_transaction(transactions, t)
			balance.current_total = calculate_balance(transactions)
			print("Transaktion hinzugefügt.")
		elif choice == "3":
			print(f"Aktueller Kontostand: {balance.current_total:.2f}€")
		elif choice == "4":
			balance.current_total = calculate_balance(transactions)
			save_to_json(data_path, transactions, balance)
			print("Gespeichert. Tschüss.")
			break
		else:
			print("Bitte wähle eine Zahl von 1 bis 4.")


if __name__ == "__main__":
	main()

