"""German UI and diagnostics catalog."""
MESSAGES = {
 'title':'Drive Manager','refresh':'Verbindungen aktualisieren','mount':'Verbinden','unmount':'Trennen',
 'open':'In Dolphin öffnen','quit':'Anwendung beenden','oauth_open':'Browser zur Autorisierung öffnen',
 'oauth_port':'Eine andere Autorisierung verwendet Port 53682. Schließen oder beenden Sie sie und versuchen Sie es erneut.',
 'oauth_server':'Der lokale Autorisierungsserver konnte nicht gestartet werden.',
 'onedrive_error':'OneDrive konnte nicht eingerichtet werden. Prüfen Sie die Microsoft-Berechtigungen und das ausgewählte Laufwerk.',
 'choose_drive':'OneDrive-Laufwerk auswählen','first_transfer':'Erste Übertragung','queued_label':'Wartend',
 'uploading_label':'Hochladen','transfers':'Übertragungen','uploading':'Änderungen werden hochgeladen','queued':'Warten auf Hochladen',
 'transferring':'Dateien werden übertragen','idle':'Warteschlange leer · Cloud-Verbindung nicht geprüft',
 'network_retry':'Netzwerkfehler · Übertragungen werden erneut versucht','auth_required':'Authentifizierung erfordert Aufmerksamkeit',
 'transfer_error':'Übertragungsfehler · Änderungen stehen noch aus','monitor_unknown':'Synchronisierung konnte nicht geprüft werden',
 'unmonitored':'Lokal eingebunden · Synchronisierung nicht überwacht','provider_column':'Anbieter','account':'Konto',
 'status':'Status','access':'Zugriff','mode':'Modus für neue Verbindungen','mode_ro':'Nur lesen','mode_rw':'Lesen/Schreiben',
 'mounted_rw':'Eingebunden (Lesen/Schreiben)','sync_pending':'Änderungen werden hochgeladen oder stehen noch aus',
 'sync_unknown':'Upload-Status konnte nicht geprüft werden','sync_clean':'Upload-Warteschlange leer',
 'uploads_pending':'Änderungen stehen noch aus. Warten Sie auf die Uploads oder verbinden Sie im Schreibmodus erneut, um sie wiederherzustellen.',
 'uploads_unknown':'Ausstehende Änderungen konnten nicht geprüft werden. Trennen und Löschen sind gesperrt.',
 'files_open':'Schließen Sie vor dem Trennen die Dateien und Dolphin-Fenster dieses Laufwerks.',
 'needs_write_auth':'Dieses Konto wurde zum Lesen autorisiert. Aktivieren Sie Lesen/Schreiben in den Kontoeinstellungen, um den Zugriff zu erlauben.',
 'write_note':'Lesen/Schreiben ändert Cloud-Dateien. Google/Microsoft kann eine Autorisierung im Browser verlangen.',
 'provider':'Anbieter der neuen Verbindung','email':'E-Mail','password':'Passwort','twofa':'Internxt-Zwei-Faktor-Code',
 'internxt_error':'Internxt-Anmeldung fehlgeschlagen. Prüfen Sie Zugangsdaten, Zwei-Faktor-Code und Tarifkompatibilität.',
 'wallet_error':'Entsperren oder erstellen Sie die KDE-Passwortspeicherdatei kdewallet und versuchen Sie es erneut.',
 'internxt_wait':'Verbindung mit Internxt. Entsperren Sie KWallet, wenn Sie dazu aufgefordert werden.',
 'name_error':'Verwenden Sie einen eindeutigen Namen, der mit einem Buchstaben beginnt und nur Buchstaben, Zahlen, Bindestriche oder Unterstriche enthält.',
 'folder_error':'Wählen Sie einen leeren, separaten Ordner in Ihrem persönlichen Ordner ohne symbolische Links.',
 'browser_error':'Der Browser konnte nicht geöffnet werden. Prüfen Sie den Standardbrowser und versuchen Sie es mit der Schaltfläche erneut.',
 'add':'Neue Verbindung','cancel_oauth':'Autorisierung abbrechen','name':'Kontoname',
 'oauth_note':'Konto authentifiziert. Wählen Sie einen Namen und einen leeren Ordner.',
 'auth_wait':'Schließen Sie die Autorisierung im Browser ab (höchstens 10 Minuten).',
 'auth_error':'Konto konnte nicht hinzugefügt werden. Prüfen Sie den eindeutigen Namen und den leeren, separaten Ordner; die Autorisierung wurde möglicherweise abgebrochen.',
 'automount':'Dieses Konto bei der Anmeldung einbinden','settings':'Kontoeinstellungen','path':'Einhängeordner',
 'cache_size':'Cache-Zielgröße (GiB)','cache_age':'Ungenutzten Cache behalten (Stunden)','choose':'Ordner auswählen',
 'prefs_note':'Gilt ab dem nächsten Einbinden. Die Cache-Größe ist ein Bereinigungsziel.',
 'prefs_error':'Speichern fehlgeschlagen. Wählen Sie einen leeren Ordner in Ihrem persönlichen Ordner ohne Links oder Überschneidungen.',
 'note':'Unabhängige Konten · Zugriffsmodus je Konto',
 'confirm':'Dieses Konto trennen? Geöffnete Dateien funktionieren möglicherweise nicht mehr.',
 'disable_auto':'Auch Einbinden bei der Anmeldung deaktivieren','delete':'Verbindung löschen',
 'delete_own':'{name} löschen? Das verwaltete Laufwerk wird getrennt und gespeicherte Zugangsdaten werden entfernt. Cloud-Dateien bleiben erhalten.',
 'delete_external':'{name} gehört zur vorhandenen Rclone-Konfiguration. Löschen ändert diese Konfiguration und wirkt sich auf andere Werkzeuge aus. Cloud-Dateien bleiben erhalten.',
 'delete_error':'Löschen nicht möglich: Trennen Sie zuerst externe oder belegte Laufwerke. Prüfen Sie den Zugriff auf die Konfiguration.',
 'external_origin':'Vorhandene Rclone-Verbindung','app_origin':'Drive-Manager-Konto','error':'Vorgang fehlgeschlagen',
 'empty':'Keine Verbindungen gefunden','busy':'Wird bearbeitet…','mounted':'Eingebunden (nur lesen)',
 'external':'Externes Laufwerk/Dienst','starting':'Starten / erneut verbinden','unmounted':'Nicht eingebunden','failed':'Einbinden fehlgeschlagen',
 'capacity':'Speicher','quota_refresh':'Speicher aktualisieren','quota_loading':'Speicher wird abgefragt…',
 'quota_unknown':'Speicher: Nicht verfügbar','quota_used':'Belegt','quota_free':'Verfügbar','quota_total':'Gesamt',
 'quota_other':'Andere Dienste','quota_trash':'Papierkorb','quota_low':'Wenig Speicher verfügbar',
 'notifications':'Desktop-Benachrichtigungen','notification_settings_error':'Benachrichtigungseinstellung konnte nicht gespeichert werden.',
 'uploads_done':'Die beobachtete Upload-Warteschlange ist jetzt leer.',
 'notice_auth':'Authentifizierung erfordert Aufmerksamkeit. Öffnen Sie die Anwendung und autorisieren Sie dieses Konto erneut, sobald dies sicher möglich ist.',
 'notice_error':'Eine Übertragung ist fehlgeschlagen. Behalten Sie die Verbindung und den Cache, solange Änderungen ausstehen.',
 'file_name':'Datei','account_menu':'Konto','diagnostics':'Diagnose','copy_report':'Bericht kopieren','close_report':'Schließen',
 'upgrade_confirm':'Darf diese Verbindung Ihre Cloud-Dateien ändern? Der Browser wird zur Autorisierung von Lesen/Schreiben geöffnet. Melden Sie sich mit DEMSELBEN Konto an. Abbrechen behält den bisherigen Modus bei.',
 'reauth':'Konto erneut autorisieren',
 'reauth_confirm':'Melden Sie sich mit DEMSELBEN Konto wie bei dieser Verbindung an. Ordner, Cache und Einstellungen bleiben erhalten. Das Konto muss getrennt sein und darf keine ausstehenden Uploads haben. Fortfahren?',
 'reauth_error':'Autorisierung konnte nicht erneuert werden. Verwenden Sie eine getrennte Google-Drive-, OneDrive- oder Dropbox-Verbindung dieser Anwendung ohne eigene OAuth-Zugangsdaten. Die ursprüngliche Verbindung bleibt erhalten.',
 'reauth_identity':'Das ausgewählte OneDrive-Laufwerk ist ein anderes. Die ursprüngliche Verbindung bleibt erhalten.',
 'language':'Sprache','language_error':'Sprache konnte nicht gespeichert werden. Die bisherige Sprache bleibt erhalten.'}

DIAGNOSTICS = {
 'title':'Drive-Manager-Diagnose','ok':'OK','warning':'Prüfen','error':'Fehler',
 'rclone':'Rclone','fuse':'FUSE 3','device':'FUSE-Gerät','systemd_run':'systemd-run','systemd':'Benutzer-systemd',
 'dolphin':'Dolphin','fuser':'Schutz geöffneter Dateien','wallet':'KWallet (Internxt)',
 'connection':'Ausgewählte Verbindung','uploads':'Ausstehende Uploads','installed':'Verfügbar.',
 'missing_rclone':'Installieren Sie rclone (Version 1.73 oder neuer).','old_rclone':'Aktualisieren Sie rclone auf Version 1.73 oder neuer.',
 'missing_fuse':'Installieren Sie fuse3.','missing_systemd_run':'Installieren Sie systemd.',
 'missing_dolphin':'Installieren Sie dolphin, um Ordner zu öffnen.',
 'missing_fuser':'Installieren Sie psmisc zum Schutz geöffneter Dateien beim Trennen.',
 'missing_wallet':'Installieren Sie kf6-kwallet, wenn Sie Internxt verwenden möchten.',
 'probe_failed':'Prüfung nicht möglich. Die Komponente ist möglicherweise belegt oder die Zeitgrenze wurde überschritten.',
 'manager_unavailable':'Benutzer-systemd ist nicht erreichbar. Starten Sie die Anwendung in Ihrer KDE-Sitzung ohne sudo.',
 'device_unavailable':'/dev/fuse kann nicht verwendet werden. Prüfen Sie, ob FUSE in dieser Sitzung verfügbar ist.',
 'no_selection':'Wählen Sie ein Konto, um seinen lokalen Status zu prüfen.','mounted':'Verwaltetes Laufwerk ist aktiv.',
 'external':'Externes Laufwerk: Verwenden Sie das ursprüngliche Werkzeug zur Verwaltung.',
 'starting':'Das Laufwerk wird gestartet oder ist belegt. Warten Sie und aktualisieren Sie die Diagnose.',
 'unmounted':'Konto ist getrennt.','failed':'Einbinden fehlgeschlagen. Prüfen Sie die Abhängigkeiten und verbinden Sie erneut.',
 'unknown':'Status konnte nicht geprüft werden. Aktualisieren Sie die Verbindungen und versuchen Sie es erneut.',
 'pending':'Änderungen stehen noch aus. Warten Sie auf die Uploads; behalten Sie die Verbindung und den Cache.',
 'clean':'Keine ausstehenden Änderungen im Schreibcache erkannt.',
 'unmonitored':'Externes Laufwerk: Die Upload-Warteschlange kann nicht geprüft werden.',
 'footer':'Lokale Prüfung: Internetzugriff, OAuth-Berechtigungen und Cloud-Verfügbarkeit werden nicht geprüft.\nEnthält keine Tokens, Passwörter, E-Mails, Kontonamen, persönlichen Pfade oder Protokolle.\nÄndert keine Konfiguration und startet oder stoppt keine Dienste.'}

MESSAGES.update({'updates': 'Nach Updates suchen',
 'update_checking': 'Updates werden geprüft…',
 'update_installed': 'Installierte Version',
 'update_latest': 'Neueste stabile Version',
 'update_available': 'Ein Update ist verfügbar. Laden Sie das RPM herunter und installieren Sie es '
                     'manuell.',
 'update_current': 'Sie verwenden die neueste veröffentlichte stabile Version.',
 'update_ahead': 'Die installierte Version ist neuer als die zuletzt veröffentlichte stabile '
                 'Version.',
 'update_error': 'Updates konnten nicht geprüft werden. Prüfen Sie die Internetverbindung und '
                 'versuchen Sie es später erneut.',
 'update_rate_limit': 'GitHub begrenzt vorübergehend die Anfragen. Versuchen Sie es später erneut.',
 'update_rpm_missing': 'Kein passendes RPM für Fedora 44 verfügbar. Öffnen Sie die Release-Seite, '
                       'um die Dateien anzuzeigen.',
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

MESSAGES.update({'operation_cancel': 'Prüfung abbrechen', 'operation_cancelling': 'Abbruch läuft… Warten auf den sicheren Abschluss. Ein begonnenes Neuverbinden versucht weiterhin einzubinden.', 'operation_elapsed': 'Vergangen: {seconds} s', 'operation_status': 'Mountstatus prüfen…', 'operation_listing': 'Ordnereinträge lesen…', 'operation_space': 'Dateisystemspeicher abfragen…', 'operation_finished': 'Vorgang beendet. Siehe ausführliches Ergebnis.'})

MESSAGES['operation_close']='Schließen'

MESSAGES.update({'browse_incomplete': 'Unvollständige Messung: Eine Abfrage ist fehlgeschlagen oder hat ihr Zeitlimit überschritten. Mount und Verbindung prüfen und wiederholen. Dies beweist keine Cloudunterbrechung.', 'browse_both_slow': 'Beide Abfragen dauerten mindestens 2 Sekunden. Mit einer Verbindungsprüfung vergleichen, ausstehende Uploads prüfen und später wiederholen. Wiederholtes Aktualisieren während einer laufenden Abfrage vermeiden.', 'browse_listing_slow': 'Die Ordnerliste dauerte mindestens 2 Sekunden. Mit einer Verbindungsprüfung vergleichen. Ordnergröße, Cache oder entfernte Latenz können beitragen; die Messung unterscheidet diese Ursachen nicht.', 'browse_space_slow': 'Die Speicherabfrage dauerte mindestens 2 Sekunden, die Ordnerliste war schneller. Speicher- oder Kontingentabfragen können beitragen. Kontingent separat prüfen; Mountoptionen nicht allein aufgrund dieses Ergebnisses ändern.', 'browse_fast': 'Beide Abfragen dauerten weniger als 2 Sekunden. Wenn der Dateimanager weiterhin hängt, ohne Vorschau und automatische Ordnergrößenberechnung vergleichen, sofern Ihre Version dies anbietet. Einen kleinen Ordner testen. Schnelle Stammordnerabfragen schließen Verzögerungen bei Dateien oder Unterordnern nicht aus.', 'browse_scope': 'Hinweise mit einer Schwelle von 2 Sekunden und einem Zeitlimit von 10 Sekunden je Abfrage. Gemessen wird nur der eingebundene Stammordner, nicht der Dateimanager, Vorschauen, Inhalte oder Uploadabschluss. Der Cache kann Ergebnisse beschleunigen. Keine Dateimanager-Einstellungen, Zugangsdaten oder Mounts geändert.'})

MESSAGES.update({'open': 'Ordner öffnen', 'import_select_note': 'Konten auswählen und Zielordner bearbeiten. Nicht ausgewählte Konten bleiben unverändert. Speichern übernimmt angezeigten Zugriff, Anmeldemontage und Limits nur für getrennte Konten mit sauberem Uploadcache und sicheren leeren Ordnern.'})

MESSAGES.update({'import_mode': 'Importierter Zugriff', 'import_apply': 'Auswahl anwenden', 'import_cancel': 'Abbrechen'})

DIAGNOSTICS.update({'dolphin': 'Standard-Dateimanager', 'missing_dolphin': 'Installieren Sie xdg-utils und richten Sie einen Standard-Dateimanager ein.'})
