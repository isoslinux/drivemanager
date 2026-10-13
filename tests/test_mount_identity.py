"""Backend overrides must not turn managed mounts into unrecognized sources."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from drive_manager.mounts import Mount
from drive_manager.service import Manager
from drive_manager.settings import Preferences
from drive_manager.process import OperationError
from test_accounts import AccountRunner

class MountIdentityTests(unittest.TestCase):
    def test_backend_override_mount_is_recognized_and_uploads_are_monitored(self):
        for backend in ['protondrive','dropbox']:
            with self.subTest(backend=backend),tempfile.TemporaryDirectory() as home:
                runner=AccountRunner();mounted=[];manager=Manager(runner,home,lambda:mounted)
                config=manager.accounts.path('cloud');config.parent.mkdir(parents=True)
                config.write_text('[cloud]\ntype='+backend+'\n')
                manager.settings.save('cloud',Preferences(writable=True))
                with patch('drive_manager.service.shutil.which',return_value='/usr/bin/rclone'):
                    manager.mount('cloud')
                command=next(c for c in runner.calls if c[0]=='systemd-run')
                source=next(a.split('=',1)[1] for a in command if a.startswith('--devname='))
                _,target=manager.identity('cloud');mounted.append(Mount(str(target),source,'fuse.rclone'))
                runner.props='ActiveState=active\nDescription=Drive Manager read-write mount v1\nExecStart='+' '.join(command)+'\n'
                with patch('drive_manager.transfers.pending',return_value=2) as pending:
                    status=manager.status('cloud')
                self.assertEqual(status.state,'mounted');self.assertTrue(status.managed)
                self.assertTrue(status.writable);self.assertEqual(status.pending,2)
                pending.assert_called_once_with(manager.rc_endpoint('cloud'))

    def test_foreign_or_suffixed_source_is_never_adopted_by_prefix(self):
        with tempfile.TemporaryDirectory() as home:
            runner=AccountRunner();manager=Manager(runner,home)
            _,target=manager.identity('cloud')
            runner.props='ActiveState=active\nDescription=Drive Manager read-write mount v1\nExecStart=rclone mount cloud: --vfs-cache-mode=full --rc-addr=unix:///private\n'
            for source in ['cloud{override}:','other:']:
                manager.mounts=lambda:[Mount(str(target),source,'fuse.rclone')]
                self.assertEqual(manager.status('cloud').state,'external')
                with self.assertRaises(OperationError):manager.unmount('cloud',True)
            self.assertFalse(any('stop' in c or c[0]=='fusermount3' for c in runner.calls))
