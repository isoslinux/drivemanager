from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from threading import Event
import os
import test_bulk as fixtures
from drive_manager import validation,test_files
from drive_manager.service import Status

class CleanupDetailTests(TestCase):
    setUp=fixtures.BulkTests.setUp
    def test_missing_fixture_removed_from_registry(self):
        name='DriveManager-test-'+('a'*32)+'.txt';test_files.add(self.manager,'a',[name]);folder=self.home/'Drives/a';folder.mkdir(parents=True)
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)):
            result=validation.cleanup_test(self.manager,'a',name,True,Event())
        self.assertEqual(result.state,'validation_cleanup_absent');self.assertEqual(test_files.read(self.manager,'a'),[])
    def test_creation_enoent_does_not_leave_phantom_record(self):
        folder=self.home/'Drives/a';original=os.open
        def opening(path,*args,**kwargs):
            if Path(path).name.startswith('DriveManager-test-'):raise FileNotFoundError()
            return original(path,*args,**kwargs)
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)),patch('drive_manager.validation.os.open',side_effect=opening):
            result=validation.write_test(self.manager,'a',Event(),True)
        self.assertEqual(result.state,'validation_error');self.assertEqual(result.file,'');self.assertEqual(test_files.read(self.manager,'a'),[])
    def test_both_cleanup_children_use_isolated_python(self):
        name='DriveManager-test-'+('a'*32)+'.txt';folder=self.home/'Drives/a';folder.mkdir(parents=True);commands=[]
        def output(args,event,**kwargs):commands.append(args);return 'operation_finished',b'[1,2,3,4]'
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)),patch('drive_manager.validation.bounded_output',side_effect=output):
            validation.cleanup_test(self.manager,'a',name,True,Event())
        self.assertEqual(len(commands),2)
        self.assertTrue(all(command[1]=='-I' for command in commands))
    def test_unverified_missing_timeout_keeps_record(self):
        name='DriveManager-test-'+('a'*32)+'.txt';test_files.add(self.manager,'a',[name]);folder=self.home/'Drives/a'
        with patch.object(self.manager,'status',return_value=Status('mounted',str(folder),True,True,0)),patch('drive_manager.validation.bounded_output',return_value=('validation_timeout',None)):
            result=validation.cleanup_test(self.manager,'a',name,True,Event())
        self.assertEqual(result.state,'validation_timeout');self.assertEqual(test_files.read(self.manager,'a'),[name])
