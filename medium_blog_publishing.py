"""
Script Name: Medium Blog Auto-Publishing Script
Description:
    This script automates the process of publishing articles to Medium from Airtable. It retrieves records marked
    as "READY_TO_PUBLISH" from an Airtable table, uploads a randomly selected header image from a specified directory,
    and publishes the articles using the Medium API. Once published, it updates the Airtable record with the Medium
    post ID and URL, along with changing the state to "PUBLISHED".
       © [2025] [Boes Marie]. All rights reserved.
"""

import os
import random
import requests
from pyairtable import Api
from dotenv import load_dotenv, find_dotenv

# Load environment variables from the .env file
load_dotenv(find_dotenv())

# Airtable and Medium Credentials (loaded from .env)
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
BASE_ID = os.getenv('AIRTABLE_BASE_ID')
TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
MEDIUM_INTEGRATION_TOKEN = os.getenv('MEDIUM_INTEGRATION_TOKEN')
MEDIUM_USER_ID = os.getenv('MEDIUM_USER_ID')

# Directory containing header images
HEADER_IMAGE_DIRECTORY = os.getenv('IMAGE_FILE_PATH')

def get_random_image_path():
    # List all files in the directory
    files = os.listdir(HEADER_IMAGE_DIRECTORY)
    # Filter files to include only images
    images = [f for f in files if f.endswith('.png')]
    # Randomly select an image
    if images:
        return os.path.join(HEADER_IMAGE_DIRECTORY, random.choice(images))
    else:
        print("No images found in the specified directory.")
        return None

# Airtable - Get text from article_text column
def get_ready_to_publish_articles():
    api = Api(AIRTABLE_API_KEY)
    base = api.base(BASE_ID)
    table = base.table(TABLE_NAME)
    records = table.all()
    # Filter records that are ready to publish
    ready_to_publish = [
        record for record in records
        if record['fields'].get('title') and
        record['fields'].get('article_text') and
        record['fields'].get('state') == 'READY_TO_PUBLISH'
    ]
    return ready_to_publish

def upload_image_to_medium(image_path):
    headers = {
        'Authorization': f'Bearer {MEDIUM_INTEGRATION_TOKEN}',
        'Accept': 'application/json'
    }
    # Open the image in binary mode
    with open(image_path, 'rb') as image_file:
        # Requests will handle the Content-Type and boundary when using the files parameter
        files = {'image': (os.path.basename(image_path), image_file, 'image/png')}
        url = f"https://api.medium.com/v1/images"
        response = requests.post(url, headers=headers, files=files)
    # Check for valid image upload
    if response.status_code == 201:
        return response.json()['data']['url']
    else:
        print("Failed to upload the image.")
        print("Response:", response.status_code, response.text)
        return None

# Medium - Create and publish new article
def publish_to_medium(article_title, article_content, image_url, publication_id):
    # Use the publication ID instead of the user ID in the URL
    url = f"https://api.medium.com/v1/publications/{publication_id}/posts"
    headers = {
        'Authorization': f'Bearer {MEDIUM_INTEGRATION_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    data = {
        "title": article_title,
        "contentFormat": "markdown",
        "content": f"![Header Image]({image_url})\n\n{article_content}",
        "publishStatus": "public"
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        post_id = response.json().get('data').get('id')
        url = response.json().get('data').get('url')
        print("Article published successfully!")
        print("Article URL:", url)
        return post_id, url
    else:
        print("Failed to publish the article.")
        print("Response:", response.status_code, response.text)
        return None, None

# Update Airtable with the new post_id and article URL
def update_airtable_with_post_data(record_id, post_id, article_url):
    api = Api(AIRTABLE_API_KEY)
    table = api.base(BASE_ID).table(TABLE_NAME)
    table.update(record_id, {
        "post_id": post_id,
        "state": "PUBLISHED",
        "medium_url": article_url
    })

def main():
    publication_id = os.getenv('PUBLICATION_ID')
    try:
        articles = get_ready_to_publish_articles()
        if articles:
            for article in articles:
                article_title = article['fields'].get('title')
                article_content = article['fields'].get('article_text')
                image_path = get_random_image_path()
                if image_path:
                    image_url = upload_image_to_medium(image_path)
                    if image_url:
                        post_id, article_url = publish_to_medium(article_title, article_content, image_url, publication_id)
                        if post_id and article_url:
                            update_airtable_with_post_data(article['id'], post_id, article_url)
        else:
            print("No articles ready to publish found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()