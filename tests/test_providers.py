"""Synthetic registrations: no OAuth consent, real credentials or cloud services."""
import configparser
import json
from pathlib import Path
import subprocess
from threading import Event
import tempfile
import unittest
from unittest.mock import patch
from drive_manager import credentials, internxt
from drive_manager.accounts import Accounts
from drive_manager.providers import ACTIVE_TYPES, Registration
from drive_manager.process import OperationError
from drive_manager.remotes import discover
from drive_manager.service import Manager
from drive_manager.settings import Preferences
from test_accounts import AccountRunner

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.manager = Manager(AccountRunner(), self.temp.name, lambda: [])

    def test_metadata_discovery_includes_new_file_backends_only(self):
        class Runner:
            def run(self, args):
                return json.dumps([{'name':p, 'type':p, 'source':'file'} for p in ACTIVE_TYPES]
                    + [{'name':'environment','type':'dropbox','source':'environment'},
                       {'name':'other','type':'s3','source':'file'}])
        self.assertEqual(set(discover(Runner())), ACTIVE_TYPES)

    def test_https_url_validation_prevents_embedded_secrets(self):
        good='https://cloud.example/remote.php/dav/files/user/'
        self.assertEqual(credentials.webdav_url(good),good)
        for value in ['http://cloud.example/', 'https://user:SECRET@cloud.example/',
                      'https://cloud.example/?token=SECRET', 'https://cloud.example/#SECRET',
                      'https://', 'https://cloud.example:bad/', 'https://cloud.example/ bad']:
            with self.subTest(value=value), self.assertRaises(OperationError) as error:
                credentials.webdav_url(value)
            self.assertNotIn('SECRET',str(error.exception))

    def test_nextcloud_parameters_use_vendor_and_app_password(self):
        with patch('drive_manager.credentials.encrypted_authorize') as stage:
            credentials.authorize(self.manager.accounts,'nc','webdav',' user ','SECRET',Event(),url='https://cloud.example/dav/')
        self.assertEqual(stage.call_args.kwargs['parameters'],
            {'url':'https://cloud.example/dav/','vendor':'nextcloud','user':'user','pass':'SECRET'})

    def test_proton_uses_current_rclone_option_names(self):
        with patch('drive_manager.credentials.encrypted_authorize') as stage:
            credentials.authorize(self.manager.accounts,'proton','protondrive','me','SECRET',Event(),code='012345',mailbox_password='MAILBOX')
        self.assertEqual(stage.call_args.kwargs['parameters'],
            {'username':'me','password':'SECRET','2fa':'012345','mailbox_password':'MAILBOX','enable_caching':'false'})

    def test_invalid_inputs_never_open_wallet(self):
        event=Event();event.set()
        with patch('drive_manager.credentials.encrypted_authorize') as stage:
            for args,options in [(('nc','webdav','me','SECRET',Event()),{'url':'http://cloud.example/'}),
                                 (('p','protondrive','me','SECRET',event),{}),
                                 (('p','protondrive','','SECRET',Event()),{})]:
                with self.assertRaises(OperationError): credentials.authorize(self.manager.accounts,*args,**options)
            stage.assert_not_called()

    def test_browser_registration_dispatches_dropbox(self):
        def auth(remote,cancel,on_url,writable,provider):
            self.assertEqual(provider,'dropbox')
            path=self.manager.accounts.folder/'.oauth-test.tmp';path.parent.mkdir(parents=True)
            path.write_text('['+remote+']\ntype=dropbox\ntoken=PRIVATE\n');return path
        with patch.object(self.manager.accounts,'authorize',side_effect=auth):
            name,path=self.manager.begin_authorization(Event(),lambda url:None,'dropbox',writable=True)
        self.assertTrue(name.startswith('dropbox_'));self.assertTrue(path.exists())

    def test_dropbox_oauth_command_has_no_google_scope(self):
        class Process:
            stdout=None;returncode=0
            def poll(self): return 0
        def start(args,**options):
            self.assertIn('dropbox',args);self.assertNotIn('scope=drive.readonly',args)
            self.assertIn('config_auth_no_browser=true',args)
            path=Path(next(a.split('=',1)[1] for a in args if a.startswith('--config=')))
            path.write_text('[db]\ntype=dropbox\ntoken=PRIVATE\n');return Process()
        with patch('subprocess.Popen',side_effect=start):
            path=self.manager.accounts.authorize('db',Event(),lambda url:None,provider='dropbox')
        self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def simulate_encrypted(self,provider,failure=False,cancel_after_auth=False):
        cancel=Event(); commands=[]
        class Process:
            def poll(self): return None
            def terminate(self): pass
            def wait(self,timeout=None): return 0
        def encrypt(args,**options):
            commands.append(args)
            self.assertEqual(options['stderr'],subprocess.DEVNULL)
            path=Path(next(a.split('=',1)[1] for a in args if a.startswith('--config=')))
            path.write_text('RCLONE_ENCRYPT_V0:\nCIPHERTEXT');return subprocess.CompletedProcess(args,0)
        def start(args,**options):
            commands.append(args)
            endpoint=Path(next(a.split('unix://',1)[1] for a in args if a.startswith('--rc-addr=')))
            endpoint.touch();self.assertEqual(options['stdout'],subprocess.DEVNULL);return Process()
        def request(endpoint,method,body):
            self.assertEqual(endpoint.stat().st_mode & 0o777,0o600)
            if method=='config/create':
                self.assertEqual(body['type'],provider);self.assertTrue(body['opt']['obscure'])
                self.assertTrue(any(self.manager.accounts.encrypted(p) for p in self.manager.accounts.folder.glob('.oauth-*')))
                return {}
            self.assertEqual(method,'operations/list')
            if failure: raise OperationError('credentials_error')
            if cancel_after_auth:cancel.set()
            return {'list':[]}
        with patch('drive_manager.internxt.Wallet.ensure'),patch('subprocess.run',side_effect=encrypt),patch('subprocess.Popen',side_effect=start),patch('drive_manager.internxt.request',side_effect=request) as rpc:
            if failure or cancel_after_auth:
                with self.assertRaises(OperationError):
                    credentials.authorize(self.manager.accounts,'account',provider,'me','SECRET',cancel,url='https://cloud.example/dav/')
                self.assertEqual(list(self.manager.accounts.folder.glob('.oauth-*')),[])
                return
            registration=credentials.authorize(self.manager.accounts,'account',provider,'me','SECRET',cancel,url='https://cloud.example/dav/')
            self.assertEqual(rpc.call_count,2)
        self.assertNotIn('SECRET',str(commands));self.assertNotIn('me', ' '.join(commands[-1]))
        prefs=Preferences(str(Path(self.temp.name)/'Cloud'))
        self.manager.add_account('account',prefs,Event(),registration=registration)
        self.assertEqual(self.manager.discover_accounts(),['account'])
        self.assertEqual(self.manager.provider_of('account'),provider)
        self.assertEqual(self.manager.accounts.path('account').stat().st_mode & 0o777,0o600)
        with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'),patch('drive_manager.wallet.Wallet.ensure'):
            self.manager.mount('account')
        command=next(c for c in self.manager.runner.calls if c[0]=='systemd-run')
        self.assertIn('--read-only',command)
        if provider=='protondrive': self.assertIn('--protondrive-enable-caching=false',command)

    def test_nextcloud_encrypted_registration_and_mount(self):self.simulate_encrypted('webdav')
    def test_proton_encrypted_registration_and_mount(self):self.simulate_encrypted('protondrive')
    def test_authentication_failure_removes_staged_secrets(self):self.simulate_encrypted('protondrive',failure=True)
    def test_cancel_after_authentication_removes_staged_secrets(self):self.simulate_encrypted('webdav',cancel_after_auth=True)

    def test_corrupt_encrypted_provider_metadata_rejected(self):
        path=self.manager.accounts.path('cloud');path.parent.mkdir(parents=True)
        path.write_text('RCLONE_ENCRYPT_V0:\nCIPHERTEXT')
        self.manager.accounts.metadata_path('cloud').write_text('{"name":"cloud","type":"s3"}')
        with self.assertRaises(OperationError):self.manager.discover_accounts()
        with self.assertRaises(OperationError):self.manager.provider_of('cloud')

    def test_dropbox_mount_waits_for_batch_commit(self):
        path=self.manager.accounts.path('db');path.parent.mkdir(parents=True)
        path.write_text('[db]\ntype=dropbox\ntoken=PRIVATE\nbatch_mode=async\n')
        self.manager.settings.save('db',Preferences(str(Path(self.temp.name)/'Dropbox'),writable=True))
        with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'):
            self.manager.mount('db')
        command=next(c for c in self.manager.runner.calls if c[0]=='systemd-run')
        self.assertIn('--dropbox-batch-mode=sync',command);self.assertNotIn('--read-only',command)

    def test_dropbox_reauthorization_keeps_folder_options(self):
        path=self.manager.accounts.path('db');path.parent.mkdir(parents=True)
        path.write_text('[db]\ntype=dropbox\ntoken=OLD\nroot_folder_id=KEEP\n')
        def auth(remote,*args,**kwargs):
            self.assertEqual(kwargs['provider'],'dropbox')
            staged=path.parent/'.oauth-renew.tmp';staged.write_text('[db]\ntype=dropbox\ntoken=NEW\n');return staged
        with patch.object(self.manager.accounts,'authorize',side_effect=auth):
            self.manager.reauthorize('db',Event(),lambda url:None,confirmed=True)
        parser=configparser.ConfigParser();parser.read(path)
        self.assertEqual(parser['db']['token'],'NEW');self.assertEqual(parser['db']['root_folder_id'],'KEEP')

    @unittest.skipUnless(__import__('os').environ.get('QT_QPA_PLATFORM')=='offscreen','Offscreen Qt required')
    def test_ui_routes_new_providers_and_cancels_credentials_dialog(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        from drive_manager.app import Window
        app=QApplication.instance() or QApplication([])
        with patch('drive_manager.app.Manager',return_value=self.manager):
            window=Window();window.timer.stop()
            try:
                with patch.object(window,'credentials_login') as login:
                    for provider in ['webdav','protondrive']:
                        window.provider.setCurrentIndex(window.provider.findData(provider));window.add_account()
                        self.assertEqual(login.call_args.args,(provider,))
                for provider in ['webdav','protondrive']:
                    with patch.object(self.manager,'begin_credentials') as begin:
                        QTimer.singleShot(0,lambda: app.activeModalWidget().reject())
                        window.credentials_login(provider);begin.assert_not_called()
            finally:
                window.timer.stop();window.pool.shutdown();window.quota_pool.shutdown();window.update_pool.shutdown()
                window.tray.hide();window.hide()
