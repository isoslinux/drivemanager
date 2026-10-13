"""Qt controllers for setup, portability, live acceptance and cache health."""
import time
from threading import Event
from queue import Empty
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,
    QPlainTextEdit,QDialogButtonBox,QFileDialog,QMessageBox,QTableWidget,QTableWidgetItem,QAbstractItemView,QHeaderView,QSystemTrayIcon)
from .providers import PROVIDERS
from .performance import CacheHealth,inspect,slow
from .quota import size

class BulkActions:
    def request_health(self,force=False):
        remote=self.accounts.currentText()
        if not remote or self.health_future is not None or not force and time.monotonic()-self.health_last<30:return
        self.health_remote=remote;self.health_last=time.monotonic()
        self.health_future=self.health_pool.submit(inspect,self.manager,remote)

    def tick_health(self):
        self.tick_browse()
        if self.health_future is not None and self.health_future.done():
            future,self.health_future=self.health_future,None
            try:result=future.result()
            except Exception:result=CacheHealth()
            names=[self.accounts.item(row,0).text() for row in range(self.accounts.rowCount())]
            if self.health_remote in names:
                self.health_results[self.health_remote]=result
                if result.low and self.health_remote not in self.health_warned:
                    self.health_warned.add(self.health_remote)
                    if self.notifications_enabled and self.tray.isSystemTrayAvailable() and self.tray.supportsMessages():
                        self.tray.showMessage('Drive Manager',self.t['cache_low'],QSystemTrayIcon.MessageIcon.Warning,6000)
                elif result.free is not None and not result.low:self.health_warned.discard(self.health_remote)
            self.show_health()
            if self.accounts.currentText()!=self.health_remote:self.request_health(force=True)
        self.request_health()

    def show_health(self):
      …18569 tokens truncated…ie Dateien anzuzeigen.',
 'update_open_rpm': 'RPM herunterladen',
 'update_open_release': 'Release-Seite öffnen',
 'update_open_error': 'Der Standardbrowser konnte nicht geöffnet werden.',
 'update_manual': 'Die Installation erfolgt manuell. Diese Prüfung lädt keine Software herunter '
                  'und führt sie nicht aus, ändert keine Zugangsdaten und unterbricht keine '
                  'Laufwerke oder Uploads.'})

MESSAGES.update({'username': 'Benutzername', 'webdav_url': 'WebDAV-URL (HTTPS)', 'app_password': 'App-Passwort', 'optional_2fa': 'Zwei-Faktor-Code (optional)', 'mailbox_password': 'Postfachpasswort (optional)', 'nextcloud_note': 'Kopieren Sie die WebDAV-Adresse aus den Nextcloud-Dateieinstellungen. Erstellen Sie ein App-Passwort in den Nextcloud-Sicherheitseinstellungen.', 'proton_note': 'Experimentelle Rclone-Unterstützung. Melden Sie sich zuerst mindestens einmal im Web bei Proton Drive an. Geben Sie bei Bedarf einen aktuellen Zwei-Faktor-Code ein. Das Postfachpasswort wird nur für Konten mit zwei Passwörtern benötigt.', 'credentials_wait': 'Zugangsdaten werden sicher geprüft…', 'credentials_error': 'Anmeldung fehlgeschlagen. Prüfen Sie Zugangsdaten, Zwei-Faktor-Code, Serververfügbarkeit und Rclone-Kompatibilität.', 'webdav_url_error': 'Geben Sie eine gültige HTTPS-WebDAV-URL ohne Zugangsdaten, Abfrage oder Fragment ein.'})

MESSAGES.update({'check_connection': 'Verbindung prüfen', 'connection_checking': 'Lesezugriff auf den Stammordner wird geprüft…', 'connection_ok': 'Stammordner lesbar. Schreibzugriff und Abschluss der Uploads wurden nicht geprüft.', 'connection_auth': 'Anmeldung fehlgeschlagen. Erneuern Sie die Autorisierung oder prüfen Sie Ihre Zugangsdaten.', 'connection_permission': 'Lesezugriff verweigert. Prüfen Sie die Kontoberechtigungen auf dem Server.', 'connection_network': 'Netzwerkanfrage fehlgeschlagen. Prüfen Sie Verbindung und Serververfügbarkeit.', 'connection_rate': 'Anfragelimit erreicht. Warten Sie vor einer erneuten Prüfung.', 'connection_timeout': 'Zeitlimit überschritten. Der Anbieter kann langsam sein; dies beweist keine Unterbrechung.', 'connection_error': 'Zugriff konnte nicht geprüft werden. Prüfen Sie Kompatibilität und Kontoeinstellungen.', 'connection_wallet': 'Private Konfiguration konnte nicht entsperrt werden. Prüfen Sie KDE Wallet.', 'connection_locked': 'Externe verschlüsselte Konfigurationen benötigen ihre ursprüngliche Anmeldung.', 'connection_cancelled': 'Prüfung abgebrochen.', 'connection_elapsed': '{seconds:.1f} s'})

MESSAGES['connection_last']='Letzte Prüfung'

MESSAGES.update({'renew_credentials': 'Zugangsdaten erneuern', 'credential_confirm': 'Verwenden Sie DASSELBE Konto und denselben Server. Die Verbindung muss getrennt sein und darf keine ausstehenden Uploads haben. Ordner, Einstellungen und Cache bleiben erhalten. Zugangsdaten ersetzen?', 'credential_identity': 'Benutzername oder Nextcloud-Server weicht von der ursprünglichen Verbindung ab. Die bisherigen Zugangsdaten bleiben erhalten.', 'credential_custom': 'Konfigurationen mit eigenem Bearer-Token oder OTP-Geheimnis benötigen ihre ursprüngliche Einrichtung. Die bisherigen Zugangsdaten bleiben erhalten.', 'credential_renew_error': 'Zugangsdaten konnten nicht erneuert werden. Verwenden Sie eine verschlüsselte Verbindung dieser Anwendung, getrennt und ohne ausstehende Uploads. Die bisherigen Zugangsdaten bleiben erhalten.'})

MESSAGES.update({'tools': 'Werkzeuge', 'setup_guide': 'Einrichtungsassistent', 'export_settings': 'Einstellungen exportieren', 'import_settings': 'Einstellungen importieren', 'setup_steps': '1. Prüfen Sie lokale Abhängigkeiten. Der Assistent installiert keine Programme.\n2. Wählen Sie einen Anbieter und richten Sie das Konto schreibgeschützt ein.\n3. Wählen Sie einen leeren Ordner, verbinden Sie ihn und öffnen Sie Dolphin. Aktivieren Sie Schreiben nur bei Bedarf.', 'setup_finish': 'Assistent abschließen', 'export_done': 'Einstellungen für {count} Konten exportiert. Keine Zugangsdaten oder Cache-Inhalte enthalten.', 'import_note': 'Prüfen Sie Ordner, Zugriff, Anmeldungsmontage und Geschwindigkeitslimits. Konten müssen hier bereits eingerichtet sein. Speichern gilt nur für getrennte Konten ohne ausstehende lokale Änderungen. Schreiben und automatisches Einbinden gelten bei der nächsten Verbindung/Anmeldung.', 'portable_error': 'Datei konnte nicht verarbeitet werden. Prüfen Sie Format, passende Konten/Anbieter, getrennte leere Ordner, Schreibberechtigung und Dateirechte. Keine Zugangsdaten werden importiert.', 'portable_busy': 'Trennen Sie betroffene Konten und beenden Sie ausstehende Uploads vor dem Import.', 'upload_limit': 'Uploadlimit', 'download_limit': 'Downloadlimit', 'unlimited': 'Unbegrenzt', 'cache_health': 'Lokaler Cache: freier Speicher {free} · Ausstehende lokale Dateien {pending}', 'cache_low': 'Wenig lokaler Speicher. Bewahren Sie ausstehende Dateien auf und schaffen Sie Platz außerhalb des Uploadcaches.', 'cache_unknown': 'Lokaler Cachezustand konnte nicht geprüft werden.', 'cloud_slow': 'Langsame Cloudantwort; Vorschau, Ordnerzählung und Geschwindigkeitslimits können verzögern.', 'validate_all': 'Konten validieren', 'validation_note': 'Leseprüfungen betreffen nur eingerichtete Konten. Anbieter ohne Ergebnis benötigen ein Konto. Schreiben und Neuverbinden brauchen getrennte Bestätigung. Lesen bestätigt weder Uploads noch 2FA, Erneuerung oder Wiederherstellung nach Ausfällen.', 'validation_read': 'Stammordner lesen', 'validation_time': 'Antwortzeit', 'validation_unchecked': 'Nicht geprüft / kein Ergebnis', 'validation_write': 'Schreiben testen', 'validation_reconnect': 'Neuverbinden testen', 'validation_guide': 'Validierungsanleitung', 'validation_confirm': 'Ausdrückliche Testbestätigung erforderlich.', 'validation_write_confirm': 'Eine kleine Testdatei erstellen und direkt aus der Cloud zurücklesen? Die Datei bleibt zum Prüfen oder manuellen Löschen erhalten. Das Konto muss von dieser Anwendung mit Schreibzugriff eingebunden sein und darf keine ausstehenden Uploads haben.', 'validation_reconnect_confirm': 'Dieses ausgewählte Konto trennen und neu verbinden? Ausstehende Uploads oder offene Dateien verhindern dies. Andere Konten werden nicht neu gestartet.', 'validation_write_requires': 'Binden Sie dieses Konto mit Schreibzugriff ein und beenden Sie ausstehende Uploads.', 'validation_write_ok': 'Testinhalt direkt aus der Cloud geprüft. Die Testdatei bleibt erhalten.', 'validation_timeout': 'Test nicht rechtzeitig abgeschlossen. Bewahren Sie Testdatei und ausstehenden Cache auf; prüfen Sie Übertragungen.', 'validation_error': 'Test konnte nicht geprüft werden. Prüfen Sie Zugriff, Uploads und lokale Diagnose. Bewahren Sie ausstehende Daten auf.', 'validation_finished': 'Leseprüfungen beendet. Prüfen Sie jedes Konto; fehlende oder abgebrochene Konten bleiben ungeprüft.', 'validation_file': 'Testdatei', 'validation_reconnect_ok': 'Verwalteter Mount neu verbunden. Dateiintegrität und Ausfallwiederherstellung sind separate Prüfungen.', 'acceptance_steps': 'Für jeden Anbieter:\n1. Richten Sie ein Testkonto ein und prüfen Sie den Stammordner.\n2. Binden Sie schreibgeschützt ein und prüfen Sie die Schreibsperre.\n3. Aktivieren Sie Schreiben ausdrücklich und testen Sie es; prüfen Sie die behaltene Datei auf der Webseite.\n4. Schließen Sie Dateien, testen Sie Neuverbinden und lesen Sie die Datei erneut.\n5. Prüfen Sie 2FA und Zugangsdaten-Erneuerung manuell mit demselben Konto.\n6. Testen Sie Ausfälle mit entbehrlichen Daten; prüfen Sie Uploadschutz und Wiederaufnahme.\n7. Vergleichen Sie das Kontingent mit dem Anbieter.\nDiese Betreiberprüfungen werden nicht automatisch als bestanden markiert.'})

MESSAGES.update({'browse_measure': 'Navigation messen', 'browse_result': 'Ordnerliste: {listing} · Speicherabfrage: {space}', 'browse_note': 'Leseprüfungen mit je 10 Sekunden Zeitlimit. — bedeutet nicht verfügbar oder Zeitüberschreitung. Vorschau und Inhaltszählung werden nicht gemessen. Bei schneller Liste und langsamem Dolphin vergleichen Sie ohne Vorschau und Ordnergrößenberechnung.'})

DIAGNOSTICS.update({'wallet': 'KWallet (verschlüsselte Konten)', 'missing_wallet': 'Installieren Sie kf6-kwallet für Internxt, Nextcloud und Proton Drive.'})
