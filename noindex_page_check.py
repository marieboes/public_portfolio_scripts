"""
Script Name: NoIndex Page Check Based On Sitemap (To Pick Up Accidental No Index Settings)
Description:
    This script is designed to automate the process of validating and retrieving URLs from a website's sitemap
    while checking for SEO-related indexing directives. Specifically, it identifies URLs that are set with the
    "noindex" directive, indicating that they should not be indexed by search engines. Here's how the script works:

    1. **Environment Configuration**: The script uses environment variables for configuration management,
       loading sitemap URLs from a specified environment variable using the dotenv library. This ensures flexibility
       and security, allowing easy adaptation for different environments.

    2. **Fetching URLs from Sitemap**: It fetches and parses the sitemap at each specified URL, extracting only the
       HTML page links and filtering out common file types such as images, documents, and video files that are not
       typically subject to search engine indexing.

    3. **Checking Noindex Status**: For each extracted URL, the script performs an HTTP request to determine its
       "indexability." It checks both the X-Robots-Tag in the HTTP headers and the 'robots' meta tags within the
       HTML body for any "noindex" directives.

    4. **Output Results**: The script compiles a list of URLs that are marked with "noindex" and prints these.
               © [2025] [Boes Marie]. All rights reserved.
"""


import os
import requests
from bs4 import BeautifulSoup
from lxml import html
from dotenv import load_dotenv

load_dotenv()


def fetch_urls_from_sitemap(sitemap_url):
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'xml')

        urls = [element.text for element in soup.find_all('loc')]
        urls = [
            url for url in urls
            if not any(url.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif',
                                                     '.pdf', '.doc', '.docx', '.xls',
                                                     '.xlsx', '.csv', '.zip', '.mp4',
                                                     '.svg', '.webp'])
        ]
        print(f"Found {len(urls)} HTML URLs in sitemap: {sitemap_url}")
        return urls

    except requests.RequestException as e:
        print(f"Error fetching sitemap {sitemap_url}: {e}")
        return []


def is_noindex(header):
    return 'noindex' in header.get('X-Robots-Tag', '').lower()


def check_noindex_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        headers = response.headers

        tree = html.fromstring(response.content)
        # Check for X-Robots-Tag in headers
        if is_noindex(headers):
            print(f"NOINDEX detected in headers for URL: {url}")
            return True

        meta_tags = tree.xpath("//meta[@name='robots' or @name='googlebot']")
        noindex_content = [
            'noindex' in (tag.get('content') or '').lower() for tag in meta_tags
        ]

        if any(noindex_content):
            print(f"NOINDEX detected in meta tag for URL: {url}")
            return True

        print(f"URL is indexed: {url}")
        return False

    except requests.RequestException as e:
        print(f"Error checking URL {url}: {e}")
        return False


def parse_env_urls(env_var):
    urls = os.getenv(env_var, '').split(',')
    return [url.strip() for url in urls if url.strip() and not url.strip().startswith('#')]


if __name__ == "__main__":
    sitemap_urls = parse_env_urls('SITEMAP_URLS')

    for sitemap_url in sitemap_urls:
        print(f"Processing sitemap: {sitemap_url}")
        page_urls = fetch_urls_from_sitemap(sitemap_url)
        noindex_urls = []

        for page_url in page_urls:
            if check_noindex_url(page_url):
                noindex_urls.append(page_url)

        print(f"Noindex URLs found: {noindex_urls}")