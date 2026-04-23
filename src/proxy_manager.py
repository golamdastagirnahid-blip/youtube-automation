import requests
import random
import time
from src.config import DOWNLOADS_DIR


class ProxyManager:
    def __init__(self):
        self.proxy_sources = {
            "BD": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/BD.txt",
            "IN": "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/countries/IN.txt",
        }
        self.working_proxies = []

    def get_fresh_proxies(self):
        """Fetch latest proxies from proxifly repo"""
        all_proxies = []
        print("🔄 Fetching fresh proxies from Bangladesh & India...")

        for country, url in self.proxy_sources.items():
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    proxies = [line.strip() for line in r.text.splitlines() 
                              if line.strip() and not line.startswith('#')]
                    all_proxies.extend([f"http://{proxy}" for proxy in proxies])
                    print(f"   Found {len(proxies)} {country} proxies")
            except Exception as e:
                print(f"   Failed to fetch {country} proxies: {e}")

        random.shuffle(all_proxies)
        self.working_proxies = all_proxies
        print(f"✅ Total fresh proxies loaded: {len(all_proxies)}")
        return all_proxies

    def test_proxy(self, proxy, timeout=8):
        """Test if proxy works"""
        try:
            proxies = {"http": proxy, "https": proxy}
            r = requests.get("https://www.youtube.com", proxies=proxies, timeout=timeout)
            return r.status_code in (200, 403)  # 403 is acceptable for YouTube
        except:
            return False

    def get_working_proxy(self):
        """Return a working proxy from BD/IN"""
        if not self.working_proxies:
            self.get_fresh_proxies()

        # Try up to 15 proxies
        for _ in range(15):
            if not self.working_proxies:
                self.get_fresh_proxies()
            
            proxy = random.choice(self.working_proxies)
            print(f"   🔍 Testing proxy: {proxy}")

            if self.test_proxy(proxy):
                print(f"   ✅ Working proxy found: {proxy}")
                return proxy
            else:
                if proxy in self.working_proxies:
                    self.working_proxies.remove(proxy)

        print("⚠️ No working proxy found after testing")
        return None
