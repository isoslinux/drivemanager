"""Microsoft browser OAuth and explicit drive choice using Rclone's state machine."""
import configparser
import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import time
from .accounts import AuthorizationError
from .oauth_output import OAuthOutput
from .wallet import clean_env

WRITE_SCOPES = 'Files.Read Files.ReadWrite Files.Read.All Files.ReadWrite.All offline_access'
SCOPES = 'Files.Read Files.Read.All offline_access'

def run_step(args, cancel, on_url):
    process=None; data=bytearray(); output=OAuthOutput(on_url)
    selector=selectors.DefaultSelector()
    try:
        process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 env=clean_env(),umask=0o077)
        for stream in (process.stdout,process.stderr):
            os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ)
        deadline=time.monotonic()+600
        while selector.get_map():
            if cancel.is_set() or time.monotonic()>deadline: raise AuthorizationError('auth_error')
            for event,_ in selector.select(.2):
                chunk=os.read(event.fileobj.fileno(),4096)
                if not chunk:
                    selector.unregister(event.fileobj);continue
                if event.fileobj is process.stdout:
                    data.extend(chunk)
                    if len(data)>1024*1024:raise AuthorizationError('auth_error')
                else:output.feed(chunk)
        process.wait(timeout=3)
        if process.returncode or cancel.is_set():raise AuthorizationError(output.error_key or 'auth_error')
        result=json.loads(data)
        if not isinstance(result,dict) or result.get('Error'):raise AuthorizationError('auth_error')
        return result
    except AuthorizationError:raise
    except Exception:raise AuthorizationError(output.error_key or 'auth_error') from None
    finally:
        selector.close()
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait()
            for stream in (process.stdout,process.stderr):stream.close()

def authorize(accounts, remote, cancel, on_url, ask_drive, writable=False):
    if cancel.is_set():raise AuthorizationError('auth_error')
    folder=accounts.folder
    if any(parent.is_symlink() for parent in [folder,*folder.parents]):raise AuthorizationError('auth_error')
    folder.mkdir(parents=True,exist_ok=True,mode=0o700);os.chmod(folder,0o700);os.chmod(folder.parent,0o700)
    fd,temp=tempfile.mkstemp(dir=folder,prefix='.oauth-',suffix='.tmp');os.close(fd)
    staged=Path(temp)
    options=['config_is_local=true','config_auth_no_browser=true','config_type=onedrive',
             'config_drive_ok=true','access_scopes='+(WRITE_SCOPES if writable else SCOPES)]
    flags=['--config='+temp,'--non-interactive','--log-level=NOTICE']
    try:
        result=run_step(['rclone','config','create',remote,'onedrive']+options+flags,cancel,on_url)
        for _ in range(6):
            state=result.get('State','')
            if not state:break
            option=result.get('Option') or {}
            if option.get('Name')!='config_driveid':raise AuthorizationError('onedrive_error')
            choices=[(item['Value'],item.get('Help', 'OneDrive')) for item in option.get('Examples',[])
                     if isinstance(item.get('Value'),str) and item['Value']]
            if not choices:raise AuthorizationError('onedrive_error')
            value=choices[0][0] if len(choices)==1 else ask_drive(choices,cancel) if ask_drive else None
            if cancel.is_set() or value not in {entry[0] for entry in choices}:raise AuthorizationError('onedrive_error')
            result=run_step(['rclone','config','update',remote,'--continue','--state='+state,'--result='+value]+options+flags,cancel,on_url)
        else:raise AuthorizationError('onedrive_error')
        parser=configparser.ConfigParser(interpolation=None);parser.read(staged)
        if (not parser.has_section(remote) or parser.get(remote,'type',fallback='')!='onedrive'
            or not parser.get(remote,'token',fallback='') or not parser.get(remote,'drive_id',fallback='')
            or parser.get(remote,'drive_type',fallback='') not in {'personal','business'}):
            raise AuthorizationError('onedrive_error')
        os.chmod(staged,0o600);return staged
    except Exception:
        staged.unlink(missing_ok=True);raise
