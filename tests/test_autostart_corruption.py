import tempfile
from pathlib import Path
from unittest import TestCase
from drive_manager.settings import Settings,Preferences
from drive_manager import autostart
from drive_manager.process import OperationError

class AutostartCorruptionTests(TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.settings=Settings(Path(self.temp.name));self.settings.save('a',Preferences(automount=True));self.bad=self.settings.path('b')
        self.launcher=self.settings.home/'.config/autostart/drive-manager-automount.desktop'
    def test_bad_json_does_not_block_healthy_launcher_or_change_bad_bytes(self):
        self.bad.write_bytes(b'{corrupt');autostart.update(self.settings)
        self.assertTrue(self.launcher.exists());self.assertEqual(self.bad.read_bytes(),b'{corrupt')
    def test_wrong_types_and_unknown_fields_do_not_enable_automount(self):
        self.settings.save('a',Preferences())
        for value in ['[]','{"automount":"yes"}','{"automount":true,"token":"fixture"}']:
            self.bad.write_text(value);autostart.update(self.settings);self.assertFalse(self.launcher.exists())
    def test_symlink_preferences_are_not_read_or_enabled(self):
        self.settings.save('a',Preferences());outside=self.settings.home/'outside';outside.write_text('{"automount":true}');self.bad.symlink_to(outside)
        autostart.update(self.settings);self.assertFalse(self.launcher.exists())
    def test_owned_launcher_removed_when_only_damaged_accounts_remain(self):
        autostart.update(self.settings);self.settings.path('a').write_text('{corrupt')
        autostart.update(self.settings);self.assertFalse(self.launcher.exists())
    def test_foreign_launcher_still_preserved_with_damaged_preferences(self):
        self.bad.write_text('{corrupt');self.launcher.parent.mkdir(parents=True);self.launcher.write_text('foreign')
        with self.assertRaises(OperationError):autostart.update(self.settings)
        self.assertEqual(self.launcher.read_text(),'foreign')
