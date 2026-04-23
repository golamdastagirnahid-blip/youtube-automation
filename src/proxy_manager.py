"""
Proxy Manager
Gets free working proxies and rotates them
"""

import requests
import random


# ✅ Free Proxy Sources
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=5000&country=US&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
]

# US Based proxy list (hardcoded backup)
BACKUP_PROXIES = [
    "http://103.152.112.162:80",
    "http://103.149.162.195:80",
    "http://45.77.56.114:80",
    "http://191.96.42.80:8080",
    "http://20.206.106.192:80",
    "http://103.83.232.122:80",
]


class ProxyManager:

    def __init__(self):
        self.working_proxies = []
        self.current_index   = 0

    def fetch_proxies(self):
        """Fetch fresh proxies from free sources"""
        print("🔄 Fetching fresh proxies...")
        proxies = set()

        for source in PROXY_SOURCES:
            try:
                r = requests.get(source, timeout=10)
                if r.status_code == 200:
                    lines = r.text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line:
                            if not line.startswith('http'):
                                line = f"http://{line}"
                            proxies.add(line)
            except Exception:
                continue

        # Add backup proxies
        for p in BACKUP_PROXIES:
            proxies.add(p)

        print(f"   Found {len(proxies)} proxies")
        self.working_proxies = list(proxies)
        return self.working_proxies

    def get_proxy(self):
        """Get a random proxy"""
        if not self.working_proxies:
            self.fetch_proxies()

        if self.working_proxies:
            proxy = random.choice(self.working_proxies)
            return proxy
        return None

    def get_next_proxy(self):
        """Get next proxy in rotation"""
        if not self.working_proxies:
            self.fetch_proxies()

        if self.working_proxies:
            proxy = self.working_proxies[
                self.current_index % len(self.working_proxies)
            ]
            self.current_index += 1
            return proxy
        return None

    def test_proxy(self, proxy):
        """Test if a proxy is working"""
        try:
            r = requests.get(
                "https://www.google.com",
                proxies={"http": proxy, "https": proxy},
                timeout=5
            )
            return r.status_code == 200
        except Exception:
            return False

    def get_working_proxy(self):
        """Get a verified working proxy"""
        if not self.working_proxies:
            self.fetch_proxies()

        random.shuffle(self.working_proxies)

        for proxy in self.working_proxies[:10]:
            if self.test_proxy(proxy):
                print(f"   ✅ Working proxy: {proxy}")
                return proxy

        print("   ⚠️ No verified proxy found, using random")
        return self.get_proxy()