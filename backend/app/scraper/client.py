import os
import time
import hashlib
import requests
from typing import Optional

class SafeHttpClient:
    def __init__(self, cache_dir: Optional[str] = None, min_interval: float = 1.5):
        self.min_interval = min_interval
        self.last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
        })
        
        if cache_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(base_dir, ".cache_html")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, url: str) -> str:
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.html")

    def fetch(self, url: str, use_cache: bool = True, encoding: Optional[str] = None) -> str:
        cache_path = self._get_cache_path(url)
        
        if use_cache and os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        resp = self.session.get(url, timeout=10)
        self.last_request_time = time.time()
        resp.raise_for_status()

        if encoding:
            resp.encoding = encoding
        else:
            # Detect or fallback to apparent encoding / euc-jp / utf-8
            if "euc-jp" in resp.text.lower() or "euc-jp" in resp.headers.get("Content-Type", "").lower():
                resp.encoding = "euc-jp"
            else:
                resp.encoding = resp.apparent_encoding or "utf-8"

        html = resp.text
        if use_cache:
            try:
                with open(cache_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(html)
            except Exception as e:
                print(f"Warning: Failed to write cache: {e}")

        return html
