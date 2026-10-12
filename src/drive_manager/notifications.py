"""Session-local transition tracking; never include filenames or raw errors."""
from dataclasses import dataclass
from pathlib import Path
import json
import os
import tempfile
from .process import OperationError

@dataclass(frozen=True)
class Notice:
    remote: str
    event: str

class Tracker:
    def __init__(self):
        self.active = set()
        self.warned = {}
    def retain(self, remotes):
        self.active.intersection_update(remotes)
        self.warned = {key:value for key,value in self.warned.items() if key in remotes}
    def observe(self, remote, status):
        if not status.managed or status.state != 'mounted':
            self.active.discard(remote); self.warned.pop(remote, None)
            return []
        detail = status.progress
        if detail is None or detail.state == 'monitor_unknown': return []
        notices = []
        if status.writable and (detail.queued > 0 or detail.uploading > 0 or status.pending > 0):
            self.active.add(remote)
        if detail.state in {'auth_required','transfer_error'}:
            seen = self.warned.setdefault(remote, set())
            if detail.state not in seen:
                notices.append(Notice(remote, detail.state)); seen.add(detail.state)
        elif detail.state in {'idle','uploading','queued','transferring'} and detail.errors == 0:
            self.warned.pop(remote, None)
        if (remote in self.active and status.writable and status.pending == 0
            and detail.state == 'idle' and detail.errors == 0 and detail.queued == 0 and detail.uploading == 0):
            self.active.discard(remote)
            notices.append(Notice(remote, 'uploads_done'))
        return notices

class NotificationSettings:
    def __init__(self, home):
        self.folder = Path(home)/'.config/drive-manager'
        self.path = self.folder/'notifications.json'
    def load(self):
        try:
            if any(p.is_symlink() for p in [self.path,*self.path.parents]): raise ValueError()
            data = json.loads(self.path.read_text())
            if set(data) != {'enabled'} or type(data['enabled']) is not bool: raise ValueError()
            return data['enabled']
        except FileNotFoundError:
            return True
        except (OSError,ValueError,TypeError):
            return False  # Do not silently enable alerts after an unreadable preference.
    def save(self, enabled):
        if type(enabled) is not bool: raise OperationError('notification_settings_error')
        if any(p.is_symlink() for p in [self.path,*self.path.parents]):
            raise OperationError('notification_settings_error')
        self.folder.mkdir(parents=True,exist_ok=True,mode=0o700);self.folder.chmod(0o700)
        fd,temp = tempfile.mkstemp(dir=self.folder,prefix='.notifications-')
        try:
            with os.fdopen(fd,'w') as file:
                os.fchmod(file.fileno(),0o600);json.dump({'enabled':enabled},file)
                file.flush();os.fsync(file.fileno())
            os.replace(temp,self.path)
        except OSError:
            raise OperationError('notification_settings_error') from None
        finally:
            Path(temp).unlink(missing_ok=True)
