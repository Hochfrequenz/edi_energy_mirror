# edi_energy_mirror
![Pytest status badge](https://github.com/Hochfrequenz/edi_energy_mirror/workflows/Unittests/badge.svg)
![Coverage status badge](https://github.com/Hochfrequenz/edi_energy_mirror/workflows/Coverage/badge.svg)
![Pylint status badge](https://github.com/Hochfrequenz/edi_energy_mirror/workflows/Linting/badge.svg)
![Black status badge](https://github.com/Hochfrequenz/edi_energy_mirror/workflows/Black%20Code%20Formatter/badge.svg)

Diese Repository spiegelt die Dokumente, die auf edi-energy.de veröffentlicht werden. Weil der BDEW keine saubere Änderungshistorie pflegt lädt ein cronjob auf unserem [Berliner Server](https://wiki.hochfrequenz.de/index.php/Berlin_Server) regelmäßig die Übersichtsseiten der aktuell- und zukünftig gültigen Dokumente herunter und speichert sie in diesem Repository. So werden Änderungen als Diffs einzelner git commits sichtbar und still/heimlich gepflegte Änderungen sind leichter aufzufinden. 

## Benutzung
Um Änderungen auf edi-energy.de zu monitoren schaut man sich die [Commit-Historie](https://github.com/Hochfrequenz/edi_energy_mirror/commits/master) an. Oder die "zuletzt geändert" Datümer im Verzeichnis [edi_energy_de](/edi_energy_de).

## Technische Details
Der Großteil des Codes lebt im öffentlichen [edi_energy_scraper](https://github.com/Hochfrequenz/edi_energy_scraper) -Repository.

Das Skript [download_and_post_process.py](/download_and_post_process.py) lädt die Startseite von edi-energy.de, die Seiten für aktuell und zukünftig gültige sowie archivierte Dokumente und die jeweils verlinkten PDFs herunter und speichert sie in den drei Verzeichnissen [current](/edi_energy_de/current) (aktuell), [future](/edi_energy_de/future) (zukünftig), [past](/edi_energy_de/past) (archiviert).

Das Skript [delete_and_download.bat](/delete_and_download.bat) löscht erst alle gespiegelten Dateien, stößt dann das o.g. Python-Skript an und erzeugt daraus einen git commit.
