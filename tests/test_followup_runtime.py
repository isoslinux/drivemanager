from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock,patch
from threading import Event,Timer
from types import SimpleNamespace
import json,sys,time
import test_bulk as fixtures
from drive_manager import test_files,validation
from drive_manager.service import Status,Manager
from drive_manager.app import Window
from drive_manager.mounts import Mount
from drive_manager.process import OperationError

class RuntimeFollowupTests(TestCase):
    setUp=fixtures.BulkTests.setUp
    def test_dead_mount_recovery_preserves_dirty_cache(self):
        _,target=self.manager.identity('a');mounts=[Mount(str(target),'a:','fuse.rclone')];self.manager.mounts=lambda:mounts
        cache=self.manager.write_cache_path('a')/'vfsMeta';cache.mkdir(parents=True);dirty=cache/'pending';dirty.write_bytes(b'{"Dirty":true}')
        original=self.manager.runner.run
        def run(args):
            if args[0]=='fusermount3':mounts.clear();return ''
            return original(args)
        with patch.object(self.manager.runner,'run',side_effect=run),patch('drive_manager.mounts.disconnected',return_value=True),patch('drive_manager.transfers.ensure_closed'),patch.object(self.manager,'ensure_no_dirty_cache',side_effect=AssertionError('must preserve rather than reject cache')):
            self.manager.recover_mount('a',True)
        self.assertEqual(dirty.read_bytes(),b'{"Dirty":true}')
    def test_full_disk_is_unknown_even_with_auth_or_network_error(self):
        _,target=self.manager.identity('a');self.manager.mounts=lambda:[Mount(str(target),'a:','fuse.rclone')]
        endpoint=self.manager.rc_endpoint('a');endpoint.parent.mkdir(parents=True);endpoint.touch()
        props={'ActiveState':'active','Description':'Drive Manager read-write mount v1','ExecStart':'--vfs-cache-mode=full --rc-addr=unix://test'}
        vfs={'diskCache':{'uploadsQueued':0,'uploadsInProgress':0,'erroredFiles':0,'outOfSpace':True}}
        for error in ['authentication 401','network is unreachable']:
            with patch.object(self.manager,'properties',return_value=props),patch('drive_manager.transfers.request',side_effect=[vfs,{'lastError':error}]):status=self.manager.status('a')
            self.assertEqual(status.pending,-1);self.assertTrue(status.progress.out_of_space)
    def test_poll_labels_systemd_failure_as_unavailable(self):
        accounts=Mock();accounts.currentText.return_value='a';accounts.rowCount.return_value=1;accounts.item.return_value.text.return_value='a'
        manager=Mock();manager.provider_types.return_value={'a':'drive'};manager.status.side_effect=OperationError('systemctl failure')
        owner=SimpleNamespace(last_error=False,accounts=accounts,manager=manager,show_accounts=Mock())
        owner.submit=lambda task,callback,**kwargs:callback(task())
        Window.poll(owner);self.assertEqual(owner.show_accounts.call_args.args[0][0][2].state,'status_unavailable')
    def test_registry_survives_new_manager_and_keeps_multiple_files(self):
        names=['DriveManager-test-'+c*32+'.txt' for c in ['a','b']];test_files.add(self.manager,'a',names)
        another=Manager(self.manager.runner,self.home,lambda:[])
        self.assertEqual(test_files.read(another,'a'),names);self.assertEqual(test_files.path(another,'a').stat().st_mode&0o777,0o600)
        self.assertEqual(test_files.read(another,'b'),[])
    def test_registry_rejects_symlink_and_nonfixture_names(self):
        with self.assertRaises(OperationError):test_files.add(self.manager,'a',['normal.txt'])
        path=test_files.path(self.manager,'a');outside=self.home/'outside';outside.write_text('[]');path.symlink_to(outside)
        with self.assertRaises(OperationError):test_files.read(self.manager,'a')
    def test_discovery_recovers_old_names_but_not_arbitrary_files(self):
        name='DriveManager-test-'+('a'*32)+'.txt'
        with patch('drive_manager.validation.bounded_output',return_value=('operation_finished',(name+'\nnormal.txt\n../DriveManager-test-'+('b'*32)+'.txt\n').encode())):
            result=validation.discover_test_files(self.manager,'a',Event())
        self.assertEqual(result.state,'validation_discovered');self.assertEqual(test_files.read(self.manager,'a'),[name])
    def test_cancelled_discovery_does_not_write_registry(self):
        with patch('drive_manager.validation.bounded_output',return_value=('connection_cancelled',None)):
            result=validation.discover_test_files(self.manager,'a',Event())
        self.assertEqual(result.state,'connection_cancelled');self.assertEqual(test_files.read(self.manager,'a'),[])
    def test_cleanup_cancel_before_start_does_not_read_mount(self):
        event=Event();event.set();name='DriveManager-test-'+('a'*32)+'.txt'
        with patch('drive_manager.validation.bounded_output') as child:
            self.assertEqual(validation.cleanup_test(self.manager,'a',name,True,event).state,'connection_cancelled')
        child.assert_not_called()
    def test_cleanup_verify_phase_does_not_hold_global_lock(self):
        name='DriveManager-test-'+('a'*32)+'.txt';status=Status('mounted',str(self.home/'Drives/a'),True,True,0)
        def probe(args,event):
            with self.manager.lock():pass
            return 'validation_timeout',None
        with patch.object(self.manager,'status',return_value=status),patch('drive_manager.validation.bounded_output',side_effect=probe):
            result=validation.cleanup_test(self.manager,'a',name,True,Event())
        self.assertEqual(result.state,'validation_timeout')
    def test_bounded_child_timeout_and_cancellation_return_promptly(self):
        args=[sys.executable,'-c','import time;time.sleep(10)']
        start=time.monotonic();state,_=validation.bounded_output(args,Event(),limit=.15)
        self.assertEqual(state,'validation_timeout');self.assertLess(time.monotonic()-start,2)
        cancel=Event();timer=Timer(.15,cancel.set);timer.start()
        try:
            start=time.monotonic();state,_=validation.bounded_output(args,cancel)
            self.assertEqual(state,'connection_cancelled');self.assertLess(time.monotonic()-start,2)
        finally:timer.join()
    def test_successful_cleanup_removes_only_selected_registry_entry(self):
        names=['DriveManager-test-'+c*32+'.txt' for c in ['a','b']];test_files.add(self.manager,'a',names)
        folder=self.home/'Drives/a';folder.mkdir(parents=True)
        for name in names:(folder/name).write_text('Drive Manager disposable acceptance test\n'+name+'\n')
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)):
            result=validation.cleanup_test(self.manager,'a',names[0],True,Event())
        self.assertEqual(result.state,'validation_cleanup_requested');self.assertEqual(test_files.read(self.manager,'a'),[names[1]])
        self.assertTrue((folder/names[1]).exists());self.assertFalse((folder/names[0]).exists())
