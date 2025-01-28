"""
Script Name: Markdown to HTML conversion for Wordpress Publishing
Description:
    This script automates the conversion of Markdown text to HTML for articles stored
    in an Airtable database. The primary purpose is to prepare articles for publication
    on WordPress by ensuring the content is in a suitable HTML format. The script filters
    records to find those marked as "READY_TO_PUBLISH" where the HTML field is empty.
    Upon finding such records, it converts the Markdown content to HTML, updates the
    corresponding Airtable records, and prints a confirmation message for each processed
    article.
           © [2025] [Boes Marie]. All rights reserved.
"""

import os
from pyairtable import Api
from markdown import markdown
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup


# Load environment variables
load_dotenv(find_dotenv())
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')

# Initialize the Airtable API
api = Api(AIRTABLE_API_KEY)
table = api.table(BASE_ID, TABLE_NAME)


# Function to process and convert Markdown text
def convert_markdown_to_html(article_text):
    # Convert Markdown to HTML
    html_content = markdown(article_text)

    # Optionally, use BeautifulSoup to ensure HTML is properly formatted
    soup = BeautifulSoup(html_content, 'html.parser')

    # Convert the BeautifulSoup object back to a string
    return str(soup)


# Function to fetch records where the status is READY_TO_PUBLISH and html is empty
def fetch_ready_articles_with_empty_html():
    # Use the Airtable formula to filter out records based on the conditions
    formula = "AND({state} = 'READY_TO_PUBLISH', {html} = '')"
    records = table.all(view='Grid view', formula=formula)
    return records

# Fetch all relevant records from the Airtable table
records = fetch_ready_articles_with_empty_html()

for record in records:
    record_id = record['id']
    fields = record['fields']
    article_text = fields.get('article_text')
    html = fields.get('html')

    # Check if 'html' field is empty and 'article_text' contains data
    if article_text and not html:
        # Convert Markdown article to HTML
        html_content = convert_markdown_to_html(article_text)
        # Update the Airtable record with the new HTML content
        table.update(record_id, {'html': html_content})
        print(f"Converted and updated record {record_id} from Markdown to HTML.")