"""HTTP client for source adapters."""

import json
import urllib.request
import urllib.error


class HttpClient:
    """Minimal HTTP client for source adapters."""
    
    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self._headers = headers or {}
    
    def get_json(self, url: str) -> dict | list:
        """GET request returning parsed JSON."""
        req = urllib.request.Request(url)
        for key, value in self._headers.items():
            req.add_header(key, value)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
