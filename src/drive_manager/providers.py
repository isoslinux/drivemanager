"""Supported providers and their authentication flow; OneDrive uses the browser flow."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Provider:
    key: str
    label: str
    authentication: str
    available: bool = True

PROVIDERS = (
    Provider('drive', 'Google Drive', 'browser'),
    Provider('internxt', 'Internxt', 'credentials'),
    Provider('onedrive', 'OneDrive', 'browser'),
    Provider('webdav', 'Nextcloud / WebDAV', 'credentials'),
    Provider('dropbox', 'Dropbox', 'browser'),
    Provider('protondrive', 'Proton Drive (beta)', 'credentials'),
)
ACTIVE_TYPES = {provider.key for provider in PROVIDERS if provider.available}

ENCRYPTED_TYPES = {"internxt", "webdav", "protondrive"}

class Registration(tuple):
    """Two-item staging result with allowlisted, non-secret backend metadata."""
    def __new__(cls, name, path, provider):
        if provider not in ACTIVE_TYPES: raise ValueError("Unsupported provider")
        result = super().__new__(cls, (name, path)); result.provider = provider
        return result
