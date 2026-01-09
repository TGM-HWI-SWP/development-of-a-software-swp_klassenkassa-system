# Klassenkassa-System

Die Klassenkassa ist eine Python-Anwendung zur Verwaltung von Schüler-Guthaben,
Transaktionen und Sparzielen.
Sie wurde im Rahmen eines SWP-Projekts entwickelt und verfolgt das Ziel,
einen sauber strukturierten Durchstich mit klaren Schnittstellen,
Dummy-Daten und testbarer Architektur umzusetzen.

Die Anwendung wird ausschließlich über Docker betrieben.

## Projektziel

- Verwaltung von Einzahlungen und Ausgaben
- Anzeige des aktuellen Kontostands
- Klare Trennung von Model, Controller, View und Datenzugriff
- Vorbereitung für Erweiterungen (echte Datenbank, UI, Tests)

## Architektur

Das Projekt ist nach dem Port-&-Adapter- (Hexagonal-)Prinzip aufgebaut
und orientiert sich an einer MVC-Struktur.

- Models – Pydantic-Datenmodelle (z. B. Transaction, Balance)
- Controller – Geschäftslogik und Use-Cases
- DB-Port – Schnittstelle für den Datenzugriff
- View-Port – Schnittstelle zur Benutzeroberfläche
- Dummydata – Dummy-Daten und Stubs ohne echte Datenbank
- Adapter – Konkrete Implementierungen (In-Memory, MongoDB, GUI)

## Installation

Voraussetzungen (Pflicht)

- Docker
- Docker Compose

Eine lokale Installation ohne Docker ist nicht vorgesehen.

Projekt beziehen

git clone <REPO-URL>
cd Klassenkassa

## Start der Anwendung

Die gesamte Anwendung (GUI, Businesslogik und Datenbank) wird mit Docker Compose gestartet:

docker-compose up --build

Nach dem Start ist die grafische Benutzeroberfläche (Gradio)
im Browser erreichbar.
Die genaue URL wird im Terminal ausgegeben (z. B. http://localhost:7860).

## Nutzung

Die Anwendung bietet eine grafische Benutzeroberfläche zur:

- Verwaltung von Schülern
- Erfassen von Transaktionen (Ein- und Ausgaben)
- Anzeigen des aktuellen Guthabens
- Optional: Verwalten von Sparzielen

Die Geschäftslogik ist strikt von der GUI getrennt
und folgt dem MVC-Prinzip (Model–View–Controller).

## Features 

- Transaktion anlegen
- Transaktionen auflisten
- Kontostand berechnen
- Verwendung von Dummy-Daten ohne echte Datenbank

## Konfiguration

Die Konfiguration erfolgt vollständig über die Datei docker-compose.yml.

- Startet alle benötigten Services
- Kapselt sämtliche Abhängigkeiten
- Ermöglicht reproduzierbare Builds

Wichtige Befehle:

docker-compose up --build  
docker-compose down

Anpassungen (z. B. Ports oder Datenbank-Anbindung) erfolgen direkt
in der docker-compose.yml.

## Tests und Qualität

Contract-Tests stellen sicher, dass:

- Schnittstellen eingehalten werden
- Dummy- und echte Implementierungen gleich funktionieren
- Controller korrekt mit View und DB kommuniziert

Das Projekt verwendet:
- PEP 8 (Code Style)
- Typing nach PEP 484
- Pydantic für Datenmodelle
- pytest für Unittests

## Projektstruktur (Auszug)

src/myapp  
adapters        – Datenbank-Adapter (In-Memory, MongoDB)  
backend         – Businesslogik / Controller  
frontend        – GUI (Gradio)  
models.py       – Pydantic-Datenmodelle  
dummydata       – Dummy-Daten und Stubs  
test            – Unittests  

## Branching und Commits

Branches:

- main (stabil)
- develop (Entwicklung)
- mit-docker
- test_felix

Commits:

Format:
typ: kurze beschreibung

Beispiel:
feat: add transaction validation

## Beitrag leisten

Pull Requests sind willkommen.

Bitte beachte:
- Saubere Commit-Nachrichten
- Einhaltung von PEP 8 und Typing
- Tests für neue Features

## Team

Projekt im Rahmen des SWP-Unterrichts – Klassenkassa-System

- Wippel Sofia
- Theussl Felix
- Zwanzinger Max

## Lizenz

Dieses Projekt wurde im Rahmen einer schulischen Ausbildung erstellt
und dient ausschließlich Ausbildungszwecken.
