from dataclasses import replace
from pathlib import Path
from threading import Event
import json,tempfile,unittest
from unittest.mock import patch,Mock
from drive_manager.service import Manager,Status
from drive_manager.settings import Preferences
from drive_manager import portable,performance,validation
from drive_manager.connectivity import Result
from drive_manager.process import OperationError
from test_accounts import AccountRunner

class BulkTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name);self.manager=Manager(AccountRunner(),self.home,lambda:[])
        for name in ['a','b']:
            config=self.manager.accounts.path(name);config.parent.mkdir(parents=True,exist_ok=True)
            config.write_text('['+name+']\ntype=drive\nscope=drive\ntoken=NEVER_LEAK\n')
            self.manager.settings.save(name,Preferences(str(self.home/'Drives'/name)))
        self.file=self.home/'export.json'

    def exported(self):portable.export(self.manager,self.file);return json.loads(self.file.read_text())
    def update_export(self,callback):
        data=self.exported();callback(data);self.file.write_text(json.dumps(data))

    def test_old_preferences_get_unlimited_default_limits(self):
        path=self.manager.settings.path('a');path.write_text('{"mount_path":"","writable":false}')
        prefs=self.manager.settings.load('a');self.assertEqual((prefs.upload_kib,prefs.download_kib),(0,0))

    def test_invalid_limits_rejected(self):
        for value in [True,-1,'100',1048577]:
            with self.assertRaises(OperationError):self.manager.settings.validate(Preferences(upload_kib=value))

    def test_independent_limits_reach_mount_and_keep_readonly(self):
        prefs=Preferences(str(self.home/'Drives/a'),upload_kib=256,download_kib=1024)
        self.manager.settings.save('a',prefs)
        with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'):self.manager.mount('a')
        command=next(c for c in self.manager.runner.calls if c[0]=='systemd-run')
        self.assertIn('--bwlimit=256k:1024k',command);self.assertIn('--read-only',command)
        self.assertEqual(self.manager.settings.load('b').upload_kib,0)

    def test_export_is_private_portable_and_has_no_secrets(self):
        data=self.exported();text=self.file.read_text()
        self.assertNotIn('NEVER_LEAK',text);self.assertNotIn(str(self.home),text)
        self.assertEqual(data['accounts'][0]['preferences']['mount_path'],'Drives/a')
        self.assertEqual(self.file.stat().st_mode & 0o777,0o600)

    def test_export_does_not_overwrite_runtime_configuration(self):
        with self.assertRaises(OperationError):portable.export(self.manager,self.manager.settings.path('a'))
        with self.assertRaises(OperationError):portable.export(self.manager,self.home/'wrong.conf')

    def test_import_requires_confirmation(self):
        self.exported()
        with self.assertRaises(OperationError):portable.apply(self.manager,self.file)

    def test_import_updates_preferences_without_touching_credentials(self):
        credentials=self.manager.accounts.path('a').read_bytes()
        self.update_export(lambda data:data['accounts'][0]['preferences'].update(upload_kib=200))
        rows=portable.plan(self.manager,self.file)
        portable.apply(self.manager,self.file,True,reviewed=rows)
        self.assertEqual(self.manager.settings.load('a').upload_kib,200)
        self.assertEqual(self.manager.accounts.path('a').read_bytes(),credentials)
        self.assertFalse(any('stop' in call or call[0]=='systemd-run' for call in self.manager.runner.calls))

    def test_import_rebases_mount_folder_on_another_computer(self):
        self.exported()
        with tempfile.TemporaryDirectory() as newhome:
            manager=Manager(AccountRunner(),newhome,lambda:[])
            for name in ['a','b']:
                config=manager.accounts.path(name);config.parent.mkdir(parents=True,exist_ok=True)
                config.write_text('['+name+']\ntype=drive\n')
            rows=portable.plan(manager,self.file)
            self.assertEqual(rows[0][2].mount_path,str(Path(newhome)/'Drives/a'))

    def test_unknown_secret_fields_and_duplicates_are_rejected(self):
        for mutate in [lambda data:data.update(token='SECRET'),
                       lambda data:data['accounts'][0]['preferences'].update(token='SECRET'),
                       lambda data:data['accounts'].append(data['accounts'][0]),
                       lambda data:data['accounts'][0].update(provider='s3')]:
            self.update_export(mutate)
            with self.assertRaises(OperationError):portable.plan(self.manager,self.file)

    def test_traversal_and_absolute_paths_rejected(self):
        for value in ['../outside','/etc','Drives/../../outside','.config/rclone']:
            self.update_export(lambda data:data['accounts'][0]['preferences'].update(mount_path=value))
            with self.assertRaises(OperationError):portable.plan(self.manager,self.file)

    def test_reviewed_file_cannot_change_before_apply(self):
        data=self.exported();review=portable.plan(self.manager,self.file)
        data['accounts'][0]['preferences']['writable']=True;self.file.write_text(json.dumps(data))
        with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True,reviewed=review)
        self.assertFalse(self.manager.settings.load('a').writable)

    def test_mounted_import_rejected_before_any_changes(self):
        self.exported();before=self.manager.settings.path('a').read_bytes()
        with patch.object(self.manager,'status',return_value=Status('mounted','/folder',True)):
            with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True)
        self.assertEqual(self.manager.settings.path('a').read_bytes(),before)

    def test_dirty_cache_blocks_import(self):
        self.exported();root=self.manager.write_cache_path('a')/'vfsMeta/a';root.mkdir(parents=True)
        (root/'pending').write_text('{"Dirty":true}')
        with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True)
        self.assertTrue((root/'pending').exists())

    def test_late_import_failure_rolls_back_every_preference(self):
        self.update_export(lambda data:data['accounts'][0]['preferences'].update(cache_gib=10))
        originals={name:self.manager.settings.path(name).read_bytes() for name in ['a','b']}
        with patch('drive_manager.portable.autostart.update',side_effect=OperationError('FAIL')):
            with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True)
        for name,value in originals.items():self.assertEqual(value,self.manager.settings.path(name).read_bytes())

    def test_setup_marker_private_and_explicit(self):
        self.assertFalse(portable.setup_done(self.manager));portable.finish_setup(self.manager)
        self.assertTrue(portable.setup_done(self.manager))
        self.assertEqual((self.home/'.config/drive-manager/setup.json').stat().st_mode & 0o777,0o600)

    def test_cache_health_retains_dirty_data_and_detects_low_space(self):
        root=self.manager.write_cache_path('a')/'vfsMeta/a';root.mkdir(parents=True)
        file=root/'pending';file.write_text('{"Dirty":true}')
        with patch('drive_manager.performance.shutil.disk_usage',return_value=Mock(free=100)):
            result=performance.inspect(self.manager,'a')
        self.assertEqual(result.pending,1);self.assertTrue(result.low);self.assertTrue(file.exists())

    def test_malformed_cache_never_assumed_clean(self):
        root=self.manager.write_cache_path('a')/'vfsMeta/a';root.mkdir(parents=True)
        (root/'bad').write_text('PRIVATE_DATA')
        result=performance.inspect(self.manager,'a');self.assertIsNone(result.pending)
        self.assertNotIn('PRIVATE_DATA',repr(result))

    def test_slow_read_is_advisory_not_an_error(self):
        self.assertTrue(performance.slow(Result('connection_ok',6)))
        self.assertFalse(performance.slow(Result('connection_error',6)))
        self.assertFalse(performance.slow(Result('connection_ok',1)))

    def test_browse_measurement_uses_readonly_children(self):
        folder=self.home/'measure';folder.mkdir();(folder/'PRIVATE_NAME').mkdir()
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True)):
            result=performance.browse(self.manager,'a')
        self.assertIsNotNone(result.listing);self.assertIsNotNone(result.space)
        self.assertNotIn('PRIVATE_NAME',repr(result));self.assertTrue((folder/'PRIVATE_NAME').exists())

    def test_batch_validation_cancels_and_never_mounts(self):
        cancel=Event();observed=[]
        with patch('drive_manager.validation.check',return_value=Result('connection_ok',1)):
            rows=validation.read_all(self.manager,cancel,observed.append)
        self.assertEqual(len(rows),2);self.assertEqual(observed,rows)
        cancel.set();self.assertEqual(validation.read_all(self.manager,cancel),[])
        self.assertFalse(any(c[0]=='systemd-run' or 'stop' in c for c in self.manager.runner.calls))

    def test_write_without_confirmation_creates_nothing(self):
        result=validation.write_test(self.manager,'a',Event())
        self.assertEqual(result.state,'validation_confirm')
        self.assertFalse(list(self.home.rglob('DriveManager-test-*')))

    def test_write_requires_managed_writable_clean_mount(self):
        for status in [Status('external',str(self.home),False,True),Status('mounted',str(self.home),True,False),Status('mounted',str(self.home),True,True,1)]:
            with patch.object(self.manager,'status',return_value=status):
                self.assertEqual(validation.write_test(self.manager,'a',Event(),True).state,'validation_write_requires')
        self.assertFalse(list(self.home.glob('DriveManager-test-*')))

    def test_write_reads_back_from_remote_and_keeps_only_new_test_file(self):
        folder=self.home/'mounted';folder.mkdir();(folder/'keep.txt').write_text('IMPORTANT')
        def read(manager,remote,name,cancel):return (folder/name).read_bytes()
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)),patch('drive_manager.validation.transfers.pending',return_value=0),patch('drive_manager.validation.remote_bytes',side_effect=read):
            result=validation.write_test(self.manager,'a',Event(),True)
        self.assertEqual(result.state,'validation_write_ok');self.assertTrue((folder/result.file).exists())
        self.assertEqual((folder/'keep.txt').read_text(),'IMPORTANT')

    def test_reconnect_requires_confirmation_and_never_touches_foreign_mount(self):
        with patch.object(self.manager,'unmount') as stop:
            with self.assertRaises(OperationError):validation.reconnect(self.manager,'a')
            with self.assertRaises(OperationError):validation.reconnect(self.manager,'a',True)
            stop.assert_not_called()

    def test_reconnect_uses_existing_guarded_manager_operations(self):
        status=Status('mounted','/folder',True)
        with patch.object(self.manager,'status',return_value=status),patch.object(self.manager,'unmount') as stop,patch.object(self.manager,'mount',return_value=status) as mount:
            self.assertEqual(validation.reconnect(self.manager,'a',True),status)
        stop.assert_called_once_with('a',confirmed=True);mount.assert_called_once_with('a')

    @unittest.skipUnless(__import__('os').environ.get('QT_QPA_PLATFORM')=='offscreen','Offscreen Qt required')
    def test_ui_setup_and_live_validation_translate_without_claiming_missing_providers(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer,QEventLoop
        from drive_manager.app import Window
        from drive_manager.quota import Quota
        app=QApplication.instance() or QApplication([])
        with patch('drive_manager.app.Manager',return_value=self.manager),patch('drive_manager.quota.read_quota',return_value=Quota()),patch('drive_manager.validation.check',return_value=Result('connection_ok',6)):
            window=Window()
            try:
                loop=QEventLoop();QTimer.singleShot(650,loop.quit);loop.exec()
                window.setup_guide();self.assertTrue(window.setup_dialog.isVisible())
                window.validation_panel();self.assertEqual(window.validation_table.rowCount(),6)
                window.start_validation('read')
                loop=QEventLoop();QTimer.singleShot(400,loop.quit);loop.exec()
                self.assertEqual(len(window.validation_rows),2)
                self.assertEqual(window.validation_table.rowCount(),7)
                for language in ['en','es','fr','de']:
                    window.language_selector.setCurrentIndex(window.language_selector.findData(language))
                    self.assertEqual(window.validation_dialog.windowTitle(),window.t['validate_all'])
                    self.assertEqual(window.validation_table.horizontalHeaderItem(2).text(),window.t['validation_read'])
                    self.assertEqual(window.setup_dialog.windowTitle(),window.t['setup_guide'])
                states=[window.validation_table.item(row,2).text() for row in range(window.validation_table.rowCount())]
                self.assertEqual(sum(value==window.t['validation_unchecked'] for value in states),5)
                self.assertTrue(any(window.t['cloud_slow'] in value for value in states))
                window.setup_actions['setup_finish'].click();self.assertTrue(portable.setup_done(self.manager))
            finally:
                if window.validation_dialog:window.validation_dialog.reject()
                if getattr(window,'setup_dialog',None):window.setup_dialog.hide()
                window.timer.stop();window.validation_cancel.set();window.connection_cancel.set()
                for pool in [window.health_pool,window.validation_pool,window.connection_pool,window.pool,window.quota_pool,window.update_pool]:pool.shutdown()
                window.tray.hide();window.hide()

    @unittest.skipUnless(__import__('os').environ.get('QT_QPA_PLATFORM')=='offscreen','Offscreen Qt required')
    def test_ui_speed_controls_save_independent_limits(self):
        from PySide6.QtWidgets import QApplication,QSpinBox
        from PySide6.QtCore import QTimer,QEventLoop
        from drive_manager.app import Window
        from drive_manager.quota import Quota
        app=QApplication.instance() or QApplication([])
        with patch('drive_manager.app.Manager',return_value=self.manager),patch('drive_manager.quota.read_quota',return_value=Quota()):
            window=Window()
            try:
                loop=QEventLoop();QTimer.singleShot(650,loop.quit);loop.exec()
                def accept():
                    dialog=app.activeModalWidget();spins=dialog.findChildren(QSpinBox)
                    self.assertEqual(len(spins),4);spins[2].setValue(100);spins[3].setValue(500);dialog.accept()
                with patch.object(window,'save_account_preferences') as save:
                    QTimer.singleShot(0,accept);window.settings_dialog(self.manager.settings.load('a'))
                    prefs=save.call_args.args[1];self.assertEqual((prefs.upload_kib,prefs.download_kib),(100,500))
            finally:
                window.timer.stop();window.validation_cancel.set();window.connection_cancel.set()
                for pool in [window.health_pool,window.validation_pool,window.connection_pool,window.pool,window.quota_pool,window.update_pool]:pool.shutdown()
                window.tray.hide();window.hide()

    def test_browse_unmounted_account_does_not_start_children(self):
        with patch('drive_manager.performance.subprocess.Popen') as start:
            self.assertEqual(performance.browse(self.manager,'a'),performance.BrowseTiming());start.assert_not_called()

    def test_missing_account_import_rejected(self):
        self.update_export(lambda data:data['accounts'][0].update(name='missing'))
        with self.assertRaises(OperationError):portable.plan(self.manager,self.file)

    def test_symlink_export_and_import_rejected(self):
        original=self.home/'original.json';original.write_text('PRIVATE');self.file.symlink_to(original)
        with self.assertRaises(OperationError):portable.export(self.manager,self.file)
        with self.assertRaises(OperationError):portable.plan(self.manager,self.file)
        self.assertEqual(original.read_text(),'PRIVATE')

    def test_cancelled_reconnect_never_stops_a_service(self):
        cancel=Event();cancel.set()
        with patch.object(self.manager,'unmount') as stop:
            with self.assertRaises(OperationError):validation.reconnect(self.manager,'a',True,cancel)
            stop.assert_not_called()

    def test_non_directory_metadata_is_unknown_and_blocks_changes(self):
        root=self.manager.write_cache_path('a');root.mkdir(parents=True)
        (root/'vfsMeta').write_text('PENDING_DATA')
        self.assertIsNone(performance.inspect(self.manager,'a').pending)
        with self.assertRaises(OperationError):self.manager.ensure_no_dirty_cache('a')

    def test_overlap_import_rolls_back_the_first_account(self):
        self.update_export(lambda data:[row['preferences'].update(mount_path='Shared') for row in data['accounts']])
        before={name:self.manager.settings.path(name).read_bytes() for name in ['a','b']}
        with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True)
        for name,value in before.items():self.assertEqual(self.manager.settings.path(name).read_bytes(),value)

    def test_import_cannot_grant_oauth_write_without_scope(self):
        self.manager.accounts.path('a').write_text('[a]\ntype=drive\nscope=drive.readonly\n')
        self.update_export(lambda data:data['accounts'][0]['preferences'].update(writable=True))
        with self.assertRaises(OperationError):portable.apply(self.manager,self.file,True)
        self.assertFalse(self.manager.settings.load('a').writable)
