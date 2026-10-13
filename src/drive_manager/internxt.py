"""Encrypted credential staging over private Unix RC, including Internxt 2FA."""
import http.client
import json
from pathlib import Path
import os
import socket
import subprocess
import tempfile
import time
import shutil
from .process import OperationError
from .wallet import Wallet, PASSWORD_COMMAND, clean_env

class UnixConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__('localhost', timeout=45); self.socket_path=str(path)
    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout); self.sock.connect(self.socket_path)

def request(path, method, body):
    error_key = 'credentials_error'
    connection=UnixConnection(path)
    try:
        connection.request('POST','/'+method,json.dumps(body),{'Content-Type':'application/json'})
        response=connection.getresponse(); data=response.read(1024*1024)
        if response.status!=200: raise OperationError(error_key)
        return json.loads(data)
    except Exception:
        raise OperationError(error_key) from None
    finally: connection.close()

def authorize(accounts, remote, email, password, cancel, ask_code, *, provider="internxt", parameters=None, existing=None):
    from .providers import ENCRYPTED_TYPES, Registration
    if provider not in ENCRYPTED_TYPES: raise OperationError('credentials_error')
    error_key = 'internxt_error' if provider == 'internxt' else 'credentials_error'
    accounts.validate_name(remote)
    if not email.strip() or not password: raise OperationError(error_key)
    if existing is not None:
        if Path(existing)!=accounts.path(remote) or Path(existing).is_symlink() or not accounts.encrypted(existing):
            raise OperationError('credential_renew_error')
    else: Wallet().ensure()
    folder=accounts.folder
    if any(parent.is_symlink() for parent in [folder,*folder.parents]): raise OperationError(error_key)
    folder.mkdir(parents=True,exist_ok=True,mode=0o700); os.chmod(folder,0o700); os.chmod(folder.parent,0o700)
    fd,temp=tempfile.mkstemp(dir=folder,prefix='.oauth-',suffix='.tmp')
    staged=Path(temp); process=None; completed=False
    try:
        with os.fdopen(fd,'wb') as file:
            if existing is not None:
                with Path(existing).open('rb') as original: shutil.copyfileobj(original,file)
            else: file.write(('['+remote+']\ntype = '+provider+'\n').encode())
        encrypted=None if existing is not None else subprocess.run(['rclone','config','encryption','set','--config='+temp,
            '--password-command='+PASSWORD_COMMAND],stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,env=clean_env(),umask=0o077)
        if (encrypted is not None and encrypted.returncode) or not accounts.encrypted(staged): raise OperationError('wallet_error')
        with tempfile.TemporaryDirectory(prefix='drive-manager-auth-') as channel:
            endpoint=Path(channel)/'rc.sock'
            process=subprocess.Popen(['rclone','rcd','--config='+temp,'--password-command='+PASSWORD_COMMAND,
                '--rc-addr=unix://'+str(endpoint),'--rc-no-auth','--log-level=ERROR'],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                env=clean_env(),umask=0o077)
            deadline=time.monotonic()+15
            while not endpoint.exists():
                if cancel.wait(.1) or process.poll() is not None or time.monotonic()>deadline:
                    raise OperationError(error_key)
            os.chmod(endpoint,0o600)
            if cancel.is_set(): raise OperationError(error_key)
            parameters=parameters if parameters is not None else {'email':email.strip(),'pass':password}
            if existing is not None:
                previous=request(endpoint,'config/get',{'name':remote})
                field={'internxt':'email','webdav':'user','protondrive':'username'}[provider]
                old_user=str(previous.get(field,'')).strip();new_user=str(parameters.get(field,'')).strip()
                same_user=old_user==new_user if provider=='webdav' else old_user.casefold()==new_user.casefold()
                if previous.get('type')!=provider or not old_user or not same_user:
                    raise OperationError('credential_identity')
                if provider=='webdav' and str(previous.get('url','')).rstrip('/')!=str(parameters.get('url','')).rstrip('/'):
                    raise OperationError('credential_identity')
                if provider=='webdav' and previous.get('vendor')!='nextcloud':
                    raise OperationError('credential_custom')
                if previous.get('bearer_token') or previous.get('otp_secret_key'):
                    raise OperationError('credential_custom')
                excluded={'type','pass','password','mailbox_password','2fa','mnemonic','token','access_token',
                          'refresh_token','client_uid','client_access_token','client_refresh_token','client_salted_key_pass'}
                retained={key:value for key,value in previous.items() if key not in excluded}
                previous.clear();retained.update(parameters);parameters=retained
                request(endpoint,'config/delete',{'name':remote})
            result=request(endpoint,'config/create',{'name':remote,'type':provider,
                'parameters':parameters,
                'opt':{'obscure':True,'nonInteractive':True}})
            password=''
            state=result.get('State','')
            if state:
                option=result.get('Option') or {}
                if option.get('Name')!='config_2fa': raise OperationError(error_key)
                code=ask_code(cancel)
                if cancel.is_set() or not code: raise OperationError(error_key)
                result=request(endpoint,'config/update',{'name':remote,'parameters':{},
                    'opt':{'nonInteractive':True,'continue':True,'state':state,'result':code}})
            if cancel.is_set() or result.get('State'): raise OperationError(error_key)
            if provider != 'internxt' or existing is not None:
                # Force backend authentication before committing credentials. List only
                # one directory level; names stay in memory and are never displayed/logged.
                request(endpoint, 'operations/list', {'fs':remote+':', 'remote':'', 'opt':{'dirsOnly':True, 'recurse':False}})
                if cancel.is_set(): raise OperationError(error_key)
        if not accounts.encrypted(staged): raise OperationError(error_key)
        completed=True
        return Registration(remote,staged,provider)
    except OperationError as error:
        if str(error) == 'credentials_error': raise OperationError(error_key) from None
        raise
    except Exception:
        raise OperationError(error_key) from None
    finally:
        if process is not None:
            process.terminate()
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired: process.kill();process.wait()

        if not completed: staged.unlink(missing_ok=True)
