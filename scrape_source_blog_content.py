"""
Script Name: Naver Blog Article Fetch and Airtable Update
Description:
    This script fetches the latest articles from a given Naver Blog URL (The Korean National Tax Office Official Blog),
    storing new article URLs into an Airtable base. It then processes these stored URLs
    to fetch and update the article content in the Airtable records.

Functions:
- parse_date: Parses date strings from the blog articles, handling both relative and absolute dates.
- fetch_latest_articles: Fetches the latest blog articles posted after a certain cutoff date.
- store_article_url_in_airtable: Stores new article URLs in Airtable if they do not already exist.
- fetch_and_update_airtable: Retrieves URLs from Airtable, fetches their body content, and updates Airtable with the content.
   © [2025] [Boes Marie]. All rights reserved.
"""
import os
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta
import re

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Airtable API credentials from environment variables
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

# Naver Blog URL
BLOG_URL = 'https://blog.naver.com/ntscafe'

# Define date to filter articles
PUBLISH_DATE_CUTOFF = datetime(2024, 12, 4)


def parse_date(date_str):
    # Check for relative time format
    match = re.match(r'(\d+)\s*시간\s*전', date_str)
    if match:
        hours_ago = int(match.group(1))
        return datetime.now() - timedelta(hours=hours_ago)

    # Check for absolute date format
    try:
        return datetime.strptime(date_str, '%Y. %m. %d.')
    except ValueError:
        pass

    # If parsing fails
    raise ValueError(f"Unsupported date format: {date_str}")


def fetch_latest_articles():
    print("Fetching the blog page...")
    response = requests.get(BLOG_URL)
    if response.status_code != 200:
        raise Exception("Failed to load blog page")

    soup = BeautifulSoup(response.content, 'html.parser')

    # Get the iframe containing the blog posts
    iframe_element = soup.find('iframe', id='mainFrame')
    if not iframe_element:
        raise Exception("Failed to find iframe containing blog posts")

    # Correctly construct the iframe URL
    iframe_src = iframe_element['src']
    if 'http' not in iframe_src:
        iframe_src = 'https://blog.naver.com' + iframe_src

    print(f"Fetching the iframe content from: {iframe_src}")
    iframe_response = requests.get(iframe_src)
    if iframe_response.status_code != 200:
        raise Exception("Failed to load iframe content")

    iframe_soup = BeautifulSoup(iframe_response.content, 'html.parser')

    # Find articles in iframe content
    articles = iframe_soup.find_all('dd', class_='p_photo_d')

    latest_articles = []
    for article in articles:
        try:
            # Extract URL
            url_element = article.find('a')
            if not url_element:
                continue
            url = url_element['href']
            if not url.startswith('https://blog.naver.com'):
                url = 'https://blog.naver.com' + url

            # Avoid processing if URL points to "이벤트" category
            if 'categoryNo=9' in url:
                continue

            # Extract Date
            date_element = article.find('span', class_='pcol2 fil5')
            if not date_element:
                continue
            date_str = date_element.get_text().strip()
            publish_date = parse_date(date_str)

            if publish_date > PUBLISH_DATE_CUTOFF:
                latest_articles.append(url)
                print(f"Article accepted - URL: {url}")

        except Exception as e:
            print(f"Error processing article: {e}")

    return latest_articles


def store_article_url_in_airtable(article_url):
    try:
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_NAME)

        # Check if the URL already exists in the table
        match = table.first(formula=f"{{source_content_url}} = '{article_url}'")
        if match:
            print("Article URL already exists in the table.")
        else:
            # Storing new article URL into Airtable
            new_record = {'source_content_url': article_url}
            table.create(new_record)
            print(f"Stored new article URL: {article_url}")

    except Exception as e:
        print(f"Error storing article URL in Airtable: {e}")


def fetch_and_update_airtable():
    try:
        # Initialize Airtable API and table connection
        api = Api(AIRTABLE_API_KEY)
        table = api.table(BASE_ID, TABLE_NAME)

        # Fetch records from Airtable
        formula = "AND(NOT({source_content_url} = ''), OR({source_content_text} = '', {source_content_text} = BLANK()))"
        records = table.all(formula=formula)

        # Process each record
        for record in records:
            fields = record['fields']
            source_content_url = fields.get('source_content_url')
            source_content_text = fields.get('source_content_text')

            # Only process records where source_content_text is empty and source_content_url is not empty
            if source_content_url and not source_content_text:
                print(f"Processing URL: {source_content_url}")

                try:
                    # Fetch the content from the URL
                    response = requests.get(source_content_url)
                    response.raise_for_status()
                    html_content = response.content

                    # Parse the HTML content using BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    scraped_text = soup.get_text(separator=' ', strip=True)

                    # Store the scraped content back into Airtable
                    table.update(record['id'], {'source_content_text': scraped_text})
                    print("Content updated successfully.")

                except requests.exceptions.RequestException as e:
                    print(f"Failed to retrieve or parse content from {source_content_url}: {e}")

        print("Completed processing all records.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    try:
        latest_articles = fetch_latest_articles()
        for article_url in latest_articles:
            store_article_url_in_airtable(article_url)
        fetch_and_update_airtable()
    except Exception as e:
        print(f"Error: {e}")