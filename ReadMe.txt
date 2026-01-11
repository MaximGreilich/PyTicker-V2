🤖 Discord To-Do Bot (PyTicker-V2)
Ein intelligenter und benutzerfreundlicher Discord-Bot zur Verwaltung von Aufgaben, Deadlines und Prioritäten. Der Bot unterstützt mehrere Nutzer gleichzeitig (jeder hat seine eigene Liste), speichert Daten persistent und erinnert automatisch an fällige Deadlines.

✨ Features
📝 Smart Input: Erkennt Titel, Datum und Uhrzeit automatisch ohne Anführungszeichen.

👤 Multi-User Support: Jeder Nutzer sieht und verwaltet nur seine eigenen Aufgaben.

🔥 Prioritäten-System: Sortierung nach Wichtigkeit (1-5).

⏰ Automatische Erinnerungen: Benachrichtigt im Channel bei fälligen Aufgaben (mit Panic-GIFs bei Prio 5!).

💤 Smart Snooze: Deadlines einfach verschieben (z. B. "2h", "1d").

💾 Auto-Save: Alle Aufgaben werden sicher in einer JSON-Datei gespeichert.

🎉 Gamification: Party-GIFs beim Erledigen von Aufgaben.

🚀 Installation & Start
Voraussetzungen Du brauchst Python (Version 3.8 oder höher).

Abhängigkeiten installieren Installiere die benötigte Bibliothek discord.py: pip install discord.py

Bot starten Stelle sicher, dass deine Bot-Dateien (main.py, todo.py) im selben Ordner liegen. Trage deinen Bot-Token in der main.py ein und starte den Bot: python main.py

📖 Befehls-Übersicht
Hier sind alle Befehle, die der Bot versteht.

➕ Aufgabe erstellen
Erstellt eine neue Aufgabe. Der Bot erkennt das Format automatisch. Syntax: !neu <Titel> <Datum> <Uhrzeit> [Prio 1-5] Alias: !add

Beispiele:

!neu Mathe lernen 20.05.2025 14:00 5 (Sehr wichtig)

!neu Müll rausbringen 12.01.2026 10:00 (Standard Prio 3)

📋 Liste anzeigen
Zeigt deine persönlichen, offenen Aufgaben an. Syntax: !liste Alias: !list

Sortiert intelligent: Erst nach Wichtigkeit, dann nach Zeit.

Markiert überfällige Aufgaben rot (ÜBERFÄLLIG!).

✅ Aufgabe erledigen
Markiert eine Aufgabe als fertig und löscht sie aus der Liste (+ Party GIF 🎉). Syntax: !fertig <Nummer oder Name> Alias: !done

Beispiele:

!fertig 1 (Erledigt deine Aufgabe Nr. 1)

!fertig Mathe (Sucht nach einer Aufgabe mit "Mathe" im Namen)

🗑️ Aufgabe löschen
Löscht eine Aufgabe komplett (ohne Erfolgsmeldung/GIF), falls man sich vertippt hat. Syntax: !loeschen <Nummer> Alias: !del, !remove

Beispiel: !loeschen 2

💤 Deadline verschieben
Verschiebt die Deadline einer Aufgabe nach hinten. Syntax: !verschieben <Nummer> <Zeit> Alias: !snooze, !delay

Beispiele:

!verschieben 1 30m (30 Minuten später)

!verschieben 1 2h (2 Stunden später)

!verschieben 1 1d (1 Tag später)

⏳ Genaue Zeit prüfen
Zeigt exakt an, wie viele Tage, Stunden und Minuten noch bleiben. Syntax: !zeit <Nummer> Alias: !time, !check

💪 Motivation
Gibt einen zufälligen Motivationsspruch aus. Syntax: !motivation

🔔 Erinnerungs-Intervalle
Je nach Wichtigkeit (Prio 1-5) nervt der Bot öfter oder weniger oft. Hier ist der Zeitplan, wann Erinnerungen gesendet werden:

PRIORITÄT 5 (Kritisch 🔥): Erinnerung bei: 24h, 12h, 6h, 3h, 1h, 30m, 15m, 10m, 5m, JETZT

PRIORITÄT 4 (Wichtig): Erinnerung bei: 24h, 6h, 1h, 30m, 10m, JETZT

PRIORITÄT 3 (Standard): Erinnerung bei: 24h, 3h, 1h, 10m, JETZT

PRIORITÄT 2 (Gering): Erinnerung bei: 24h, 1h, JETZT

PRIORITÄT 1 (Optional): Erinnerung bei: 24h, JETZT

Hinweis: Bei Prio 5 (Stress) und beim Erreichen der Deadline sendet der Bot zufällige Panic-GIFs in den Channel!

⚙️ Technische Details
Speicherort: Alle Daten werden in saved_tasks.json gespeichert.

Prüf-Intervall: Der Bot prüft alle 30 Sekunden im Hintergrund (tasks.loop), ob Deadlines erreicht wurden.

Datumsformat: Der Bot nutzt intern ISO-Formatierung, zeigt aber europäisches Format (TT.MM.JJJJ) an.

🤝 Mitwirken
Fühle dich frei, den Code anzupassen! Die Hauptlogik befindet sich in der Klasse Todo in todo.py.

Viel Spaß beim Produktivsein! 🚀