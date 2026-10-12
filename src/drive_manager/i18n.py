"""Four complete catalogs, private language preference and Qt dialog translations."""
from pathlib import Path
import json
import locale
import os
import tempfile
from PySide6.QtCore import QTranslator, QLibraryInfo
from .messages import TEXT
from .messages_fr import MESSAGES as FRENCH
from .messages_de import MESSAGES as GERMAN
from .process import OperationError

TEXT.update(fr=FRENCH, de=GERMAN)
LANGUAGES = {'es':'Castellano', 'en':'English', 'fr':'Français', 'de':'Deutsch'}

class LanguageSettings:
    def __init__(self, home):
        self.folder = Path(home)/'.config/drive-manager'
        self.path = self.folder/'language.json'
    def load(self):
        default = (locale.getlocale()[0] or 'en').split('_')[0].split('-')[0]
        if default not in LANGUAGES: default = 'en'
        try:
            if any(p.is_symlink() for p in [self.path,*self.path.parents]): return default
            data = json.loads(self.path.read_text())
            if set(data) == {'language'} and data['language'] in LANGUAGES: return data['language']
        except (OSError,ValueError,TypeError): pass
        return default
    def save(self, language):
        if language not in LANGUAGES: raise OperationError('language_error')
        temporary = None
        try:
            if any(p.is_symlink() for p in [self.path,*self.path.parents]): raise OSError()
            self.folder.mkdir(parents=True,exist_ok=True,mode=0o700);self.folder.chmod(0o700)
            fd,temporary = tempfile.mkstemp(dir=self.folder,prefix='.language-')
            with os.fdopen(fd,'w') as file:
                os.fchmod(file.fileno(),0o600);json.dump({'language':language},file)
                file.flush();os.fsync(file.fileno())
            os.replace(temporary,self.path)
        except OSError: raise OperationError('language_error') from None
        finally:
            if temporary is not None: Path(temporary).unlink(missing_ok=True)

STANDARD = {
 'en': {'OK':'OK','Cancel':'Cancel','Save':'Save','Yes':'Yes','No':'No','Open':'Open','Close':'Close'},
 'es': {'OK':'Aceptar','Cancel':'Cancelar','Save':'Guardar','Yes':'Sí','No':'No','Open':'Abrir','Close':'Cerrar'},
 'fr': {'OK':'OK','Cancel':'Annuler','Save':'Enregistrer','Yes':'Oui','No':'Non','Open':'Ouvrir','Close':'Fermer'},
 'de': {'OK':'OK','Cancel':'Abbrechen','Save':'Speichern','Yes':'Ja','No':'Nein','Open':'Öffnen','Close':'Schließen'},
}
class StandardTranslator(QTranslator):
    """Ensure safety-critical standard buttons work without optional Qt catalogs."""
    def __init__(self, language, parent=None):
        super().__init__(parent);self.language = language
    def isEmpty(self): return False
    def translate(self, context, sourceText, disambiguation=None, n=-1):
        if context not in {'QPlatformTheme','QDialogButtonBox','QMessageBox','QInputDialog','QFileDialog'}: return ''
        key = sourceText.replace('&','')
        return STANDARD[self.language].get(key,'')

def install_qt_language(application, language, previous=None):
    if previous is not None: application.removeTranslator(previous)
    translator = QTranslator(application)
    translator.load('qtbase_'+language,QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    application.installTranslator(translator)
    return translator
