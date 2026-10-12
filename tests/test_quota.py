import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from drive_manager.quota import Quota,parse,read_quota
from drive_manager.service import Manager
from test_core import FakeRunner

class QuotaTests(unittest.TestCase):
    def test_shared_google_usage_uses_free_for_bar_and_preserves_drive_usage(self):
        quota=parse({'total':100,'used':20,'free':10,'other':60,'trashed':10})
        self.assertEqual(quota.used,20);self.assertEqual(quota.percentage,90)
        self.assertTrue(quota.low)
    def test_missing_fields_not_assumed_zero_or_unlimited(self):
        quota=parse({'used':10})
        self.assertIsNone(quota.free);self.assertIsNone(quota.percentage)
        self.assertFalse(quota.low)
        self.assertEqual(parse({}),Quota())
        self.assertEqual(Quota(100,20,None,60,10).percentage,80)
        self.assertEqual(parse({'total':100,'free':0}).percentage,100)
    def test_malformed_quota_rejected_without_raw_data(self):
        for data in [{'free':-1},{'used':True},{'total':'SECRET'},{'total':10,'free':11},[],{'used':2**64}]:
            self.assertEqual(parse(data),Quota())
    def test_isolated_token_refresh_keeps_original_and_removes_temporary_copy(self):
        with tempfile.TemporaryDirectory() as home:
            manager=Manager(FakeRunner(),home,lambda:[])
            source=manager.accounts.path('personal');source.parent.mkdir(parents=True)
            source.write_text('[personal]\ntype=drive\ntoken=OLD_SECRET\n')
            before=source.read_bytes()
            def query(args):
                self.assertEqual(args[:4],['rclone','about','personal:','--json'])
                copy=Path(next(a.split('=',1)[1] for a in args if a.startswith('--config=')))
                self.assertNotEqual(copy,source);self.assertEqual(copy.stat().st_mode & 0o777,0o600)
                self.assertEqual(copy.parent.stat().st_mode & 0o777,0o700)
                copy.write_text('NEW_SECRET')
                return {'total':100,'used':40,'free':60}
            with patch('drive_manager.quota.run',side_effect=query):
                quota=read_quota(manager,'personal')
            self.assertEqual(quota.free,60);self.assertEqual(source.read_bytes(),before)
            self.assertEqual(list((Path(home)/'.local/state/drive-manager/quota').iterdir()),[])
    def test_failed_query_cleans_copy_and_never_returns_error_text(self):
        with tempfile.TemporaryDirectory() as home:
            manager=Manager(FakeRunner(),home,lambda:[])
            source=manager.accounts.path('personal');source.parent.mkdir(parents=True)
            source.write_text('[personal]\ntype=drive\ntoken=SECRET\n')
            with patch('drive_manager.quota.run',side_effect=RuntimeError('SECRET')):
                self.assertEqual(read_quota(manager,'personal'),Quota())
            self.assertEqual(list((Path(home)/'.local/state/drive-manager/quota').iterdir()),[])
            self.assertIn('SECRET',source.read_text())
    def test_encrypted_unmounted_account_never_opens_wallet(self):
        with tempfile.TemporaryDirectory() as home:
            manager=Manager(FakeRunner(),home,lambda:[])
            source=manager.accounts.path('personal');source.parent.mkdir(parents=True)
            source.write_text('RCLONE_ENCRYPT_V0:\nENCRYPTED')
            with patch('drive_manager.quota.run') as run,patch('drive_manager.wallet.Wallet.ensure') as wallet:
                self.assertEqual(read_quota(manager,'personal'),Quota())
                run.assert_not_called();wallet.assert_not_called()
    def test_process_timeout_stderr_and_clean_env(self):
        from drive_manager.quota import run
        with patch('drive_manager.quota.subprocess.run',return_value=Mock(returncode=0,stdout='{"free":0}')) as process:
            with patch.dict('os.environ',{'RCLONE_TOKEN':'SECRET'}):self.assertEqual(run(['rclone','about']),{'free':0})
            self.assertEqual(process.call_args.kwargs['timeout'],12)
            self.assertNotIn('RCLONE_TOKEN',process.call_args.kwargs['env'])
