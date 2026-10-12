"""Read-only, allowlisted diagnostics. Never include config, logs or raw errors."""
from dataclasses import dataclass
from pathlib import Path
import os
import re
import shutil
import stat
import subprocess
from . import __version__

@dataclass(frozen=True)
class Check:
    name: str
    state: str
    message: str
    version: str = ''

@dataclass(frozen=True)
class Report:
    checks: tuple[Check, ...]

class Probe:
    """Only fixed diagnostic commands; stderr is discarded and time is bounded."""
    def run(self, args):
        result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, timeout=4, check=False)
        if result.returncode:
            raise RuntimeError('probe_failed')
        return result.stdout

CATALOG = {
    'es': {
        'title': 'Diagnóstico de Drive Manager', 'ok': 'Correcto', 'warning': 'Revisar', 'error': 'Error',
        'rclone': 'Rclone', 'fuse': 'FUSE 3', 'device': 'Dispositivo FUSE',
        'systemd_run': 'systemd-run', 'systemd': 'systemd de usuario', 'dolphin': 'Dolphin',
        'fuser': 'Protección de archivos abiertos', 'wallet': 'KWallet (Internxt)',
        'connection': 'Conexión seleccionada', 'uploads': 'Subidas pendientes',
        'installed': 'Disponible.', 'missing_rclone': 'Instala rclone (versión 1.73 o posterior).',
        'old_rclone': 'Actualiza rclone a la versión 1.73 o posterior.',
        'missing_fuse': 'Instala fuse3.', 'missing_systemd_run': 'Instala systemd.',
        'missing_dolphin': 'Instala dolphin para abrir las carpetas.',
        'missing_fuser': 'Instala psmisc para proteger los archivos abiertos al desconectar.',
        'missing_wallet': 'Instala kf6-kwallet si vas a usar Internxt.',
        'probe_failed': 'No se pudo comprobar. Puede estar ocupado o haber excedido el tiempo de espera.',
        'manager_unavailable': 'No se puede acceder a systemd de usuario. Inicia la aplicación desde tu sesión KDE, sin sudo.',
        'device_unavailable': 'No se puede usar /dev/fuse. Comprueba que FUSE esté disponible en esta sesión.',
        'no_selection': 'Selecciona una cuenta para comprobar su estado local.',
        'mounted': 'Montaje propio activo.', 'external': 'Montaje externo: usa su herramienta original para gestionarlo.',
        'starting': 'El montaje está iniciándose o está ocupado. Espera y actualiza el diagnóstico.',
        'unmounted': 'Cuenta desconectada.', 'failed': 'El montaje ha fallado. Revisa las dependencias y vuelve a conectar.',
        'unknown': 'No se pudo verificar el estado. Actualiza las conexiones y vuelve a intentarlo.',
        'pending': 'Hay cambios pendientes. Espera las subidas; no elimines la conexión ni su caché.',
        'clean': 'No se detectan cambios pendientes en la caché de escritura.',
        'unmonitored': 'Montaje externo: no se puede comprobar su cola de subidas.',
        'footer': 'Comprobación local: no verifica acceso a Internet, permisos OAuth ni disponibilidad de la nube.\nNo incluye tokens, contraseñas, correos, nombres de cuentas, rutas personales ni registros.\nNo cambia la configuración ni inicia o detiene servicios.',
    },
    'en': {
        'title': 'Drive Manager diagnostics', 'ok': 'OK', 'warning': 'Review', 'error': 'Error',
        'rclone': 'Rclone', 'fuse': 'FUSE 3', 'device': 'FUSE device',
        'systemd_run': 'systemd-run', 'systemd': 'User systemd', 'dolphin': 'Dolphin',
        'fuser': 'Open-file protection', 'wallet': 'KWallet (Internxt)',
        'connection': 'Selected connection', 'uploads': 'Pending uploads',
        'installed': 'Available.', 'missing_rclone': 'Install rclone (version 1.73 or later).',
        'old_rclone': 'Update rclone to version 1.73 or later.',
        'missing_fuse': 'Install fuse3.', 'missing_systemd_run': 'Install systemd.',
        'missing_dolphin': 'Install dolphin to open folders.',
        'missing_fuser': 'Install psmisc to protect open files when disconnecting.',
        'missing_wallet': 'Install kf6-kwallet if you want to use Internxt.',
        'probe_failed': 'Could not check. It may be busy or the check may have timed out.',
        'manager_unavailable': 'Cannot reach user systemd. Start this application in your KDE session, without sudo.',
        'device_unavailable': 'Cannot use /dev/fuse. Check that FUSE is available in this session.',
        'no_selection': 'Select an account to check its local state.',
        'mounted': 'Managed mount is active.', 'external': 'External mount: manage it with its original tool.',
        'starting': 'Mount is starting or busy. Wait and refresh diagnostics.',
        'unmounted': 'Account is disconnected.', 'failed': 'Mount failed. Check dependencies and connect again.',
        'unknown': 'Could not verify state. Refresh connections and try again.',
        'pending': 'Changes remain pending. Wait for uploads; keep the connection and its cache.',
        'clean': 'No pending changes detected in the write cache.',
        'unmonitored': 'External mount: its upload queue cannot be checked.',
        'footer': 'Local checks: Internet access, OAuth permissions and cloud availability are not verified.\nContains no tokens, passwords, emails, account names, personal paths or logs.\nDoes not change configuration or start or stop services.',
    },
}

def collect(manager, remote='', probe=None, which=shutil.which, device=Path('/dev/fuse'), access=os.access):
    """The report contains fixed keys and validated numeric versions only."""
    probe = probe or Probe()
    checks = []
    def version_check(name, executable, args, pattern):
        if not which(executable):
            checks.append(Check(name, 'error', 'missing_'+name)); return
        try:
            output = probe.run(args)
            first = output.splitlines()[0] if output else ''
            match = re.fullmatch(pattern, first[:256]) if len(first) <= 256 else None
            if not match: raise ValueError('unexpected_version')
            version = match.group(1)
            if name == 'rclone' and tuple(map(int, version.split('.'))) < (1,73,0):
                checks.append(Check(name, 'error', 'old_rclone', version)); return
            checks.append(Check(name, 'ok', 'installed', version))
        except Exception:
            checks.append(Check(name, 'warning', 'probe_failed'))
    version_check('rclone','rclone',['rclone','version'],r'rclone v(\d{1,3}\.\d{1,3}\.\d{1,3})')
    version_check('fuse','fusermount3',['fusermount3','--version'],r'fusermount3 version: (\d{1,3}\.\d{1,3}\.\d{1,3})')
    try:
        available = stat.S_ISCHR(device.stat().st_mode) and access(device, os.R_OK | os.W_OK)
    except OSError:
        available = False
    checks.append(Check('device','ok' if available else 'error','installed' if available else 'device_unavailable'))
    for name,exe in [('systemd_run','systemd-run'),('dolphin','dolphin'),('fuser','fuser'),('wallet','kwallet-query')]:
        available = bool(which(exe))
        checks.append(Check(name,'ok' if available else 'warning' if name=='wallet' else 'error',
                            'installed' if available else 'missing_'+name))
    try:
        if not which('systemctl'): raise RuntimeError('missing')
        # Query a single non-sensitive manager property, never show-environment/journal.
        version = probe.run(['systemctl','--user','show','--property=Version','--value']).strip()
        match = re.fullmatch(r'(\d{1,4}(?:\.\d{1,3})?)(?:[-+~][A-Za-z0-9._+~:-]{1,64})?', version)
        if not match: raise ValueError('unexpected_version')
        checks.append(Check('systemd','ok','installed',match.group(1)))
    except Exception:
        checks.append(Check('systemd','error','manager_unavailable'))
    if not remote:
        checks.append(Check('connection','warning','no_selection'))
        return Report(tuple(checks))
    try:
        status = manager.status(remote)
        state = status.state if status.state in {'mounted','unmounted','failed','external','starting'} else 'unknown'
        checks.append(Check('connection','error' if state in {'failed','unknown'} else 'warning' if state in {'external','starting'} else 'ok', state))
        if state in {'external','starting'}:
            checks.append(Check('uploads','warning','unmonitored'))
        else:
            from .transfers import dirty_files
            dirty = dirty_files(manager.write_cache_path(remote))
            if status.pending < 0:
                checks.append(Check('uploads','warning','unknown'))
            else:
                pending = bool(dirty or status.pending)
                checks.append(Check('uploads','warning' if pending else 'ok','pending' if pending else 'clean'))
    except Exception:
        if not any(check.name == 'connection' for check in checks):
            checks.append(Check('connection','warning','unknown'))
        checks.append(Check('uploads','warning','unknown'))
    return Report(tuple(checks))

def format_report(report, language='es'):
    t = CATALOG['en' if language=='en' else 'es']
    lines = [t['title']+' · '+__version__, '']
    for check in report.checks:
        # Unknown values cannot introduce raw output, even from an injected report.
        if check.name not in t or check.state not in {'ok','warning','error'} or check.message not in t: continue
        version = ' '+check.version if re.fullmatch(r'\d{1,4}(?:\.\d{1,3}){0,2}',check.version) else ''
        lines.append(f'{t[check.state]} · {t[check.name]}{version}: {t[check.message]}')
    return '\n'.join(lines+['',t['footer']])
