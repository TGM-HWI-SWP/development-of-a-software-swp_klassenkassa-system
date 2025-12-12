import sys
from pathlib import Path
from datetime import datetime
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    raise


def _ensure_src_in_path():
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


_ensure_src_in_path()

from myapp.adapters import db
from myapp.models import Transaction


class GUIApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Klassenkassa — Futuristic UI")
        self.master.geometry("820x520")
        self._setup_style()

        # Mit der Memory-Datenbank verbinden und Startdaten holen
        db.connect()
        self.transactions = db.get_all_transactions()
        self.balance = db.get_balance()

        self._build_widgets()
        self._refresh_list()

    # -------------------------------------------------------------------------
    # FUTURISTIC STYLE
    # -------------------------------------------------------------------------
    def _setup_style(self):
        style = ttk.Style(self.master)

        try:
            style.theme_use("clam")
        except Exception:
            pass

        bg = "#0a0f1f"
        fg = "#e8f6ff"
        neon = "#00eaff"
        neon2 = "#b300ff"
        glass_bg = "#101828"

        # Main window background
        self.master.configure(bg=bg)

        style.configure(
            "Glass.TFrame",
            background=glass_bg,
            borderwidth=1,
            relief="solid",
            bordercolor="#1b2b3c"
        )

        style.configure(
            "Title.TLabel",
            background=bg,
            foreground=neon,
            font=("Segoe UI", 14, "bold")
        )

        style.configure(
            "TLabel",
            background=bg,
            foreground=fg,
            font=("Segoe UI", 10)
        )

        style.configure(
            "TEntry",
            fieldbackground="#0d1628",
            background="#0d1628",
            foreground="#cde6ff",
            borderwidth=1,
            relief="flat"
        )

        # Cyberpunk Buttons
        style.configure(
            "Accent.TButton",
            background=neon,
            foreground="#001018",
            font=("Segoe UI", 10, "bold"),
            padding=6
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#00c2d6")]
        )

        style.configure(
            "Soft.TButton",
            background="#1f2a44",
            foreground=fg,
            font=("Segoe UI", 10),
            padding=6
        )
        style.map(
            "Soft.TButton",
            background=[("active", "#273554")]
        )

        # Treeview style (glass-like)
        style.configure(
            "Treeview",
            background="#0d1626",
            foreground=fg,
            fieldbackground="#0d1626",
            rowheight=26,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#111b2e",
            foreground=neon,
            font=("Segoe UI", 10, "bold")
        )

    # -------------------------------------------------------------------------
    # BUILD GUI
    # -------------------------------------------------------------------------
    def _build_widgets(self):
        # TITLE BAR
        title = ttk.Label(self.master, text="Transaktionen", style="Title.TLabel")
        title.pack(pady=10)

        # TOP BUTTON BAR
        btn_row = ttk.Frame(self.master, style="Glass.TFrame")
        btn_row.pack(fill=tk.X, padx=12, pady=(0, 12))

        ttk.Button(btn_row, text="Refresh", style="Soft.TButton", command=self._refresh_list).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_row, text="Save", style="Accent.TButton", command=self._save).pack(side=tk.LEFT, padx=4)

        # TREEVIEW
        cols = ("id", "type", "amount", "desc", "ts")
        self.tree = ttk.Treeview(self.master, columns=cols, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("type", text="Typ")
        self.tree.heading("amount", text="Betrag")
        self.tree.heading("desc", text="Beschreibung")
        self.tree.heading("ts", text="Zeitstempel")
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("type", width=120, anchor=tk.CENTER)
        self.tree.column("amount", width=120, anchor=tk.E)
        self.tree.column("desc", width=340, anchor=tk.W)
        self.tree.column("ts", width=180, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=12)

        # FORM (Glass Panel)
        form = ttk.Frame(self.master, style="Glass.TFrame")
        form.pack(fill=tk.X, padx=12, pady=10, ipadx=5, ipady=5)

        ttk.Label(form, text="Typ:").grid(row=0, column=0, sticky=tk.W)
        self.type_var = tk.StringVar(value="einzahlung")
        ttk.OptionMenu(form, self.type_var, "einzahlung", "einzahlung", "ausgabe").grid(row=0, column=1, sticky=tk.W)

        ttk.Label(form, text="Betrag:").grid(row=0, column=2, sticky=tk.W, padx=(12, 0))
        self.amount_entry = ttk.Entry(form)
        self.amount_entry.grid(row=0, column=3, sticky=tk.W)

        ttk.Label(form, text="Beschreibung:").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        self.desc_entry = ttk.Entry(form, width=60)
        self.desc_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=(6, 0))

        ttk.Button(form, text="Add", style="Accent.TButton", command=self._on_add).grid(
            row=0, column=4, rowspan=2, padx=(12, 0))

        # BALANCE FOOTER
        footer = ttk.Frame(self.master)
        footer.pack(fill=tk.X, padx=12, pady=(4, 6))

        self.balance_lbl = ttk.Label(
            footer,
            text=f"Kontostand: {self.balance.current_total:.2f}€",
            font=("Segoe UI", 11, "bold"),
            foreground="#00ffaa"
        )
        self.balance_lbl.pack(side=tk.LEFT)

    # -------------------------------------------------------------------------
    def _refresh_list(self):
        # aktuelle Daten aus der Memory-DB holen
        self.transactions = db.get_all_transactions()
        self.balance = db.get_balance()

        for i in self.tree.get_children():
            self.tree.delete(i)
        for t in self.transactions:
            self.tree.insert("", tk.END, values=(
                t.id, t.type, f"{t.amount:.2f}€", t.description, t.timestamp
            ))
        self.balance_lbl.config(text=f"Kontostand: {self.balance.current_total:.2f}€")

    # -------------------------------------------------------------------------
    def _on_add(self):
        ttype = self.type_var.get()
        try:
            amt = float(self.amount_entry.get())
        except Exception:
            messagebox.showerror("Fehler", "Ungültiger Betrag")
            return

        desc = self.desc_entry.get().strip()

        # aktuellen Kontostand aus DB holen und prüfen, ob die Transaktion ins Minus gehen würde
        current_total = db.get_balance().current_total
        new_total = current_total + amt if ttype == "einzahlung" else current_total - amt
        if new_total < 0:
            messagebox.showwarning("Nicht erlaubt", "Diese Transaktion würde den Kontostand ins Minus bringen.")
            return

        # Transaktion in der DB anlegen
        try:
            # Optional: zuerst Transaction für Validierung bauen
            _ = Transaction(id=0, type=ttype, amount=amt, description=desc, timestamp=datetime.now())
            db.create_transaction(
                type_=ttype,
                amount=amt,
                description=desc,
                timestamp=datetime.now(),
            )
        except Exception as e:
            messagebox.showerror("Validierungsfehler", str(e))
            return

        self._refresh_list()

        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)

    # -------------------------------------------------------------------------
    def _save(self):
        # Memory-DB speichert nur im RAM – kein echtes Speichern
        messagebox.showinfo(
            "Hinweis",
            "Die aktuelle Memory-Datenbank speichert nur im Arbeitsspeicher.\n"
            "Es wird keine Datei auf der Festplatte geschrieben."
        )


def run_gui():
    root = tk.Tk()
    app = GUIApp(root)
    root.mainloop()
    # optional: nach GUI-Ende die DB trennen, falls dein Adapter das unterstützt
    try:
        db.disconnect()
    except Exception:
        pass
