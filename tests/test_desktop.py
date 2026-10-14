from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
from drive_manager.app import Window
from drive_manager.service import Manager,Status

class DesktopTests(TestCase):
    def test_no_tray_close_exits_instead_of_hiding(self):
        owner=SimpleNamespace(tray=Mock(),hide=Mock(),quit=Mock());owner.tray.isVisible.return_value=False;event=Mock()
        Window.closeEvent(owner,event);owner.quit.assert_called_once();owner.hide.assert_not_called();event.accept.assert_called_once()
    def test_visible_tray_close_keeps_window_recoverable(self):
        owner=SimpleNamespace(tray=Mock(),hide=Mock(),quit=Mock());owner.tray.isVisible.return_value=True;event=Mock()
        Window.closeEvent(owner,event);owner.hide.assert_called_once();owner.quit.assert_not_called();event.ignore.assert_called_once()
    def test_default_launcher_receives_safe_file_uri(self):
        manager=Manager(Mock())
        with patch.object(manager,'status',return_value=Status('mounted','/home/demo/My folder #1')):manager.open_folder('a')
        manager.runner.launch.assert_called_once_with(['xdg-open','file:///home/demo/My%20folder%20%231'])
    def test_unmounted_folder_is_never_opened(self):
        manager=Manager(Mock())
        with patch.object(manager,'status',return_value=Status('unmounted','/home/demo')):
            with self.assertRaises(Exception):manager.open_folder('a')
        manager.runner.launch.assert_not_called()
