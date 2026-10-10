from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch
from drive_manager.service import Manager,Status
from drive_manager.settings import Preferences
from drive_manager.process import OperationError
from drive_manager import transfers
from test_accounts import AccountRunner

class WritableTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.manager=Manager(AccountRunner(),self.tmp.name,lambda:[])
        path=self.manager.accounts.path('a');path.parent.mkdir(parents=True)
        path.write_text('[a]\ntype = drive\nscope = drive\ntoken = PRIVATE\n')
    def dirty(self,value=True):
        root=self.manager.write_cache_path('a')/'vfsMeta/a'
        root.mkdir(parents=True,exist_ok=True);file=root/'test'
        file.write_text(json.dumps({'Dirty':value}));return file
    def test_readonly_profile_rejected_before_preferences_change(self):
        path=self.manager.accounts.path('a');path.write_text('[a]\ntype = drive\nscope = drive.readonly\n')
        with self.assertRaises(OperationError):self.manager.save_preferences('a',Preferences(writable=True))
        self.assertFalse(self.manager.settings.load('a').writable)
    def test_default_readonly_compatible(self):self.assertFalse(self.manager.settings.load('a').writable)
    def test_writable_arguments_and_isolated_cache(self):
        readonly=self.manager.cache_directory('a')
        self.manager.settings.save('a',Preferences(writable=True))
        with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'):
            self.manager.mount('a')
        command=next(c for c in self.manager.runner.calls if c[0]=='systemd-run')
        self.assertNotIn('--read-only',command)
        self.assertIn('--rc',command);self.assertIn('--property=TimeoutStopSec=infinity',command)
        self.assertNotEqual(readonly,self.manager.cache_directory('a'))
        self.assertIn('--rc-addr=unix://'+str(self.manager.rc_endpoint('a')),command)
    def test_old_readonly_oauth_cannot_write(self):
        path=self.manager.accounts.path('a');path.write_text('[a]\ntype = drive\nscope = drive.readonly\n')
        with self.assertRaises(OperationError) as error:self.manager.ensure_write_permission('a',path)
        self.assertEqual(str(error.exception),'needs_write_auth')
    def test_microsoft_read_scopes_cannot_write(self):
        path=self.manager.accounts.path('a');path.write_text('[a]\ntype = onedrive\naccess_scopes = Files.Read offline_access\n')
        with self.assertRaises(OperationError):self.manager.ensure_write_permission('a',path)
    def test_dirty_cache_blocks_delete_even_when_unmounted(self):
        self.dirty()
        with self.assertRaises(transfers.TransferError):self.manager.remove_connection('a',True)
        self.assertTrue(self.manager.accounts.path('a').exists())
    def test_dirty_cache_blocks_switch_to_readonly(self):
        self.manager.settings.save('a',Preferences(writable=True));self.dirty()
        with self.assertRaises(transfers.TransferError):self.manager.save_preferences('a',Preferences())
        self.assertTrue(self.manager.settings.load('a').writable)
    def test_pending_uploads_never_unmount_or_stop(self):
        with patch('drive_manager.transfers.pending',return_value=1):
            with self.assertRaises(transfers.TransferError):
                self.manager.stop_managed('a',Status('mounted','/test',True,True,1))
        self.assertFalse(any('stop' in c or c[0]=='fusermount3' for c in self.manager.runner.calls))
    def test_unknown_upload_status_blocks_stop(self):
        with patch('drive_manager.transfers.pending',side_effect=transfers.TransferError('uploads_unknown')):
            with self.assertRaises(transfers.TransferError):
                self.manager.stop_managed('a',Status('mounted','/test',True,True,-1))
        self.assertEqual(self.manager.runner.calls,[])
    def test_open_files_block_stop(self):
        with patch('drive_manager.transfers.pending',return_value=0),patch('drive_manager.transfers.ensure_closed',side_effect=transfers.TransferError('files_open')):
            with self.assertRaises(transfers.TransferError):
                self.manager.stop_managed('a',Status('mounted','/test',True,True))
        self.assertEqual(self.manager.runner.calls,[])
    def test_final_write_race_preserves_credentials(self):
        with patch('drive_manager.transfers.pending',return_value=0),patch('drive_manager.transfers.ensure_closed'),patch.object(self.manager,'ensure_no_dirty_cache',side_effect=[None,transfers.TransferError('uploads_pending')]):
            with self.assertRaises(transfers.TransferError):self.manager.stop_managed('a',Status('mounted','/test',True,True))
        self.assertTrue(self.manager.accounts.path('a').exists())
        self.assertIn(['fusermount3','-u','--','/test'],self.manager.runner.calls)
    def test_bad_cache_metadata_blocks_deletion(self):
        file=self.dirty();file.write_text('{broken')
        with self.assertRaises(transfers.TransferError):self.manager.remove_connection('a',True)
        self.assertTrue(self.manager.accounts.path('a').exists())
    def test_rc_schema_validated_and_errors_counted(self):
        with patch('drive_manager.transfers.request',return_value={'diskCache':{'uploadsQueued':1,'uploadsInProgress':2,'erroredFiles':0,'outOfSpace':False}}):
            self.assertEqual(transfers.pending('/private'),3)
        with patch('drive_manager.transfers.request',return_value={'diskCache':{}}):
            with self.assertRaises(transfers.TransferError):transfers.pending('/private')
