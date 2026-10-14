import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from drive_manager.mounts import Mount, read_mounts
from drive_manager.remotes import discover
from drive_manager.service import Manager
from drive_manager.process import OperationError, Runner

class FakeRunner:
    def __init__(self, props='ActiveState=inactive\n'):
        self.props = props; self.calls = []
    def run(self, args):
        self.calls.append(args)
        return self.props if args[0] == 'systemctl' and 'show' in args else ''

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.runner = FakeRunner()
        self.manager = Manager(self.runner, self.tmp.name, lambda: [])
    def test_discovery_only_drive_file(self):
        class R:
            def run(self, args):
                assert args == ['rclone', 'listremotes', '--json']
                return json.dumps([{'name':'account','type':'drive','source':'file'},
                    {'name':'other','type':'s3','source':'file'},
                    {'name':'env','type':'drive','source':'environment'}])
        self.assertEqual(discover(R()), ['account'])
    def test_private_snapshot_preserves_original(self):
        source = Path(self.tmp.name) / 'original.conf'
        source.write_text('[account]\ntype = drive\ntoken = SECRET\n')
        self.manager.lock().close()
        class R:
            def run(self, args): return 'Configuration file is stored at:\n' + str(source)
        self.manager.runner = R()
        snapshot = self.manager.snapshot_config('account')
        self.assertEqual(snapshot.stat().st_mode & 0o777, 0o600)
        snapshot.write_text('updated token')
        self.assertIn('SECRET', source.read_text())

    def test_default_file_manager_launch_is_detached(self):
        self.manager.mounts = lambda: [Mount('/other', 'account:', 'fuse.rclone')]
        self.runner.launch = lambda args: self.runner.calls.append(args)
        self.manager.open_folder('account')
        self.assertEqual(self.runner.calls[-1], ['xdg-open', 'file:///other'])

    def test_invalid_metadata(self):
        with self.assertRaises(OperationError): discover(FakeRunner())
    def test_mountinfo_escape(self):
        path = Path(self.tmp.name) / 'info'
        path.write_text('1 2 0:1 / /home/a\\040b rw - fuse.rclone account: rw\n')
        self.assertEqual(read_mounts(path)[0].path, '/home/a b')
    def test_external_mount_blocked(self):
        self.manager.mounts = lambda: [Mount('/other', 'account:', 'fuse.rclone')]
        self.assertEqual(self.manager.status('account').state, 'external')
        with self.assertRaises(OperationError): self.manager.mount('account')
        with self.assertRaises(OperationError): self.manager.unmount('account', True)
        self.assertFalse(any('stop' in c for c in self.runner.calls))
    def test_stop_requires_confirmation(self):
        with self.assertRaises(OperationError): self.manager.unmount('account')
        self.assertEqual(self.runner.calls, [])
    def test_read_only_mount_arguments(self):
        with patch('drive_manager.service.shutil.which', return_value='/usr/bin/rclone'), patch.object(self.manager, 'snapshot_config', return_value=Path('/private/snapshot')):
            self.manager.mount('account')
        call = next(c for c in self.runner.calls if c[0] == 'systemd-run')
        self.assertIn('--read-only', call); self.assertIn('--vfs-cache-mode=full', call)
        self.assertIn('--property=UMask=0077', call)
        self.assertIn('--vfs-cache-max-size=2G', call)
        self.assertIn('--vfs-cache-max-age=24h', call)
        self.assertIn('--vfs-cache-min-free-space=512M', call)
        cache_arg = next(a for a in call if a.startswith('--cache-dir='))
        cache = Path(cache_arg.split('=', 1)[1])
        self.assertEqual(cache.stat().st_mode & 0o777, 0o700)
        self.assertIn('--property=StandardError=null', call)
        self.assertNotIn('--daemon', call)
    def test_nonempty_target(self):
        _, path = self.manager.identity('account'); path.mkdir(parents=True)
        (path / 'keep').write_text('keep')
        with self.assertRaises(OperationError): self.manager.mount('account')
    def test_unsafe_remote(self):
        for remote in ['../bad', '-flag', 'x:y', 'x\nsecret']:
            with self.assertRaises(OperationError): self.manager.identity(remote)
    def test_names_are_distinct(self):
        self.assertNotEqual(self.manager.identity('a'), self.manager.identity('b'))
    def test_active_external_service(self):
        self.runner.props = 'ActiveState=active\nDescription=External\n'
        with self.assertRaises(OperationError): self.manager.mount('account')
    def test_owned_stop(self):
        _, target = self.manager.identity('account')
        self.manager.mounts = lambda: [Mount(str(target), 'account:', 'fuse.rclone')]
        self.runner.props = ('ActiveState=active\nDescription=Drive Manager read-only mount v1\n'
            'ExecStart=/usr/bin/rclone mount account: --read-only --vfs-cache-mode=off\n')
        self.manager.unmount('account', True)
        self.assertTrue(any('stop' in c for c in self.runner.calls))
    def test_cache_isolated_between_accounts_and_persistent(self):
        a = self.manager.cache_directory('a')
        b = self.manager.cache_directory('b')
        self.assertNotEqual(a, b)
        (a / 'cached').write_text('downloaded')
        self.assertEqual(self.manager.cache_directory('a'), a)
        self.assertEqual((a / 'cached').read_text(), 'downloaded')
        self.assertEqual(a.parent.stat().st_mode & 0o777, 0o700)

    def test_cache_symlink_rejected(self):
        folder = Path(self.tmp.name) / '.cache'
        folder.symlink_to(Path(self.tmp.name), target_is_directory=True)
        with self.assertRaises(OperationError): self.manager.cache_directory('a')

    def test_cached_service_can_stop_with_confirmation(self):
        _, target = self.manager.identity('account')
        self.manager.mounts = lambda: [Mount(str(target), 'account:', 'fuse.rclone')]
        self.runner.props = ('ActiveState=active\nDescription=Drive Manager read-only mount v1\n'
            'ExecStart=/usr/bin/rclone mount account: --read-only --vfs-cache-mode=full\n')
        self.manager.unmount('account', True)
        self.assertTrue(any('stop' in c for c in self.runner.calls))

    def test_writable_cached_service_never_owned(self):
        props = {'Description': 'Drive Manager read-only mount v1',
                 'ExecStart': '/usr/bin/rclone mount account: --vfs-cache-mode=full'}
        self.assertFalse(self.manager.owned(props))

    def test_secret_output_is_not_exposed(self):
        import subprocess
        with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'TOKEN=SECRET')):
            with self.assertRaises(OperationError) as ctx: Runner().run(['rclone'])
        self.assertNotIn('SECRET', str(ctx.exception))

if __name__ == '__main__': unittest.main()
