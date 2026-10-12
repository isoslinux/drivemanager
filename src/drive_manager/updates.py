"""Manual public-release checks. No credentials, downloads, installation or services."""
from dataclasses import dataclass
import json
import re
from urllib.error import HTTPError
from urllib.request import Request, HTTPRedirectHandler, build_opener

REPOSITORY = 'https://github.com/isoslinux/drivemanager'
API = 'https://api.github.com/repos/isoslinux/drivemanager/releases/latest'
LIMIT = 512 * 1024

@dataclass(frozen=True)
class Update:
    state: str
    installed: str
    latest: str = ''
    release_url: str = ''
    rpm_url: str = ''

def version(value):
    if not isinstance(value,str): raise ValueError('invalid_version')
    match = re.fullmatch(r'v?(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})\.(0|[1-9][0-9]{0,3})',value)
    if not match: raise ValueError('invalid_version')
    return tuple(map(int,match.groups()))

def parse_release(data, installed):
    try:
        current = version(installed)
        if not isinstance(data,dict) or data.get('draft') is not False or data.get('prerelease') is not False:
            raise ValueError('not_stable')
        tag = data.get('tag_name'); latest = version(tag)
        number = '.'.join(map(str,latest))
        release_url = REPOSITORY+'/releases/tag/'+tag
        if data.get('html_url') != release_url: raise ValueError('unexpected_repository')
        assets = data.get('assets',[])
        if not isinstance(assets,list): raise ValueError('invalid_assets')
        candidates = []
        for asset in assets:
            if not isinstance(asset,dict) or asset.get('state')!='uploaded': continue
            name = asset.get('name','')
            if not isinstance(name,str): continue
            match = re.fullmatch(r'drive-manager-'+re.escape(number)+r'-([0-9]{1,4})\.fc44\.noarch\.rpm',name)
            if not match: continue
            expected = REPOSITORY+'/releases/download/'+tag+'/'+name
            if asset.get('browser_download_url')==expected:
                candidates.append((int(match.group(1)),expected))
        state = 'update_available' if latest>current else 'update_current' if latest==current else 'update_ahead'
        rpm = max(candidates)[1] if candidates and state=='update_available' else ''
        return Update(state,installed,number,release_url,rpm)
    except (ValueError,TypeError):
        return Update('update_error',installed)

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('unexpected_redirect')

def check(installed):
    try:
        version(installed)
        request = Request(API, headers={'Accept':'application/vnd.github+json',
            'User-Agent':'Drive-Manager/'+installed,'X-GitHub-Api-Version':'2026-03-10'})
        with build_opener(NoRedirect()).open(request,timeout=10) as response:
            if response.status!=200: return Update('update_error',installed)
            payload = response.read(LIMIT+1)
            if len(payload)>LIMIT: return Update('update_error',installed)
        return parse_release(json.loads(payload),installed)
    except HTTPError as error:
        try:
            headers = error.headers or {}
            limited = error.code==429 or (error.code==403 and (headers.get('X-RateLimit-Remaining')=='0' or headers.get('Retry-After')))
            return Update('update_rate_limit' if limited else 'update_error',installed)
        finally: error.close()
    except Exception:
        return Update('update_error',installed)  # Never display server bodies or raw network errors.
