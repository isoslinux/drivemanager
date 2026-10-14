"""Qt UI: operations run in a single worker; polling never stops a service."""
import sys
from threading import Event
from .performance import slow
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QTimer, QUrl, Qt
from PySide6.QtGui import QIcon, QAction, QDesktopServices
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox, QSystemTrayIcon, QMenu, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QDialogButtonBox, QFileDialog, QHBoxLayout, QCheckBox, QInputDialog, QProgressBar, QPlainTextEdit, QToolButton, QTableWidget, QTableWidgetItem, QAbstractItemView)
from .process import Runner, OperationError
from .remotes import discover
from .service import Manager
from .settings import Preferences
from queue import Queue, Empty
from .accounts import AuthorizationError
from .providers import PROVIDERS
from .account_list import AccountList
from . import __version__

from .i18n import TEXT, LANGUAGES, LanguageSettings, StandardTranslator, install_qt_language

from .bulk_ui import BulkActions

class Window(BulkActions,QMainWindow):
    def __init__(self):
        super().__init__()
        self.manager = Manager(Runner())
        self.language_settings = LanguageSettings(self.manager.home)
        self.language = self.language_settings.load()
        self.t = TEXT[self.language]
        self.qt_translator = install_qt_language(QApplication.instance(), self.language)
        self.standard_translator = StandardTranslator(self.language, self)
        QApplication.instance().installTranslator(self.standard_translator)
        from .notifications import Tracker, NotificationSettings
        self.notice_tracker = Tracker()
        self.notification_settings = NotificationSettings(self.manager.home)
        self.notifications_enabled = self.notification_settings.load()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.update_pool = ThreadPoolExecutor(max_workers=1)
        self.update_future = None
        self.health_pool = ThreadPoolExecutor(max_workers=1)
        self.health_future = None
        self.browse_future = None
        self.health_results = {}
        self.health_warned = set()
        self.health_last = 0
        self.validation_pool = ThreadPoolExecutor(max_workers=1)
        self.validation_future = None
        self.validation_queue = Queue()
        self.validation_dialog = None
        self.validation_cancel = Event()
        self.connection_pool = ThreadPoolExecutor(max_workers=1)
        self.connection_future = None
        self.connection_results = {}
        self.connection_cancel = Event()
        self.quota_pool = ThreadPoolExecutor(max_workers=1)
        self.quota_future = None
        self.quota_cache = {}
        self.quota_warned = set()
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
        self.account_states = {}
        self.setWindowTitle(self.t['title']+' '+__version__)
        self.resize(1000, 600)
        body = QWidget(); layout = QVBoxLayout(body); self.setCentralWidget(body)
        self.buttons = {}
        def button(key, callback, row):
            control = QPushButton(self.t[key]); control.clicked.connect(callback)
            row.addWidget(control); self.buttons[key] = control
            return control
        toolbar = QHBoxLayout()
        button('add', self.add_account, toolbar)
        toolbar.addStretch()
        self.update_button = QToolButton(); self.update_button.setText(self.t['updates'])
        self.update_button.clicked.connect(self.check_updates); toolbar.addWidget(self.update_button)
        button('refresh', self.refresh, toolbar)
        button('diagnostics', self.diagnose, toolbar)
        self.tools_button=QToolButton();self.tools_button.setText(self.t['tools'])
        tools_menu=QMenu(self)
        self.tools_actions={}
        for key,callback in [('setup_guide',self.setup_guide),('browse_measure',self.browse_measure),('validate_all',self.validation_panel),('export_settings',self.export_settings),('import_settings',self.import_settings)]:
            action=QAction(self.t[key],self);action.triggered.connect(callback);tools_menu.addAction(action);self.tools_actions[key]=action
        self.tools_button.setMenu(tools_menu);self.tools_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar.addWidget(self.tools_button)
        layout.addLayout(toolbar)
        self.setup_banner=QPushButton(self.t['setup_guide']);self.setup_banner.clicked.connect(self.setup_guide);self.setup_banner.hide();layout.addWidget(self.setup_banner)
        connection_options = QHBoxLayout()
        self.provider_label = QLabel(self.t['provider']); connection_options.addWidget(self.provider_label)
        self.provider = QComboBox()
        for provider in PROVIDERS:
            self.provider.addItem(provider.label, provider.key)
            self.provider.model().item(self.provider.count()-1).setEnabled(provider.available)
        connection_options.addWidget(self.provider)
        connection_options.addSpacing(16)
        self.mode_label = QLabel(self.t['mode']); connection_options.addWidget(self.mode_label)
        self.access_mode = QComboBox(); self.access_mode.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents); self.access_mode.addItems([self.t['mode_ro'], self.t['mode_rw']])
        connection_options.addWidget(self.access_mode); connection_options.addStretch()
        layout.addLayout(connection_options)
        language_row = QHBoxLayout()
        self.note_label = QLabel(self.t['note']); language_row.addWidget(self.note_label)
        language_row.addStretch()
        self.language_label = QLabel(self.t['language']); language_row.addWidget(self.language_label)
        self.language_selector = QComboBox()
        for key,name in LANGUAGES.items(): self.language_selector.addItem(name,key)
        self.language_selector.setCurrentIndex(self.language_selector.findData(self.language))
        language_row.addWidget(self.language_selector); layout.addLayout(language_row)
        self.accounts = AccountList([self.t['account'],self.t['provider_column'],self.t['path'],self.t['access'],self.t['status']])
        layout.addWidget(self.accounts, 1)
        primary = QHBoxLayout()
        for key, callback in [('mount', self.mount), ('unmount', self.unmount), ('open', self.open_folder)]:
            button(key, callback, primary)
        primary.addStretch()
        self.account_menu = QMenu(self)
        for key, callback in [('check_connection', self.check_connection), ('settings', self.edit_settings), ('reauth', self.reauthorize_account), ('renew_credentials', self.renew_account_credentials), ('delete', self.delete_connection)]:
            if key == 'delete': self.account_menu.addSeparator()
            action = QAction(self.t[key], self); action.triggered.connect(callback)
            action.setEnabled(False); self.account_menu.addAction(action); self.buttons[key] = action
        self.account_menu_button = QToolButton()
        self.account_menu_button.setText(self.t['account_menu'])
        self.account_menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.account_menu_button.setMenu(self.account_menu); self.account_menu_button.setEnabled(False)
        primary.addWidget(self.account_menu_button); layout.addLayout(primary)
        self.accounts.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.accounts.customContextMenuRequested.connect(self.open_account_menu)
        self.label = QLabel(); self.label.setWordWrap(True); layout.addWidget(self.label)
        self.connection_label = QLabel(); self.connection_label.setWordWrap(True)
        layout.addWidget(self.connection_label)
        self.health_label=QLabel();self.health_label.setWordWrap(True);layout.addWidget(self.health_label)
        quota_header = QHBoxLayout()
        self.quota_label = QLabel(self.t['quota_unknown']); self.quota_label.setWordWrap(True)
        quota_header.addWidget(self.quota_label, 1)
        self.quota_refresh = QToolButton(); self.quota_refresh.setText(self.t['quota_refresh'])
        self.quota_refresh.clicked.connect(self.refresh_quota); quota_header.addWidget(self.quota_refresh)
        layout.addLayout(quota_header)
        self.quota_bar = QProgressBar(); self.quota_bar.setRange(0,100); self.quota_bar.hide()
        layout.addWidget(self.quota_bar)
        oauth_row = QHBoxLayout()
        for key, callback in [('cancel_oauth', self.cancel_authorization), ('oauth_open', self.open_authorization)]:
            control = button(key, callback, oauth_row); control.setEnabled(False); control.hide()
        oauth_row.addStretch(); layout.addLayout(oauth_row)
        self.transfer_toggle = QToolButton(); self.transfer_toggle.setText(self.t['transfers'])
        self.transfer_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.transfer_toggle.setCheckable(True); self.transfer_toggle.setArrowType(Qt.ArrowType.RightArrow)
        transfer_header = QHBoxLayout(); transfer_header.addWidget(self.transfer_toggle)
        transfer_header.addStretch()
        self.notification_checkbox = QCheckBox(self.t['notifications'])
        self.notification_checkbox.setChecked(self.notifications_enabled)
        transfer_header.addWidget(self.notification_checkbox); layout.addLayout(transfer_header)
        self.transfer_panel = QWidget(); transfers_layout = QVBoxLayout(self.transfer_panel)
        transfers_layout.setContentsMargins(0, 0, 0, 0)
        self.transfer_table = AccountList([self.t['file_name'],'%','KiB/s','ETA'], stretch_column=0)
        self.transfer_table.setMaximumHeight(160); transfers_layout.addWidget(self.transfer_table)
        self.progress_bar = QProgressBar(); self.progress_bar.setRange(0,100); self.progress_bar.hide()
        transfers_layout.addWidget(self.progress_bar); layout.addWidget(self.transfer_panel)
        self.transfer_panel.hide(); self.transfer_toggle.toggled.connect(self.toggle_transfers)
        self.accounts.currentIndexChanged.connect(self.selection_changed)
        self.tray = QSystemTrayIcon(QIcon.fromTheme('drive-harddisk'), self)
        menu = QMenu(self)
        self.tray_show_action = QAction(self.t['title'], self); self.tray_show_action.triggered.connect(self.showNormal); menu.addAction(self.tray_show_action)
        self.tray_quit_action = QAction(self.t['quit'], self); self.tray_quit_action.triggered.connect(self.quit); menu.addAction(self.tray_quit_action)
        menu.addSeparator()
        self.notification_action = QAction(self.t['notifications'], self)
        self.notification_action.setCheckable(True)
        self.notification_action.setChecked(self.notifications_enabled)
        self.notification_action.toggled.connect(self.set_notifications)
        self.notification_checkbox.toggled.connect(self.set_notifications)
        menu.addAction(self.notification_action)
        self.tray.messageClicked.connect(self.showNormal)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda reason: self.showNormal())
        if self.tray.isSystemTrayAvailable(): self.tray.show()
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(250)
        self.poll_ticks = 0
        self.language_selector.currentIndexChanged.connect(self.change_language)
        self.refresh()

    def change_language(self):
        language = self.language_selector.currentData()
        if language == self.language: return
        try: self.language_settings.save(language)
        except OperationError:
            self.language_selector.blockSignals(True)
            self.language_selector.setCurrentIndex(self.language_selector.findData(self.language))
            self.language_selector.blockSignals(False)
            self.label.setText(self.t['language_error']); return
        label_key = next((key for key,value in self.t.items() if value == self.label.text()), None)
        loading_quota = self.quota_label.text() == self.t['quota_loading']
        self.language = language; self.t = TEXT[language]
        self.qt_translator = install_qt_language(QApplication.instance(), language, self.qt_translator)
        QApplication.instance().removeTranslator(self.standard_translator)
        self.standard_translator.language = language
        QApplication.instance().installTranslator(self.standard_translator)
        self.setWindowTitle(self.t['title']+' '+__version__)
        self.update_button.setText(self.t['update_checking' if self.update_future is not None else 'updates'])
        for key,control in self.buttons.items(): control.setText(self.t[key])
        for control,key in [(self.provider_label,'provider'),(self.mode_label,'mode'),(self.note_label,'note'),
                (self.language_label,'language'),(self.account_menu_button,'account_menu'),
                (self.transfer_toggle,'transfers'),(self.notification_checkbox,'notifications'),
                (self.notification_action,'notifications'),(self.tray_show_action,'title'),
                (self.tray_quit_action,'quit'),(self.quota_refresh,'quota_refresh')]:
            control.setText(self.t[key])
        self.access_mode.setItemText(0,self.t['mode_ro']); self.access_mode.setItemText(1,self.t['mode_rw'])
        self.accounts.setHorizontalHeaderLabels([self.t[key] for key in ('account','provider_column','path','access','status')])
        self.transfer_table.setHorizontalHeaderLabels([self.t['file_name'],'%','KiB/s','ETA'])
        for remote,status in self.account_states.items():
            self.accounts.update_account(remote, next((self.accounts.item(row,1).text() for row in range(self.accounts.rowCount())
                if self.accounts.item(row,0).text()==remote),''), status.path,
                '—' if status.state=='external' else self.t['mode_rw' if status.writable else 'mode_ro'],
                self.t[status.progress.state] if status.progress is not None else self.t['mounted_rw' if status.writable and status.state=='mounted' else status.state])
        remote = self.accounts.currentText()
        if label_key is not None: self.label.setText(self.t[label_key])
        elif remote in self.account_states: self.label.setText(self.status_text(self.account_states[remote]))
        if remote in self.account_states:
            status = self.account_states[remote]
            self.tray.setToolTip(self.t[status.progress.state] if status.progress is not None else self.t[status.state])
        self.progress_bar.setFormat(self.t['first_transfer']+' %p%')
        if loading_quota: self.quota_label.setText(self.t['quota_loading'])
        elif remote in self.quota_cache: self.show_quota(remote,self.quota_cache[remote][1])
        else: self.quota_label.setText(self.t['quota_unknown'])
        self.tools_button.setText(self.t['tools']);self.setup_banner.setText(self.t['setup_guide'])
        for key,action in self.tools_actions.items():action.setText(self.t[key])
        self.show_health()
        self.retranslate_bulk_dialogs()
        self.show_connection_result(update_controls=False)

    def set_notifications(self, enabled):
        previous = self.notifications_enabled
        try:
            # A tiny atomic local preference write also works while OAuth is busy.
            self.notification_settings.save(enabled)
            self.notifications_enabled = enabled
        except (OperationError, OSError):
            enabled = previous
            self.label.setText(self.t['notification_settings_error'])
        for control in (self.notification_action, self.notification_checkbox):
            control.blockSignals(True); control.setChecked(enabled); control.blockSignals(False)

    def notify_status(self, remote, status):
        notices = self.notice_tracker.observe(remote, status)
        if not self.notifications_enabled or not self.tray.isSystemTrayAvailable() or not self.tray.supportsMessages():
            return
        for notice in notices:
            key = {'uploads_done':'uploads_done','auth_required':'notice_auth','transfer_error':'notice_error'}[notice.event]
            account = ''.join(c for c in remote if c.isalnum() or c in '_- ')[:48]
            self.tray.showMessage('Drive Manager · '+account, self.t[key],
                QSystemTrayIcon.MessageIcon.Information if notice.event=='uploads_done' else QSystemTrayIcon.MessageIcon.Warning, 6000)

    def toggle_transfers(self, expanded):
        self.transfer_panel.setVisible(expanded)
        self.transfer_toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)

    def prepare_account_menu(self, position):
        if not self.accounts.isEnabled(): return False
        index = self.accounts.indexAt(position)
        if not index.isValid(): return False
        self.accounts.setCurrentCell(index.row(), 0)
        return True

    def open_account_menu(self, position):
        if self.prepare_account_menu(position):
            # Opening a menu never performs an operation; each action keeps its guards.
            self.account_menu.exec(self.accounts.viewport().mapToGlobal(position))

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
        self.buttons['cancel_oauth'].setVisible(self.oauth_cancel is not None)
        self.buttons['oauth_open'].setVisible(self.oauth_cancel is not None)

    def open_authorization(self):
        if self.browser_url and not QDesktopServices.openUrl(QUrl(self.browser_url)):
            self.label.setText(self.t['browser_error'])

    def tick(self):
        self.tick_health()
        self.tick_validation()
        self.tick_connection()
        self.tick_updates()
        self.tick_quota()
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
                    self.buttons['oauth_open'].setVisible(True)
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
            self.buttons['diagnostics'].setEnabled(True)
            self.buttons['add'].setEnabled(True)
            if not was_polling:
                self.buttons['cancel_oauth'].setEnabled(False)
                self.buttons['oauth_open'].setEnabled(False)
                self.buttons['cancel_oauth'].hide()
                self.buttons['oauth_open'].hide()
                self.browser_url = None
                self.oauth_cancel = None
            try: self.callback(future.result())
            except Exception as error:
                # Raw diagnostics may contain OAuth secrets. Never display or log them.
                self.last_error = True
                key = self.error_key
                if isinstance(error, OperationError) and str(error) in {'uploads_pending','uploads_unknown','files_open','needs_write_auth','reauth_identity','portable_busy'}:
                    key = str(error)
                if isinstance(error, AuthorizationError): key = error.key
                elif key in {'auth_error', 'credentials_error'} and isinstance(error, OperationError):
                    message = str(error)
                    if message in {'wallet_error', 'internxt_error', 'credentials_error', 'webdav_url_error', 'credential_identity', 'credential_custom', 'credential_renew_error', 'credential_confirm'}: key = message
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

    def check_updates(self):
        if self.update_future is not None: return
        from .updates import check
        self.update_button.setEnabled(False); self.update_button.setText(self.t['update_checking'])
        self.update_future = self.update_pool.submit(check, __version__)

    def tick_updates(self):
        if self.update_future is None or not self.update_future.done(): return
        from .updates import Update
        future, self.update_future = self.update_future, None
        try: result = future.result()
        except Exception: result = Update('update_error', __version__)
        self.update_button.setEnabled(True); self.update_button.setText(self.t['updates'])
        self.show_updates(result)

    def show_updates(self, result):
        dialog = QDialog(self); dialog.setWindowTitle(self.t['updates']); dialog.resize(580, 260)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(self.t['update_installed']+': '+result.installed))
        if result.latest: layout.addWidget(QLabel(self.t['update_latest']+': '+result.latest))
        message = self.t[result.state]
        if result.state=='update_available' and not result.rpm_url:
            message += '\n'+self.t['update_rpm_missing']
        status = QLabel(message); status.setWordWrap(True); layout.addWidget(status)
        note = QLabel(self.t['update_manual']); note.setWordWrap(True); layout.addWidget(note)
        actions = QHBoxLayout()
        def open_url(url):
            if not QDesktopServices.openUrl(QUrl(url)):
                status.setText(self.t['update_open_error'])
        if result.rpm_url:
            download = QPushButton(self.t['update_open_rpm']); download.clicked.connect(lambda:open_url(result.rpm_url))
            actions.addWidget(download)
        if result.release_url:
            release = QPushButton(self.t['update_open_release']); release.clicked.connect(lambda:open_url(result.release_url))
            actions.addWidget(release)
        close = QPushButton(self.t['close_report']); close.clicked.connect(dialog.accept); actions.addWidget(close)
        layout.addLayout(actions)
        # Keep transfer polling active while this read-only dialog is open.
        dialog.exec()

    def check_connection(self):
        remote = self.accounts.currentText()
        if not remote or self.connection_future is not None: return
        from .connectivity import check
        self.connection_cancel = Event()
        self.connection_remote = remote
        from .activity import Activity
        self.connection_activity = Activity(self,"check_connection",remote,self.connection_cancel)
        self.connection_future = self.connection_pool.submit(check, self.manager, remote, self.connection_cancel)
        self.show_connection_result()

    def show_connection_result(self, update_controls=True):
        remote = self.accounts.currentText()
        loading = self.connection_future is not None and self.connection_remote == remote
        result = self.connection_results.get(remote)
        if update_controls:
            self.buttons['check_connection'].setEnabled(bool(remote) and self.connection_future is None)
        if loading: self.connection_label.setText(self.t['connection_checking'])
        elif result is not None:
            self.connection_label.setText(self.t['connection_last'] + ' · ' + self.t[result.state] + (' · '+self.t['connection_elapsed'].format(seconds=result.seconds) if result.seconds else '') + (' · '+self.t['cloud_slow'] if slow(result) else ''))
        else: self.connection_label.clear()

    def tick_connection(self):
        if self.connection_future is None or not self.connection_future.done(): return
        from .connectivity import Result
        future, self.connection_future = self.connection_future, None
        try: result = future.result()
        except Exception: result = Result('connection_error')
        names = [self.accounts.item(row,0).text() for row in range(self.accounts.rowCount())]
        if self.connection_remote in names:
            self.connection_results[self.connection_remote] = result
        self.connection_activity.complete(result.state)
        self.show_connection_result()

    def refresh_quota(self):
        self.quota_cache.pop(self.accounts.currentText(), None)
        self.request_quota()

    def request_quota(self):
        import time
        remote = self.accounts.currentText()
        self.quota_bar.hide()
        if not remote:
            self.quota_label.setText(self.t['quota_unknown']); return
        cached = self.quota_cache.get(remote)
        if cached is not None and time.monotonic()-cached[0] < 300:
            self.show_quota(remote, cached[1]); return
        self.quota_label.setText(self.t['quota_loading'])
        if self.quota_future is not None: return
        from .quota import read_quota
        self.quota_remote = remote
        self.quota_future = self.quota_pool.submit(read_quota, self.manager, remote)
        self.quota_refresh.setEnabled(False)

    def tick_quota(self):
        if self.quota_future is None or not self.quota_future.done(): return
        import time
        from .quota import Quota
        future, self.quota_future = self.quota_future, None
        remote = self.quota_remote
        try: quota = future.result()
        except Exception: quota = Quota()
        names = [self.accounts.item(row,0).text() for row in range(self.accounts.rowCount())]
        self.quota_refresh.setEnabled(True)
        if remote in names:
            self.quota_cache[remote] = (time.monotonic(), quota)
            if quota.low and remote not in self.quota_warned:
                self.quota_warned.add(remote)
                if self.notifications_enabled and self.tray.isSystemTrayAvailable() and self.tray.supportsMessages():
                    self.tray.showMessage('Drive Manager · '+''.join(c for c in remote if c.isalnum() or c in '_- ')[:48], self.t['quota_low'], QSystemTrayIcon.MessageIcon.Warning, 6000)
            elif not quota.low and quota.free is not None:
                self.quota_warned.discard(remote)
        if remote == self.accounts.currentText(): self.show_quota(remote, quota)
        elif self.accounts.currentText(): self.request_quota()

    def show_quota(self, remote, quota):
        if remote != self.accounts.currentText(): return
        from .quota import size
        fields = [(self.t['quota_'+key],getattr(quota,key)) for key in ('used','free','total','other')]
        fields.append((self.t['quota_trash'],quota.trashed))
        values = [label+': '+size(value) for label,value in fields if value is not None]
        self.quota_label.setText((' · '.join(values) if values else self.t['quota_unknown'])
            + ('\n'+self.t['quota_low'] if quota.low else ''))
        percentage = quota.percentage
        self.quota_bar.setVisible(percentage is not None)
        if percentage is not None:
            self.quota_bar.setValue(percentage); self.quota_bar.setFormat(self.t['capacity']+' %p%')

    def diagnose(self):
        from .diagnostics import collect
        remote = self.accounts.currentText()
        self.submit(lambda: collect(self.manager, remote), self.show_diagnostics)

    def show_diagnostics(self, report):
        from .diagnostics import format_report
        text = format_report(report, self.language)
        dialog = QDialog(self); dialog.setWindowTitle(self.t['diagnostics'])
        dialog.resize(740, 500)
        layout = QVBoxLayout(dialog)
        output = QPlainTextEdit(text); output.setReadOnly(True); layout.addWidget(output)
        actions = QHBoxLayout()
        copy = QPushButton(self.t['copy_report'])
        copy.clicked.connect(lambda: QApplication.clipboard().setText(text))
        close = QPushButton(self.t['close_report']); close.clicked.connect(dialog.accept)
        actions.addWidget(copy); actions.addWidget(close); layout.addLayout(actions)
        self.timer.stop()
        try: dialog.exec()
        finally: self.timer.start(250)
        self.poll()

    def refresh(self):
        self.submit(self.manager.discover_accounts, self.set_accounts)

    def set_accounts(self, names, selected=None):
        self.account_states.clear()
        self.connection_results = {name:result for name,result in self.connection_results.items() if name in names}
        self.notice_tracker.retain(names)
        self.health_results={name:result for name,result in self.health_results.items() if name in names}
        from .portable import setup_done
        self.setup_banner.setVisible(not names and not setup_done(self.manager))
        self.quota_cache = {name:value for name,value in self.quota_cache.items() if name in names}
        self.quota_warned.intersection_update(names)
        current = selected or self.accounts.currentText()
        self.accounts.blockSignals(True); self.accounts.clear(); self.accounts.addItems(names)
        if current in names: self.accounts.setCurrentText(current)
        self.accounts.blockSignals(False)
        if names:
            self.request_health(force=True)
            self.show_connection_result()
            self.poll(); self.request_quota()
        else:
            self.account_menu_button.setEnabled(False)
            self.quota_label.setText(self.t['quota_unknown']); self.quota_bar.hide()
            self.connection_label.clear();self.health_label.clear()
            self.label.setText(self.t['empty'])
            self.transfer_table.clear(); self.progress_bar.hide()
            for key in ('mount', 'unmount', 'settings', 'open', 'delete', 'reauth', 'check_connection', 'renew_credentials'):
                self.buttons[key].setEnabled(False)

    def selection_changed(self):
        self.show_health()
        self.request_health(force=True)
        self.show_connection_result()
        self.last_error = False
        self.request_quota()
        remote = self.accounts.currentText()
        if remote in self.account_states:
            self.show_status(self.account_states[remote])
        else:
            self.account_menu_button.setEnabled(False)
            for key in ('mount', 'unmount', 'open', 'settings', 'reauth', 'renew_credentials', 'delete'):
                self.buttons[key].setEnabled(False)
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
            self.account_states[name] = status
            self.notify_status(name, status)
            self.accounts.update_account(name,labels.get(provider,provider),status.path,
                '—' if status.state=='external' else self.t['mode_rw' if status.writable else 'mode_ro'],
                self.t[status.progress.state] if status.progress is not None else self.t['mounted_rw' if status.writable and status.state=='mounted' else status.state])
            if name==self.accounts.currentText():self.show_status(status)

    def show_status(self, status):
        self.account_states[self.accounts.currentText()] = status
        self.account_menu_button.setEnabled(bool(self.accounts.currentText()))
        self.accounts.update_account(self.accounts.currentText(), self.accounts.item(self.accounts.currentRow(),1).text(),
            status.path, '—' if status.state=='external' else self.t['mode_rw' if status.writable else 'mode_ro'], self.t[status.progress.state] if status.progress is not None else self.t['mounted_rw' if status.writable and status.state=='mounted' else status.state])
        self.label.setText(self.status_text(status))
        detail = status.progress
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
        self.show_connection_result()
        self.buttons['mount'].setEnabled(status.state in {'unmounted', 'failed'})
        self.buttons['reauth'].setEnabled(self.manager.is_app_account(self.accounts.currentText())
            and not self.manager.accounts.encrypted(self.manager.accounts.path(self.accounts.currentText()))
            and status.state in {'unmounted', 'failed'})
        self.buttons['renew_credentials'].setEnabled(self.manager.is_app_account(self.accounts.currentText())
            and self.manager.accounts.encrypted(self.manager.accounts.path(self.accounts.currentText()))
            and status.state in {'unmounted','failed'})
        self.buttons['settings'].setEnabled(status.state in {'unmounted', 'failed'})
        self.buttons['unmount'].setEnabled(status.managed)
        self.buttons['delete'].setEnabled(status.managed or status.state in {'unmounted', 'failed'})
        self.buttons['open'].setEnabled(status.state in {'mounted', 'external'})

    def status_text(self, status):
        origin = 'app_origin' if self.manager.is_app_account(self.accounts.currentText()) else 'external_origin'
        title = self.t['mounted_rw'] if status.writable and status.state=='mounted' else self.t[status.state]
        sync = ('\n'+self.t['sync_unknown' if status.pending<0 else 'sync_pending' if status.pending else 'sync_clean']) if status.writable and status.managed else ''
        detail=status.progress
        if status.managed and detail is not None:
            sync='\n'+self.t[detail.state]+f" · {self.t['queued_label']}: {detail.queued} · {self.t['uploading_label']}: {detail.uploading}"
        elif status.managed: sync='\n'+self.t['unmonitored']
        return title + ' · ' + self.t[origin] + '\n' + status.path + sync

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
        upload=QSpinBox();download=QSpinBox()
        for control,value in [(upload,prefs.upload_kib),(download,prefs.download_kib)]:
            control.setRange(0,1048576);control.setSpecialValueText(self.t['unlimited']);control.setValue(value);control.setSuffix(' KiB/s')
        form.addRow(self.t['upload_limit'],upload);form.addRow(self.t['download_limit'],download)
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
            updated = Preferences(path.text().strip(), size.value(), age.value(), automount.isChecked(), writable.isChecked(), upload.value(), download.value())
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
        import time
        event = Event(); answer = {}; self.twofa_requests.put((event, answer))
        deadline = time.monotonic() + 180
        while not event.wait(.2):
            if cancel.is_set() or time.monotonic() > deadline: return ''
        return answer.get('code', '')

    def internxt_login(self, renewal=None):
        dialog = QDialog(self); dialog.setWindowTitle('Internxt')
        form = QFormLayout(dialog)
        name = QLineEdit(renewal or 'internxt'); name.setReadOnly(renewal is not None); email = QLineEdit(); password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(self.t['name'], name); form.addRow(self.t['email'], email); form.addRow(self.t['password'], password)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        self.timer.stop()
        try: accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally: self.timer.start(250)
        if not accepted: password.clear(); return
        remote = name.text().strip(); user = email.text().strip(); secret = password.text(); password.clear()
        cancel = Event(); self.oauth_cancel = cancel
        self.label.setText(self.t['internxt_wait'])
        if renewal is not None:
            self.submit(lambda:self.manager.renew_credentials(remote,user,secret,cancel,confirmed=True,ask_code=self.ask_internxt_code),
                        lambda names:self.credentials_renewed(names,remote),'credentials_error')
        else:
            self.submit(lambda: self.manager.begin_internxt(remote, user, secret, cancel, self.ask_internxt_code),
                        self.connection_details, 'auth_error')

    def credentials_login(self, provider, renewal=None):
        dialog = QDialog(self)
        dialog.setWindowTitle('Nextcloud' if provider == 'webdav' else 'Proton Drive (beta)')
        dialog.setMinimumWidth(520)
        form = QFormLayout(dialog)
        name = QLineEdit(renewal or ('nextcloud' if provider == 'webdav' else 'proton'));name.setReadOnly(renewal is not None)
        user = QLineEdit(); password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(self.t['name'], name)
        url = QLineEdit(); code = QLineEdit(); mailbox = QLineEdit()
        code.setEchoMode(QLineEdit.EchoMode.Password); mailbox.setEchoMode(QLineEdit.EchoMode.Password)
        if provider == 'webdav':
            url.setPlaceholderText('https://cloud.example/remote.php/dav/files/username/')
            form.addRow(self.t['webdav_url'], url)
        form.addRow(self.t['username'], user)
        form.addRow(self.t['app_password'] if provider == 'webdav' else self.t['password'], password)
        if provider == 'protondrive':
            form.addRow(self.t['optional_2fa'], code); form.addRow(self.t['mailbox_password'], mailbox)
        note = QLabel(self.t['nextcloud_note'] if provider == 'webdav' else self.t['proton_note'])
        note.setWordWrap(True); form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        self.timer.stop()
        try: accepted = dialog.exec() == QDialog.DialogCode.Accepted
        finally: self.timer.start(250)
        if not accepted:
            password.clear(); code.clear(); mailbox.clear(); return
        remote = name.text().strip(); username = user.text().strip(); secret = password.text()
        options = {'url':url.text(), 'code':code.text(), 'mailbox_password':mailbox.text()}
        password.clear(); code.clear(); mailbox.clear()
        cancel = Event(); self.oauth_cancel = cancel
        self.label.setText(self.t['credentials_wait'])
        if renewal is not None:
            self.submit(lambda:self.manager.renew_credentials(remote,username,secret,cancel,confirmed=True,**options),
                        lambda names:self.credentials_renewed(names,remote),'credentials_error')
        else:
            self.submit(lambda: self.manager.begin_credentials(remote, provider, username, secret, cancel, **options),
                        self.connection_details, 'credentials_error')

    def ask_onedrive_drive(self, choices, cancel):
        import time
        event = Event(); answer = {}; self.drive_requests.put((choices, event, answer, cancel))
        deadline = time.monotonic() + 180
        while not event.wait(.2):
            if cancel.is_set() or time.monotonic() > deadline: return None
        return answer.get('value')

    def credentials_renewed(self, names, remote):
        self.connection_results.pop(remote,None)
        self.set_accounts(names,remote)

    def renew_account_credentials(self):
        remote=self.accounts.currentText()
        if not remote:return
        if QMessageBox.question(self,self.t['renew_credentials'],self.t['credential_confirm'],
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        try:provider=self.manager.encrypted_provider(remote)
        except OperationError:
            self.label.setText(self.t['credential_renew_error']);return
        if self.connection_future is not None and self.connection_remote==remote:self.connection_cancel.set()
        if provider=='internxt':self.internxt_login(renewal=remote)
        else:self.credentials_login(provider,renewal=remote)

    def reauthorize_account(self):
        remote = self.accounts.currentText()
        if not remote: return
        if QMessageBox.question(self, self.t['reauth'], self.t['reauth_confirm'],
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
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
        if self.provider.currentData() in {"webdav", "protondrive"}:
            self.credentials_login(self.provider.currentData()); return
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
        prefix = next((p for p in ('onedrive_', 'dropbox_') if registration[0].startswith(p)), 'google_')
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
        if hasattr(self,"browse_cancel"):self.browse_cancel.set()
        self.validation_cancel.set()
        self.validation_pool.shutdown(wait=False,cancel_futures=True)
        self.health_pool.shutdown(wait=False,cancel_futures=True)
        self.connection_cancel.set()
        self.connection_pool.shutdown(wait=False, cancel_futures=True)
        self.update_pool.shutdown(wait=False, cancel_futures=True)
        self.quota_pool.shutdown(wait=False, cancel_futures=True)
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
