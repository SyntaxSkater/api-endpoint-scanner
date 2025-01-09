import asyncio
import aiohttp
from bs4 import BeautifulSoup, FeatureNotFound
import re
from urllib.parse import urljoin, urlparse
import os
import json
import time
from collections import Counter, defaultdict
from aiofiles import open as aio_open
import socket

class APIScanner:
    def __init__(self, base_url, results_dir="results", output_file="output.json", objects_file="objects.json", keywords_file="keywords.txt", denied_urls_file="denied_urls.txt", errors_file="errors.txt", changing_data_file="changing_data.txt", custom_keywords_file="custom_keywords.txt", rate_limit=1.0, max_depth=3, scan_urls=True, scan_objects=True, download_files=False):
        self.base_url = base_url
        self.results_dir = results_dir
        self.output_file = os.path.join(results_dir, output_file)
        self.objects_file = os.path.join(results_dir, objects_file)
        self.keywords_file = os.path.join(results_dir, keywords_file)
        self.denied_urls_file = os.path.join(results_dir, denied_urls_file)
        self.errors_file = os.path.join(results_dir, errors_file)
        self.changing_data = {}
        self.changing_data_file = os.path.join(results_dir, changing_data_file)
        self.custom_keywords_file = os.path.join(results_dir, custom_keywords_file)
        self.keyword_results_file = os.path.join(results_dir, "keyword_results.txt")
        self.download_dir = os.path.join(results_dir, "downloads")
        self.rate_limit = rate_limit
        self.max_depth = max_depth
        self.discovered_urls = set()
        self.visited_urls = set()
        self.denied_urls = set()
        self.errors = []
        self.objects = []  # To store all scanned objects
        self.keywords = Counter()  # To store keyword occurrences
        self.custom_keywords_results = defaultdict(list)  # To store locations and counts of custom keywords
        self.scan_urls = scan_urls
        self.scan_objects = scan_objects
        self.download_files = download_files

        os.makedirs(self.results_dir, exist_ok=True)
        if self.download_files:
            os.makedirs(self.download_dir, exist_ok=True)

    def is_online(self):
        try:
            # Check connectivity by connecting to a common DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    async def fetch(self, session, url):
        while not self.is_online():
            print("Offline. Waiting to reconnect...")
            await asyncio.sleep(5)  # Wait before checking again

        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    try:
                        return (await response.text(encoding='utf-8')), response.url
                    except UnicodeDecodeError:
                        print(f"Warning: Failed to decode content from {url}, using raw bytes.")
                        return (await response.read()), response.url
                else:
                    if response.status in [403, 401]:
                        self.denied_urls.add(url)
                    self.errors.append(f"Failed to fetch {url}: Status {response.status}")
                    return None, None
        except Exception as e:
            self.errors.append(f"Error fetching {url}: {e}")
            return None, None

    async def parse_html(self, html, base_url):
        urls = set()
        if isinstance(html, bytes):
            try:
                html = html.decode('utf-8')
            except UnicodeDecodeError:
                print("Warning: Content could not be fully decoded, continuing with partial data.")
                html = html.decode('utf-8', errors='replace')

        try:
            soup = BeautifulSoup(html, 'html.parser')
        except FeatureNotFound:
            try:
                soup = BeautifulSoup(html, 'lxml-xml')
            except FeatureNotFound:
                self.errors.append("No suitable parser found. Skipping content.")
                return urls
        except Exception as e:
            self.errors.append(f"Failed to parse HTML: {e}")
            return urls

        for tag in soup.find_all(['a', 'script', 'img', 'link', 'form']):
            attr = 'href' if tag.name in ['a', 'link', 'form'] else 'src'
            url = tag.get(attr)
            if self.scan_objects:
                self.objects.append({
                    "tag": tag.name,
                    "attributes": tag.attrs,
                    "text": tag.text.strip() if tag.text else ""
                })
            if self.scan_urls and url and isinstance(url, str) and isinstance(base_url, str):  # Validate both base_url and url
                try:
                    full_url = urljoin(base_url, url)
                    urls.add(full_url)
                except Exception as e:
                    self.errors.append(f"Error joining URL {url} with base {base_url}: {e}")

        # Extract text for keywords analysis
        if self.scan_objects:
            text_content = soup.get_text(separator=" ").lower()
            words = re.findall(r'\b\w+\b', text_content)
            self.keywords.update(words)

            # Search for custom keywords
            custom_keywords = await self.load_custom_keywords()
            for keyword in custom_keywords:
                if keyword in text_content:
                    self.custom_keywords_results[keyword].append(base_url)

        # Extract URLs using regex if scanning URLs
        if self.scan_urls:
            urls.update(re.findall(r'http[s]?://[^\s"\'<>]+', html))  # Fixed regex
        return urls

    async def load_custom_keywords(self):
        if not os.path.exists(self.custom_keywords_file):
            return []

        async with aio_open(self.custom_keywords_file, 'r') as file:
            content = await file.read()
            return [line.strip().lower() for line in content.splitlines() if line.strip()]

    async def save_to_file(self):
        if self.scan_urls:
            async with aio_open(self.output_file, 'w') as file:
                await file.write(json.dumps(list(self.discovered_urls), indent=4))

        if self.scan_objects:
            async with aio_open(self.objects_file, 'w') as file:
                await file.write(json.dumps(self.objects, indent=4))

        # Save denied URLs
        async with aio_open(self.denied_urls_file, 'w') as file:
            await file.write("\n".join(self.denied_urls))

        # Save errors
        async with aio_open(self.errors_file, 'w') as file:
            await file.write("\n".join(self.errors))

        # Save changing data
        async with aio_open(self.changing_data_file, 'w') as file:
            for entry in self.changing_data:
                await file.write(f"{entry['source']} -> {entry['data']}\n")

        # Save keywords to keywords.txt
        sorted_keywords = sorted(self.keywords.items(), key=lambda x: x[1], reverse=True)
        async with aio_open(self.keywords_file, 'w') as file:
            await file.write(", ".join([f"{word}:{count}" for word, count in sorted_keywords]))

        # Save custom keyword results
        async with aio_open(self.keyword_results_file, 'w') as file:
            for keyword, locations in self.custom_keywords_results.items():
                await file.write(f"{keyword}: {len(locations)} occurrences\nLocations: {', '.join(locations)}\n\n")

    async def display_status(self, task, start_time, total_items, completed_items):
        elapsed_time = time.time() - start_time
        remaining_items = total_items - completed_items
        estimated_time_left = (elapsed_time / completed_items) * remaining_items if completed_items else 0
        print(f"Task: {task} | Completed: {completed_items}/{total_items} | Elapsed Time: {elapsed_time:.2f}s | Estimated Time Left: {estimated_time_left:.2f}s")

    async def scan_backwards(self, session):
        print("Starting backward scan to detect changing data...")
        changes_found = False
        start_time = time.time()
        total_urls = len(self.discovered_urls)
        for i, url in enumerate(self.discovered_urls):
            if url not in self.visited_urls:
                html, final_url = await self.fetch(session, url)
                if html:
                    snapshot = self.objects.copy()
                    await self.parse_html(html, final_url)
                    new_snapshot = self.objects[len(snapshot):]
                    if new_snapshot:
                        self.changing_data.append({"source": final_url, "data": new_snapshot})
                        changes_found = True
            await self.display_status("Backward Scan", start_time, total_urls, i + 1)
        return changes_found

    async def download_file(self, session, url):
        try:
            while not self.is_online():
                print("Offline. Waiting to reconnect...")
                await asyncio.sleep(5)

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    parsed_url = urlparse(url)
                    file_extension = os.path.splitext(parsed_url.path)[-1].lower() or ".unknown"
                    folder_path = os.path.join(self.download_dir, file_extension.lstrip('.'))
                    os.makedirs(folder_path, exist_ok=True)

                    filename = os.path.basename(parsed_url.path) or "index.html"
                    file_path = os.path.join(folder_path, filename)

                    async with aio_open(file_path, 'wb') as file:
                        await file.write(await response.read())

                    print(f"Downloaded {url} to {file_path}")
                else:
                    self.errors.append(f"Failed to download {url}: Status {response.status}")
        except Exception as e:
            self.errors.append(f"Error downloading {url}: {e}")

    async def crawl(self, url, session, depth):
        if depth > self.max_depth or url in self.visited_urls:
            return

        self.visited_urls.add(url)
        html, final_url = await self.fetch(session, url)
        if not html:
            return

        urls = await self.parse_html(html, final_url)
        start_time = time.time()
        total_urls = len(urls)
        for i, discovered_url in enumerate(urls):
            if discovered_url not in self.discovered_urls:
                self.discovered_urls.add(discovered_url)
                await self.crawl(discovered_url, session, depth + 1)
                if self.download_files:
                    await self.download_file(session, discovered_url)
            await self.display_status("Crawl", start_time, total_urls, i + 1)

    async def parse_endpoint_objects(self, url, session):
        if url in self.visited_urls:
            return

        self.visited_urls.add(url)
        html, _ = await self.fetch(session, url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup.find_all():  # Collect all tags and their attributes
                self.objects.append({
                    "tag": tag.name,
                    "attributes": tag.attrs,
                    "text": tag.text.strip() if tag.text else ""
                })

    async def enumerate_objects(self, session):
        while True:
            current_urls = list(self.discovered_urls - self.visited_urls)
            if not current_urls:
                break
            start_time = time.time()
            total_urls = len(current_urls)
            for i, url in enumerate(current_urls):
                await self.parse_endpoint_objects(url, session)
                await self.display_status("Enumerate Objects", start_time, total_urls, i + 1)

    async def scan(self):
        async with aiohttp.ClientSession(headers={"User-Agent": "APIScanner/1.0"}) as session:
            forward_scan = True

            while forward_scan:
                await self.crawl(self.base_url, session, 0)

                if self.scan_objects:
                    await self.enumerate_objects(session)

                forward_scan = await self.scan_backwards(session)

            await self.save_to_file()

    async def analyze_js(self, session, js_url):
        if not self.scan_urls:
            return
        html, _ = await self.fetch(session, js_url)
        if html:
            # Look for API endpoints or similar patterns in JS files
            endpoints = re.findall(r'"(http[s]?://[^\"]+?)"', html)
            for endpoint in endpoints:
                if endpoint not in self.discovered_urls:
                    self.discovered_urls.add(endpoint)

    async def run(self):
        start_time = time.time()
        async with aiohttp.ClientSession(headers={"User-Agent": "APIScanner/1.0"}) as session:
            await self.crawl(self.base_url, session, 0)

            # Analyze JavaScript files for additional endpoints
            if self.scan_urls:
                js_files = [url for url in self.discovered_urls if url.endswith('.js')]
                for js_url in js_files:
                    await self.analyze_js(session, js_url)

            if self.scan_objects:
                await self.enumerate_objects(session)

            await self.scan()  # Perform continuous forward and backward scans

        print(f"Scanning completed in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    base_url = "https://" + input("Enter a URL: Https://")  # Replace with the target URL
    results_dir = "results"
    output_file = "output.json"
    objects_file = "objects.json"
    keywords_file = "keywords.txt"
    denied_urls_file = "denied_urls.txt"
    errors_file = "errors.txt"
    changing_data_file = "changing_data.txt"
    custom_keywords_file = "custom_keywords.txt"
    rate_limit = 0.5  # Adjust rate limit (seconds between requests)
    max_depth = 3  # Set maximum crawl depth

    scan_urls = input("Scan for URLs? (yes/no): ").strip().lower() == "yes"
    scan_objects = input("Scan for Objects? (yes/no): ").strip().lower() == "yes"
    download_files = input("Download Files? (yes/no): ").strip().lower() == "yes"

    scanner = APIScanner(base_url, results_dir, output_file, objects_file, keywords_file, denied_urls_file, errors_file, changing_data_file, custom_keywords_file, rate_limit, max_depth, scan_urls, scan_objects, download_files)
    asyncio.run(scanner.run())

    print(f"Results saved in: {results_dir}")
