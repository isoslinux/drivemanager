"""Internxt registration through a private Unix RC socket and encrypted config."""
import http.client
import json
from pathlib import Path
import os
import socket
import subprocess
import tempfile
import time
from .process import OperationError
from .wallet import Wallet, PASSWORD_COMMAND, clean_env

class UnixConnection(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__('localhost', timeout=45); self.socket_path=str(path)
    def connect(self):
        self.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout); self.sock.connect(self.socket_path)

def request(path, method, body):
    connection=UnixConnection(path)
    try:
        connection.request('POST','/'+method,json.dumps(body),{'Content-Type':'application/json'})
        response=connection.getresponse(); data=response.read(1024*1024)
        if response.status!=200: raise OperationError('internxt_error')
        return json.loads(data)
    except Exception:
        raise OperationError('internxt_error') from None
    finally: connection.close()

def authorize(accounts, remote, email, password, cancel, ask_code):
    accounts.validate_name(remote)
    if not email.strip() or not password: raise OperationError('internxt_error')
    Wallet().ensure()
    folder=accounts.folder
    if any(parent.is_symlink() for parent in [folder,*folder.parents]): raise OperationError('internxt_error')
    folder.mkdir(parents=True,exist_ok=True,mode=0o700); os.chmod(folder,0o700); os.chmod(folder.parent,0o700)
    fd,temp=tempfile.mkstemp(dir=folder,prefix='.oauth-',suffix='.tmp')
    with os.fdopen(fd,'w') as file: file.write('['+remote+']\ntype = internxt\n')
    staged=Path(temp); process=None; completed=False
    try:
        encrypted=subprocess.run(['rclone','config','encryption','set','--config='+temp,
            '--password-command='+PASSWORD_COMMAND],stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=60,env=clean_env(),umask=0o077)
        if encrypted.returncode or not accounts.encrypted(staged): raise OperationError('wallet_error')
        with tempfile.TemporaryDirectory(prefix='drive-manager-internxt-') as channel:
            endpoint=Path(channel)/'rc.sock'
            process=subprocess.Popen(['rclone','rcd','--config='+temp,'--password-command='+PASSWORD_COMMAND,
                '--rc-addr=unix://'+str(endpoint),'--rc-no-auth','--log-level=ERROR'],
                stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                env=clean_env(),umask=0o077)
            deadline=time.monotonic()+15
            while not endpoint.exists():
                if cancel.wait(.1) or process.poll() is not None or time.monotonic()>deadline:
                    raise OperationError('internxt_error')
            os.chmod(endpoint,0o600)
            if cancel.is_set(): raise OperationError('internxt_error')
            result=request(endpoint,'config/create',{'name':remote,'type':'internxt',
                'parameters':{'email':email.strip(),'pass':password},
                'opt':{'obscure':True,'nonInteractive':True}})
            password=''
            state=result.get('State','')
            if state:
                option=result.get('Option') or {}
                if option.get('Name')!='config_2fa': raise OperationError('internxt_error')
                code=ask_code(cancel)
                if cancel.is_set() or not code: raise OperationError('internxt_error')
                result=request(endpoint,'config/update',{'name':remote,'parameters':{},
                    'opt':{'nonInteractive':True,'continue':True,'state':state,'result':code}})
            if cancel.is_set() or result.get('State'): raise OperationError('internxt_error')
        if not accounts.encrypted(staged): raise OperationError('internxt_error')
        completed=True
        return remote,staged
    except OperationError:
        raise
    except Exception:
        raise OperationError('internxt_error') from None
    finally:
        if process is not None:
            process.terminate()
            try: process.wait(timeout=3)
            except subprocess.TimeoutExpired: process.kill();process.wait()

        if not completed: staged.unlink(missing_ok=True)
