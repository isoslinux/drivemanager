"""Transient user units only. External services are never adopted or stopped."""
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
import fcntl
import os
import shutil
import stat
from .mounts import read_mounts
from .process import OperationError
from .settings import Settings
from .accounts import Accounts
from .remotes import discover
from . import autostart
from . import transfers

@dataclass(frozen=True)
class Status:
    state: str
    path: str
    managed: bool = False
    writable: bool = False
    pending: int = 0
    progress: transfers.Progress | None = None

class Manager:
    def __init__(self, runner, home=None, mounts=read_mounts):
        self.runner = runner
        self.home = Path(home or Path.home())
        self.mounts = mounts
        self.settings = Settings(self.home)
        self.accounts = Accounts(self.home)

    def provider_types(self,names):
        """One external metadata query per refresh, local accounts stay local."""
        result={};external=[]
        for name in names:
            if self.is_app_account(name):result[name]=self.provider_of(name)
            else:external.append(name)
        if external:
            import json
            entries=json.loads(self.runner.run(['rclone','listremotes','--json']))
            if not isinstance(entries,list):raise OperationError('Unsupported rclone metadata format')
            for item in entries:
                if isinstance(item,dict) and isinstance(item.get('name'),str):
                    name=item['name'].removesuffix(':')
                    if name in external:result[name]=item.get('type','')
        return result

    def provider_of(self, remote):
        private=self.accounts.path(remote)
        if private.is_file():
            if self.accounts.encrypted(private):
                return self.encrypted_provider(remote)
            import configparser
            parser=configparser.ConfigParser(interpolation=None);parser.read(private)
            return parser.get(remote,'type',fallback='')
        import json
        entries=json.loads(self.runner.run(['rclone','listremotes','--json']))
        return next((item.get('type','') for item in entries if item.get('name','').removesuffix(':')==remote),'')

    def encrypted_provider(self, remote):
        import json
        from .providers import ENCRYPTED_TYPES
        try:
            metadata=json.loads(self.accounts.metadata_path(remote).read_text())
            if metadata.get('name') != remote or metadata.get('type') not in ENCRYPTED_TYPES:
                raise ValueError()
            return metadata['type']
        except Exception:
            raise OperationError('Invalid encrypted account metadata') from None

    def begin_credentials(self, remote, provider, user, password, cancel, **options):
        from .credentials import authorize
        with self.lock():
            self.accounts.validate_name(remote)
            if remote in self.discover_accounts() or self.settings.path(remote).exists():
                raise OperationError('Connection name already exists')
            return authorize(self.accounts, remote, provider, user, password, cancel, **options)

    def discover_accounts(self):
        existing = discover(self.runner)
        added = self.accounts.names(self.runner)
        if set(existing) & set(added):
            raise OperationError("Account names conflict with existing Rclone connections")
        return sorted(set(existing + added))

    def begin_internxt(self, remote, email, password, cancel, ask_code):
        from .internxt import authorize
        with self.lock():
            self.accounts.validate_name(remote)
            if remote in self.discover_accounts() or self.settings.path(remote).exists():
                raise OperationError("Connection name already exists")
            return authorize(self.accounts, remote, email, password, cancel, ask_code)

    def renew_credentials(self, remote, user, password, cancel, *, confirmed=False, ask_code=None, **options):
        """Stage a fresh login to the same encrypted account; preserve state on failure."""
        if not confirmed: raise OperationError('credential_confirm')
        if cancel.is_set(): raise OperationError('credential_renew_error')
        with self.lock():
            if not self.is_app_account(remote): raise OperationError('credential_renew_error')
            path=self.accounts.path(remote)
            if path.is_symlink() or not self.accounts.encrypted(path): raise OperationError('credential_renew_error')
            provider=self.encrypted_provider(remote)
            self.discover_accounts()
            if self.status(remote).state not in {'unmounted','failed'}: raise OperationError('credential_renew_error')
            self.ensure_no_dirty_cache(remote)
            original=path.read_bytes(); staged=None
            try:
                if provider=='internxt':
                    from .internxt import authorize
                    registration=authorize(self.accounts,remote,user,password,cancel,ask_code or (lambda event:''),existing=path)
                else:
                    from .credentials import authorize
                    registration=authorize(self.accounts,remote,provider,user,password,cancel,existing=path,**options)
                name,staged=registration
                if (name!=remote or registration.provider!=provider or staged.parent!=self.accounts.folder
                    or not staged.name.startswith('.oauth-') or staged.is_symlink() or not self.accounts.encrypted(staged)):
                    raise OperationError('credential_renew_error')
                if cancel.is_set() or path.read_bytes()!=original: raise OperationError('credential_renew_error')
                if self.status(remote).state not in {'unmounted','failed'}: raise OperationError('credential_renew_error')
                self.ensure_no_dirty_cache(remote)
                if self.encrypted_provider(remote)!=provider: raise OperationError('credential_renew_error')
                names=self.discover_accounts()
                staged.chmod(0o600)
                with staged.open('rb') as data:os.fsync(data.fileno())
                os.replace(staged,path)
            finally:
                if staged is not None: staged.unlink(missing_ok=True)
            return names

    def begin_authorization(self, cancel, on_url, provider="drive", ask_drive=None, writable=False):
        from uuid import uuid4
        with self.lock():
            if provider not in {'drive','onedrive','dropbox'}: raise OperationError("Unsupported provider")
            remote = ('google_' if provider == 'drive' else provider+'_') + uuid4().hex
            if provider == 'onedrive':
                from .onedrive import authorize
                staged = (authorize(self.accounts, remote, cancel, on_url, ask_drive, True) if writable
                          else authorize(self.accounts, remote, cancel, on_url, ask_drive))
            elif provider == 'dropbox':
                staged = self.accounts.authorize(remote, cancel, on_url, writable, provider='dropbox')
            else:
                staged = (self.accounts.authorize(remote, cancel, on_url, True) if writable
                          else self.accounts.authorize(remote, cancel, on_url))
            if cancel.is_set():
                staged.unlink(missing_ok=True)
                raise OperationError("Authorization cancelled")
            return remote, staged

    def reauthorize(self, remote, cancel, on_url, ask_drive=None, confirmed=False, request_write=False):
        """Replace only OAuth credentials after explicit same-account confirmation.

        External configurations and encrypted credentials are outside this workflow.
        Failed/cancelled authorization leaves the original configuration untouched.
        """
        if not confirmed:
            raise OperationError('Explicit same-account confirmation required')
        import configparser
        with self.lock():
            if not self.is_app_account(remote):
                raise OperationError('reauth_error')
            if self.status(remote).state not in {'unmounted', 'failed'}:
                raise OperationError('reauth_error')
            self.ensure_no_dirty_cache(remote)
            path = self.accounts.path(remote)
            if self.accounts.encrypted(path):
                raise OperationError('reauth_error')
            original = path.read_bytes()
            old = configparser.ConfigParser(interpolation=None)
            old.read_string(original.decode('utf-8'))
            provider = old.get(remote, 'type', fallback='')
            if provider not in {'drive', 'onedrive', 'dropbox'}:
                raise OperationError('reauth_error')
            # Custom OAuth clients need their own authorization flow.
            if any(old.get(remote, key, fallback='') for key in ('client_id', 'client_secret', 'service_account_file')):
                raise OperationError('reauth_error')
            writable = request_write or self.settings.load(remote).writable
            if provider == 'drive':
                writable = writable or old.get(remote, 'scope', fallback='drive') in {'drive', 'drive.file'}
                staged = self.accounts.authorize(remote, cancel, on_url, writable)
            elif provider == 'dropbox':
                staged = self.accounts.authorize(remote, cancel, on_url, writable, provider='dropbox')
            else:
                from .onedrive import authorize
                writable = writable or 'ReadWrite' in old.get(remote, 'access_scopes', fallback='Files.ReadWrite')
                staged = authorize(self.accounts, remote, cancel, on_url, ask_drive, writable)
            try:
                if staged.parent != self.accounts.folder or not staged.name.startswith('.oauth-') or staged.is_symlink():
                    raise OperationError('reauth_error')
                new = configparser.ConfigParser(interpolation=None)
                new.read(staged)
                if new.get(remote, 'type', fallback='') != provider or not new.get(remote, 'token', fallback=''):
                    raise OperationError('reauth_error')
                if provider == 'onedrive' and any(old.get(remote, key, fallback='') != new.get(remote, key, fallback='')
                                                for key in ('drive_id', 'drive_type')):
                    raise OperationError('reauth_identity')
                if request_write:
                    self.ensure_write_permission(remote, staged)
                # Keep root-folder, backend options, and every application preference.
                keys = ('token',) if provider == 'dropbox' else ('token', 'scope' if provider == 'drive' else 'access_scopes')
                for key in keys:
                    if new.has_option(remote, key):
                        old.set(remote, key, new.get(remote, key))
                with staged.open('w') as file:
                    old.write(file); file.flush(); os.fsync(file.fileno())
                if cancel.is_set() or not self.is_app_account(remote) or path.read_bytes() != original:
                    raise OperationError('reauth_error')
                if self.status(remote).state not in {'unmounted', 'failed'}:
                    raise OperationError('reauth_error')
                self.ensure_no_dirty_cache(remote)
                staged.chmod(0o600)
                os.replace(staged, path)
            finally:
                staged.unlink(missing_ok=True)
            return self.discover_accounts()

    def add_account(self, remote, prefs, cancel, on_url=None, registration=None):
        with self.lock():
            self.accounts.validate_name(remote)
            self.settings.validate(prefs)
            self.validate_mount_targets([(remote,prefs)])
            if not prefs.mount_path:
                raise OperationError("Choose a mount folder for this account")
            if remote in self.discover_accounts() or self.accounts.path(remote).exists() or self.settings.path(remote).exists():
                raise OperationError("Connection name already exists")
            target = Path(prefs.mount_path)
            if target.exists() and (not target.is_dir() or any(target.iterdir())):
                raise OperationError("Choose an empty folder")
            if registration is None:
                staged = (self.accounts.authorize(remote, cancel, on_url) if on_url is not None
                          else self.accounts.authorize(remote, cancel))
            else:
                original, staged = registration
                if staged.is_symlink(): raise OperationError('Invalid staged authorization')
                from .providers import ENCRYPTED_TYPES
                encrypted_provider = getattr(registration, 'provider', 'internxt')
                if self.accounts.encrypted(staged) and encrypted_provider not in ENCRYPTED_TYPES:
                    raise OperationError('Invalid encrypted provider')
                if staged.parent != self.accounts.folder or not staged.name.startswith('.oauth-'):
                    raise OperationError("Invalid staged authorization")
                if self.accounts.encrypted(staged):
                    if original != remote: raise OperationError("Encrypted account name cannot change")
                else:
                    import configparser
                    parser = configparser.ConfigParser(interpolation=None)
                    parser.read(staged)
                    if not parser.has_section(original): raise OperationError("Authorization expired")
                    values = dict(parser[original]); parser.remove_section(original)
                    parser[remote] = values
                    with staged.open('w') as file:
                        parser.write(file); file.flush(); os.fsync(file.fileno())
            try:
                if cancel.is_set(): raise OperationError("Authorization cancelled")
                self.validate_mount_targets([(remote,prefs)])
                self.settings.save(remote, prefs)
                autostart.update(self.settings)
                if self.accounts.encrypted(staged):
                    import json
                    metadata=self.accounts.metadata_path(remote)
                    fd=os.open(metadata,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                    with os.fdopen(fd,'w') as file: json.dump({'name':remote,'type':encrypted_provider},file)
                os.replace(staged, self.accounts.path(remote))
            except Exception:
                staged.unlink(missing_ok=True)
                self.accounts.metadata_path(remote).unlink(missing_ok=True)
                self.settings.path(remote).unlink(missing_ok=True)
                autostart.update(self.settings)
                raise
            return self.discover_accounts()

    def validate_mount_targets(self,rows,tolerate_corrupt=False):
        """Check effective paths, including accounts without preference files."""
        targets={name:Path(prefs.mount_path) if prefs.mount_path else self.home/'DriveManager'/self.settings.path(name).stem for name,prefs in rows}
        changed=set(targets)
        for name in self.discover_accounts():
            if name in targets:continue
            try:targets[name]=self.identity(name)[1]
            except OperationError:
                if not tolerate_corrupt:raise OperationError('Cannot validate preferences for account: '+name) from None
                # A damaged account cannot mount until repaired. Reserve its default
                # and protect all actual FUSE mounts, without rewriting its JSON.
                targets[name]=self.home/'DriveManager'/self.settings.path(name).stem
        if tolerate_corrupt:
            for mount in self.mounts():
                if mount.kind.startswith('fuse'):
                    path=Path(mount.path)
                    for name in changed:
                        target=targets[name]
                        if target.is_relative_to(path) or path.is_relative_to(target):
                            raise OperationError('Mount path is already in use')
        items=list(targets.items())
        for i,(name,path) in enumerate(items):
            for other,target in items[i+1:]:
                if (name in changed or other in changed) and (path.is_relative_to(target) or target.is_relative_to(path)):
                    raise OperationError('Mount paths of accounts must not overlap')

    def unit_name(self,remote):
        if not remote or any(c in remote for c in "\r\n:/\0") or remote.startswith('-'):
            raise OperationError('Invalid connection name')
        return 'drive-manager-'+sha256(remote.encode()).hexdigest()[:24]+'.service'

    def identity(self, remote):
        unit=self.unit_name(remote)
        key=unit.removeprefix('drive-manager-').removesuffix('.service')
        prefs = self.settings.load(remote)
        target = Path(prefs.mount_path) if prefs.mount_path else self.home / "DriveManager" / key
        return unit, target

    def properties(self, remote):
        unit = self.unit_name(remote)
        output = self.runner.run(["systemctl", "--user", "show", unit,
                                  "--property=ActiveState,Description,ExecStart", "--no-pager"])
        return dict(line.split("=", 1) for line in output.splitlines() if "=" in line)

    def owned(self, props):
        # The namespace alone is insufficient: verify the managed read-only command.
        command = props.get("ExecStart", "")
        if props.get("Description") == "Drive Manager read-write mount v1":
            return "--vfs-cache-mode=full" in command and "--rc-addr=unix://" in command and "--read-only" not in command
        return (props.get("Description") == "Drive Manager read-only mount v1"
                and "--read-only" in command
                and any(mode in command for mode in ("--vfs-cache-mode=off", "--vfs-cache-mode=full")))

    def status(self, remote):
        self.unit_name(remote)
        try:_,target=self.identity(remote)
        except OperationError:return Status('prefs_damaged','')
        matches = [m for m in self.mounts()
                   if m.path == str(target) or (m.kind.startswith("fuse") and m.source == remote + ":")]
        props = self.properties(remote)
        active = props.get("ActiveState", "inactive")
        if matches:
            own = self.owned(props) and active == "active" and matches[0].path == str(target) and matches[0].source == remote + ":" and matches[0].kind == "fuse.rclone"
            writable=own and props.get('Description') == 'Drive Manager read-write mount v1'
            pending=0
            progress=None
            if own and self.rc_endpoint(remote).exists():
                progress=transfers.progress(self.rc_endpoint(remote))
            if writable:
                if progress is None or progress.out_of_space or progress.state in {'monitor_unknown','transfer_error'}:pending=-1
                else:pending=progress.queued+progress.uploading+progress.errors
            return Status("mounted" if own else "external", matches[0].path, own, writable, pending, progress)
        if active in {"active", "activating", "deactivating", "reloading"}:
            return Status("starting" if self.owned(props) else "external", str(target))
        return Status("failed" if active == "failed" else "unmounted", str(target), False, self.settings.load(remote).writable)

    def recover_mount(self,remote,confirmed=False):
        if not confirmed:raise OperationError('recovery_confirm')
        with self.lock():
            _,target=self.identity(remote)
            props=self.properties(remote)
            if props.get('ActiveState') not in {'inactive','failed'}:raise OperationError('recovery_error')
            matches=[m for m in self.mounts() if m.path==str(target)]
            if len(matches)!=1 or matches[0].source!=remote+':' or matches[0].kind!='fuse.rclone':raise OperationError('recovery_error')
            from .mounts import disconnected
            if not disconnected(target):raise OperationError('recovery_error')
            transfers.ensure_closed(target)
            self.runner.run(['fusermount3','-u','--',str(target)])
            return self.status(remote)

    def repair_preferences(self,remote,confirmed=False):
        """Quarantine only damaged preferences; never replace account credentials."""
        if not confirmed:raise OperationError('recovery_confirm')
        with self.lock():
            self.unit_name(remote)
            source=self.settings.path(remote)
            if not source.is_file() or any(p.is_symlink() for p in [source,*source.parents]):raise OperationError('repair_error')
            try:self.settings.load(remote)
            except OperationError:pass
            else:raise OperationError('repair_error')
            if self.properties(remote).get('ActiveState') not in {'inactive','failed'}:raise OperationError('repair_error')
            if any(m.kind.startswith('fuse') and (m.source==remote+':' or m.source.startswith(remote+'{')) for m in self.mounts()):raise OperationError('repair_error')
            self.ensure_no_dirty_cache(remote)
            from .settings import Preferences
            self.validate_mount_targets([(remote,Preferences())],tolerate_corrupt=True)
            folder=self.home/'.local/state/drive-manager/preference-backups'
            if any(p.is_symlink() for p in [folder,*folder.parents]):raise OperationError('repair_error')
            folder.mkdir(parents=True,exist_ok=True,mode=0o700);folder.chmod(0o700)
            from uuid import uuid4
            backup=folder/(source.stem+'-'+uuid4().hex+'.json.bak')
            try:
                os.replace(source,backup)
                backup.chmod(0o600)
                autostart.update(self.settings)
            except Exception:
                if backup.exists() and not source.exists():os.replace(backup,source)
                raise OperationError('repair_error') from None
            return self.discover_accounts()

    def lock(self):
        folder = self.home / ".local/state/drive-manager"
        folder.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(folder, 0o700)
        file = open(folder / "operations.lock", "a")
        os.chmod(folder / "operations.lock", 0o600)
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            file.close()
            raise OperationError("Another operation is running") from None
        return file

    def snapshot_config(self, remote):
        # OAuth refresh may rewrite rclone.conf; use a private isolated copy.
        private = self.accounts.path(remote)
        if private.is_file() and not private.is_symlink():
            return private
        output = self.runner.run(["rclone", "config", "file"])
        lines = output.strip().splitlines()
        source = Path(lines[-1]) if lines else Path("/nonexistent")
        if not source.is_absolute() or not source.is_file():
            raise OperationError("Cannot locate the existing rclone configuration")
        unit, _ = self.identity(remote)
        folder = self.home / ".local/state/drive-manager"
        target = folder / (unit + ".conf")
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW
        fd = os.open(target, flags, 0o600)
        with os.fdopen(fd, "wb") as dest, source.open("rb") as src:
            os.fchmod(dest.fileno(), stat.S_IRUSR | stat.S_IWUSR)
            shutil.copyfileobj(src, dest)
        return target

    def write_cache_path(self, remote):
        unit=self.unit_name(remote)
        return self.home / '.cache/drive-manager-write-v1' / unit.removesuffix('.service')

    def rc_endpoint(self, remote):
        unit=self.unit_name(remote)
        return self.home / '.local/state/drive-manager/rc' / (unit.removesuffix('.service')+'.sock')

    def ensure_no_dirty_cache(self, remote):
        if transfers.dirty_files(self.write_cache_path(remote)):
            raise transfers.TransferError('uploads_pending')

    def ensure_write_permission(self, remote, config):
        if self.accounts.encrypted(config): return  # Credential backends use mount flags to enforce the selected mode.
        import configparser
        parser=configparser.ConfigParser(interpolation=None);parser.read(config)
        kind=parser.get(remote,'type',fallback='')
        if kind not in {'drive','onedrive','internxt','dropbox','webdav','protondrive'}: raise OperationError('needs_write_auth')
        scope=parser.get(remote,'scope',fallback='drive')
        access=parser.get(remote,'access_scopes',fallback='Files.ReadWrite')
        if ((kind=='drive' and scope not in {'drive','drive.file'})
            or (kind=='onedrive' and not any('ReadWrite' in word for word in access.split()))):
            raise OperationError('needs_write_auth')

    def stop_managed(self, remote, status):
        unit, _=self.identity(remote)
        if status.writable:
            if transfers.pending(self.rc_endpoint(remote)):
                raise transfers.TransferError('uploads_pending')
            self.ensure_no_dirty_cache(remote)
            transfers.ensure_closed(status.path)
            # Normal FUSE unmount blocks open handles; never force or lazy-unmount.
            self.runner.run(['fusermount3','-u','--',status.path])
            if self.properties(remote).get('ActiveState') in {'active','activating'}:
                self.runner.run(['systemctl','--user','stop',unit])
            # If a final write raced with unmount, keep cache and credentials for recovery.
            self.ensure_no_dirty_cache(remote)
        else:
            self.runner.run(['systemctl','--user','stop',unit])

    def cache_directory(self, remote):
        """Isolated read-only cache, never reuse a writable mount's cache."""
        unit, _ = self.identity(remote)
        folder = self.home
        for part in (".cache", "drive-manager-write-v1" if self.settings.load(remote).writable else "drive-manager-readonly-v1", unit.removesuffix(".service")):
            folder = folder / part
            if folder.is_symlink():
                raise OperationError("Cache path must not be a symbolic link")
            folder.mkdir(mode=0o700, exist_ok=True)
            if part != ".cache":
                os.chmod(folder, 0o700)
        return folder

    def save_preferences(self, remote, prefs):
        with self.lock():
            current = self.status(remote)
            if current.state not in {"unmounted", "failed"}:
                raise OperationError("Unmount this account before changing preferences")
            self.settings.validate(prefs)
            self.validate_mount_targets([(remote,prefs)])
            if prefs.mount_path:
                target = Path(prefs.mount_path)
                for mount in self.mounts():
                    path = Path(mount.path)
                    if target.is_relative_to(path) and path != Path("/"):
                        # Normal home filesystems are allowed, FUSE mount ancestry is not.
                        if mount.kind.startswith("fuse") or target == path:
                            raise OperationError("Mount path is already in use")
                    if path.is_relative_to(target):
                        raise OperationError("Mount path contains another mount")
                if target.exists() and (not target.is_dir() or any(target.iterdir())):
                    raise OperationError("Mount directory must be empty")
            old = self.settings.load(remote)
            if prefs.writable: self.ensure_write_permission(remote,self.snapshot_config(remote))
            else: self.ensure_no_dirty_cache(remote)
            self.settings.save(remote, prefs)
            try:
                autostart.update(self.settings)
            except Exception:
                self.settings.save(remote, old)
                raise
            return self.status(remote)

    def mount(self, remote):
        with self.lock():
            status = self.status(remote)
            if status.state not in {"unmounted", "failed"}:
                raise OperationError("Connection already mounted or busy")
            unit, target = self.identity(remote)
            prefs = self.settings.load(remote)
            self.settings.validate(prefs)
            self.validate_mount_targets([(remote,prefs)],tolerate_corrupt=True)
            if target.is_symlink() or target.parent.is_symlink():
                raise OperationError("Mount path must not be a symbolic link")
            target.mkdir(parents=True, exist_ok=True, mode=0o700)
            if any(target.iterdir()):
                raise OperationError("Mount directory must be empty")
            rclone = shutil.which("rclone")
            if not rclone:
                raise OperationError("Rclone is not installed")
            cache = self.cache_directory(remote)
            config = self.snapshot_config(remote)
            if prefs.writable: self.ensure_write_permission(remote, config)
            else: self.ensure_no_dirty_cache(remote)
            import configparser
            if self.accounts.encrypted(config):
                backend = self.encrypted_provider(remote)
            else:
                parser=configparser.ConfigParser(interpolation=None); parser.read(config)
                backend=parser.get(remote,'type',fallback='')
            rate=lambda value:str(value)+"k" if value else "off"
            extra=["--bwlimit="+rate(prefs.upload_kib)+":"+rate(prefs.download_kib)]
            if backend == 'dropbox': extra.append('--dropbox-batch-mode=sync')
            if backend == 'protondrive': extra.append('--protondrive-enable-caching=false')
            endpoint=self.rc_endpoint(remote)
            if any(parent.is_symlink() for parent in [endpoint,*endpoint.parents]): raise OperationError('uploads_unknown')
            endpoint.parent.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(endpoint.parent,0o700)
            endpoint.unlink(missing_ok=True)
            extra+=['--rc','--rc-addr=unix://'+str(endpoint),'--rc-no-auth']
            if self.accounts.encrypted(config):
                from .wallet import Wallet, PASSWORD_COMMAND
                Wallet().ensure()
                extra+=['--password-command='+PASSWORD_COMMAND]
            self.runner.run(["systemd-run", "--user", "--collect", "--expand-environment=no", "--unit=" + unit,
                "--description=Drive Manager "+("read-write" if prefs.writable else "read-only")+" mount v1", "--service-type=exec",
                "--property=StandardOutput=null", "--property=StandardError=null",
                "--property=UMask=0077", "--property=TimeoutStopSec="+("infinity" if prefs.writable else "30"), "--property=Restart=no",
                "--", rclone, "mount", remote + ":", str(target),
                "--devname=" + remote + ":",
                *([] if prefs.writable else ["--read-only"]), "--vfs-cache-mode=full", "--log-level=ERROR",
                "--cache-dir=" + str(cache), f"--vfs-cache-max-size={prefs.cache_gib}G",
                f"--vfs-cache-max-age={prefs.cache_hours}h", "--vfs-cache-min-free-space=512M",
                "--buffer-size=8M", "--vfs-read-ahead=16M",
                "--config=" + str(config)] + extra)
            return self.status(remote)

    def unmount(self, remote, confirmed=False):
        if not confirmed:
            raise OperationError("Explicit confirmation required")
        with self.lock():
            status = self.status(remote)
            if not status.managed:
                raise OperationError("External or busy mounts cannot be stopped")
            self.stop_managed(remote,status)
            return self.status(remote)

    def disconnect(self, remote, confirmed=False, disable_automount=False):
        if not confirmed: raise OperationError("Explicit confirmation required")
        with self.lock():
            status = self.status(remote)
            if status.state not in {"unmounted", "failed"}:
                if not status.managed:
                    raise OperationError("Disconnect the external mount with its original tool first")
                self.stop_managed(remote,status)
                status = self.status(remote)
                if status.state not in {"unmounted", "failed"}:
                    raise OperationError("Mount is still busy")
            if disable_automount:
                old = self.settings.load(remote)
                self.settings.save(remote, replace(old, automount=False))
                try: autostart.update(self.settings)
                except Exception:
                    self.settings.save(remote, old)
                    raise
            return status

    def remove_connection(self, remote, confirmed=False, external_confirmed=False):
        if not confirmed: raise OperationError("Explicit confirmation required")
        with self.lock():
            unit, _ = self.identity(remote)
            private = self.accounts.path(remote)
            external = not private.is_file()
            if external and not external_confirmed:
                raise OperationError("Explicit confirmation required to edit the existing Rclone configuration")
            status = self.status(remote)
            if status.managed:
                self.stop_managed(remote,status)
                status = self.status(remote)
            if status.state not in {"unmounted", "failed"}:
                raise OperationError("Disconnect external or busy mounts before deleting")
            self.ensure_no_dirty_cache(remote)
            # No remote-data command is ever issued: only local connection metadata.
            if external:
                self.runner.run(["rclone", "config", "delete", remote])
            else:
                if private.is_symlink(): raise OperationError("Invalid account configuration")
                private.unlink()
            self.accounts.metadata_path(remote).unlink(missing_ok=True)
            self.settings.path(remote).unlink(missing_ok=True)
            autostart.update(self.settings)
            snapshot = self.home / ".local/state/drive-manager" / (unit + ".conf")
            snapshot.unlink(missing_ok=True)
            # Keep local folders and read cache: deleting a connection must not delete files.
            return self.discover_accounts()

    def is_app_account(self, remote):
        path = self.accounts.path(remote)
        return path.is_file() and not path.is_symlink()

    def open_folder(self, remote):
        status = self.status(remote)
        if status.state not in {"mounted", "external"}:
            raise OperationError("Connection is not mounted")
        self.runner.launch(["xdg-open", Path(status.path).as_uri()])
