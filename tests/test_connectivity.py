import json
from pathlib import Path
import sys
import tempfile
from threading import Event
import unittest
from unittest.mock import patch
from drive_manager.connectivity import check,probe,classify,Result
from drive_manager.service import Manager
from drive_manager.wallet import PASSWORD_COMMAND
from test_accounts import AccountRunner

class ConnectivityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.manager=Manager(AccountRunner(),self.temp.name,lambda:[])
        self.source=self.manager.accounts.path('account');self.source.parent.mkdir(parents=True)
        self.source.write_text('[account]\ntype=drive\ntoken=OLD_SECRET\n')

    def test_source_credentials_and_services_unchanged(self):
        before=self.source.read_bytes()
        def query(args,cancel):
            self.assertEqual(args[:3],['rclone','lsf','account:'])
            self.assertIn('--dirs-only',args);self.assertIn('--max-depth=1',args)
            self.assertIn('--low-level-retries=1',args)
            staged=Path(next(a.split('=',1)[1] for a in args if a.startswith('--config=')))
            self.assertNotEqual(staged,self.source);self.assertEqual(staged.stat().st_mode & 0o777,0o600)
            self.assertEqual(staged.parent.stat().st_mode & 0o777,0o700)
            staged.write_text('NEW_SECRET')
            return Result('connection_ok',.1)
        with patch('drive_manager.connectivity.probe',side_effect=query):
            self.assertEqual(check(self.manager,'account').state,'connection_ok')
        self.assertEqual(before,self.source.read_bytes());self.assertEqual(self.manager.runner.calls,[])
        self.assertEqual(list((Path(self.temp.name)/'.local/state/drive-manager/connectivity').iterdir()),[])

    def test_encrypted_account_key_is_not_in_arguments(self):
        self.source.write_text('RCLONE_ENCRYPT_V0:\nCIPHERTEXT')
        with patch('drive_manager.connectivity.probe',return_value=Result('connection_wallet')) as query:
            self.assertEqual(check(self.manager,'account').state,'connection_wallet')
        self.assertIn('--password-command='+PASSWORD_COMMAND,query.call_args.args[0])
        self.assertIn('CIPHERTEXT',self.source.read_text())

    def test_external_config_copied_and_preserved(self):
        self.source.unlink()
        original=Path(self.temp.name)/'external.conf';original.write_text('[account]\ntype=drive\ntoken=SECRET\n')
        with patch.object(self.manager.runner,'run',return_value='Config file:\n'+str(original)),patch('drive_manager.connectivity.probe',return_value=Result('connection_ok')) as query:
            self.assertEqual(check(self.manager,'account').state,'connection_ok')
        self.assertNotIn('--config='+str(original),query.call_args.args[0]);self.assertIn('SECRET',original.read_text())

    def test_external_encryption_not_assumed_to_use_our_wallet(self):
        self.source.unlink()
        original=Path(self.temp.name)/'external.conf';original.write_text('RCLONE_ENCRYPT_V0:\nCIPHERTEXT')
        with patch.object(self.manager.runner,'run',return_value=str(original)),patch('drive_manager.connectivity.probe') as query:
            self.assertEqual(check(self.manager,'account').state,'connection_locked');query.assert_not_called()

    def test_failure_cleans_staging_and_hides_raw_errors(self):
        with patch('drive_manager.connectivity.probe',side_effect=RuntimeError('TOKEN=SECRET')):
            result=check(self.manager,'account')
        self.assertEqual(result.state,'connection_error');self.assertNotIn('SECRET',repr(result))
        self.assertEqual(list((Path(self.temp.name)/'.local/state/drive-manager/connectivity').iterdir()),[])

    def test_cancel_before_start_does_not_launch_or_copy(self):
        event=Event();event.set()
        with patch('drive_manager.connectivity.probe') as query:
            self.assertEqual(check(self.manager,'account',event).state,'connection_cancelled');query.assert_not_called()
        self.assertFalse((Path(self.temp.name)/'.local').exists())

    def test_invalid_and_symlink_configs_fail_closed(self):
        with patch('drive_manager.connectivity.probe') as query:
            self.assertEqual(check(self.manager,'../bad').state,'connection_error')
            original=self.source.with_suffix('.original');self.source.rename(original);self.source.symlink_to(original)
            self.assertEqual(check(self.manager,'account').state,'connection_error');query.assert_not_called()

    def test_known_errors_return_only_catalog_keys(self):
        for message,key in [('401 TOKEN=SECRET','connection_auth'),('403 SECRET','connection_permission'),
            ('invalid_grant SECRET','connection_auth'),('no such host SECRET','connection_network'),
            ('429 SECRET','connection_rate'),('failed password command SECRET','connection_wallet'),
            ('Unexpected SECRET','connection_error')]:
            self.assertEqual(classify(message),key)

    def test_process_success_never_returns_directory_names(self):
        result=probe([sys.executable,'-c','print("PRIVATE_FOLDER")'],limit=1)
        self.assertEqual(result.state,'connection_ok');self.assertNotIn('PRIVATE_FOLDER',repr(result))

    def test_process_failure_never_returns_secret_diagnostics(self):
        result=probe([sys.executable,'-c','import sys; sys.stderr.write("403 SECRET"); sys.exit(1)'],limit=1)
        self.assertEqual(result.state,'connection_permission');self.assertNotIn('SECRET',repr(result))

    def test_large_error_output_is_drained_without_hanging(self):
        result=probe([sys.executable,'-c','import sys; sys.stderr.write("403 "+"SECRET"*200000); sys.exit(1)'],limit=2)
        self.assertEqual(result.state,'connection_permission')

    def test_process_timeout_is_bounded(self):
        result=probe([sys.executable,'-c','import time; time.sleep(60)'],limit=.1)
        self.assertEqual(result.state,'connection_timeout');self.assertLess(result.seconds,2)

    @unittest.skipUnless(__import__('os').environ.get('QT_QPA_PLATFORM')=='offscreen','Offscreen Qt required')
    def test_ui_check_is_independent_and_results_follow_selection_and_language(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QEventLoop,QTimer
        from drive_manager.app import Window
        from drive_manager.quota import Quota
        from drive_manager.i18n import TEXT
        app=QApplication.instance() or QApplication([])
        release=Event()
        def query(manager,remote,cancel):release.wait(2);return Result('connection_ok',.2)
        with patch('drive_manager.app.Manager',return_value=self.manager),patch('drive_manager.quota.read_quota',return_value=Quota()),patch('drive_manager.connectivity.check',side_effect=query):
            window=Window()
            try:
                initial=QEventLoop();QTimer.singleShot(300,initial.quit);initial.exec()
                window.set_accounts(['account','other'],'account')
                window.check_connection()
                self.assertIsNotNone(window.connection_future)
                self.assertIn(window.t['connection_checking'],window.connection_label.text())
                self.assertFalse(window.buttons['check_connection'].isEnabled())
                window.accounts.setCurrentText('other')
                self.assertEqual(window.connection_label.text(),'')
                release.set()
                loop=QEventLoop();QTimer.singleShot(350,loop.quit);loop.exec()
                self.assertIn('account',window.connection_results)
                self.assertEqual(window.connection_label.text(),'')
                window.accounts.setCurrentText('account')
                self.assertIn(window.t['connection_ok'],window.connection_label.text())
                for language in ['en','es','fr','de']:
                    window.language_selector.setCurrentIndex(window.language_selector.findData(language))
                    self.assertEqual(window.buttons['check_connection'].text(),TEXT[language]['check_connection'])
                    self.assertIn(TEXT[language]['connection_ok'],window.connection_label.text())
                window.set_accounts([])
                self.assertFalse(window.buttons['check_connection'].isEnabled());self.assertEqual(window.connection_label.text(),'')
            finally:
                release.set();window.timer.stop();window.connection_cancel.set()
                window.connection_pool.shutdown();window.pool.shutdown();window.quota_pool.shutdown();window.update_pool.shutdown()
                window.tray.hide();window.hide()
