import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from drive_manager.diagnostics import Check, Report, Probe, collect, format_report
from drive_manager.service import Status

class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.manager=Mock()
        self.manager.status.return_value=Status('unmounted','/private/SECRET-path')
        self.manager.write_cache_path.return_value=Path(self.tmp.name)/'cache'
        self.probe=Mock()
        def run(args):
            if args[0]=='rclone':return 'rclone v1.74.3\n- token SECRET\n'
            if args[0]=='fusermount3':return 'fusermount3 version: 3.18.3\n'
            return '259.9-1.fc44\n'
        self.probe.run.side_effect=run
    def collect(self,remote='SECRET-account',**kwargs):
        return collect(self.manager,remote,self.probe,which=lambda name:'/usr/bin/'+name,
            device=Path('/dev/null'),access=lambda *args:True,**kwargs)
    def test_healthy_local_state_and_numeric_versions_only(self):
        report=self.collect()
        self.assertTrue(all(c.state=='ok' for c in report.checks))
        rendered=format_report(report)
        self.assertIn('1.74.3',rendered);self.assertIn('259.9',rendered)
        self.assertNotIn('SECRET',rendered);self.assertNotIn('fc44',rendered)
        self.assertNotIn(self.tmp.name,rendered)
    def test_missing_programs_have_actionable_hints_and_no_processes(self):
        report=collect(self.manager,'',self.probe,which=lambda name:None,device=Path('/nonexistent'))
        rendered=format_report(report)
        self.assertIn('rclone',rendered);self.assertIn('psmisc',rendered);self.assertIn('kf6-kwallet',rendered)
        self.probe.run.assert_not_called();self.manager.status.assert_not_called()
    def test_old_rclone_is_flagged(self):
        self.probe.run.return_value='rclone v1.72.0';self.probe.run.side_effect=None
        self.assertEqual(self.collect().checks[0].message,'old_rclone')
    def test_error_timeout_and_unexpected_output_cannot_leak_secrets(self):
        for value in ['access_token=SECRET','rclone v1.74.3 SECRET','SECRET\nrclone v1.74.3']:
            self.probe.run.side_effect=None;self.probe.run.return_value=value
            self.assertNotIn('SECRET',format_report(self.collect()))
            self.assertEqual(self.collect().checks[0].message,'probe_failed')
        self.probe.run.side_effect=subprocess.TimeoutExpired(['SECRET'],4,output='SECRET')
        self.assertNotIn('SECRET',format_report(self.collect()))
    def test_failed_selected_state_remains_unknown(self):
        self.manager.status.side_effect=RuntimeError('SECRET')
        checks=self.collect().checks
        self.assertEqual(next(c for c in checks if c.name=='connection').message,'unknown')
        self.assertEqual(next(c for c in checks if c.name=='uploads').message,'unknown')
    def test_pending_and_unknown_uploads_are_not_reported_clean(self):
        for pending,message in [(2,'pending'),(-1,'unknown')]:
            self.manager.status.return_value=Status('mounted','/private',True,True,pending)
            self.assertEqual(next(c for c in self.collect().checks if c.name=='uploads').message,message)
        self.manager.status.return_value=Status('unmounted','/private')
        with patch('drive_manager.transfers.dirty_files',return_value=2):
            self.assertEqual(next(c for c in self.collect().checks if c.name=='uploads').message,'pending')
        with patch('drive_manager.transfers.dirty_files',side_effect=RuntimeError('SECRET')):
            self.assertEqual(next(c for c in self.collect().checks if c.name=='uploads').message,'unknown')
    def test_external_mount_not_claimed_safe(self):
        self.manager.status.return_value=Status('external','/private')
        with patch('drive_manager.transfers.dirty_files') as dirty:
            report=self.collect();dirty.assert_not_called()
        self.assertEqual(next(c for c in report.checks if c.name=='uploads').message,'unmonitored')
    def test_probe_is_bounded_and_discards_stderr(self):
        with patch('drive_manager.diagnostics.subprocess.run',return_value=Mock(returncode=0,stdout='rclone v1.74.3')) as run:
            Probe().run(['rclone','version'])
            self.assertEqual(run.call_args.kwargs['timeout'],4)
            self.assertEqual(run.call_args.kwargs['stderr'],subprocess.DEVNULL)
    def test_report_formatter_rejects_raw_values(self):
        report=Report((Check('rclone','ok','installed','SECRET'),Check('SECRET','error','SECRET'),Check('rclone','SECRET','installed')))
        for language in ['es','en']:
            text=format_report(report,language);self.assertNotIn('SECRET',text)
            self.assertIn('Rclone',text)
    def test_device_access_required(self):
        report=collect(self.manager,'',self.probe,which=lambda name:'/usr/bin/'+name,
            device=Path('/dev/null'),access=lambda *args:False)
        self.assertEqual(next(c for c in report.checks if c.name=='device').message,'device_unavailable')
