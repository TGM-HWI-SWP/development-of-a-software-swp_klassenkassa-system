[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/cqMTK5D_)
# Klassenkassa-System

Ein einfaches, modular aufgebautes Softwareprojekt zur Verwaltung einer Klassenkassa. Ziel ist ein sauber strukturierter Durchstich mit klaren Schnittstellen, Dummy-Daten und testbarer Architektur.

---

## 📌 Projektziel
- Verwaltung von Einzahlungen und Ausgaben
- Anzeige des aktuellen Kontostands
- Klare Trennung von Model, Controller, View und Datenzugriff
- Vorbereitung für Erweiterungen (echte DB, UI, Tests)

---

## 🧱 Architektur
Das Projekt ist nach dem Port-&-Adapter-Prinzip aufgebaut:

- **Models** – Pydantic-Datenmodelle (Transaction, Balance)
- **Controller** – Geschäftslogik & Use-Cases
- **DB-Port** – Schnittstelle für Datenzugriff
- **View-Port** – Schnittstelle zur UI
- **Dummydata** – Testdaten & Stubs ohne echte DB

---



## ▶ Ausführen
Im Ordner `src`:

```
python -m myapp.app.main
```

Dummy-Daten testen:
```
python -m myapp.dummydata.dummydata
```

---

## Features (MVP)
- Transaktion anlegen
- Transaktionen auflisten
- Kontostand berechnen
- Dummy-Daten ohne echte Datenbank

---

##  Tests
Contract-Tests stellen sicher, dass:
- Schnittstellen eingehalten werden
- Dummy- und echte Implementierungen gleich funktionieren
- Controller korrekt mit View und DB kommuniziert

---



##  Branching & Commits
**Branches:**
- main (stabil)
- develop (Entwicklung)
- mit-docker

**Commits:**
Format:
```
typ: kurze beschreibung
```
Beispiel:
```
feat: add transaction validation
```

---

## Team
Projekt im Rahmen des SWP-Unterrichts – Klassenkassa-System
Wippel Sofia
Theussl Felix
Zwanzinger Max
---

