import os
import time
import hashlib
import requests
from typing import Optional

class SafeHttpClient:
    def __init__(self, cache_dir: Optional[str] = None, min_interval: float = 1.0):
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
        
        # 不要な古いキャッシュによる誤動作を防ぐため、live速報系はキャッシュしない
        if "race_list_sub.html" in url or "shutuba.html" in url:
            use_cache = False

        if use_cache and os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                pass

        # レートリミット（サーバー負荷軽減）
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        resp = self.session.get(url, timeout=12)
        self.last_request_time = time.time()
        resp.raise_for_status()

        # エンコーディングの適切な自動判定
        # db.netkeiba.com は EUC-JP、race.netkeiba.com は UTF-8
        if encoding:
            target_encodings = [encoding, "utf-8", "euc-jp", "cp932"]
        elif "db.netkeiba.com" in url:
            target_encodings = ["euc-jp", "utf-8", "cp932"]
        elif "race.netkeiba.com" in url:
            target_encodings = ["utf-8", "euc-jp", "cp932"]
        else:
            target_encodings = [resp.apparent_encoding or "utf-8", "euc-jp", "utf-8"]

        html = None
        for enc in target_encodings:
            if not enc: continue
            try:
                html = resp.content.decode(enc)
                break
            except Exception:
                continue

        if html is None:
            html = resp.content.decode("utf-8", errors="replace")

        if use_cache:
            try:
                with open(cache_path, "w", encoding="utf-8", errors="replace") as f:
                    f.write(html)
            except Exception as e:
                print(f"Warning: Failed to write cache: {e}")

        return html
