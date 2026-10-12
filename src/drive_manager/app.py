"""Qt UI: operations run in a single worker; polling never stops a service."""
import sys
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QIcon, QAction, QDesktopServices
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QSystemTrayIcon, QMenu, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QDialogButtonBox, QFileDialog, QHBoxLayout, QCheckBox, QInputDialog, QProgressBar)
from .process import Runner, OperationError
from .remotes import discover
from .service import Manager
from .settings import Preferences
from queue import Queue, Empty
from .accounts import AuthorizationError
from .providers import PROVIDERS
from .account_list import AccountList

TEXT = {
'en': {'title':'Drive Manager 1.7.0', 'refresh':'Refresh connections', 'mount':'Connect',
'unmount':'Disconnect', 'open':'Open in Dolphin', 'quit':'Quit application', 'oauth_open':'Open authorization browser', 'oauth_port':'Another authorization is using port 53682. Close it or cancel it and retry.',
'oauth_server':'Could not start the local authorization server.',
'onedrive_error':'Could not configure OneDrive. Check Microsoft permissions and selected drive.',
'choose_drive':'Choose your OneDrive drive', 'first_transfer':'First transfer', 'queued_label':'Queued','uploading_label':'Uploading', 'transfers':'Transfers', 'uploading':'Uploading changes', 'queued':'Waiting to upload',
 'transferring':'Transferring files', 'idle':'Queue empty · Cloud connectivity not checked',
 'network_retry':'Network error · Retrying transfers', 'auth_required':'Authentication needs attention',
 'transfer_error':'Transfer error · Changes remain pending', 'monitor_unknown':'Cannot verify synchronization',
 'unmonitored':'Mounted locally · Synchronization not monitored', 'provider_column':'Provider','account':'Account','status':'Status','access':'Access', 'mode':'Mode for new connections', 'mode_ro':'Read only', 'mode_rw':'Read/write',
'mounted_rw':'Mounted (read/write)', 'sync_pending':'Changes uploading or pending',
'sync_unknown':'Upload status could not be verified', 'sync_clean':'Upload queue empty',
'uploads_pending':'Pending changes remain. Wait for uploads, or reconnect in read/write mode to recover them.',
'uploads_unknown':'Cannot verify pending changes. Disconnect and deletion are blocked.',
'files_open':'Close files and Dolphin windows on this drive before disconnecting.',
'needs_write_auth':'This account was authorized for reading. Enable read/write in account settings to authorize access.',
'write_note':'Read/write changes your cloud files. Google/Microsoft may ask you to authorize write access in your browser.',
'provider':'Provider for new connection', 'email':'Email', 'password':'Password', 'twofa':'Internxt two-factor code',
'internxt_error':'Internxt login failed. Check credentials, two-factor code and plan compatibility.',
'wallet_error':'Unlock or create the KDE wallet named kdewallet, then retry.',
'internxt_wait':'Connecting to Internxt. Unlock KDE Wallet if requested.',
'name_error':'Use a unique name starting with a letter, with only letters, numbers, hyphens or underscores.',
'folder_error':'Choose an empty, separate folder inside your home directory, without symlinks.',
'browser_error':'The browser could not be opened. Check your default browser and retry the button.',
'add':'New connection', 'cancel_oauth':'Cancel authorization', 'name':'Account name',
'oauth_note':'Account authenticated. Choose its name and an empty folder.',
'auth_wait':'Complete authorization in your browser (up to 10 minutes).',
'auth_error':'Could not add account. Check unique name and empty, separate home folder; authorization may have been cancelled.',
'automount':'Mount this account at login', 'settings':'Account settings', 'path':'Mount folder',
'cache_size':'Cache target (GiB)', 'cache_age':'Keep unused cache (hours)',
'choose':'Choose folder', 'prefs_note':'Applies on next mount. Cache size is a cleanup target.',
'prefs_error':'Cannot save. Use an empty folder inside your home, without symlinks or account overlap.',
'note':'Independent accounts · Choose access mode per account',
'confirm':'Disconnect this account? Open files may stop working.',
'disable_auto':'Also disable mounting at login', 'delete':'Delete connection',
'delete_own':'Delete {name}? Its managed mount will be disconnected and saved credentials removed. Google Drive files are preserved.',
'delete_external':'{name} belongs to the existing Rclone configuration. Deleting it modifies that configuration and affects other tools. Google Drive files are preserved.',
'delete_error':'Cannot delete: disconnect external or busy mounts first. Check access to the connection configuration.',
'external_origin':'Existing Rclone connection', 'app_origin':'Drive Manager account',
'error':'Operation failed', 'empty':'No connections found',
'busy':'Working…', 'mounted':'Mounted (read-only)', 'external':'External mount/service',
'starting':'Starting / reconnecting', 'unmounted':'Unmounted', 'failed':'Mount failed'},
'es': {'title':'Drive Manager 1.7.0', 'refresh':'Actualizar conexiones', 'mount':'Conectar',
'unmount':'Desconectar', 'open':'Abrir en Dolphin', 'quit':'Salir de la aplicación', 'oauth_open':'Abrir navegador para autorizar', 'oauth_port':'Otra autorización ocupa el puerto 53682. Ciérrala o cancélala y vuelve a intentarlo.',
'oauth_server':'No se pudo iniciar el servidor local de autorización.',
'onedrive_error':'No se pudo configurar OneDrive. Comprueba permisos de Microsoft y unidad elegida.',
'choose_drive':'Elige tu unidad de OneDrive', 'first_transfer':'Primera transferencia', 'queued_label':'En espera','uploading_label':'Subiendo', 'transfers':'Transferencias', 'uploading':'Subiendo cambios', 'queued':'Esperando subida',
 'transferring':'Transfiriendo archivos', 'idle':'Cola vacía · Conectividad con la nube no comprobada',
 'network_retry':'Error de red · Reintentando transferencias', 'auth_required':'La autenticación requiere atención',
 'transfer_error':'Error de transferencia · Quedan cambios pendientes', 'monitor_unknown':'No se puede verificar la sincronización',
 'unmonitored':'Montado localmente · Sin supervisión de sincronización', 'provider_column':'Proveedor','account':'Cuenta','status':'Estado','access':'Acceso', 'mode':'Modo de las nuevas conexiones', 'mode_ro':'Solo lectura', 'mode_rw':'Lectura/escritura',
'mounted_rw':'Montado (lectura/escritura)', 'sync_pending':'Cambios subiendo o pendientes',
'sync_unknown':'No se pudo verificar el estado de las subidas', 'sync_clean':'Cola de subidas vacía',
'uploads_pending':'Quedan cambios pendientes. Espera las subidas o vuelve a conectar en escritura para recuperarlos.',
'uploads_unknown':'No se pueden verificar los cambios pendientes. Se bloquea desconectar y eliminar.',
'files_open':'Cierra los archivos y ventanas de Dolphin de esta unidad antes de desconectar.',
'needs_write_auth':'Esta cuenta se autorizó para lectura. Activa lectura/escritura en los ajustes de la cuenta para autorizar el acceso.',
'write_note':'Lectura/escritura modifica archivos de la nube. Las cuentas Google/Microsoft autorizadas solo para lectura requieren una nueva autorización.',
'provider':'Proveedor de la nueva conexión', 'email':'Correo', 'password':'Contraseña', 'twofa':'Código de dos factores de Internxt',
'internxt_error':'Falló el acceso a Internxt. Comprueba credenciales, código de dos factores y compatibilidad del plan.',
'wallet_error':'Desbloquea o crea la cartera KDE llamada kdewallet y vuelve a intentarlo.',
'internxt_wait':'Conectando a Internxt. Desbloquea KWallet si lo solicita.',
'name_error':'Usa un nombre único que empiece por una letra, solo con letras, números, guiones o guiones bajos.',
'folder_error':'Elige una carpeta vacía e independiente dentro de tu directorio personal, sin enlaces simbólicos.',
'browser_error':'No se pudo abrir el navegador. Comprueba el navegador predeterminado y reintenta con el botón.',
'add':'Nueva conexión', 'cancel_oauth':'Cancelar autorización', 'name':'Nombre de la cuenta',
'oauth_note':'Cuenta autenticada. Elige su nombre y una carpeta vacía.',
'auth_wait':'Completa la autorización en el navegador (hasta 10 minutos).',
'auth_error':'No se pudo añadir. Comprueba nombre único y carpeta vacía e independiente; la autorización puede haberse cancelado.',
'automount':'Montar esta cuenta al iniciar sesión', 'settings':'Ajustes de la cuenta', 'path':'Carpeta de montaje',
'cache_size':'Objetivo de caché (GiB)', 'cache_age':'Conservar caché sin uso (horas)',
'choose':'Elegir carpeta', 'prefs_note':'Se aplica al próximo montaje. El tamaño es un objetivo de limpieza.',
'prefs_error':'No se pudo guardar. Usa una carpeta vacía dentro de tu directorio personal, sin enlaces ni solapamientos.',
'note':'Cuentas independientes · Modo de acceso por cuenta',
'confirm':'¿Desconectar esta cuenta? Los archivos abiertos pueden dejar de funcionar.',
'disable_auto':'Desactivar también el montaje al iniciar sesión', 'delete':'Eliminar conexión',
'delete_own':'¿Eliminar {name}? Se desconectará su montaje propio y se retirarán las credenciales guardadas. Los archivos de Google Drive se conservan.',
'delete_external':'{name} pertenece a la configuración existente de Rclone. Eliminarla modifica esa configuración y afecta a otras herramientas. Los archivos de Google Drive se conservan.',
'delete_error':'No se pudo eliminar: desmonta primero los montajes externos u ocupados y comprueba el acceso a la configuración.',
'external_origin':'Conexión existente de Rclone', 'app_origin':'Cuenta de Drive Manager',
'error':'La operación ha fallado', 'empty':'No hay conexiones guardadas',
'busy':'Procesando…', 'mounted':'Montado (solo lectura)', 'external':'Montaje/servicio externo',
'starting':'Iniciando / reconectando', 'unmounted':'Desmontado', 'failed':'Montaje fallido'}}

TEXT['en'].update({
    'upgrade_confirm': 'Allow this connection to modify your cloud files? Your browser will open to authorize read/write access. Sign in with the SAME account. Cancelling keeps the current mode.',
    'reauth': 'Reauthorize account',
    'reauth_confirm': 'Sign in with the SAME account as this connection. Its folder, cache and settings will be kept. The connection must be disconnected, with no pending uploads. Continue?',
    'reauth_error': 'Could not renew authorization. Use a disconnected Google Drive or OneDrive connection created by this app, without custom OAuth credentials. The original connection has been preserved.',
    'reauth_identity': 'The selected OneDrive belongs to another drive. The original connection has been preserved.'})
TEXT['es'].update({
    'upgrade_confirm': '¿Permitir que esta conexión modifique tus archivos en la nube? Se abrirá el navegador para autorizar lectura/escritura. Inicia sesión con la MISMA cuenta. Cancelar conserva el modo actual.',
    'reauth': 'Reautorizar cuenta',
    'reauth_confirm': 'Inicia sesión con la MISMA cuenta de esta conexión. Se conservarán su carpeta, caché y ajustes. Debe estar desconectada y sin subidas pendientes. ¿Continuar?',
    'reauth_error': 'No se pudo renovar la autorización. Usa una conexión Google Drive o OneDrive creada por esta aplicación, desconectada y sin credenciales OAuth personalizadas. Se conserva la conexión original.',
    'reauth_identity': 'La unidad OneDrive seleccionada es distinta. Se conserva la conexión original.'})

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        import locale
        self.t = TEXT['es' if (locale.getlocale()[0] or '').startswith('es') else 'en']
        self.manager = Manager(Runner())
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.polling = False
        self.pending_action = None
        self.oauth_cancel = None
        self.oauth_urls = Queue()
        self.twofa_requests = Queue()
        self.drive_requests = Queue()
        self.browser_url = None
        self.last_error = False
        self.pending_registration = None
        self.auth_write = False
        self.setWindowTitle(self.t['title'])
        self.resize(900, 650)
        body = QWidget(); layout = QVBoxLayout(body); self.setCentralWidget(body)
        layout.addWidget(QLabel(self.t['note']))
        self.accounts = AccountList([self.t['account'],self.t['provider_column'],self.t['path'],self.t['access'],self.t['status']]); layout.addWidget(self.accounts)
        layout.addWidget(QLabel(self.t['provider']))
        self.provider = QComboBox()
        for provider in PROVIDERS:
            self.provider.addItem(provider.label, provider.key)
            self.provider.model().item(self.provider.count()-1).setEnabled(provider.available)
        layout.addWidget(self.provider)
        layout.addWidget(QLabel(self.t['mode']))
        self.access_mode = QComboBox(); self.access_mode.addItems([self.t['mode_ro'], self.t['mode_rw']]); layout.addWidget(self.access_mode)
        self.label = QLabel(); self.label.setWordWrap(True); layout.addWidget(self.label)
        layout.addWidget(QLabel(self.t['transfers']))
        self.transfer_table = AccountList([self.t['name'],'%','KiB/s','ETA'])
        self.transfer_table.setMaximumHeight(160)
        layout.addWidget(self.transfer_table)
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0,100); self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        self.buttons = {}
        for key, callback in [('refresh', self.refresh), ('mount', self.mount),
                              ('unmount', self.unmount), ('open', self.open_folder),
                              ('reauth', self.reauthorize_account), ('settings', self.edit_settings), ('delete', self.delete_connection), ('add', self.add_account),
                              ('cancel_oauth', self.cancel_authorization), ('oauth_open', self.open_authorization)]:
            button = QPushButton(self.t[key]); button.clicked.connect(callback)
            layout.addWidget(button); self.buttons[key] = button
        self.buttons['cancel_oauth'].setEnabled(False)
        self.buttons['oauth_open'].setEnabled(False)
        self.accounts.currentIndexChanged.connect(self.selection_changed)
        self.tray = QSystemTrayIcon(QIcon.fromTheme('drive-harddisk'), self)
        menu = QMenu(self)
        show = QAction(self.t['title'], self); show.triggered.connect(self.showNormal); menu.addAction(show)
        quit_action = QAction(self.t['quit'], self); quit_action.triggered.connect(self.quit); menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.showNormal())
        if self.tray.isSystemTrayAvailable(): self.tray.show()
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(250)
        self.poll_ticks = 0
        self.refresh()

    def submit(self, task, callback, error_key="error", quiet=False):
        if self.future is not None:
            if self.polling and not quiet and self.pending_action is None:
                self.pending_action=(task,callback,error_key)
                for button in self.buttons.values():button.setEnabled(False)
                self.accounts.setEnabled(False)
                self.provider.setEnabled(False)
                self.access_mode.setEnabled(False)
            return
        self.last_error = False
        self.polling = quiet
        self.future = self.pool.submit(task)
        self.callback = callback
        self.error_key = error_key
        if quiet: return
        for button in self.buttons.values(): button.setEnabled(False)
        self.accounts.setEnabled(False)
        self.provider.setEnabled(False)
        self.access_mode.setEnabled(False)
        self.buttons['cancel_oauth'].setEnabled(self.oauth_cancel is not None)

    def open_authorization(self):
        if self.browser_url and not QDesktopServices.openUrl(QUrl(self.browser_url)):
            self.label.setText(self.t['browser_error'])

    def tick(self):
        try:
            while True:
                choices, event, answer, cancel = self.drive_requests.get_nowait()
                if cancel.is_set(): event.set(); continue
                labels = [str(index+1)+'. '+str(label)[:200] for index, (_, label) in enumerate(choices)]
                self.timer.stop()
                try:
                    selected, accepted = QInputDialog.getItem(self, self.t['choose_drive'], self.t['choose_drive'], labels, 0, False)
                    answer['value'] = choices[labels.index(selected)][0] if accepted else None
                finally: event.set(); self.timer.start(250)
        except Empty:
            pass
        try:
            while True:
                event, answer = self.twofa_requests.get_nowait()
                self.timer.stop()
                try:
                    code, accepted = QInputDialog.getText(self, self.t['twofa'], self.t['twofa'], QLineEdit.EchoMode.Password)
                    answer['code'] = code if accepted else ''
                finally:
                    event.set(); self.timer.start(250)
        except Empty:
            pass
        try:
            while True:
                url = self.oauth_urls.get_nowait()
                if self.oauth_cancel is not None and not self.oauth_cancel.is_set():
                    self.browser_url = url
                    self.buttons['oauth_open'].setEnabled(True)
                    self.open_authorization()
        except Empty:
            pass
        if self.future is not None and self.future.done():
            future, self.future = self.future, None
            was_polling,self.polling=self.polling,False
            if self.pending_action is not None:
                action,self.pending_action=self.pending_action,None
                self.submit(*action)
                return
            self.accounts.setEnabled(True)
            self.provider.setEnabled(True)
            self.access_mode.setEnabled(True)
            self.buttons['refresh'].setEnabled(True)
            self.buttons['add'].setEnabled(True)
            if not was_polling:
                self.buttons['cancel_oauth'].setEnabled(False)
                self.buttons['oauth_open'].setEnabled(False)
                self.browser_url = None
                self.oauth_cancel = None
            try: self.callback(future.result())
            except Exception as error:
                # Raw diagnostics may contain OAuth secrets. Never display or log them.
                self.last_error = True
                key = self.error_key
                if isinstance(error, OperationError) and str(error) in {'uploads_pending','uploads_unknown','files_open','needs_write_auth','reauth_identity'}:
                    key = str(error)
                if isinstance(error, AuthorizationError): key = error.key
                elif key == 'auth_error' and isinstance(error, OperationError):
                    message = str(error)
                    if message in {'wallet_error', 'internxt_error'}: key = message
                    if message in {'Connection name already exists', 'Use a unique name with letters, numbers, underscores or hyphens'}:
                        key = 'name_error'
                    elif any(word in message.lower() for word in ('folder', 'path', 'preferences')):
                        key = 'folder_error'
                self.label.setText(self.t[key])
                self.tray.setToolTip(self.t['error'])
                self.buttons['mount'].setEnabled(bool(self.accounts.currentText()))
        self.poll_ticks += 1
        if self.poll_ticks >= 8:
            self.poll_ticks = 0; self.poll()

    def refresh(self):
        self.submit(self.manager.discover_accounts, self.set_accounts)

    def set_accounts(self, names, selected=None):
        current = selected or self.accounts.currentText()
        self.accounts.blockSignals(True); self.accounts.clear(); self.accounts.addItems(names)
        if current in names: self.accounts.setCurrentText(current)
        self.accounts.blockSignals(False)
        if names: self.poll()
        else:
            self.label.setText(self.t['empty'])
            self.transfer_table.clear(); self.progress_bar.hide()
            for key in ('mount', 'unmount', 'settings', 'open', 'delete', 'reauth'):
                self.buttons[key].setEnabled(False)

    def selection_changed(self):
        self.last_error = False
        self.poll()

    def poll(self):
        if self.last_error: return
        remote = self.accounts.currentText()
        if remote:
            names=[self.accounts.item(row,0).text() for row in range(self.accounts.rowCount())]
            self.submit(lambda:[(name,self.manager.provider_of(name),self.manager.status(name)) for name in names],self.show_accounts,quiet=True)

    def show_accounts(self, rows):
        labels={provider.key:provider.label for provider in PROVIDERS}
        for name,provider,status in rows:
            self.accounts.update_account(name,labels.get(provider,provider),status.path,
                '—' if status.state=='external' else self.t['mode_rw' if status.writable else 'mode_ro'],
                self.t[status.progress.state] if status.progress is not None else self.t['mounted_rw' if status.writable and status.state=='mounted' else status.state])
            if name==self.accounts.currentText():self.show_status(status)

    def show_status(self, status):
        self.accounts.update_account(self.accounts.currentText(), self.accounts.item(self.accounts.currentRow(),1).text(),
            status.path, '—' if status.state=='external' else self.t['mode_rw' if status.writable else 'mode_ro'], self.t[status.progress.state] if status.progress is not None else self.t['mounted_rw' if status.writable and status.state=='mounted' else status.state])
        origin = 'app_origin' if self.manager.is_app_account(self.accounts.currentText()) else 'external_origin'
        title = self.t['mounted_rw'] if status.writable and status.state=='mounted' else self.t[status.state]
        sync = ('\n'+self.t['sync_unknown' if status.pending<0 else 'sync_pending' if status.pending else 'sync_clean']) if status.writable and status.managed else ''
        detail=status.progress
        if status.managed and detail is not None:
            sync='\n'+self.t[detail.state]+f" · {self.t['queued_label']}: {detail.queued} · {self.t['uploading_label']}: {detail.uploading}"
        elif status.managed: sync='\n'+self.t['unmonitored']
        self.label.setText(title + ' · ' + self.t[origin] + '\n' + status.path + sync)
        self.transfer_table.clear();self.progress_bar.hide()
        if detail is not None:
            self.transfer_table.addItems([file.name for file in detail.files])
            from PySide6.QtWidgets import QTableWidgetItem
            for row,file in enumerate(detail.files):
                values=[file.name, '—' if file.percentage is None else f'{file.percentage:.0f}%',
                        f'{file.speed/1024:.1f}', '—' if file.eta is None else f'{file.eta:.0f} s']
                for col,value in enumerate(values): self.transfer_table.setItem(row,col,QTableWidgetItem(value))
            if detail.files:
                percent=detail.files[0].percentage
                self.progress_bar.setFormat(self.t['first_transfer'] + ' %p%')
                self.progress_bar.setRange(0,0 if percent is None else 100)
                if percent is not None:self.progress_bar.setValue(round(percent))
                self.progress_bar.show()
        self.tray.setToolTip(self.t[detail.state] if detail is not None else self.t[status.state])
        self.tray.setIcon(QIcon.fromTheme('drive-harddisk' if status.managed else 'network-server'))
        self.buttons['mount'].setEnabled(status.state in {'unmounted', 'failed'})
        self.buttons['reauth'].setEnabled(self.manager.is_app_account(self.accounts.currentText()) and status.state in {'unmounted', 'failed'})
        self.buttons['settings'].setEnabled(status.state in {'unmounted', 'failed'})
        self.buttons['unmount'].setEnabled(status.managed)
        self.buttons['delete'].setEnabled(status.managed or status.state in {'unmounted', 'failed'})
        self.buttons['open'].setEnabled(status.state in {'mounted', 'external'})

    def edit_settings(self):
        remote = self.accounts.currentText()
        self.submit(lambda: self.manager.settings.load(remote), self.settings_dialog)

    def settings_dialog(self, prefs):
        remote = self.accounts.currentText()
        dialog = QDialog(self); dialog.setWindowTitle(self.t['settings'] + ' · ' + remote)
        form = QFormLayout(dialog)
        path = QLineEdit(prefs.mount_path or str(self.manager.identity(remote)[1]))
        browse = QPushButton(self.t['choose'])
        row = QWidget(); row_layout = QHBoxLayout(row); row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.addWidget(path); row_layout.addWidget(browse)
        def choose():
            folder = QFileDialog.getExistingDirectory(dialog, self.t['choose'], path.text())
            if folder: path.setText(folder)
        browse.clicked.connect(choose)
        form.addRow(self.t['path'], row)
        size = QSpinBox(); size.setRange(1, 1024); size.setValue(prefs.cache_gib)
        age = QSpinBox(); age.setRange(1, 8760); age.setValue(prefs.cache_hours)
        form.addRow(self.t['cache_size'], size); form.addRow(self.t['cache_age'], age)
        automount = QCheckBox(self.t['automount']); automount.setChecked(prefs.automount)
        form.addRow(automount)
        writable = QCheckBox(self.t['mode_rw']); writable.setChecked(prefs.writable); form.addRow(writable)
        note = QLabel(self.t['write_note']); note.setWordWrap(True); form.addRow(note)
        form.addRow(QLabel(self.t['prefs_note']))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        self.timer.stop()
        try:
            accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally:
            self.timer.start(250)
        if accepted:
            updated = Preferences(path.text().strip(), size.value(), age.value(), automount.isChecked(), writable.isChecked())
            self.save_account_preferences(remote, updated)
        else:
            self.poll()

    def save_account_preferences(self, remote, prefs):
        def save():
            try:
                return self.manager.save_preferences(remote, prefs)
            except OperationError as error:
                if str(error) == 'needs_write_auth' and self.manager.is_app_account(remote):
                    return None
                raise
        def saved(status):
            if status is not None:
                self.show_status(status)
                return
            if QMessageBox.question(self, self.t['reauth'], self.t['upgrade_confirm'],
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                self.poll()
                return
            from threading import Event
            cancel = Event(); self.oauth_cancel = cancel
            self.browser_url = None
            while not self.oauth_urls.empty(): self.oauth_urls.get_nowait()
            self.label.setText(self.t['auth_wait'])
            def authorize_and_save():
                self.manager.reauthorize(remote, cancel, self.oauth_urls.put,
                    self.ask_onedrive_drive, confirmed=True, request_write=True)
                # Mode remains read-only until all preference checks succeed.
                if cancel.is_set(): raise OperationError('reauth_error')
                return self.manager.save_preferences(remote, prefs)
            self.submit(authorize_and_save, self.show_status, 'reauth_error')
        self.submit(save, saved, 'prefs_error')

    def ask_internxt_code(self, cancel):
        from threading import Event
        import time
        event = Event(); answer = {}; self.twofa_requests.put((event, answer))
        deadline = time.monotonic() + 180
        while not event.wait(.2):
            if cancel.is_set() or time.monotonic() > deadline: return ''
        return answer.get('code', '')

    def internxt_login(self):
        dialog = QDialog(self); dialog.setWindowTitle('Internxt')
        form = QFormLayout(dialog)
        name = QLineEdit('internxt'); email = QLineEdit(); password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(self.t['name'], name); form.addRow(self.t['email'], email); form.addRow(self.t['password'], password)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        self.timer.stop()
        try: accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally: self.timer.start(250)
        if not accepted: password.clear(); return
        remote = name.text().strip(); user = email.text().strip(); secret = password.text(); password.clear()
        from threading import Event
        cancel = Event(); self.oauth_cancel = cancel
        self.label.setText(self.t['internxt_wait'])
        self.submit(lambda: self.manager.begin_internxt(remote, user, secret, cancel, self.ask_internxt_code),
                    self.connection_details, 'auth_error')

    def ask_onedrive_drive(self, choices, cancel):
        from threading import Event
        import time
        event = Event(); answer = {}; self.drive_requests.put((choices, event, answer, cancel))
        deadline = time.monotonic() + 180
        while not event.wait(.2):
            if cancel.is_set() or time.monotonic() > deadline: return None
        return answer.get('value')

    def reauthorize_account(self):
        remote = self.accounts.currentText()
        if not remote: return
        if QMessageBox.question(self, self.t['reauth'], self.t['reauth_confirm'],
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        from threading import Event
        self.browser_url = None
        while not self.oauth_urls.empty(): self.oauth_urls.get_nowait()
        cancel = Event(); self.oauth_cancel = cancel
        self.label.setText(self.t['auth_wait'])
        self.submit(lambda: self.manager.reauthorize(remote, cancel, self.oauth_urls.put,
                    self.ask_onedrive_drive, confirmed=True),
                    lambda names: self.set_accounts(names, remote), 'reauth_error')

    def add_account(self):
        self.auth_write = self.access_mode.currentIndex() == 1
        if self.provider.currentData() == "internxt":
            self.internxt_login(); return
        from threading import Event
        self.browser_url = None
        while not self.oauth_urls.empty(): self.oauth_urls.get_nowait()
        cancel = Event(); self.oauth_cancel = cancel
        self.label.setText(self.t['auth_wait'])
        provider = self.provider.currentData()
        self.submit(lambda: self.manager.begin_authorization(cancel, self.oauth_urls.put, provider, self.ask_onedrive_drive, self.auth_write),
                    self.connection_details, 'auth_error')

    def connection_details(self, registration):
        self.pending_registration = registration
        dialog = QDialog(self); dialog.setWindowTitle(self.t['add'])
        form = QFormLayout(dialog)
        from pathlib import Path
        encrypted = self.manager.accounts.encrypted(registration[1])
        prefix = 'onedrive_' if registration[0].startswith('onedrive_') else 'google_'
        default = registration[0] if encrypted else prefix + registration[0][-6:]
        name = QLineEdit(default); name.setReadOnly(encrypted); form.addRow(self.t['name'], name)
        path = QLineEdit(str(self.manager.home / 'Drives' / default)); browse = QPushButton(self.t['choose'])
        row = QWidget(); layout = QHBoxLayout(row); layout.addWidget(path); layout.addWidget(browse)
        def choose():
            folder = QFileDialog.getExistingDirectory(dialog, self.t['choose'], str(self.manager.home))
            if folder: path.setText(folder)
        browse.clicked.connect(choose)
        form.addRow(self.t['path'], row)
        auto = QCheckBox(self.t['automount']); form.addRow(auto)
        writable = QCheckBox(self.t['mode_rw']); writable.setChecked(self.auth_write)
        writable.setEnabled(encrypted or self.auth_write); form.addRow(writable)
        note = QLabel(self.t['oauth_note']); note.setWordWrap(True); form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        self.timer.stop()
        try: accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally: self.timer.start(250)
        if not accepted:
            registration[1].unlink(missing_ok=True)
            self.pending_registration = None
            self.refresh()
            return
        from threading import Event
        prefs = Preferences(path.text().strip(), automount=auto.isChecked(), writable=writable.isChecked())
        remote = name.text().strip()
        def finish():
            try:
                return self.manager.add_account(remote, prefs, Event(), registration=registration)
            finally:
                registration[1].unlink(missing_ok=True)
        self.pending_registration = None
        self.submit(finish, lambda names: self.set_accounts(names, remote), 'auth_error')

    def cancel_authorization(self):
        if self.oauth_cancel is not None: self.oauth_cancel.set()

    def mount(self):
        remote = self.accounts.currentText()
        self.submit(lambda: self.manager.mount(remote), self.show_status)

    def unmount(self):
        remote = self.accounts.currentText()
        box = QMessageBox(self)
        box.setWindowTitle(self.t['unmount'] + ' · ' + remote)
        box.setText(self.t['confirm'])
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        option = QCheckBox(self.t['disable_auto']); box.setCheckBox(option)
        self.timer.stop()
        try: accepted = box.exec() == QMessageBox.StandardButton.Yes
        finally: self.timer.start(250)
        if accepted:
            disable = option.isChecked()
            self.submit(lambda: self.manager.disconnect(remote, confirmed=True, disable_automount=disable), self.show_status)

    def delete_connection(self):
        remote = self.accounts.currentText()
        own = self.manager.is_app_account(remote)
        text = self.t['delete_own' if own else 'delete_external'].format(name=remote)
        self.timer.stop()
        try:
            accepted = QMessageBox.question(self, self.t['delete'], text,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
        finally: self.timer.start(250)
        if accepted:
            self.submit(lambda: self.manager.remove_connection(remote, confirmed=True, external_confirmed=not own),
                        self.set_accounts, 'delete_error')

    def open_folder(self):
        remote = self.accounts.currentText()
        self.submit(lambda: (self.manager.open_folder(remote), self.manager.status(remote))[1], self.show_status)

    def closeEvent(self, event):
        if self.tray.isVisible(): self.hide(); event.ignore()
        else: self.quit(); event.accept()

    def quit(self):
        self.cancel_authorization()
        self.pending_action = None
        if self.pending_registration is not None:
            self.pending_registration[1].unlink(missing_ok=True)
            self.pending_registration = None
        self.pool.shutdown(wait=False, cancel_futures=True)
        QApplication.instance().quit()

def main():
    if '--automount' in sys.argv:
        from .autostart import run
        return run()
    app = QApplication(sys.argv)
    app.setApplicationName('Drive Manager')
    app.setQuitOnLastWindowClosed(False)
    window = Window(); window.show()
    return app.exec()

if __name__ == '__main__':
    sys.exit(main())
