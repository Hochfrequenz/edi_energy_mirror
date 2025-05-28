# edi_energy_mirror

Diese Repository spiegelt die Dokumente, die auf edi-energy.de veröffentlicht werden.

## Benutzung

Um Änderungen auf edi-energy.de zu betrachten kann man sich die [Commit-Historie](https://github.com/Hochfrequenz/edi_energy_mirror/commits/master) ansehen.
Oder die "zuletzt geändert" Datümer im Verzeichnis [edi_energy_de](/edi_energy_de).

## Updates abbonieren

edi-energy.de bietet keinen Service bei dem Interessierte per Push benachrichtigt würden, wenn sich Dokumente ändern.
Dieses Repository schafft Abhilfe:

- Es gibt ein [Atom-Feed](https://github.com/Hochfrequenz/edi_energy_mirror/commits/master.atom) `https://github.com/Hochfrequenz/edi_energy_mirror/commits/master.atom`.
- Per "Watch"/Beobachten (oben rechts) können angemeldete Github-User sich z.B. per Email informieren lassen, wenn Dokumente geändert wurden.

## Technische Grundlagen

Eine [periodisch eingeplante Github Action](https://github.com/Hochfrequenz/edi_energy_mirror/blob/main/.github/workflows/mirror.yml) lädt regelmäßig die Übersichtsseiten der aktuell- und zukünftig gültigen Dokumente herunter und speichert sie in diesem Repository.

Der Großteil des dazu notwendigen Codes lebt im [edi_energy_scraper](https://github.com/Hochfrequenz/edi_energy_scraper)-Repository.

Das Skript [download_and_post_process.py](/download_and_post_process.py) lädt die Startseite von edi-energy.de, die Seiten für aktuell und zukünftig gültige sowie archivierte Dokumente und die jeweils verlinkten PDFs herunter und speichert sie in den für den jeweiligen Gültigkeitszeitraum passenden Ordner; z.B. [`FV2310`](edi_energy_de/FV2310) für Dokumente, die seit 01. Oktober 2023 gültig waren.

So werden Änderungen an MIGs, AHBs und weiteren Dokumenten als Diffs einzelner git commits sichtbar und Änderungen sind leichter aufzufinden und auszuwerten.

## Weiterverarbeitung der Rohdaten
* Eine [Github Action](/.github/workflows/migmose.yml) spiegelt jegliche Änderungen in den Rohdaten in das Repository [machine-readable_message-implementation-guide](https://github.com/Hochfrequenz/machine-readable_message-implementation-guide).
* Eine [Github Action](/.github/workflows/ebdamame_rebdhuhn.yml) spiegelt jegliche Änderungen in den Rohdaten in das Repository [machine-readable_entscheidungsbaumdiagramme](https://github.com/Hochfrequenz/machine-readable_entscheidungsbaumdiagramme) - das ist die Grundlage für [ebd.hochfrequenz.de](https://ebd.hochfrequenz.de/).


## Urheberrecht

Das Urheberrecht der hier versionierten Daten liegt bei EDI@energy bzw. den Autor\*innen der jeweiligen Dokumente selbst.
Dieses Repository macht die Daten und deren Änderungen lediglich leichter zugänglich.
Hochfrequenz garantiert weder für die Korrektheit noch die Vollständigkeit der hier bereitgestellten Daten, stellt aber auch keine Bedingungen an deren Nutzung.

## Weiterführendes Tooling

Dieses Repository ist Teil der [Hochfrequenz Libraries und Tool für eine echte Digitalisierung der Marktkommunikation](https://github.com/Hochfrequenz/digital_market_communication/).
