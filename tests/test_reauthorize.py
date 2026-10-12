"""Renewal must preserve working credentials until a complete, safe commit."""
import configparser
from pathlib import Path
from threading import Event
from unittest.mock import patch
import unittest
import tempfile
from test_accounts import AccountRunner
from drive_manager.service import Manager
from drive_manager.process import OperationError
from drive_manager.service import Status
from drive_manager import transfers

class ReauthorizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.manager=Manager(AccountRunner(),self.tmp.name,lambda:[])
        self.remote='personal'
        from drive_manager.settings import Preferences
        self.prefs=Preferences(str(Path(self.tmp.name)/'Drive'),cache_gib=7,cache_hours=48)
        with patch.object(self.manager.accounts,'authorize',side_effect=self.fake_oauth):
            self.manager.add_account(self.remote,self.prefs,Event())
        self.path=self.manager.accounts.path(self.remote)
        with self.path.open('a') as file:file.write('root_folder_id = keep-root\n')
        self.original=self.path.read_bytes()
    def fake_oauth(self,name,cancel,on_url=None):
        folder=self.manager.accounts.folder;folder.mkdir(parents=True,exist_ok=True)
        staged=folder/'.oauth-staged';staged.write_text(f'[{name}]\ntype=drive\ntoken=PRIVATE\n');staged.chmod(0o600)
        return staged
    def renewed(self,name,cancel,on_url,writable):
        staged=self.fake_oauth(name,cancel,on_url)
        staged.write_text(f'[{name}]\ntype = drive\ntoken = NEW\nscope = drive.readonly\n')
        return staged
    def renew(self,cancel=None):
        return self.manager.reauthorize(self.remote,cancel or Event(),lambda url:None,confirmed=True)
    def test_reauthorization_preserves_options_preferences_and_permissions(self):
        with patch.object(self.manager.accounts,'authorize',side_effect=self.renewed):self.renew()
        parser=configparser.ConfigParser();parser.read(self.path)
        self.assertEqual(parser.get(self.remote,'token'),'NEW')
        self.assertEqual(parser.get(self.remote,'root_folder_id'),'keep-root')
        self.assertEqual(self.manager.settings.load(self.remote),self.prefs)
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)
        self.assertFalse(any('stop' in c for c in self.manager.runner.calls))
    def test_failure_and_cancellation_preserve_credentials(self):
        with patch.object(self.manager.accounts,'authorize',side_effect=OperationError('failed')):
            with self.assertRaises(OperationError):self.renew()
        cancel=Event()
        def cancelled(*args):
            staged=self.renewed(*args);cancel.set();return staged
        with patch.object(self.manager.accounts,'authorize',side_effect=cancelled):
            with self.assertRaises(OperationError):self.renew(cancel)
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertEqual(list(self.manager.accounts.folder.glob('.oauth-*')),[])
    def test_mounted_pending_and_external_accounts_never_start_oauth(self):
        with patch.object(self.manager.accounts,'authorize') as auth:
            with patch.object(self.manager,'status',return_value=Status('mounted','/demo',True)):
                with self.assertRaises(OperationError):self.renew()
            with patch.object(self.manager,'ensure_no_dirty_cache',side_effect=transfers.TransferError('uploads_pending')):
                with self.assertRaises(OperationError):self.renew()
            with patch.object(self.manager,'is_app_account',return_value=False):
                with self.assertRaises(OperationError):self.renew()
            auth.assert_not_called()
    def test_confirmation_required(self):
        with patch.object(self.manager.accounts,'authorize') as auth:
            with self.assertRaises(OperationError):self.manager.reauthorize(self.remote,Event(),None)
            auth.assert_not_called()
    def test_busy_after_authentication_preserves_credentials(self):
        with patch.object(self.manager.accounts,'authorize',side_effect=self.renewed):
            with patch.object(self.manager,'status',side_effect=[Status('unmounted','/demo'),Status('external','/demo')]):
                with self.assertRaises(OperationError):self.renew()
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertEqual(list(self.manager.accounts.folder.glob('.oauth-*')),[])
    def test_wrong_onedrive_identity_preserves_credentials(self):
        self.path.write_text('[personal]\ntype=onedrive\ntoken=OLD\ndrive_id=original\ndrive_type=personal\n')
        before=self.path.read_bytes()
        def wrong(accounts,name,*args):
            staged=self.fake_oauth(name,Event());staged.write_text('[personal]\ntype=onedrive\ntoken=NEW\ndrive_id=other\ndrive_type=personal\n');return staged
        with patch('drive_manager.onedrive.authorize',side_effect=wrong):
            with self.assertRaisesRegex(OperationError,'reauth_identity'):self.renew()
        self.assertEqual(self.path.read_bytes(),before)
    def test_write_upgrade_requests_scope_without_changing_mode(self):
        from dataclasses import replace
        self.path.write_text(self.path.read_text()+'scope = drive.readonly\n')
        def write_scope(name,cancel,on_url,writable):
            self.assertTrue(writable)
            staged=self.renewed(name,cancel,on_url,writable)
            staged.write_text(staged.read_text().replace('drive.readonly','drive'))
            return staged
        with patch.object(self.manager.accounts,'authorize',side_effect=write_scope):
            self.manager.reauthorize(self.remote,Event(),lambda url:None,confirmed=True,request_write=True)
        self.assertFalse(self.manager.settings.load(self.remote).writable)
        self.manager.save_preferences(self.remote,replace(self.prefs,writable=True))
        self.assertTrue(self.manager.settings.load(self.remote).writable)
        self.assertEqual(self.manager.settings.load(self.remote).mount_path,self.prefs.mount_path)
    def test_insufficient_new_permissions_preserve_original(self):
        with patch.object(self.manager.accounts,'authorize',side_effect=self.renewed):
            with self.assertRaisesRegex(OperationError,'needs_write_auth'):
                self.manager.reauthorize(self.remote,Event(),None,confirmed=True,request_write=True)
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertEqual(self.manager.settings.load(self.remote),self.prefs)
    def test_cancelled_write_upgrade_keeps_read_only(self):
        cancel=Event()
        def cancel_write(*args):
            staged=self.renewed(*args);staged.write_text(staged.read_text().replace('drive.readonly','drive'))
            cancel.set();return staged
        with patch.object(self.manager.accounts,'authorize',side_effect=cancel_write):
            with self.assertRaises(OperationError):
                self.manager.reauthorize(self.remote,cancel,None,confirmed=True,request_write=True)
        self.assertEqual(self.path.read_bytes(),self.original)
        self.assertFalse(self.manager.settings.load(self.remote).writable)
    def test_onedrive_write_upgrade_preserves_drive_and_options(self):
        self.path.write_text('[personal]\ntype=onedrive\ntoken=OLD\ndrive_id=original\ndrive_type=personal\naccess_scopes=Files.Read offline_access\nchunk_size=20M\n')
        def auth(accounts,name,cancel,on_url,ask_drive,writable):
            self.assertTrue(writable)
            staged=self.fake_oauth(name,cancel)
            staged.write_text('[personal]\ntype=onedrive\ntoken=NEW\ndrive_id=original\ndrive_type=personal\naccess_scopes=Files.ReadWrite offline_access\n')
            return staged
        with patch('drive_manager.onedrive.authorize',side_effect=auth):
            self.manager.reauthorize(self.remote,Event(),None,confirmed=True,request_write=True)
        parser=configparser.ConfigParser();parser.read(self.path)
        self.assertEqual(parser.get(self.remote,'chunk_size'),'20M')
        self.assertEqual(parser.get(self.remote,'drive_id'),'original')
        self.assertFalse(self.manager.settings.load(self.remote).writable)
