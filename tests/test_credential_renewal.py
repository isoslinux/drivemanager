import json
from pathlib import Path
import subprocess
import tempfile
from threading import Event
import unittest
from unittest.mock import patch
from drive_manager.service import Manager,Status
from drive_manager.providers import Registration
from drive_manager.settings import Preferences
from drive_manager.process import OperationError
from drive_manager import internxt
from test_accounts import AccountRunner

class RenewalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.manager=Manager(AccountRunner(),self.temp.name,lambda:[])
        self.source=self.manager.accounts.path('cloud');self.source.parent.mkdir(parents=True)
        self.source.write_text('RCLONE_ENCRYPT_V0:\nOLD_CIPHERTEXT');self.source.chmod(0o600)
        self.meta=self.manager.accounts.metadata_path('cloud');self.meta.write_text(json.dumps({'name':'cloud','type':'protondrive'}))
        self.manager.settings.save('cloud',Preferences(str(Path(self.temp.name)/'Cloud'),writable=True))

    def staged(self,*args,**kwargs):
        path=self.source.parent/'.oauth-renew.tmp';path.write_text('RCLONE_ENCRYPT_V0:\nNEW_CIPHERTEXT')
        return Registration('cloud',path,'protondrive')

    def test_success_preserves_folder_preferences_metadata_and_cache(self):
        prefs=self.manager.settings.path('cloud').read_bytes();meta=self.meta.read_bytes()
        cache=self.manager.write_cache_path('cloud');cache.mkdir(parents=True);(cache/'local').write_text('CACHED')
        with patch('drive_manager.credentials.authorize',side_effect=self.staged) as login:
            self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
        self.assertIn('NEW_CIPHERTEXT',self.source.read_text())
        self.assertEqual(self.source.stat().st_mode & 0o777,0o600)
        self.assertEqual(prefs,self.manager.settings.path('cloud').read_bytes());self.assertEqual(meta,self.meta.read_bytes())
        self.assertEqual((cache/'local').read_text(),'CACHED')
        self.assertEqual(login.call_args.kwargs['existing'],self.source)
        self.assertFalse(any(c[0]=='systemd-run' or 'stop' in c for c in self.manager.runner.calls))

    def test_confirmation_required_before_authentication(self):
        with patch('drive_manager.credentials.authorize') as auth:
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event())
            auth.assert_not_called()

    def test_mounted_connection_never_stopped_or_reauthorized(self):
        with patch.object(self.manager,'status',return_value=Status('mounted','/cloud',True)),patch('drive_manager.credentials.authorize') as auth:
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
            auth.assert_not_called()
        self.assertFalse(any('stop' in c for c in self.manager.runner.calls))

    def test_pending_cache_blocks_authentication(self):
        root=self.manager.write_cache_path('cloud')/'vfsMeta/cloud';root.mkdir(parents=True)
        (root/'pending').write_text('{"Dirty":true}')
        with patch('drive_manager.credentials.authorize') as auth:
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
            auth.assert_not_called()

    def test_login_failure_preserves_original(self):
        original=self.source.read_bytes()
        with patch('drive_manager.credentials.authorize',side_effect=OperationError('credentials_error')):
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
        self.assertEqual(original,self.source.read_bytes())

    def test_cancellation_cleans_stage_and_preserves_original(self):
        cancel=Event();original=self.source.read_bytes()
        def auth(*args,**kwargs):result=self.staged();cancel.set();return result
        with patch('drive_manager.credentials.authorize',side_effect=auth):
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',cancel,confirmed=True)
        self.assertEqual(original,self.source.read_bytes());self.assertEqual(list(self.source.parent.glob('.oauth-*')),[])

    def test_concurrent_source_change_is_not_overwritten(self):
        def auth(*args,**kwargs):result=self.staged();self.source.write_text('RCLONE_ENCRYPT_V0:\nEXTERNAL_CHANGE');return result
        with patch('drive_manager.credentials.authorize',side_effect=auth):
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
        self.assertIn('EXTERNAL_CHANGE',self.source.read_text());self.assertEqual(list(self.source.parent.glob('.oauth-*')),[])

    def test_external_or_oauth_connection_is_outside_credential_renewal(self):
        self.source.write_text('[cloud]\ntype=drive\ntoken=PRIVATE\n')
        with patch('drive_manager.credentials.authorize') as auth:
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
            auth.assert_not_called()

    def exercise_backend(self,provider,mismatch=False):
        self.meta.write_text(json.dumps({'name':'cloud','type':provider}))
        previous={'type':provider,'description':'KEEP','password':'OLD_OBSCURED','mailbox_password':'OLD_OBSCURED','client_access_token':'OLD_TOKEN',
                  'username':'same','email':'same','user':'same','vendor':'nextcloud','url':'https://cloud.example/dav/'}
        class Process:
            def poll(self):return None
            def terminate(self):pass
            def wait(self,timeout=None):return 0
        def start(args,**kwargs):
            self.assertNotIn('NEW_SECRET',' '.join(args));self.assertEqual(kwargs['stdout'],subprocess.DEVNULL)
            endpoint=Path(next(a.split('unix://',1)[1] for a in args if a.startswith('--rc-addr=')));endpoint.touch();return Process()
        def rpc(endpoint,method,body):
            if method=='config/get':return dict(previous)
            if method=='config/create':
                params=body['parameters'];self.assertEqual(params['description'],'KEEP')
                self.assertNotIn('client_access_token',params);self.assertNotIn('mailbox_password',params)
                self.assertEqual(params['pass' if provider!='protondrive' else 'password'],'NEW_SECRET')
                self.assertEqual(params['username' if provider=='protondrive' else 'email' if provider=='internxt' else 'user'],'same')
            return {}
        field={'internxt':'email','webdav':'user','protondrive':'username'}[provider]
        params={field:'other' if mismatch else 'same','pass' if provider!='protondrive' else 'password':'NEW_SECRET'}
        if provider=='webdav':params.update(url=previous['url'],vendor='nextcloud')
        original=self.source.read_bytes()
        with patch('drive_manager.internxt.Wallet.ensure') as wallet,patch('subprocess.Popen',side_effect=start),patch('drive_manager.internxt.request',side_effect=rpc) as request:
            if mismatch:
                with self.assertRaises(OperationError) as error:
                    internxt.authorize(self.manager.accounts,'cloud','same','NEW_SECRET',Event(),lambda event:'',provider=provider,parameters=params,existing=self.source)
                self.assertEqual(str(error.exception),'credential_identity')
                self.assertEqual(list(self.source.parent.glob('.oauth-*')),[])
                self.assertEqual(request.call_count,1)
            else:
                registration=internxt.authorize(self.manager.accounts,'cloud','same','NEW_SECRET',Event(),lambda event:'',provider=provider,parameters=params,existing=self.source)
                self.assertTrue(self.manager.accounts.encrypted(registration[1]))
                self.assertEqual([c.args[1] for c in request.call_args_list],['config/get','config/delete','config/create','operations/list'])
            wallet.assert_not_called()
        self.assertEqual(original,self.source.read_bytes())

    def test_proton_fresh_login_clears_cached_tokens(self):self.exercise_backend('protondrive')
    def test_nextcloud_same_principal_and_options_preserved(self):self.exercise_backend('webdav')
    def test_internxt_fresh_login_and_root_access(self):self.exercise_backend('internxt')
    def test_different_identity_never_reaches_login(self):self.exercise_backend('protondrive',True)

    def test_changed_nextcloud_url_and_custom_credentials_rejected(self):
        for previous,params,key in [
            ({'type':'webdav','user':'same','url':'https://old.example/dav/','vendor':'nextcloud'}, {'user':'same','pass':'NEW_SECRET','url':'https://new.example/dav/','vendor':'nextcloud'},'credential_identity'),
            ({'type':'protondrive','username':'same','otp_secret_key':'SECRET'}, {'username':'same','password':'NEW_SECRET'},'credential_custom')]:
            provider=previous['type']
            class Process:
                def poll(self):return None
                def terminate(self):pass
                def wait(self,timeout=None):return 0
            def start(args,**kwargs):
                Path(next(a.split('unix://',1)[1] for a in args if a.startswith('--rc-addr='))).touch();return Process()
            with patch('subprocess.Popen',side_effect=start),patch('drive_manager.internxt.request',return_value=previous) as rpc:
                with self.assertRaises(OperationError) as error:
                    internxt.authorize(self.manager.accounts,'cloud','same','NEW_SECRET',Event(),lambda event:'',provider=provider,parameters=params,existing=self.source)
                self.assertEqual(str(error.exception),key);self.assertEqual(rpc.call_count,1)
            self.assertEqual(list(self.source.parent.glob('.oauth-*')),[])

    @unittest.skipUnless(__import__('os').environ.get('QT_QPA_PLATFORM')=='offscreen','Offscreen Qt required')
    def test_ui_routes_only_confirmed_encrypted_renewal(self):
        from PySide6.QtWidgets import QApplication,QMessageBox
        from PySide6.QtCore import QEventLoop,QTimer
        from drive_manager.app import Window
        from drive_manager.quota import Quota
        app=QApplication.instance() or QApplication([])
        with patch('drive_manager.app.Manager',return_value=self.manager),patch('drive_manager.quota.read_quota',return_value=Quota()):
            window=Window()
            try:
                loop=QEventLoop();QTimer.singleShot(650,loop.quit);loop.exec()
                self.assertTrue(window.buttons['renew_credentials'].isEnabled())
                self.assertFalse(window.buttons['reauth'].isEnabled())
                window.show_status(Status('mounted','/cloud',True))
                self.assertFalse(window.buttons['renew_credentials'].isEnabled())
                window.show_status(Status('unmounted','/cloud'))
                with patch('drive_manager.app.QMessageBox.question',return_value=QMessageBox.StandardButton.No),patch.object(window,'credentials_login') as form:
                    window.renew_account_credentials();form.assert_not_called()
                with patch('drive_manager.app.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes),patch.object(window,'credentials_login') as form:
                    window.renew_account_credentials();form.assert_called_once_with('protondrive',renewal='cloud')
                self.meta.write_text('{"name":"cloud","type":"internxt"}')
                with patch('drive_manager.app.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes),patch.object(window,'internxt_login') as form:
                    window.renew_account_credentials();form.assert_called_once_with(renewal='cloud')
            finally:
                window.timer.stop();window.connection_pool.shutdown();window.pool.shutdown();window.quota_pool.shutdown();window.update_pool.shutdown();window.tray.hide();window.hide()

    def test_cancel_before_authentication_never_opens_channel(self):
        cancel=Event();cancel.set()
        with patch('drive_manager.credentials.authorize') as auth:
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',cancel,confirmed=True)
            auth.assert_not_called()

    def test_new_dirty_cache_during_login_prevents_commit(self):
        original=self.source.read_bytes()
        def auth(*args,**kwargs):
            registration=self.staged()
            root=self.manager.write_cache_path('cloud')/'vfsMeta/cloud';root.mkdir(parents=True)
            (root/'late').write_text('{"Dirty":true}')
            return registration
        with patch('drive_manager.credentials.authorize',side_effect=auth):
            with self.assertRaises(OperationError):self.manager.renew_credentials('cloud','same','SECRET',Event(),confirmed=True)
        self.assertEqual(self.source.read_bytes(),original)
        self.assertEqual(list(self.source.parent.glob('.oauth-*')),[])
        self.assertTrue((self.manager.write_cache_path('cloud')/'vfsMeta/cloud/late').exists())
