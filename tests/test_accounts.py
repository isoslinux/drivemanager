import configparser
import json
from pathlib import Path
from threading import Event
import tempfile
import unittest
from unittest.mock import patch
from drive_manager.accounts import Accounts
from drive_manager.service import Manager
from drive_manager.settings import Preferences
from drive_manager.process import OperationError
from drive_manager import autostart
from test_core import FakeRunner

class AccountRunner(FakeRunner):
    def run(self, args):
        if args[:2] == ['rclone', 'listremotes']:
            paths = [a.split('=', 1)[1] for a in args if a.startswith('--config=')]
            if not paths: return '[]'
            parser = configparser.ConfigParser(); parser.read(paths[0])
            return json.dumps([{'name': n, 'type': 'drive', 'source': 'file'} for n in parser.sections()])
        return super().run(args)

class AccountsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.manager = Manager(AccountRunner(), self.tmp.name, lambda: [])
    def fake_oauth(self, name, cancel, on_url=None):
        folder = self.manager.accounts.folder; folder.mkdir(parents=True, exist_ok=True)
        path = folder / '.oauth-staged'
        path.write_text('[' + name + ']\ntype = drive\ntoken = PRIVATE\n')
        path.chmod(0o600); return path
    def test_authentication_before_details_then_commit_without_second_oauth(self):
        callback = lambda url: None
        with patch.object(self.manager.accounts, 'authorize', side_effect=self.fake_oauth) as auth:
            registration = self.manager.begin_authorization(Event(), callback)
            self.assertFalse(self.manager.settings.folder.exists())
            original, staged = registration
            self.assertTrue(staged.exists())
            self.assertTrue(original.startswith('google_'))
            prefs = Preferences(str(Path(self.tmp.name) / 'Personal'))
            self.manager.add_account('personal', prefs, Event(), registration=registration)
            self.assertEqual(auth.call_count, 1)
        parser = configparser.ConfigParser()
        parser.read(self.manager.accounts.path('personal'))
        self.assertEqual(parser.sections(), ['personal'])
        self.assertEqual(self.manager.settings.load('personal'), prefs)
        self.assertFalse(staged.exists())

    def test_cancel_after_browser_authentication_removes_staged_config(self):
        cancel = Event()
        def oauth(name, event, callback):
            staged = self.fake_oauth(name, event)
            cancel.set()
            return staged
        with patch.object(self.manager.accounts, 'authorize', side_effect=oauth):
            with self.assertRaises(OperationError):
                self.manager.begin_authorization(cancel, lambda url: None)
        self.assertEqual(list(self.manager.accounts.folder.glob('.oauth-*')), [])

    def test_four_accounts_isolated_and_independent_folders(self):
        with patch.object(self.manager.accounts, 'authorize', side_effect=self.fake_oauth):
            for n in range(4):
                name = 'google' + str(n)
                self.manager.add_account(name, Preferences(str(Path(self.tmp.name) / name)), Event())
        self.assertEqual(len(self.manager.discover_accounts()), 4)
        paths = [self.manager.snapshot_config(n) for n in self.manager.discover_accounts()]
        self.assertEqual(len(set(paths)), 4)
        for p in paths: self.assertEqual(p.stat().st_mode & 0o777, 0o600)
    def test_duplicate_name_rejected_before_oauth(self):
        with patch.object(self.manager.accounts, 'authorize', side_effect=self.fake_oauth) as auth:
            self.manager.add_account('google', Preferences(str(Path(self.tmp.name) / 'one')), Event())
            with self.assertRaises(OperationError):
                self.manager.add_account('google', Preferences(str(Path(self.tmp.name) / 'two')), Event())
            self.assertEqual(auth.call_count, 1)
    def test_overlapping_folder_rejected_before_oauth(self):
        with patch.object(self.manager.accounts, 'authorize', side_effect=self.fake_oauth) as auth:
            self.manager.add_account('one', Preferences(str(Path(self.tmp.name) / 'Drive')), Event())
            with self.assertRaises(OperationError):
                self.manager.add_account('two', Preferences(str(Path(self.tmp.name) / 'Drive/nested')), Event())
            self.assertEqual(auth.call_count, 1)
    def test_oauth_cancel_before_start(self):
        cancel = Event(); cancel.set()
        with patch('subprocess.Popen') as process:
            with self.assertRaises(OperationError): self.manager.accounts.authorize('one', cancel)
            process.assert_not_called()
        self.assertFalse(self.manager.accounts.path('one').exists())
    def test_oauth_private_config_and_no_output(self):
        class Process:
            returncode = 0
            def poll(self): return 0
        def start(args, **kwargs):
            self.assertIn('scope=drive.readonly', args)
            self.assertIn('--no-output', args)
            self.assertEqual(kwargs['umask'], 0o077)
            path = Path(next(a.split('=', 1)[1] for a in args if a.startswith('--config=')))
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            path.write_text('[one]\ntype = drive\ntoken = SECRET\n')
            return Process()
        with patch('subprocess.Popen', side_effect=start):
            staged = self.manager.accounts.authorize('one', Event())
        self.assertEqual(staged.stat().st_mode & 0o777, 0o600)
        staged.unlink()
    def test_no_credentials_or_preferences_on_failed_authorization(self):
        with patch.object(self.manager.accounts, 'authorize', side_effect=OperationError('failed')):
            with self.assertRaises(OperationError):
                self.manager.add_account('one', Preferences(str(Path(self.tmp.name) / 'Drive')), Event())
        self.assertFalse(self.manager.settings.path('one').exists())
    def test_login_launcher_creation_and_removal_without_stop(self):
        self.manager.save_preferences('one', Preferences(automount=True))
        path = Path(self.tmp.name) / '.config/autostart/drive-manager-automount.desktop'
        self.assertIn('Exec=drive-manager --automount', path.read_text())
        self.manager.save_preferences('one', Preferences(automount=False))
        self.assertFalse(path.exists())
        self.assertFalse(any('stop' in c for c in self.manager.runner.calls))
    def test_foreign_login_launcher_preserved(self):
        path = Path(self.tmp.name) / '.config/autostart/drive-manager-automount.desktop'
        path.parent.mkdir(parents=True); path.write_text('foreign launcher')
        with self.assertRaises(OperationError):
            self.manager.save_preferences('one', Preferences(automount=True))
        self.assertEqual(path.read_text(), 'foreign launcher')
        self.assertFalse(self.manager.settings.load('one').automount)
    def test_login_skips_active_and_unselected_accounts(self):
        from drive_manager.service import Status
        with patch('drive_manager.service.Manager') as cls:
            manager = cls.return_value
            manager.discover_accounts.return_value = ['active', 'off', 'ready']
            manager.settings.load.side_effect = lambda n: Preferences(automount=n != 'off')
            manager.status.side_effect = lambda n: Status('mounted' if n == 'active' else 'unmounted', '/demo')
            self.assertEqual(autostart.run(), 0)
            manager.mount.assert_called_once_with('ready')
