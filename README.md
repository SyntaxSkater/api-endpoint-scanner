# API Endpoint Scanner

The **API Endpoint Scanner** is a robust Python-based tool designed to crawl, analyze, and scrape information from websites. It recursively scans for URLs, objects, and files, providing insights into keyword usage, changing data, and downloadable resources.

## Features

- **URL Scanning**: Discover and list all unique URLs on the target website.
- **Object Parsing**: Extract and store HTML objects, attributes, and content.
- **File Downloading**: Download images, JavaScript files, and other resources sorted by type.
- **Keyword Analysis**:
  - Automatic keyword frequency counting.
  - Custom keyword matching from `custom_keywords.txt`.
  - Saves keyword occurrences and locations.
- **Changing Data Detection**: Detects and logs changes found during backward scans.
- **Offline Resilience**: Pauses operations when offline and resumes once connectivity is restored.
- **Comprehensive Logging**:
  - Denied URLs
  - Errors
  - Changing data

## Setup

### Prerequisites
- Python 3.8+
- Install the required Python packages:

```bash
pip install aiohttp beautifulsoup4 aiofiles
```

### Project Structure
```
project/
│
├── results/                # Output directory
│   ├── downloads/          # Downloaded files categorized by type
│   ├── output.json         # List of all discovered URLs
│   ├── objects.json        # Parsed HTML objects
│   ├── keywords.txt        # Auto-generated keyword frequencies
│   ├── custom_keywords.txt # User-defined keywords for searching
│   ├── denied_urls.txt     # List of denied or restricted URLs
│   ├── errors.txt          # Logged errors during scanning
│   ├── changing_data.txt   # Detected changing data
│   ├── keyword_results.txt # Custom keyword results with occurrences
│
├── scanner.py              # Main script
└── README.md               # Documentation
```

## Usage

1. **Clone the Repository**
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Run the Script**
   Execute the script with:
   ```bash
   python scanner.py
   ```

3. **Enter the Target URL**
   The script prompts for a URL to scan, e.g., `https://example.com`.

4. **Enable Features**
   Respond to the following prompts to enable/disable specific features:
   - `Scan for URLs? (yes/no):`
   - `Scan for Objects? (yes/no):`
   - `Download Files? (yes/no):`

## Custom Keyword Search

To use the custom keyword feature:
1. Add your desired keywords to `custom_keywords.txt`, one per line.
2. The script will log their occurrences and locations in `keyword_results.txt`.

Example `custom_keywords.txt`:
```
login
api
error
```

## Output Files
- **`output.json`**: Contains all unique URLs discovered during the scan.
- **`objects.json`**: Lists all HTML objects and their details.
- **`changing_data.txt`**: Logs any changing data with the sources.
- **`keyword_results.txt`**: Includes custom keyword occurrences and their sources.
- **`errors.txt`**: Contains error logs for troubleshooting.
- **`denied_urls.txt`**: Lists URLs that were restricted or denied access.

## Additional Notes
- Ensure stable internet connectivity for uninterrupted scans.
- If interrupted, the script resumes automatically when connectivity is restored.
- Results are saved incrementally to prevent data loss.
