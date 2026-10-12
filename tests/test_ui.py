import os
import unittest
from unittest.mock import patch

@unittest.skipUnless(os.environ.get('QT_QPA_PLATFORM') == 'offscreen', 'Set QT_QPA_PLATFORM=offscreen for UI smoke')
class UiSmoke(unittest.TestCase):
    def test_window_and_actions(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer, QEventLoop
        from drive_manager.app import Window
        from drive_manager.service import Status
        app = QApplication.instance() or QApplication([])
        with patch('drive_manager.service.Manager.provider_of', return_value='drive'), patch('drive_manager.service.Manager.discover_accounts', return_value=['demo']), patch('drive_manager.service.Manager.status', return_value=Status('unmounted', '/demo')):
            window = Window()
            window.show()
            loop = QEventLoop()
            QTimer.singleShot(800, loop.quit)
            loop.exec()
            self.assertEqual(window.accounts.currentText(), 'demo')
            self.assertTrue(window.buttons['mount'].isEnabled())
            self.assertFalse(window.buttons['unmount'].isEnabled())
            self.assertTrue(window.buttons['settings'].isEnabled())
            from drive_manager.settings import Preferences
            from PySide6.QtWidgets import QLineEdit, QSpinBox
            def accept_dialog():
                dialog = app.activeModalWidget()
                dialog.findChild(QLineEdit).setText('/demo/new')
                spins = dialog.findChildren(QSpinBox)
                spins[0].setValue(8); spins[1].setValue(48)
                dialog.accept()
            with patch.object(window.manager, 'save_preferences', return_value=Status('unmounted', '/demo/new')) as save:
                QTimer.singleShot(0, accept_dialog)
                window.settings_dialog(Preferences('/demo'))
                loop = QEventLoop()
                QTimer.singleShot(600, loop.quit)
                loop.exec()
                save.assert_called_once_with('demo', Preferences('/demo/new', 8, 48))
            window.show_status(Status('mounted', '/demo/new', True))
            self.assertFalse(window.buttons['settings'].isEnabled())
            from drive_manager.transfers import Progress, Transfer
            window.show_status(Status('mounted', '/demo/new', True, True, 1, Progress('uploading', 0, 1, 0, 1024, (Transfer('report.pdf', 43, 2048, 9),))))
            self.assertEqual(window.transfer_table.item(0,0).text(), 'report.pdf')
            self.assertEqual(window.transfer_table.item(0,1).text(), '43%')
            self.assertEqual(window.progress_bar.value(), 43)
            with patch.object(window.manager, 'begin_authorization', return_value=('temporary', None)) as begin, patch.object(window, 'connection_details') as details:
                window.add_account()
                loop = QEventLoop(); QTimer.singleShot(400, loop.quit); loop.exec()
                begin.assert_called_once()
                self.assertEqual(begin.call_args.args[2], 'drive')
                details.assert_called_once_with(('temporary', None))
                begin.reset_mock(); details.reset_mock()
                window.provider.setCurrentIndex(2)
                window.add_account()
                loop = QEventLoop(); QTimer.singleShot(400, loop.quit); loop.exec()
                self.assertEqual(begin.call_args.args[2], 'onedrive')
                details.assert_called_once_with(('temporary', None))
            from threading import Event
            window.oauth_cancel = Event()
            url = 'http://127.0.0.1:53682/auth?state=' + 'a'*22
            window.oauth_urls.put(url)
            with patch('drive_manager.app.QDesktopServices.openUrl', return_value=True) as opener:
                window.tick()
                self.assertTrue(window.buttons['oauth_open'].isEnabled())
                self.assertEqual(opener.call_args.args[0].toString(), url)
                window.open_authorization()
                self.assertEqual(opener.call_count, 2)
            window.cancel_authorization()
            window.pool.shutdown()
            window.timer.stop()
            window.tray.hide()
            window.hide()

@unittest.skipUnless(os.environ.get('QT_QPA_PLATFORM') == 'offscreen', 'Set QT_QPA_PLATFORM=offscreen for UI smoke')
class DiagnosticsUi(unittest.TestCase):
    def test_report_is_readonly_and_copy_matches_visible_content(self):
        from PySide6.QtWidgets import QApplication, QPlainTextEdit, QPushButton
        from PySide6.QtCore import QTimer, QEventLoop
        from drive_manager.app import Window
        from drive_manager.diagnostics import Check, Report
        app=QApplication.instance() or QApplication([])
        with patch('drive_manager.service.Manager.discover_accounts',return_value=[]):
            window=Window()
            loop=QEventLoop();QTimer.singleShot(350,loop.quit);loop.exec()
            observed={}
            def inspect():
                dialog=app.activeModalWidget()
                try:
                    view=dialog.findChild(QPlainTextEdit)
                    observed['readonly']=view.isReadOnly()
                    observed['text']=view.toPlainText()
                    copy=next(b for b in dialog.findChildren(QPushButton) if b.text()==window.t['copy_report'])
                    copy.click();observed['clipboard']=app.clipboard().text()
                finally:dialog.accept()
            QTimer.singleShot(0,inspect)
            window.show_diagnostics(Report((Check('rclone','ok','installed','1.74.3'),)))
            self.assertTrue(observed['readonly'])
            self.assertEqual(observed['text'],observed['clipboard'])
            self.assertIn('1.74.3',observed['text'])
            self.assertTrue(window.buttons['diagnostics'].isEnabled())
            window.timer.stop();window.pool.shutdown();window.tray.hide();window.hide()

@unittest.skipUnless(os.environ.get('QT_QPA_PLATFORM') == 'offscreen', 'Set QT_QPA_PLATFORM=offscreen for UI smoke')
class SimplifiedUi(unittest.TestCase):
    def test_collapsible_transfers_and_row_menu_use_selected_account(self):
        from PySide6.QtWidgets import QApplication, QPushButton, QMenu
        from PySide6.QtGui import QAction
        from PySide6.QtCore import QTimer, QEventLoop, Qt
        from drive_manager.app import Window
        from drive_manager.service import Status
        app=QApplication.instance() or QApplication([])
        def status(remote):return Status('external' if remote=='work' else 'unmounted','/demo/'+remote)
        with patch('drive_manager.service.Manager.discover_accounts',return_value=['personal','work']), \
             patch('drive_manager.service.Manager.provider_of',return_value='drive'), \
             patch('drive_manager.service.Manager.status',side_effect=status), \
             patch('drive_manager.service.Manager.is_app_account',return_value=True):
            window=Window();window.show()
            loop=QEventLoop();QTimer.singleShot(600,loop.quit);loop.exec()
            self.assertIsInstance(window.buttons['settings'],QAction)
            self.assertIsInstance(window.buttons['mount'],QPushButton)
            self.assertNotIn(window.t['delete'],[b.text() for b in window.findChildren(QPushButton)])
            self.assertTrue(window.transfer_panel.isHidden())
            window.transfer_toggle.click()
            self.assertFalse(window.transfer_panel.isHidden())
            self.assertEqual(window.transfer_toggle.arrowType(),Qt.ArrowType.DownArrow)
            window.transfer_toggle.click();self.assertTrue(window.transfer_panel.isHidden())
            work=window.accounts.visualItemRect(window.accounts.item(1,0)).center()
            self.assertTrue(window.prepare_account_menu(work))
            self.assertEqual(window.accounts.currentText(),'work')
            self.assertFalse(window.buttons['settings'].isEnabled())
            self.assertFalse(window.buttons['delete'].isEnabled())
            self.assertTrue(window.buttons['open'].isEnabled())
            window.accounts.setCurrentText('personal')
            self.assertTrue(window.buttons['settings'].isEnabled())
            with patch.object(window,'submit') as submit:
                window.buttons['settings'].trigger()
                submit.assert_called_once()
                with patch.object(window.manager.settings,'load') as load:
                    submit.call_args.args[0]();load.assert_called_once_with('personal')
            self.assertTrue(window.buttons['cancel_oauth'].isHidden())
            self.assertTrue(window.buttons['oauth_open'].isHidden())
            window.timer.stop();window.pool.shutdown();window.tray.hide();window.hide()
    def test_new_oauth_controls_are_visible_and_hidden_on_completion(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer, QEventLoop
        from threading import Event
        from drive_manager.app import Window
        app=QApplication.instance() or QApplication([])
        with patch('drive_manager.service.Manager.discover_accounts',return_value=[]):
            window=Window();window.show()
            loop=QEventLoop();QTimer.singleShot(350,loop.quit);loop.exec()
            finished=Event();window.oauth_cancel=Event()
            window.submit(lambda:finished.wait(1),lambda value:None)
            self.assertFalse(window.buttons['cancel_oauth'].isHidden())
            self.assertFalse(window.buttons['oauth_open'].isHidden())
            finished.set()
            loop=QEventLoop();QTimer.singleShot(350,loop.quit);loop.exec()
            self.assertTrue(window.buttons['cancel_oauth'].isHidden())
            self.assertTrue(window.buttons['oauth_open'].isHidden())
            window.timer.stop();window.pool.shutdown();window.tray.hide();window.hide()
