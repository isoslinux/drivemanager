import os
from pathlib import Path
from string import Formatter
import tempfile
import unittest
from unittest.mock import patch
from drive_manager.i18n import TEXT,LANGUAGES,LanguageSettings
from drive_manager.diagnostics import CATALOG,Check,Report,format_report
from drive_manager.process import OperationError

class LanguageTests(unittest.TestCase):
    def test_complete_catalogs_and_placeholders(self):
        for language in LANGUAGES:
            self.assertEqual(set(TEXT[language]),set(TEXT['en']))
            self.assertEqual(set(CATALOG[language]),set(CATALOG['en']))
            for key,value in TEXT[language].items():
                self.assertIsInstance(value,str);self.assertTrue(value)
                fields=lambda s:{field for _,field,_,_ in Formatter().parse(s) if field is not None}
                self.assertEqual(fields(value),fields(TEXT['en'][key]),(language,key))
            report=format_report(Report((Check('uploads','warning','pending'),)),language)
            self.assertIn(CATALOG[language]['pending'],report)
    def test_persisted_preference_overrides_system_and_stays_private(self):
        with tempfile.TemporaryDirectory() as home,patch('locale.getlocale',return_value=('es_ES','UTF-8')):
            settings=LanguageSettings(home);self.assertEqual(settings.load(),'es')
            for language in LANGUAGES:
                settings.save(language);self.assertEqual(settings.load(),language)
            self.assertEqual(settings.path.stat().st_mode & 0o777,0o600)
            self.assertEqual(settings.folder.stat().st_mode & 0o777,0o700)
    def test_invalid_preference_falls_back_without_overwriting(self):
        with tempfile.TemporaryDirectory() as home,patch('locale.getlocale',return_value=('it_IT','UTF-8')):
            settings=LanguageSettings(home);self.assertEqual(settings.load(),'en')
            settings.save('fr');settings.path.write_text('{broken')
            self.assertEqual(settings.load(),'en');self.assertEqual(settings.path.read_text(),'{broken')
            with self.assertRaises(OperationError):settings.save('it')
    def test_symlink_is_never_followed_for_saving(self):
        with tempfile.TemporaryDirectory() as home:
            settings=LanguageSettings(home);settings.save('en');settings.path.unlink()
            other=Path(home)/'other';other.write_text('untouched');settings.path.symlink_to(other)
            with self.assertRaises(OperationError):settings.save('fr')
            self.assertEqual(other.read_text(),'untouched')

@unittest.skipUnless(os.environ.get('QT_QPA_PLATFORM')=='offscreen','Set QT_QPA_PLATFORM=offscreen')
class LanguageUiTests(unittest.TestCase):
    def test_live_switch_keeps_selection_controls_and_changes_standard_buttons(self):
        from PySide6.QtWidgets import QApplication,QDialogButtonBox
        from PySide6.QtCore import QTimer,QEventLoop
        from drive_manager.app import Window
        from drive_manager.service import Manager,Status
        from drive_manager.quota import Quota
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as home,patch('drive_manager.app.Manager',side_effect=lambda runner:Manager(runner,home,lambda:[])), \
             patch('drive_manager.service.Manager.discover_accounts',return_value=['personal']), \
             patch('drive_manager.service.Manager.provider_of',return_value='drive'), \
             patch('drive_manager.service.Manager.status',return_value=Status('unmounted','/demo')), \
             patch('drive_manager.quota.read_quota',return_value=Quota()):
            window=Window();window.show()
            loop=QEventLoop();QTimer.singleShot(650,loop.quit);loop.exec()
            for language,save in [('fr','Enregistrer'),('de','Speichern'),('es','Guardar'),('en','Save')]:
                before={key:control.isEnabled() for key,control in window.buttons.items()}
                window.language_selector.setCurrentIndex(window.language_selector.findData(language))
                self.assertEqual(window.language,language)
                self.assertEqual(window.buttons['mount'].text(),TEXT[language]['mount'])
                self.assertEqual(window.language_settings.load(),language)
                self.assertEqual(window.accounts.currentText(),'personal')
                self.assertEqual(before,{key:control.isEnabled() for key,control in window.buttons.items()})
                buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
                self.assertEqual(buttons.button(QDialogButtonBox.StandardButton.Save).text().replace('&',''),save)
            # Switching while an operation is busy must not re-enable actions.
            for control in window.buttons.values():control.setEnabled(False)
            window.language_selector.setCurrentIndex(window.language_selector.findData('fr'))
            self.assertTrue(all(not c.isEnabled() for c in window.buttons.values()))
            window.timer.stop();window.quota_pool.shutdown();window.pool.shutdown();window.tray.hide();window.hide()
    def test_save_failure_reverts_selector(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer,QEventLoop
        from drive_manager.app import Window
        from drive_manager.service import Manager
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as home,patch('drive_manager.app.Manager',side_effect=lambda runner:Manager(runner,home,lambda:[])), \
             patch('drive_manager.service.Manager.discover_accounts',return_value=[]):
            window=Window();old=window.language
            with patch.object(window.language_settings,'save',side_effect=OperationError('language_error')):
                target='de' if old!='de' else 'fr'
                window.language_selector.setCurrentIndex(window.language_selector.findData(target))
            self.assertEqual(window.language,old);self.assertEqual(window.language_selector.currentData(),old)
            window.timer.stop();window.quota_pool.shutdown();window.pool.shutdown();window.tray.hide();window.hide()
