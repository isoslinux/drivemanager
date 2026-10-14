"""Progress must remain visible until cooperative cancellation completes."""
from threading import Event
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import QCoreApplication,QEvent
from shiboken6 import isValid
from drive_manager.activity import Activity
from drive_manager.i18n import TEXT
from drive_manager.performance import browse
from drive_manager.validation import read_all

class ActivityTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.owner=QWidget();self.owner.t=TEXT['es'];self.cancel=Event()
        self.dialog=Activity(self.owner,'check_connection','Demo',self.cancel)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if isValid(self.dialog):
            self.dialog.complete('operation_finished');self.dialog.reject()
        self.owner.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)

    def test_cancel_remains_visible_until_worker_finishes(self):
        self.dialog.reject();self.assertTrue(self.cancel.is_set())
        self.assertTrue(self.dialog.isVisible());self.assertFalse(self.dialog.button.isEnabled())
        self.assertIn('Cancelando',self.dialog.label.text())
        self.dialog.complete('connection_cancelled');self.assertTrue(self.dialog.button.isEnabled())
        self.dialog.reject();self.assertFalse(self.dialog.isVisible())

    def test_window_close_requests_cancel(self):
        self.dialog.close();self.assertTrue(self.cancel.is_set());self.assertTrue(self.dialog.isVisible())

    def test_elapsed_and_worker_stage_are_translated(self):
        self.dialog.started-=7;self.dialog.report('operation_space','Other')
        for lang in ['en','es','fr','de']:
            self.owner.t=TEXT[lang];self.dialog.refresh()
            self.assertIn(TEXT[lang]['operation_space'],self.dialog.label.text())
            self.assertIn('Other',self.dialog.label.text());self.assertIn('7',self.dialog.label.text())

    def test_precancelled_browse_does_not_query_mount(self):
        manager=Mock();self.cancel.set();browse(manager,'a',self.cancel)
        manager.status.assert_not_called()

    def test_browse_cancel_kills_only_its_probe_and_skips_space(self):
        manager=Mock();manager.status.return_value=SimpleNamespace(state='mounted',path='/unused')
        process=Mock();process.pid=98765;process.poll.return_value=None
        def launched(*args,**kwargs):self.cancel.set();return process
        with patch('drive_manager.performance.subprocess.Popen',side_effect=launched) as spawn,patch('drive_manager.performance.os.killpg') as kill:
            browse(manager,'a',self.cancel)
        self.assertEqual(spawn.call_count,1);kill.assert_called_once();process.wait.assert_called_once()

    def test_batch_reports_current_account_before_read(self):
        manager=Mock();manager.discover_accounts.return_value=['a'];manager.provider_of.return_value='drive'
        events=[]
        with patch('drive_manager.validation.check',side_effect=lambda *args:events.append('read')):
            read_all(manager,self.cancel,on_start=lambda stage,name:events.append((stage,name)))
        self.assertEqual(events,[('connection_checking','a'),'read'])
