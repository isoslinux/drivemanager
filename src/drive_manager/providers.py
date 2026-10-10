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
)
ACTIVE_TYPES = {provider.key for provider in PROVIDERS if provider.available}
