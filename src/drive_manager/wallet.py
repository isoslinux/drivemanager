"""KDE Wallet stores only the key for encrypted Rclone configurations."""
import os
import secrets
import subprocess
from .process import OperationError

PASSWORD_COMMAND = '/usr/bin/kwallet-query -f Passwords -r drive-manager-rclone-key kdewallet'

def clean_env():
    return {k:v for k,v in os.environ.items() if not k.startswith('RCLONE_')}

class Wallet:
    def ensure(self):
        try:
            args=['kwallet-query','-f','Passwords','-r','drive-manager-rclone-key','kdewallet']
            result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                                  stdin=subprocess.DEVNULL,timeout=60,env=clean_env())
            if result.returncode==0 and result.stdout.strip(): return
            listed=subprocess.run(['kwallet-query','-f','Passwords','-l','kdewallet'],
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                timeout=60,env=clean_env())
            if listed.returncode or b'drive-manager-rclone-key' in listed.stdout:
                raise ValueError()  # Never replace an existing key after a failed read.
            key=secrets.token_urlsafe(48)
            result=subprocess.run(['kwallet-query','-f','Passwords','-w','drive-manager-rclone-key','kdewallet'],
                input=key.encode()+b'\n',stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                timeout=60,env=clean_env())
            if result.returncode: raise ValueError()
        except Exception:
            raise OperationError('wallet_error') from None
