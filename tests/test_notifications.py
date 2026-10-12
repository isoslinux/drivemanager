from pathlib import Path
import tempfile
import unittest
from drive_manager.notifications import Tracker,NotificationSettings
from drive_manager.service import Status
from drive_manager.transfers import Progress

class NotificationTests(unittest.TestCase):
    def status(self,state='idle',pending=0,queued=0,uploading=0,errors=0,writable=True,managed=True):
        return Status('mounted','/private',managed,writable,pending,Progress(state,queued,uploading,errors))
    def test_completion_requires_observed_upload_and_known_empty_queue(self):
        tracker=Tracker()
        self.assertEqual(tracker.observe('a',self.status()),[])
        tracker.observe('a',self.status('queued',1,1))
        self.assertEqual(tracker.observe('a',self.status('monitor_unknown',-1)),[])
        self.assertEqual(tracker.observe('a',self.status(pending=-1)),[])
        self.assertEqual([n.event for n in tracker.observe('a',self.status())],['uploads_done'])
        self.assertEqual(tracker.observe('a',self.status()),[])
    def test_readonly_downloads_and_external_mounts_never_signal_uploaded(self):
        for kwargs in [{'writable':False},{'managed':False}]:
            tracker=Tracker();tracker.observe('a',self.status('transferring',1,**kwargs))
            self.assertEqual(tracker.observe('a',self.status(**kwargs)),[])
    def test_warning_deduplication_survives_unknown_states_and_rearms_on_recovery(self):
        tracker=Tracker();error=self.status('auth_required',1,errors=1)
        self.assertEqual(len(tracker.observe('a',error)),1)
        tracker.observe('a',self.status('monitor_unknown',-1))
        self.assertEqual(tracker.observe('a',error),[])
        tracker.observe('a',self.status())
        self.assertEqual(len(tracker.observe('a',error)),1)
    def test_accounts_are_independent_and_disconnect_is_not_completion(self):
        tracker=Tracker();tracker.observe('a',self.status('uploading',1,uploading=1))
        self.assertEqual(tracker.observe('b',self.status()),[])
        self.assertEqual(tracker.observe('a',Status('unmounted','/private')),[])
        self.assertEqual(tracker.observe('a',self.status()),[])
        tracker.observe('a',self.status('transfer_error',1,errors=1))
        tracker.retain(['b']);self.assertNotIn('a',tracker.warned)
    def test_preferences_private_atomic_and_corrupt_fail_muted(self):
        with tempfile.TemporaryDirectory() as home:
            prefs=NotificationSettings(home);self.assertTrue(prefs.load())
            prefs.save(False);self.assertFalse(prefs.load())
            self.assertEqual(prefs.path.stat().st_mode & 0o777,0o600)
            self.assertEqual(prefs.folder.stat().st_mode & 0o777,0o700)
            prefs.path.write_text('{broken');self.assertFalse(prefs.load())
            prefs.save(True);self.assertTrue(prefs.load())
            target=Path(home)/'other';target.write_text('untouched')
            prefs.path.unlink();prefs.path.symlink_to(target)
            self.assertFalse(prefs.load())
            from drive_manager.process import OperationError
            with self.assertRaises(OperationError):prefs.save(True)
            self.assertEqual(target.read_text(),'untouched')
    def test_muting_consumes_events_without_replaying_or_exposing_file_names(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from drive_manager.app import Window,TEXT
        tray=Mock();tray.isSystemTrayAvailable.return_value=True;tray.supportsMessages.return_value=True
        window=SimpleNamespace(notice_tracker=Tracker(),notifications_enabled=False,tray=tray,t=TEXT['es'])
        Window.notify_status(window,'personal',self.status('uploading',1,uploading=1))
        Window.notify_status(window,'personal',self.status())
        tray.showMessage.assert_not_called()
        window.notifications_enabled=True
        Window.notify_status(window,'personal',self.status())
        tray.showMessage.assert_not_called()
        Window.notify_status(window,'personal',self.status('uploading',1,uploading=1))
        Window.notify_status(window,'personal',self.status())
        tray.showMessage.assert_called_once()
        self.assertIn('personal',tray.showMessage.call_args.args[0])
        self.assertNotIn('/private',str(tray.showMessage.call_args))
    def test_preference_failure_rolls_back_window_and_tray_controls(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from drive_manager.app import Window,TEXT
        from drive_manager.process import OperationError
        window=SimpleNamespace(notifications_enabled=True,notification_settings=Mock(),
            notification_action=Mock(),notification_checkbox=Mock(),label=Mock(),t=TEXT['es'])
        window.notification_settings.save.side_effect=OperationError('notification_settings_error')
        Window.set_notifications(window,False)
        self.assertTrue(window.notifications_enabled)
        window.notification_action.setChecked.assert_called_once_with(True)
        window.notification_checkbox.setChecked.assert_called_once_with(True)
