"""
Proxy Manager
Fetches fresh BD/IN proxies from proxifly repo
"""

import requests
import random


class ProxyManager:

    def __init__(self):
        self.proxies = []
        self.sources = {
            "BD": (
                "https://raw.githubusercontent.com/proxifly/"
                "free-proxy-list/main/proxies/countries/BD/data.txt"
            ),
            "IN": (
                "https://raw.githubusercontent.com/proxifly/"
                "free-proxy-list/main/proxies/countries/IN/data.txt"
            ),
        }

    # ─────────────────────────────────────────────
    # Fetch Fresh Proxies
    # ─────────────────────────────────────────────
    def get_fresh_proxies(self):
        """Fetch latest proxies from BD and IN"""
        all_proxies = []
        print("🔄 Fetching fresh proxies...")

        for country, url in self.sources.items():
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    lines = [
                        line.strip()
                        for line in r.text.splitlines()
                        if line.strip() and not line.startswith('#')
                    ]
                    for line in lines:
                        if line.startswith("http") or \
                           line.startswith("socks"):
                            all_proxies.append(line)
                        else:
                            all_proxies.append(f"http://{line}")

                    print(f"   {country}: {len(lines)} proxies")
                else:
                    print(f"   {country}: HTTP {r.status_code}")
            except Exception as e:
                print(f"   {country} failed: {e}")

        random.shuffle(all_proxies)
        self.proxies = all_proxies
        print(f"   Total: {len(all_proxies)} proxies")
        return all_proxies

    # ─────────────────────────────────────────────
    # Test Single Proxy
    # ─────────────────────────────────────────────
    def test_proxy(self, proxy, timeout=8):
        """Test if proxy works with YouTube"""
        try:
            r = requests.get(
                "https://www.youtube.com",
                proxies = {"http": proxy, "https": proxy},
                timeout = timeout,
                headers = {"User-Agent": "Mozilla/5.0"}
            )
            return r.status_code in (200, 403)
        except Exception:
            return False

    # ─────────────────────────────────────────────
    # Get Working Proxy
    # ─────────────────────────────────────────────
    def get_working_proxy(self):
        """Get a verified working proxy"""
        if not self.proxies:
            self.get_fresh_proxies()

        tested   = 0
        max_test = min(15, len(self.proxies))

        for proxy in list(self.proxies[:max_test]):
            tested += 1
            print(f"   🔍 Testing [{tested}/{max_test}]: {proxy}")

            if self.test_proxy(proxy):
                print(f"   ✅ Working proxy: {proxy}")
                return proxy
            else:
                if proxy in self.proxies:
                    self.proxies.remove(proxy)

        # Return random if all tests failed
        if self.proxies:
            proxy = random.choice(self.proxies)
            print(f"   🎲 Using random: {proxy}")
            return proxy

        return None
