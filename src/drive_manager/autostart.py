"""Desktop login launcher. No enabling linger or replacing foreign services."""
from pathlib import Path
import os
import json
from .settings import Preferences
import tempfile
from .process import Runner, OperationError

MARKER = '# Managed by Drive Manager v1'

def update(settings):
    folder = settings.home / '.config/autostart'
    target = folder / 'drive-manager-automount.desktop'
    enabled = False
    for path in settings.folder.glob('*.json'):
        try:
            if path.is_symlink():continue
            prefs = settings.validate(Preferences(**json.loads(path.read_text())))
        except (OSError, ValueError, TypeError, OperationError):
            # Damaged preferences are preserved and never enable login mounting.
            continue
        enabled = enabled or prefs.automount
    if folder.is_symlink() or target.is_symlink(): raise OperationError('Invalid login launcher')
    if target.exists() and MARKER not in target.read_text():
        raise OperationError('Existing login launcher is not managed by Drive Manager')
    if not enabled:
        target.unlink(missing_ok=True); return
    folder.mkdir(parents=True, exist_ok=True)
    text = (MARKER + '\n[Desktop Entry]\nType=Application\nName=Drive Manager automount\n'
            'Exec=drive-manager --automount\nTerminal=false\nNoDisplay=true\n')
    fd, temp = tempfile.mkstemp(dir=folder, prefix='.drive-manager-')
    try:
        with os.fdopen(fd, 'w') as file:
            os.fchmod(file.fileno(), 0o600); file.write(text)
        os.replace(temp, target)
    finally:
        if os.path.exists(temp): os.unlink(temp)

def run():
    from .service import Manager
    manager = Manager(Runner())
    failed = False
    try: names = manager.discover_accounts()
    except Exception: return 1
    for name in names:
        try:
            if manager.settings.load(name).automount:
                status = manager.status(name)
                if status.state in {'unmounted', 'failed'}: manager.mount(name)
        except Exception:
            failed = True
    return int(failed)
