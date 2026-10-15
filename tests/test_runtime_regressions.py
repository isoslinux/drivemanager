from pathlib import Path
from dataclasses import replace
from queue import Queue
from threading import Event
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock,patch
import test_bulk as fixtures
from drive_manager.service import Manager,Status
from drive_manager.mounts import Mount
from drive_manager.process import OperationError
from drive_manager.settings import Preferences
from drive_manager.app import Window
from drive_manager.validation import cleanup_test
from PySide6.QtWidgets import QMessageBox

class RuntimeRegressionTests(TestCase):
    setUp=fixtures.BulkTests.setUp
    def test_write_upgrade_creates_cancel_event_and_authorizes(self):
        for provider in ['drive','onedrive','dropbox']:
            manager=Mock();manager.save_preferences.side_effect=[OperationError('needs_write_auth'),Status('unmounted','',False,True)]
            owner=SimpleNamespace(manager=manager,oauth_urls=Queue(),label=Mock(),t={'reauth':'Auth','upgrade_confirm':'Confirm','auth_wait':'Wait'},ask_onedrive_drive=Mock(),show_status=Mock(),poll=Mock())
            owner.submit=lambda task,callback,*args:callback(task())
            with patch('drive_manager.app.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):Window.save_account_preferences(owner,'a',Preferences(writable=True))
            self.assertIsInstance(owner.oauth_cancel,Event);manager.reauthorize.assert_called_once()
            self.assertTrue(manager.reauthorize.call_args.kwargs['request_write']);self.assertTrue(manager.save_preferences.call_args.args[1].writable)
    def test_late_status_is_bound_to_original_account(self):
        owner=SimpleNamespace(accounts=Mock(),account_states={});owner.accounts.currentText.return_value='b'
        result=Status('mounted','/a',True)
        Window.show_status(owner,result,'a');self.assertEqual(owner.account_states,{'a':result})
    def test_nonobject_other_preferences_has_controlled_error(self):
        self.manager.settings.path('b').write_text('[]')
        with self.assertRaises(OperationError):self.manager.settings.save('a',Preferences(str(self.home/'A')))
    def test_corrupt_status_is_repairable_not_global_failure(self):
        self.manager.settings.path('a').write_text('{bad')
        self.assertEqual(self.manager.status('a').state,'prefs_damaged')
        self.assertEqual(self.manager.status('b').state,'unmounted')
    def test_repair_backs_up_preferences_and_preserves_credentials(self):
        path=self.manager.settings.path('a');path.write_bytes(b'{bad');source=self.manager.accounts.path('a').read_bytes()
        self.manager.repair_preferences('a',True)
        self.assertEqual(self.manager.settings.load('a'),Preferences());self.assertEqual(self.manager.accounts.path('a').read_bytes(),source)
        backup=next((self.home/'.local/state/drive-manager/preference-backups').glob('*.bak'))
        self.assertEqual(backup.read_bytes(),b'{bad');self.assertEqual(backup.stat().st_mode&0o777,0o600)
    def test_repair_needs_confirmation_and_damaged_file(self):
        with self.assertRaises(OperationError):self.manager.repair_preferences('a')
        with self.assertRaises(OperationError):self.manager.repair_preferences('a',True)
    def test_repair_rejects_active_service_without_touching_json(self):
        path=self.manager.settings.path('a');path.write_text('{bad')
        with patch.object(self.manager,'properties',return_value={'ActiveState':'active'}):
            with self.assertRaises(OperationError):self.manager.repair_preferences('a',True)
        self.assertEqual(path.read_text(),'{bad')
    def test_repair_rejects_pending_cache(self):
        path=self.manager.settings.path('a');path.write_text('{bad')
        with patch.object(self.manager,'ensure_no_dirty_cache',side_effect=OperationError('uploads_pending')):
            with self.assertRaises(OperationError):self.manager.repair_preferences('a',True)
        self.assertEqual(path.read_text(),'{bad')
    def test_repair_launcher_failure_restores_original(self):
        path=self.manager.settings.path('a');path.write_bytes(b'{bad')
        with patch('drive_manager.service.autostart.update',side_effect=OSError()):
            with self.assertRaises(OperationError):self.manager.repair_preferences('a',True)
        self.assertEqual(path.read_bytes(),b'{bad')
    def orphan(self):
        _,target=self.manager.identity('a');mounts=[Mount(str(target),'a:','fuse.rclone')];self.manager.mounts=lambda:mounts
        return target,mounts
    def test_orphan_recovery_uses_only_normal_unmount_after_confirmation(self):
        target,mounts=self.orphan();original=self.manager.runner.run
        def run(args):
            if args[0]=='fusermount3':mounts.clear();return ''
            return original(args)
        with patch.object(self.manager.runner,'run',side_effect=run) as calls,patch('drive_manager.mounts.disconnected',return_value=True),patch('drive_manager.transfers.ensure_closed'):
            self.assertEqual(self.manager.recover_mount('a',True).state,'unmounted')
        self.assertIn(['fusermount3','-u','--',str(target)],[c.args[0] for c in calls.call_args_list])
        self.assertFalse(any(c.args[0][0]=='systemctl' and 'stop' in c.args[0] for c in calls.call_args_list))
    def test_healthy_or_foreign_mount_recovery_rejected(self):
        self.orphan()
        with patch('drive_manager.mounts.disconnected',return_value=False):
            with self.assertRaises(OperationError):self.manager.recover_mount('a',True)
        self.manager.mounts=lambda:[Mount(str(self.manager.identity('a')[1]),'foreign:','fuse.rclone')]
        with self.assertRaises(OperationError):self.manager.recover_mount('a',True)
    def test_recovery_rejects_active_service_and_no_confirmation(self):
        self.orphan()
        with self.assertRaises(OperationError):self.manager.recover_mount('a')
        with patch.object(self.manager,'properties',return_value={'ActiveState':'active'}):
            with self.assertRaises(OperationError):self.manager.recover_mount('a',True)
    def test_provider_refresh_uses_one_external_metadata_query(self):
        manager=Manager(Mock(),self.home,lambda:[]);manager.runner.run.return_value='[{"name":"external1:","type":"drive"},{"name":"external2:","type":"dropbox"}]'
        types=manager.provider_types(['external1','external2']);self.assertEqual(types,{'external1':'drive','external2':'dropbox'})
        manager.runner.run.assert_called_once_with(['rclone','listremotes','--json'])
    def test_writable_status_reuses_one_vfs_stats_query(self):
        target,mounts=self.orphan();endpoint=self.manager.rc_endpoint('a');endpoint.parent.mkdir(parents=True);endpoint.touch()
        props={'ActiveState':'active','Description':'Drive Manager read-write mount v1','ExecStart':'--vfs-cache-mode=full --rc-addr=unix://test'}
        vfs={'diskCache':{'uploadsQueued':2,'uploadsInProgress':0,'erroredFiles':0,'outOfSpace':False}}
        with patch.object(self.manager,'properties',return_value=props),patch('drive_manager.transfers.request',side_effect=[vfs,{'transferring':[]}]) as request:
            status=self.manager.status('a')
        self.assertEqual(status.pending,2);self.assertEqual([c.args[1] for c in request.call_args_list],['vfs/stats','core/stats'])
    def test_cleanup_requires_confirmation_and_unchanged_test_content(self):
        name='DriveManager-test-'+('a'*32)+'.txt';folder=self.home/'Drives/a';folder.mkdir(parents=True);path=folder/name
        path.write_bytes(('Drive Manager disposable acceptance test\n'+name+'\n').encode())
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)):
            self.assertEqual(cleanup_test(self.manager,'a',name).state,'validation_confirm');self.assertTrue(path.exists())
            self.assertEqual(cleanup_test(self.manager,'a',name,True).state,'validation_cleanup_requested');self.assertFalse(path.exists())
    def test_cleanup_preserves_modified_or_arbitrary_files(self):
        name='DriveManager-test-'+('a'*32)+'.txt';folder=self.home/'Drives/a';folder.mkdir(parents=True);path=folder/name;path.write_text('user changes')
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)):
            self.assertEqual(cleanup_test(self.manager,'a',name,True).state,'validation_error');self.assertTrue(path.exists())
            self.assertEqual(cleanup_test(self.manager,'a','ordinary.txt',True).state,'validation_error')
