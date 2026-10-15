"""Qt controllers for setup, portability, live acceptance and cache health."""
import time
from threading import Event
from queue import Empty
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QComboBox,
    QPlainTextEdit,QDialogButtonBox,QFileDialog,QMessageBox,QTableWidget,QTableWidgetItem,QAbstractItemView,QHeaderView,QSystemTrayIcon)
from .providers import PROVIDERS
from .performance import CacheHealth,inspect,slow
from .quota import size
from .process import OperationError

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
        result=self.health_results.get(self.accounts.currentText())
        if result is None:self.health_label.clear();return
        text=self.t['cache_health'].format(free=size(result.free),pending='—' if result.pending is None else result.pending)
        if result.low:text+=' · '+self.t['cache_low']
        if result.pending is None:text+=' · '+self.t['cache_unknown']
        self.health_label.setText(text)

    def setup_guide(self):
        if getattr(self,'setup_dialog',None) is not None and self.setup_dialog.isVisible():
            self.setup_dialog.show();return
        from .diagnostics import collect,format_report
        from .portable import finish_setup
        dialog=QDialog(self);dialog.setWindowTitle(self.t['setup_guide']);dialog.resize(650,420)
        layout=QVBoxLayout(dialog)
        note=QLabel(self.t['setup_steps']);self.setup_note=note;note.setWordWrap(True);layout.addWidget(note)
        report=QPlainTextEdit();report.setReadOnly(True);layout.addWidget(report)
        actions=QHBoxLayout();check=QPushButton(self.t['diagnostics']);actions.addWidget(check)
        provider=QComboBox()
        for p in PROVIDERS:provider.addItem(p.label,p.key)
        layout.addWidget(provider)
        def dependencies():
            check.setEnabled(False)
            def shown(result):report.setPlainText(format_report(result,self.language));check.setEnabled(True)
            self.submit(lambda:collect(self.manager),shown)
        check.clicked.connect(dependencies)
        create=QPushButton(self.t['add']);actions.addWidget(create)
        def begin():
            self.provider.setCurrentIndex(self.provider.findData(provider.currentData()))
            self.access_mode.setCurrentIndex(0);dialog.accept();self.add_account()
        create.clicked.connect(begin)
        finish=QPushButton(self.t['setup_finish']);actions.addWidget(finish)
        def complete():
            try:finish_setup(self.manager)
            except Exception:report.setPlainText(self.t['portable_error']);return
            self.setup_banner.hide();dialog.accept()
        finish.clicked.connect(complete);layout.addLayout(actions);dialog.show()
        self.setup_actions={"diagnostics":check,"add":create,"setup_finish":finish}
        self.setup_dialog=dialog

    def export_settings(self):
        from .portable import export
        path,_=QFileDialog.getSaveFileName(self,self.t['export_settings'],str(self.manager.home/'drive-manager-settings.json'),'JSON (*.json)')
        if path:self.submit(lambda:export(self.manager,path),lambda count:self.label.setText(self.t['export_done'].format(count=count)),'portable_error')

    def import_settings(self):
        from .portable import plan
        path,_=QFileDialog.getOpenFileName(self,self.t['import_settings'],str(self.manager.home),'JSON (*.json)')
        if path:self.submit(lambda:plan(self.manager,path),lambda rows:self.preview_import(path,rows),'portable_error')

    def preview_import(self,path,rows):
        from .portable import apply
        from .import_ui import ImportReview
        dialog=ImportReview(self,rows)
        self.timer.stop()
        try:accepted=dialog.exec()==QDialog.DialogCode.Accepted
        finally:self.timer.start(250)
        if accepted:
            selected=dialog.selected()
            self.submit(lambda:apply(self.manager,path,confirmed=True,reviewed=rows,selected=selected),self.set_accounts,'portable_error')

    def validation_panel(self):
        if self.validation_dialog is not None:self.validation_dialog.show();return
        dialog=QDialog(self);dialog.setWindowTitle(self.t['validate_all']);dialog.resize(850,500)
        layout=QVBoxLayout(dialog);note=QLabel(self.t['validation_note']);self.validation_note=note;note.setWordWrap(True);layout.addWidget(note)
        self.validation_table=QTableWidget(0,4);self.validation_table.setHorizontalHeaderLabels([self.t['provider_column'],self.t['account'],self.t['validation_read'],self.t['validation_time']])
        self.validation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);layout.addWidget(self.validation_table)
        self.validation_message=QLabel();self.validation_message.setWordWrap(True);layout.addWidget(self.validation_message)
        self.validation_selector=QComboBox();self.validation_selector.addItems([self.accounts.item(row,0).text() for row in range(self.accounts.rowCount())]);layout.addWidget(self.validation_selector)
        self.validation_test_selector=QComboBox();layout.addWidget(self.validation_test_selector)
        self.validation_selector.currentTextChanged.connect(self.refresh_test_files)
        self.refresh_test_files()
        controls=QHBoxLayout();self.validation_controls=[];self.validation_buttons={}
        for key,kind in [('validate_all','read'),('validation_write','write'),('validation_reconnect','reconnect'),('validation_cleanup','cleanup'),('validation_discover','discover')]:
            button=QPushButton(self.t[key]);button.clicked.connect(lambda checked=False,kind=kind:self.start_validation(kind));controls.addWidget(button);self.validation_controls.append(button);self.validation_buttons[key]=button
        cancel=QPushButton(self.t['operation_cancel']);self.validation_buttons['operation_cancel']=cancel;cancel.clicked.connect(self.cancel_validation);controls.addWidget(cancel);layout.addLayout(controls)
        guide=QPushButton(self.t['validation_guide']);self.validation_buttons['validation_guide']=guide;guide.clicked.connect(self.acceptance_guide);layout.addWidget(guide)
        self.validation_rows=getattr(self,'validation_rows',{})
        self.validation_dialog=dialog;self.render_validation()
        def closed():self.validation_cancel.set();self.validation_dialog=None
        dialog.finished.connect(closed);dialog.show()

    def render_validation(self):
        if self.validation_dialog is None:return
        names={self.accounts.item(row,0).text() for row in range(self.accounts.rowCount())}
        records=[]
        for provider in PROVIDERS:
            rows=[(name,result) for name,(key,result) in self.validation_rows.items() if key==provider.key and name in names]
            if rows:
                for name,result in rows:records.append([provider.label,name,self.t[result.state]+(' · '+self.t['cloud_slow'] if slow(result) else ''),f'{result.seconds:.1f} s'])
            else:records.append([provider.label,'—',self.t['validation_unchecked'],'—'])
        self.validation_table.setRowCount(len(records))
        for row,values in enumerate(records):
            for col,value in enumerate(values):self.validation_table.setItem(row,col,QTableWidgetItem(value))
        self.validation_table.resizeColumnsToContents()
        self.validation_table.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        self.validation_table.resizeRowsToContents()
        for button in self.validation_controls:button.setEnabled(self.validation_future is None)
        self.validation_selector.setEnabled(self.validation_future is None)
        self.validation_test_selector.setEnabled(self.validation_future is None)
        self.validation_buttons['operation_cancel'].setEnabled(self.validation_future is not None and not self.validation_cancel.is_set())

    def cancel_validation(self):
        self.validation_cancel.set()
        if self.validation_future is not None:self.validation_activity.refresh()
        self.render_validation()

    def start_validation(self,kind):
        if self.validation_future is not None:return
        from .validation import read_all,write_test,reconnect,cleanup_test,discover_test_files
        remote=self.validation_selector.currentText()
        if kind=='discover' and not remote:return
        if kind not in {'read','discover'}:
            if not remote:return
            message=self.t['validation_cleanup_confirm' if kind=='cleanup' else 'validation_write_confirm' if kind=='write' else 'validation_reconnect_confirm']+'\n'+remote+('\n'+self.validation_test_selector.currentText() if kind=='cleanup' else '')
            if QMessageBox.question(self,self.t['validate_all'],message,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        filename=self.validation_test_selector.currentText()
        if kind=='cleanup' and not filename:
            self.validation_message.setText(self.t['validation_cleanup_missing']);return
        self.validation_cancel=Event();self.validation_kind=kind;self.validation_remote=remote
        from .activity import Activity
        stage={'read':'connection_checking','write':'validation_write','reconnect':'validation_reconnect','cleanup':'validation_cleanup','discover':'validation_discover'}[kind]
        self.validation_activity=Activity(self,'validate_all',remote if kind!='read' else '',self.validation_cancel,stage)
        if kind=='read':self.validation_future=self.validation_pool.submit(read_all,self.manager,self.validation_cancel,self.validation_queue.put,self.validation_activity.report)
        elif kind=='write':self.validation_future=self.validation_pool.submit(write_test,self.manager,remote,self.validation_cancel,True)
        elif kind=='cleanup':self.validation_future=self.validation_pool.submit(cleanup_test,self.manager,remote,filename,True,self.validation_cancel)
        elif kind=='discover':self.validation_future=self.validation_pool.submit(discover_test_files,self.manager,remote,self.validation_cancel)
        else:self.validation_future=self.validation_pool.submit(reconnect,self.manager,remote,True,self.validation_cancel)
        self.validation_message.setText(self.t['connection_checking']);self.render_validation()

    def tick_validation(self):
        try:
            while True:
                name,provider,result=self.validation_queue.get_nowait()
                self.validation_rows[name]=(provider,result);self.connection_results[name]=result
                self.render_validation();self.show_connection_result()
        except Empty:pass
        if self.validation_future is None or not self.validation_future.done():return
        future,self.validation_future=self.validation_future,None
        key="validation_error"
        try:
            result=future.result()
            if self.validation_kind=='read':key='connection_cancelled' if self.validation_cancel.is_set() else 'validation_finished'
            elif self.validation_kind in {'write','cleanup','discover'}:key=result.state
            else:key='validation_reconnect_ok' if result.state=='mounted' and result.managed else ('connection_cancelled' if self.validation_cancel.is_set() else 'validation_error')
            if self.validation_dialog is not None:
                if self.validation_kind=='read':message=self.t['validation_finished']
                elif self.validation_kind in {'write','cleanup','discover'}:message=self.t[result.state]+('\n'+self.t['validation_file']+': '+result.file if result.file else '')
                else:message=self.t[key]
                self.validation_message.setText(message)
        except Exception:
            key='connection_cancelled' if self.validation_cancel.is_set() else 'validation_error'
            if self.validation_dialog is not None:self.validation_message.setText(self.t[key])
        self.validation_activity.complete(key)
        if self.validation_dialog is not None and self.validation_kind=='read' and self.validation_cancel.is_set():self.validation_message.setText(self.t[key])
        if self.validation_dialog is not None:self.refresh_test_files()
        self.render_validation()

    def acceptance_guide(self):
        dialog=QDialog(self);dialog.setWindowTitle(self.t['validation_guide']);dialog.resize(700,400)
        layout=QVBoxLayout(dialog);text=QPlainTextEdit();text.setReadOnly(True);text.setPlainText(self.t['acceptance_steps']);layout.addWidget(text)
        close=QPushButton(self.t['updates_close']);close.clicked.connect(dialog.accept);layout.addWidget(close);dialog.show()
        self.acceptance_dialog=dialog

    def retranslate_bulk_dialogs(self):
        if getattr(self,'setup_dialog',None) is not None:
            self.setup_dialog.setWindowTitle(self.t['setup_guide']);self.setup_note.setText(self.t['setup_steps'])
            for key,button in self.setup_actions.items():button.setText(self.t[key])
        if self.validation_dialog is not None:
            self.validation_dialog.setWindowTitle(self.t['validate_all']);self.validation_note.setText(self.t['validation_note'])
            self.validation_table.setHorizontalHeaderLabels([self.t['provider_column'],self.t['account'],self.t['validation_read'],self.t['validation_time']])
            for key,button in self.validation_buttons.items():button.setText(self.t[key])
            self.render_validation()

    def browse_measure(self):
        from .performance import browse
        remote=self.accounts.currentText()
        if not remote or self.browse_future is not None:return
        self.browse_remote=remote;self.tools_actions['browse_measure'].setEnabled(False)
        from .activity import Activity
        self.browse_cancel=Event()
        self.browse_activity=Activity(self,'browse_measure',remote,self.browse_cancel,'operation_status')
        self.browse_future=self.health_pool.submit(browse,self.manager,remote,self.browse_cancel,self.browse_activity.report)

    def tick_browse(self):
        if self.browse_future is None or not self.browse_future.done():return
        future,self.browse_future=self.browse_future,None
        self.tools_actions['browse_measure'].setEnabled(True)
        try:result=future.result()
        except Exception:result=None
        self.browse_activity.complete('connection_cancelled' if self.browse_cancel.is_set() else 'operation_finished')
        if self.browse_cancel.is_set() or self.browse_remote!=self.accounts.currentText():return
        value=lambda seconds:'—' if seconds is None else f'{seconds:.1f} s'
        text=self.t['browse_result'].format(listing=value(result.listing) if result else '—',space=value(result.space) if result else '—')
        from .performance import browsing_advice
        advice=self.t[browsing_advice(result)]
        QMessageBox.information(self,self.t['browse_measure'],text+'\n\n'+advice+'\n\n'+self.t['browse_scope'])

    def recover_selected_mount(self):
        remote=self.accounts.currentText()
        if not remote:return
        if QMessageBox.question(self,self.t['recover_mount'],self.t['recover_mount_confirm']+'\n'+remote,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.submit(lambda:self.manager.recover_mount(remote,True),lambda status:self.show_status(status,remote),'recovery_error')

    def repair_selected_preferences(self):
        remote=self.accounts.currentText()
        if not remote:return
        if QMessageBox.question(self,self.t['repair_preferences'],self.t['repair_preferences_confirm']+'\n'+remote,QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        self.submit(lambda:self.manager.repair_preferences(remote,True),self.set_accounts,'repair_error')

    def refresh_test_files(self):
        from .test_files import read
        remote=self.validation_selector.currentText()
        self.validation_test_selector.clear()
        if not remote:return
        try:self.validation_test_selector.addItems(read(self.manager,remote))
        except OperationError:self.validation_message.setText(self.t['validation_error'])
