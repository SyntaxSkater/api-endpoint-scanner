import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import json
import os
import time
from aiofiles import open as aio_open

class APIScanner:
    def __init__(self, base_url, output_file="output.json", rate_limit=1.0, max_depth=3):
        self.base_url = base_url
        self.output_file = output_file
        self.rate_limit = rate_limit
        self.max_depth = max_depth
        self.discovered_urls = set()
        self.visited_urls = set()

    async def fetch(self, session, url):
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text(), response.url
                else:
                    print(f"Failed to fetch {url}: Status {response.status}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None, None

    async def parse_html(self, html, base_url):
        urls = set()
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['a', 'script', 'img', 'link', 'form']):
            attr = 'href' if tag.name in ['a', 'link', 'form'] else 'src'
            url = tag.get(attr)
            if url and isinstance(url, str) and isinstance(base_url, str):  # Validate both base_url and url
                try:
                    full_url = urljoin(base_url, url)
                    urls.add(full_url)
                except Exception as e:
                    print(f"Error joining URL {url} with base {base_url}: {e}")

        # Extract URLs using regex
        urls.update(re.findall(r'http[s]?://[^\s\"\'<>]+', html))  # Fixed regex
        return urls

    async def save_to_file(self):
        async with aio_open(self.output_file, 'w') as file:
            await file.write(json.dumps(list(self.discovered_urls), indent=4))

    async def crawl(self, url, session, depth):
        if depth > self.max_depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        html, final_url = await self.fetch(session, url)
        if not html:
            return

        urls = await self.parse_html(html, final_url)
        for discovered_url in urls:
            if discovered_url not in self.discovered_urls:
                self.discovered_urls.add(discovered_url)
                if discovered_url.startswith(self.base_url):
                    await asyncio.sleep(self.rate_limit)  # Rate limiting
                    await self.crawl(discovered_url, session, depth + 1)

    async def scan(self):
        async with aiohttp.ClientSession(headers={"User-Agent": "APIScanner/1.0"}) as session:
            await self.crawl(self.base_url, session, 0)
            await self.save_to_file()

    async def analyze_js(self, session, js_url):
        html, _ = await self.fetch(session, js_url)
        if html:
            # Look for API endpoints or similar patterns in JS files
            endpoints = re.findall(r'\"(http[s]?://[^\"]+?)\"', html)
            for endpoint in endpoints:
                if endpoint not in self.discovered_urls:
                    self.discovered_urls.add(endpoint)

    async def run(self):
        start_time = time.time()
        async with aiohttp.ClientSession(headers={"User-Agent": "APIScanner/1.0"}) as session:
            await self.crawl(self.base_url, session, 0)

            # Analyze JavaScript files for additional endpoints
            js_files = [url for url in self.discovered_urls if url.endswith('.js')]
            for js_url in js_files:
                await self.analyze_js(session, js_url)

            await self.save_to_file()
        print(f"Scanning completed in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    base_url = "https://" + input("What URL would you like to scan? Https://")  # Replace with the target URL
    output_file = "discovered_urls.json"
    rate_limit = 0.5  # Adjust rate limit (seconds between requests)
    max_depth = 3  # Set maximum crawl depth

    scanner = APIScanner(base_url, output_file, rate_limit, max_depth)
    asyncio.run(scanner.run())

    print(f"URLs have been saved to {output_file}")
