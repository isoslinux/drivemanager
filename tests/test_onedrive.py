from pathlib import Path
from threading import Event
import tempfile
import unittest
from unittest.mock import patch
from drive_manager.accounts import Accounts, AuthorizationError
from drive_manager.service import Manager
from drive_manager.providers import ACTIVE_TYPES
from drive_manager.settings import Preferences
from drive_manager import onedrive
from test_accounts import AccountRunner

class OneDriveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.accounts=Accounts(self.tmp.name)
    def configure(self, multiple=False, reject=False, writable=False):
        choices=[{'Value':'id-one','Help':'Personal'}]
        if multiple:choices.append({'Value':'id-two','Help':'Business'})
        calls=[]
        def step(args,cancel,on_url):
            calls.append(args)
            config=Path(next(a.split('=',1)[1] for a in args if a.startswith('--config=')))
            if args[2]=='create':
                config.write_text('[test]\ntype = onedrive\ntoken = PRIVATE\n')
                return {'State':'driveid_final','Option':{'Name':'config_driveid','Examples':choices}}
            value=next(a.split('=',1)[1] for a in args if a.startswith('--result='))
            config.write_text('[test]\ntype = onedrive\ntoken = PRIVATE\ndrive_id = '+value+'\ndrive_type = personal\n')
            return {'State':''}
        picker=lambda options,cancel:None if reject else options[-1][0]
        with patch('drive_manager.onedrive.run_step',side_effect=step):
            if reject:
                with self.assertRaises(AuthorizationError):onedrive.authorize(self.accounts,'test',Event(),lambda url:None,picker,writable)
                self.assertEqual(list(self.accounts.folder.glob('.oauth-*')),[])
                return
            staged=onedrive.authorize(self.accounts,'test',Event(),lambda url:None,picker,writable)
        self.assertEqual(staged.stat().st_mode & 0o777,0o600)
        self.assertIn('access_scopes='+(onedrive.WRITE_SCOPES if writable else onedrive.SCOPES),calls[0])
        self.assertNotIn('--no-output',calls[0])
        self.assertIn('--non-interactive',calls[0])
        self.assertEqual('ReadWrite' in ' '.join(calls[0]),writable)
        self.assertIn('--result='+('id-two' if multiple else 'id-one'),calls[1])
        self.assertNotIn('PRIVATE',' '.join(calls[0]+calls[1]))
    def test_explicit_write_authorization_scopes(self):self.configure(writable=True)
    def test_single_drive_auto_selected(self):self.configure()
    def test_multiple_drives_explicit_choice(self):self.configure(True)
    def test_cancel_drive_choice_removes_staged_credentials(self):self.configure(True,True)
    def test_incomplete_configuration_rejected(self):
        with patch('drive_manager.onedrive.run_step',return_value={'State':''}):
            with self.assertRaises(AuthorizationError):onedrive.authorize(self.accounts,'test',Event(),None,None)
        self.assertEqual(list(self.accounts.folder.glob('.oauth-*')),[])
    def test_supported_provider_and_manager_routes_oauth(self):
        self.assertIn('onedrive',ACTIVE_TYPES)
        manager=Manager(AccountRunner(),self.tmp.name,lambda:[])
        staged=Path(self.tmp.name)/'staged'
        with patch('drive_manager.onedrive.authorize',return_value=staged) as auth:
            name,path=manager.begin_authorization(Event(),lambda url:None,'onedrive',None)
        self.assertTrue(name.startswith('onedrive_'))
        self.assertEqual(path,staged)
        auth.assert_called_once()
    def test_discovery_recognizes_existing_onedrive(self):
        from drive_manager.remotes import discover
        class Runner:
            def run(self,args):return '[{"name":"microsoft","type":"onedrive","source":"file"}]'
        self.assertEqual(discover(Runner()),['microsoft'])
