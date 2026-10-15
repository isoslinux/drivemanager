from pathlib import Path
from dataclasses import replace
from concurrent.futures import Future
from queue import Queue
from threading import Event
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
from PySide6.QtWidgets import QApplication,QWidget
from PySide6.QtCore import QCoreApplication,QEvent
from shiboken6 import isValid
import test_bulk as fixtures
from drive_manager import portable
from drive_manager.settings import Preferences
from drive_manager.service import Status
from drive_manager.process import OperationError
from drive_manager.activity import Activity
from drive_manager.bulk_ui import BulkActions
from drive_manager.messages import TEXT

class PathRegressionTests(TestCase):
    setUp=fixtures.BulkTests.setUp
    exported=fixtures.BulkTests.exported
    def test_import_cannot_take_unselected_implicit_folder(self):
        self.manager.settings.save('b',Preferences());target=self.manager.identity('b')[1];target.mkdir(parents=True)
        self.exported();rows=portable.plan(self.manager,self.file);before=self.manager.settings.path('a').read_bytes()
        with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True,rows,[(rows[0][0],rows[0][1],replace(rows[0][2],mount_path=str(target)))])
        self.assertEqual(self.manager.settings.path('a').read_bytes(),before)
    def test_account_without_preferences_still_reserves_default(self):
        self.manager.settings.path('b').unlink();target=self.manager.identity('b')[1]
        with self.assertRaises(OperationError):self.manager.validate_mount_targets([('a',Preferences(str(target)))])
    def test_selected_siblings_reject_shared_or_nested_target(self):
        for second in [self.home/'Shared',self.home/'Shared'/'Nested']:
            with self.assertRaises(OperationError):self.manager.validate_mount_targets([('a',Preferences(str(self.home/'Shared'))),('b',Preferences(str(second)))])
    def test_settings_direct_save_checks_default_in_both_directions(self):
        self.manager.settings.save('b',Preferences());target=self.manager.identity('b')[1]
        with self.assertRaises(OperationError):self.manager.settings.save('a',Preferences(str(target/'Nested')))
        self.manager.settings.path('b').unlink()
        self.manager.settings.save('a',Preferences(str(target)))
        with self.assertRaises(OperationError):self.manager.settings.save('b',Preferences())

class UiRegressionTests(TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_completed_activity_is_replaced_and_freed(self):
        owner=QWidget();owner.t=TEXT['es']
        first=Activity(owner,'check_connection','a',Event());first.complete('connection_ok')
        second=Activity(owner,'check_connection','b',Event())
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.assertFalse(isValid(first));self.assertTrue(second.isVisible())
        second.complete('connection_ok');second.close();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.assertFalse(isValid(second));owner.close()
    def test_reconnect_cancel_panel_and_activity_agree(self):
        future=Future();future.set_result(Status('starting','',True));cancel=Event();cancel.set()
        owner=SimpleNamespace(validation_queue=Queue(),validation_future=future,validation_cancel=cancel,validation_kind='reconnect',validation_dialog=object(),validation_message=Mock(),validation_activity=Mock(),render_validation=Mock(),refresh_test_files=Mock(),t=TEXT['es'])
        BulkActions.tick_validation(owner)
        owner.validation_activity.complete.assert_called_once_with('connection_cancelled')
        owner.validation_message.setText.assert_called_once_with(TEXT['es']['connection_cancelled'])
    def test_reconnect_cancel_exception_panel_and_activity_agree(self):
        future=Future();future.set_exception(OperationError('connection_cancelled'));cancel=Event();cancel.set()
        owner=SimpleNamespace(validation_queue=Queue(),validation_future=future,validation_cancel=cancel,validation_kind='reconnect',validation_dialog=object(),validation_message=Mock(),validation_activity=Mock(),render_validation=Mock(),refresh_test_files=Mock(),t=TEXT['es'])
        BulkActions.tick_validation(owner)
        owner.validation_activity.complete.assert_called_once_with('connection_cancelled')
        owner.validation_message.setText.assert_called_once_with(TEXT['es']['connection_cancelled'])

class CorruptPreferenceTests(TestCase):
    setUp=fixtures.BulkTests.setUp
    def test_healthy_mount_ignores_damaged_unmounted_other_and_preserves_bytes(self):
        bad=self.manager.settings.path('b');bad.write_text('{corrupt');before=bad.read_bytes()
        with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'):self.manager.mount('a')
        self.assertEqual(bad.read_bytes(),before)
        self.assertTrue(any(c[0]=='systemd-run' for c in self.manager.runner.calls))
    def test_corrupt_accounts_default_remains_reserved(self):
        self.manager.settings.path('b').write_text('{corrupt');target=self.home/'DriveManager'/self.manager.settings.path('b').stem
        with self.assertRaises(OperationError):self.manager.validate_mount_targets([('a',Preferences(str(target)))],True)
    def test_actual_fuse_mount_of_corrupt_account_still_protected(self):
        from drive_manager.mounts import Mount
        self.manager.settings.path('b').write_text('{corrupt')
        with patch.object(self.manager,'mounts',return_value=[Mount(str(self.home/'Drives/a'),'b:','fuse.rclone')]):
            with self.assertRaises(OperationError):self.manager.validate_mount_targets([('a',self.manager.settings.load('a'))],True)
    def test_preference_changes_name_corrupt_account(self):
        self.manager.settings.path('b').write_text('{corrupt')
        with self.assertRaisesRegex(OperationError,'account: b'):self.manager.validate_mount_targets([('a',self.manager.settings.load('a'))])
