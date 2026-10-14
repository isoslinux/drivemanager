"""Strict portable preference files. Credentials and cache contents are excluded."""
from dataclasses import asdict,replace
from pathlib import Path
import json,os,tempfile
from .settings import Preferences
from .providers import ACTIVE_TYPES
from .process import OperationError
from . import autostart


def atomic(path,data):
    path=Path(path)
    if any(p.is_symlink() for p in [path,*path.parents]):raise OperationError('portable_error')
    fd,temp=tempfile.mkstemp(dir=path.parent,prefix='.drive-manager-')
    try:
        with os.fdopen(fd,'wb') as file:
            os.fchmod(file.fileno(),0o600);file.write(data);file.flush();os.fsync(file.fileno())
        os.replace(temp,path)
    finally:Path(temp).unlink(missing_ok=True)


def export(manager,path):
    with manager.lock():
        rows=[]
        for name in manager.discover_accounts():
            manager.accounts.validate_name(name)
            prefs=manager.settings.load(name);data=asdict(prefs)
            if prefs.mount_path:data['mount_path']=str(Path(prefs.mount_path).relative_to(manager.home))
            rows.append({'name':name,'provider':manager.provider_of(name),'preferences':data})
        if not 1<=len(rows)<=100:raise OperationError('portable_error')
        payload={'format':'drive-manager-settings','version':1,'accounts':rows}
        destination=Path(path)
        if not destination.is_absolute() or destination.suffix.lower()!='.json' or destination.exists() and destination.is_dir():raise OperationError('portable_error')
        # Never overwrite a live account configuration or its metadata/preferences.
        if any(destination.is_relative_to(manager.home/folder) for folder in ('.config','.cache','.local')):
            raise OperationError('portable_error')
        atomic(destination,json.dumps(payload,ensure_ascii=False,indent=2).encode())
    return len(rows)


def plan(manager,path):
    try:
        source=Path(path)
        if source.is_symlink() or not source.is_file() or source.stat().st_size>1024**2:raise ValueError()
        data=json.loads(source.read_text())
        if set(data)!={'format','version','accounts'} or data['format']!='drive-manager-settings' or type(data['version']) is not int or data['version']!=1:raise ValueError()
        if not isinstance(data['accounts'],list) or not 1<=len(data['accounts'])<=100:raise ValueError()
        known=set(manager.discover_accounts());seen=set();rows=[]
        for row in data['accounts']:
            if not isinstance(row,dict) or set(row)!={'name','provider','preferences'}:raise ValueError()
            name=row['name'];manager.accounts.validate_name(name)
            if not isinstance(row['preferences'],dict):raise ValueError()
            if name not in known or name in seen or row['provider'] not in ACTIVE_TYPES or manager.provider_of(name)!=row['provider']:raise ValueError()
            seen.add(name);values=dict(row['preferences']);relative=values.get('mount_path','')
            if not isinstance(relative,str) or Path(relative).is_absolute() or '..' in Path(relative).parts:raise ValueError()
            values['mount_path']=str(manager.home/relative) if relative else ''
            prefs=manager.settings.validate(Preferences(**values));rows.append((name,row['provider'],prefs))
        return rows
    except Exception:raise OperationError('portable_error') from None


def apply(manager,path,confirmed=False,reviewed=None,selected=None):
    if not confirmed:raise OperationError('portable_error')
    with manager.lock():
        rows=plan(manager,path);originals={}
        if reviewed is not None and rows!=reviewed:raise OperationError("portable_error")
        if selected is not None:
            available={name:(provider,prefs) for name,provider,prefs in rows};seen=set()
            if not selected:raise OperationError('portable_error')
            for name,provider,prefs in selected:
                if name in seen or name not in available:raise OperationError('portable_error')
                expected_provider,original=available[name]
                if provider!=expected_provider or replace(prefs,mount_path=original.mount_path)!=original:raise OperationError('portable_error')
                manager.settings.validate(prefs);seen.add(name)
            rows=selected
        manager.validate_mount_targets([(name,prefs) for name,_,prefs in rows])
        names=manager.discover_accounts()
        for name,_,prefs in rows:
            if manager.status(name).state not in {'unmounted','failed'}:raise OperationError('portable_busy')
            manager.ensure_no_dirty_cache(name)
            if prefs.writable:manager.ensure_write_permission(name,manager.snapshot_config(name))
            target=Path(prefs.mount_path) if prefs.mount_path else manager.home/'DriveManager'/manager.settings.path(name).stem
            if target.exists() and (not target.is_dir() or any(target.iterdir())):raise OperationError('portable_error')
            settings=manager.settings.path(name)
            if any(p.is_symlink() for p in [settings,*settings.parents]):raise OperationError('portable_error')
            originals[name]=settings.read_bytes() if settings.exists() else None
        try:
            for name,_,prefs in rows:manager.settings.save(name,prefs)
            autostart.update(manager.settings)
        except Exception:
            for name,before in originals.items():
                path=manager.settings.path(name)
                if before is None:path.unlink(missing_ok=True)
                else:atomic(path,before)
            raise OperationError('portable_error') from None
        return names


def setup_done(manager):
    path=manager.home/'.config/drive-manager/setup.json'
    try:return not path.is_symlink() and json.loads(path.read_text())=={'complete':True}
    except Exception:return False


def finish_setup(manager):
    folder=manager.home/'.config/drive-manager'
    if any(p.is_symlink() for p in [folder,*folder.parents]):raise OperationError('portable_error')
    folder.mkdir(parents=True,exist_ok=True,mode=0o700);folder.chmod(0o700)
    atomic(folder/'setup.json',b'{"complete":true}\n')
