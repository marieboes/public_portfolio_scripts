"""
Script Name: Wordpress Blog Publishing
Description:
    This script automates the process of publishing articles from an Airtable database
    to a WordPress site. It begins by fetching articles that are marked as "READY_TO_PUBLISH"
    and ensures that each article's HTML content is ready for publication. For each article
    meeting these criteria, the script selects a random image from a predefined list to be
    used as the featured image on WordPress. The article's publication status is set to
    "future" if a specific schedule date is provided; otherwise, it is published immediately.
           © [2025] [Boes Marie]. All rights reserved.
"""
import os
import random
from datetime import datetime
import requests
from pyairtable import Api
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Constants from environment variables
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')
AIRTABLE_TABLE_NAME = os.getenv('AIRTABLE_TABLE_NAME')
WORDPRESS_SITE_URL = 'XXXX'
WORDPRESS_APP_USERNAME = os.getenv('WORDPRESS_APP_USERNAME')
WORDPRESS_APP_PASSWORD = os.getenv('WORDPRESS_APP_PASSWORD')

# List of WordPress Media IDs
WORDPRESS_MEDIA_IDS = [395, 394, 393, 392, 391, 390, 389, 388]

# Initialize Airtable API
airtable_api = Api(AIRTABLE_API_KEY)


def fetch_ready_articles():
    table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    records = table.all(view='Grid view', formula="state = 'READY_TO_PUBLISH'")
    return records


def get_random_image_name():
    # Randomly select a media ID
    return random.choice(WORDPRESS_MEDIA_IDS)


def publish_to_wordpress(title, content, image_id, schedule_date):
    post_data = {
        'title': title,
        'content': content,
        'status': 'future' if schedule_date else 'publish',
        'featured_media': image_id,
    }
    if schedule_date:
        post_data['date'] = schedule_date.isoformat()

    print(f"Publishing to WordPress with data: {post_data}")

    response = requests.post(
        f'{WORDPRESS_SITE_URL}/wp-json/wp/v2/posts',
        json=post_data,
        auth=(WORDPRESS_APP_USERNAME, WORDPRESS_APP_PASSWORD)
    )

    print(f"WordPress response ({response.status_code}): {response.text}")

    if response.ok:
        return response.json().get('id')
    else:
        print('Failed to post to WordPress:', response.text)
        return None


def update_airtable_record(record_id, wp_id):
    table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    fields = {
        'state': 'PUBLISHED',
        'wp_id': str(wp_id) if wp_id else None,
    }
    try:
        table.update(record_id, fields)
    except Exception as e:
        print(f'Error updating Airtable record: {e}')


def main():
    try:
        articles = fetch_ready_articles()
        if articles:
            for article in articles:
                record_id = article['id']
                title = article['fields'].get('title')
                article_html = article['fields'].get('html')

                # Parse schedule date if present, otherwise use None
                schedule_date_str = article['fields'].get('schedule_date')
                schedule_date = None
                if schedule_date_str:
                    schedule_date = datetime.fromisoformat(schedule_date_str)

                image_id = get_random_image_name()

                if image_id and title and article_html:
                    # Publish to WordPress
                    wp_post_id = publish_to_wordpress(title, article_html, image_id, schedule_date)

                    # Update Airtable with WordPress post data
                    if wp_post_id:
                        update_airtable_record(record_id, wp_post_id)
                        print(f"Article '{title}' published on WordPress successfully.")
                else:
                    print(f"Failed to process article '{title}' due to missing data.")
        else:
            print('No articles ready to publish.')
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()