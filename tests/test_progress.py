import unittest
from unittest.mock import patch
from drive_manager import transfers

class ProgressTests(unittest.TestCase):
    def snapshot(self,queued=0,uploading=0,errors=0,core=None):
        cache={'uploadsQueued':queued,'uploadsInProgress':uploading,'erroredFiles':errors,'outOfSpace':False}
        with patch('drive_manager.transfers.request',side_effect=[{'diskCache':cache},core or {}]):
            return transfers.progress('/private')
    def test_live_transfer_fields(self):
        data=self.snapshot(uploading=1,core={'speed':2048,'transferring':[{'name':'report.pdf','percentage':42,'speedAvg':1024,'eta':9}]})
        self.assertEqual(data.state,'uploading')
        self.assertEqual(data.files[0],transfers.Transfer('report.pdf',42,1024,9))
    def test_queued_and_empty_are_not_connectivity_claims(self):
        self.assertEqual(self.snapshot(queued=2).state,'queued')
        self.assertEqual(self.snapshot().state,'idle')
    def test_current_auth_failure_classified_without_raw_output(self):
        data=self.snapshot(errors=1,core={'lastError':'invalid_grant TOKEN=SECRET'})
        self.assertEqual(data.state,'auth_required')
        self.assertNotIn('SECRET',repr(data))
    def test_network_failure_classified(self):
        self.assertEqual(self.snapshot(errors=1,core={'lastError':'dial tcp timeout'}).state,'network_retry')
    def test_historical_error_does_not_overwrite_clean_current_queue(self):
        self.assertEqual(self.snapshot(core={'lastError':'invalid_grant OLD','errors':12}).state,'idle')
    def test_missing_monitor_is_unknown(self):
        with patch('drive_manager.transfers.request',side_effect=transfers.TransferError('uploads_unknown')):
            self.assertEqual(transfers.progress('/private').state,'monitor_unknown')
    def test_bad_schema_not_reported_as_clean(self):
        with patch('drive_manager.transfers.request',side_effect=[{'diskCache':{}},{}]):
            self.assertEqual(transfers.progress('/private').state,'monitor_unknown')
    def test_invalid_eta_percent_and_speed_not_displayed(self):
        data=self.snapshot(core={'transferring':[{'name':'a\nb','percentage':float('nan'),'speedAvg':-1,'eta':None}]})
        self.assertEqual(data.files[0],transfers.Transfer('ab',None,0,None))
