import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from drive_manager.settings import Settings, Preferences
from drive_manager.service import Manager
from drive_manager.mounts import Mount
from drive_manager.process import OperationError
from test_core import FakeRunner

class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.settings = Settings(self.home)
        self.manager = Manager(FakeRunner(), self.home, lambda: [])
    def test_defaults_and_atomic_private_save(self):
        self.assertEqual(self.settings.load('a'), Preferences())
        prefs = Preferences(str(self.home / 'My Drive'), 10, 72)
        self.manager.save_preferences('a', prefs)
        self.assertEqual(self.settings.load('a'), prefs)
        self.assertEqual(self.settings.path('a').stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.settings.folder.stat().st_mode & 0o777, 0o700)
        self.assertEqual(list(self.settings.folder.glob('.preferences-*')), [])
        self.assertEqual(self.settings.load('b'), Preferences())
    def test_reject_bad_values(self):
        for prefs in [Preferences('/tmp/outside'), Preferences(str(self.home)),
                      Preferences(str(self.home / '.config/x')), Preferences('relative'),
                      Preferences('', 0, 24), Preferences('', True, 24),
                      Preferences('', 2, 0), Preferences(str(self.home / '../bad'))]:
            with self.assertRaises(OperationError): self.settings.validate(prefs)
    def test_reject_symlink_ancestor(self):
        (self.home / 'link').symlink_to(self.home, target_is_directory=True)
        with self.assertRaises(OperationError):
            self.settings.validate(Preferences(str(self.home / 'link/target')))
    def test_reject_nested_account_paths(self):
        self.manager.save_preferences('a', Preferences(str(self.home / 'Drive')))
        with self.assertRaises(OperationError):
            self.manager.save_preferences('b', Preferences(str(self.home / 'Drive/nested')))
    def test_reject_busy_account_without_stop(self):
        self.manager.mounts = lambda: [Mount('/external', 'a:', 'fuse.rclone')]
        with self.assertRaises(OperationError): self.manager.save_preferences('a', Preferences())
        self.assertFalse(any('stop' in c for c in self.manager.runner.calls))
    def test_reject_nonempty_directory(self):
        folder = self.home / 'nonempty'; folder.mkdir(); (folder / 'keep').write_text('keep')
        with self.assertRaises(OperationError):
            self.manager.save_preferences('a', Preferences(str(folder)))
    def test_custom_arguments_and_stable_unit_identity(self):
        old_unit, _ = self.manager.identity('a')
        target = self.home / 'My Drive'
        self.manager.save_preferences('a', Preferences(str(target), 7, 48))
        self.assertEqual(self.manager.identity('a'), (old_unit, target))
        with patch('drive_manager.service.shutil.which', return_value='/usr/bin/rclone'), patch.object(self.manager, 'snapshot_config', return_value=self.home / 'snapshot'):
            self.manager.mount('a')
        call = next(c for c in self.manager.runner.calls if c[0] == 'systemd-run')
        self.assertIn(str(target), call)
        self.assertIn('--vfs-cache-max-size=7G', call)
        self.assertIn('--vfs-cache-max-age=48h', call)
        self.assertIn('--read-only', call)
    def test_corrupt_file_is_not_overwritten(self):
        self.settings.save('a', Preferences())
        self.settings.path('a').write_text('{broken')
        with self.assertRaises(OperationError): self.settings.load('a')
        self.assertEqual(self.settings.path('a').read_text(), '{broken')
