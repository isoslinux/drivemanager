import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from drive_manager.service import Manager
from drive_manager.settings import Preferences
from drive_manager.mounts import Mount
from drive_manager.process import OperationError
from test_accounts import AccountRunner

class RemovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.manager=Manager(AccountRunner(),self.tmp.name,lambda:[])
        self.private=self.manager.accounts.path('one')
        self.private.parent.mkdir(parents=True)
        self.private.write_text('[one]\ntype = drive\ntoken = PRIVATE\n')
        self.manager.settings.save('one', Preferences(str(Path(self.tmp.name)/'One')))
    def test_confirmation_required_before_any_mutation(self):
        with self.assertRaises(OperationError): self.manager.remove_connection('one')
        self.assertTrue(self.private.exists())
        with self.assertRaises(OperationError): self.manager.disconnect('one')
    def test_private_removal_preserves_other_account_and_folder(self):
        other=self.manager.accounts.path('two');other.write_text('[two]\ntype = drive\n')
        folder=Path(self.tmp.name)/'One';folder.mkdir();(folder/'local-file').write_text('keep')
        names=self.manager.remove_connection('one',True)
        self.assertEqual(names,['two'])
        self.assertFalse(self.private.exists())
        self.assertFalse(self.manager.settings.path('one').exists())
        self.assertTrue(other.exists()); self.assertEqual((folder/'local-file').read_text(),'keep')
        self.assertFalse(any(c[:2]==['rclone','config'] for c in self.manager.runner.calls))
    def test_external_connection_requires_explicit_scope(self):
        with self.assertRaises(OperationError): self.manager.remove_connection('external',True)
        self.assertFalse(any('delete' in c for c in self.manager.runner.calls))
    def test_external_deletion_uses_only_config_delete(self):
        self.manager.remove_connection('external',True,True)
        self.assertIn(['rclone','config','delete','external'],self.manager.runner.calls)
        self.assertFalse(any('purge' in c for c in self.manager.runner.calls))
    def test_external_active_never_stopped_or_deleted(self):
        self.manager.mounts=lambda:[Mount('/external','one:','fuse.rclone')]
        with self.assertRaises(OperationError):self.manager.remove_connection('one',True)
        self.assertTrue(self.private.exists())
        self.assertFalse(any('stop' in c or 'delete' in c for c in self.manager.runner.calls))
    def test_owned_mount_stopped_before_credentials_deleted(self):
        _,target=self.manager.identity('one')
        state={'mounted':True}
        self.manager.mounts=lambda:[Mount(str(target),'one:','fuse.rclone')] if state['mounted'] else []
        self.manager.runner.props='ActiveState=active\nDescription=Drive Manager read-only mount v1\nExecStart=rclone --read-only --vfs-cache-mode=full\n'
        original=self.manager.runner.run
        def run(args):
            if 'stop' in args:
                self.assertTrue(self.private.exists())
                state['mounted']=False
                self.manager.runner.props='ActiveState=inactive\n'
            return original(args)
        self.manager.runner.run=run
        self.manager.remove_connection('one',True)
        self.assertFalse(self.private.exists())
    def test_busy_after_stop_preserves_credentials(self):
        _,target=self.manager.identity('one')
        self.manager.mounts=lambda:[Mount(str(target),'one:','fuse.rclone')]
        self.manager.runner.props='ActiveState=active\nDescription=Drive Manager read-only mount v1\nExecStart=rclone --read-only --vfs-cache-mode=full\n'
        with self.assertRaises(OperationError):self.manager.remove_connection('one',True)
        self.assertTrue(self.private.exists())
    def test_disconnect_keeps_credentials_and_can_disable_login(self):
        self.manager.settings.save('one',Preferences(automount=True))
        self.manager.disconnect('one',True,True)
        self.assertTrue(self.private.exists())
        self.assertFalse(self.manager.settings.load('one').automount)
