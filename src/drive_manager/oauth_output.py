"""Bounded in-memory OAuth output parsing. Never persist or display raw lines."""
import re

class OAuthOutput:
    def __init__(self, on_url=None):
        self.pending = b''
        self.on_url = on_url
        self.url = None
        self.error_key = None

    def feed(self, chunk):
        self.pending += chunk
        while b'\n' in self.pending:
            line, self.pending = self.pending.split(b'\n', 1)
            text = line[:8192].decode('utf-8', errors='replace')
            match = re.search(r'http://127\.0\.0\.1:53682/auth\?state=[A-Za-z0-9_-]{16,256}(?=\s|$)', text)
            if match and self.url is None:
                self.url = match.group(0)
                if self.on_url: self.on_url(self.url)
            if 'address already in use' in text:
                self.error_key = 'oauth_port'
            elif 'failed to start auth webserver' in text:
                self.error_key = 'oauth_server'
        if len(self.pending) > 8192:
            self.pending = b''
