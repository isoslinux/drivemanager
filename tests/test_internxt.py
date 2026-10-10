import json
from pathlib import Path
import subprocess
import tempfile
from threading import Event
import unittest
from unittest.mock import patch
from drive_manager.accounts import Accounts
from drive_manager.service import Manager
from drive_manager.settings import Preferences
from drive_manager.process import OperationError
from drive_manager.wallet import Wallet, PASSWORD_COMMAND
from drive_manager import internxt
from test_accounts import AccountRunner

class InternxtTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.manager=Manager(AccountRunner(),self.tmp.name,lambda:[])
    def test_encrypted_account_registration_discovery_mount_and_removal(self):
        folder=self.manager.accounts.folder;folder.mkdir(parents=True)
        staged=folder/'.oauth-encrypted.tmp'
        staged.write_text('# Encrypted rclone configuration File\nRCLONE_ENCRYPT_V0:\nCIPHERTEXT\n')
        registration=('internxt',staged)
        prefs=Preferences(str(Path(self.tmp.name)/'Internxt'))
        self.manager.add_account('internxt',prefs,Event(),registration=registration)
        self.assertEqual(self.manager.discover_accounts(),['internxt'])
        metadata=self.manager.accounts.metadata_path('internxt')
        self.assertEqual(metadata.stat().st_mode & 0o777,0o600)
        with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'),patch('drive_manager.wallet.Wallet.ensure'):
            self.manager.mount('internxt')
        command=next(c for c in self.manager.runner.calls if c[0]=='systemd-run')
        self.assertIn('--password-command='+PASSWORD_COMMAND,command)
        self.assertIn('--read-only',command)
        self.manager.remove_connection('internxt',True)
        self.assertFalse(metadata.exists())
    def test_encrypted_registration_cannot_rename_before_commit(self):
        folder=self.manager.accounts.folder;folder.mkdir(parents=True)
        staged=folder/'.oauth-encrypted.tmp';staged.write_text('RCLONE_ENCRYPT_V0:\nCIPHERTEXT')
        with self.assertRaises(OperationError):
            self.manager.add_account('new',Preferences(str(Path(self.tmp.name)/'New')),Event(),registration=('old',staged))
    def test_missing_wallet_never_falls_back_to_plain_config(self):
        with patch('drive_manager.internxt.Wallet.ensure',side_effect=OperationError('wallet_error')):
            with self.assertRaises(OperationError):
                internxt.authorize(self.manager.accounts,'internxt','user@example.com','SECRET',Event(),lambda cancel:'')
        self.assertFalse(self.manager.accounts.folder.exists())
    def test_wallet_key_sent_only_on_stdin(self):
        responses=[subprocess.CompletedProcess([],1,b''),subprocess.CompletedProcess([],0,b''),subprocess.CompletedProcess([],0)]
        with patch('subprocess.run',side_effect=responses) as run:
            Wallet().ensure()
        command=run.call_args.args[0];secret=run.call_args.kwargs['input'].decode().strip()
        self.assertNotIn(secret,' '.join(command));self.assertGreater(len(secret),40)
    def test_wallet_existing_key_not_overwritten_on_read_error(self):
        responses=[subprocess.CompletedProcess([],1,b''),subprocess.CompletedProcess([],0,b'drive-manager-rclone-key\n')]
        with patch('subprocess.run',side_effect=responses) as run:
            with self.assertRaises(OperationError):Wallet().ensure()
        self.assertEqual(run.call_count,2)
    def simulate_login(self, cancelled=False):
        class Process:
            def poll(self): return None
            def terminate(self): pass
            def wait(self, timeout=None): return 0
        def encrypt(args, **kwargs):
            path=Path(next(a.split('=',1)[1] for a in args if a.startswith('--config=')))
            path.write_text('RCLONE_ENCRYPT_V0:\nCIPHERTEXT')
            return subprocess.CompletedProcess(args,0)
        def start(args, **kwargs):
            self.assertNotIn('SECRET',' '.join(args))
            self.assertNotIn('user@example.com',' '.join(args))
            self.assertEqual(kwargs['stdout'],subprocess.DEVNULL)
            endpoint=Path(next(a.split('unix://',1)[1] for a in args if a.startswith('--rc-addr=')))
            endpoint.touch();return Process()
        cancel=Event()
        def ask(event):
            if cancelled: event.set(); return ''
            return '123456'
        responses=[{'State':'2fa','Option':{'Name':'config_2fa'}},{'State':''}]
        with patch('drive_manager.internxt.Wallet.ensure'), patch('subprocess.run',side_effect=encrypt), patch('subprocess.Popen',side_effect=start), patch('drive_manager.internxt.request',side_effect=responses) as rpc:
            if cancelled:
                with self.assertRaises(OperationError):
                    internxt.authorize(self.manager.accounts,'internxt','user@example.com','SECRET',cancel,ask)
                self.assertEqual(list(self.manager.accounts.folder.glob('.oauth-*')),[])
                self.assertEqual(rpc.call_count,1)
            else:
                registration=internxt.authorize(self.manager.accounts,'internxt','user@example.com','SECRET',cancel,ask)
                self.assertTrue(self.manager.accounts.encrypted(registration[1]))
                self.assertEqual(rpc.call_args.args[2]['opt']['result'],'123456')
    def test_two_factor_login_over_private_channel(self): self.simulate_login()
    def test_two_factor_cancellation_cleans_credentials(self): self.simulate_login(True)

    def test_request_does_not_expose_raw_error(self):
        with patch('drive_manager.internxt.UnixConnection') as connection:
            response=connection.return_value.getresponse.return_value
            response.status=403;response.read.return_value=b'TOKEN=SECRET'
            with self.assertRaises(OperationError) as error:internxt.request('/private','config/create',{})
        self.assertNotIn('SECRET',str(error.exception))
