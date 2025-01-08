# API Endpoint Scanner

A Python-based tool to recursively scan a given URL for all associated endpoints, including links, assets, and API endpoints embedded in HTML and JavaScript files.

## Features

- **Concurrency**: Uses asynchronous requests for faster scanning.
- **Recursive Crawling**: Scans links and endpoints up to a specified depth.
- **JavaScript Analysis**: Extracts API endpoints from JavaScript files.
- **Rate Limiting**: Adjustable delay between requests to prevent being blocked.
- **Output**: Saves discovered URLs to a JSON file.
- **Regex Matching**: Finds hidden URLs embedded in the page source.

## Requirements

- Python 3.7+
- Install dependencies:
  ```bash
  pip install aiohttp beautifulsoup4 aiofiles
  ```

## Usage

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd api-endpoint-scanner
   ```

2. **Edit Configuration**:
   - Open `main.py` and set the `base_url` to the target URL.
   - Optional: Adjust `rate_limit` and `max_depth` as needed.

3. **Run the Script**:
   ```bash
   python main.py
   ```

4. **View Results**:
   - The discovered URLs will be saved to `discovered_urls.json` in the project directory.

## Configuration Options

- `base_url`: The starting URL to scan.
- `output_file`: File where discovered URLs are saved (default: `discovered_urls.json`).
- `rate_limit`: Delay between requests in seconds (default: `0.5`).
- `max_depth`: Maximum depth for recursive crawling (default: `3`).

## Example Output

The `discovered_urls.json` file will contain:

```json
[
    "https://example.com/endpoint1",
    "https://example.com/endpoint2",
    "https://example.com/assets/script.js"
]
```

## Important Notes

- Use this tool responsibly. Ensure you have permission to scan the target site.
- The tool respects ethical guidelines and is not intended for malicious use.