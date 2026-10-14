"""Modeless progress with cooperative cancellation and elapsed time."""
import time
from queue import Queue, Empty
from PySide6.QtCore import QTimer,Qt
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPushButton,QProgressBar

class Activity(QDialog):
    def __init__(self,parent,title,remote,cancel,stage='connection_checking'):
        for previous in parent.findChildren(Activity):
            if previous.title_key==title and previous.finished:previous.close()
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.owner=parent;self.cancel=cancel;self.stage=stage;self.remote=remote
        self.started=time.monotonic();self.finished=False;self.result_key=None;self.updates=Queue()
        self.setWindowTitle(parent.t[title]);self.title_key=title;self.resize(540,170)
        layout=QVBoxLayout(self);self.label=QLabel();self.label.setWordWrap(True);layout.addWidget(self.label)
        self.bar=QProgressBar();self.bar.setRange(0,0);layout.addWidget(self.bar)
        self.button=QPushButton();self.button.clicked.connect(self.reject);layout.addWidget(self.button)
        self.clock=QTimer(self);self.clock.timeout.connect(self.refresh);self.clock.start(250)
        self.refresh();self.show()

    def report(self,stage,remote=''):
        # Called by workers; Qt widgets are updated only by the GUI timer.
        self.updates.put((stage,remote))

    def refresh(self):
        try:
            while True:self.stage,self.remote=self.updates.get_nowait()
        except Empty:pass
        t=self.owner.t;self.setWindowTitle(t[self.title_key])
        key=self.result_key if self.finished else ('operation_cancelling' if self.cancel.is_set() else self.stage)
        self.label.setText(t[key]+(' · '+self.remote if self.remote else '')+'\n'+t['operation_elapsed'].format(seconds=int(time.monotonic()-self.started)))
        self.button.setText(t['operation_close'] if self.finished else t['operation_cancel'])
        self.button.setEnabled(self.finished or not self.cancel.is_set())

    def complete(self,key):
        self.finished=True;self.result_key=key;self.bar.setRange(0,1);self.bar.setValue(1)
        self.refresh();self.clock.stop()

    def reject(self):
        if self.finished:return super().reject()
        self.cancel.set();self.refresh()

    def closeEvent(self,event):
        if self.finished:event.accept()
        else:self.reject();event.ignore()
