"""
Script Name: Automated Instagram Post Scheduler from Airtable
Description:
    This script is developed to automate the process of scheduling posts for Instagram directly from Airtable records.
    It streamlines the workflow of fetching records ready for publication, preparing media content, and posting on Instagram
    without any manual intervention.

               © [2025] [Your Company Name]. All rights reserved.
"""



import os
import requests
from dotenv import load_dotenv
import time
from pyairtable import api
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

# Constants for Airtable
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = 'AIRTABLE_BASE_ID'
AIRTABLE_TABLE_ID = 'AIRTABLE_TABLE_NAME'

# Set up Airtable connection
airtable_api = api.Api(AIRTABLE_API_KEY)
table = airtable_api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)


def fetch_ready_to_publish_records():
    today_date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    formula = f"AND(NOT({{property}} = ''), {{state}} = 'READY_TO_PUBLISH', FIND('INSTAGRAM', {{platform}}), IS_SAME({{publish_date}}, DATESTR('{today_date_str}'), 'day'),{{external_instagram_post_id}} = '')"

    # Log the formulated query
    print(f"Query Formula: {formula}")

    records = table.all(formula=formula)

    # Log each record fetched from Airtable
    print(f"Number of records fetched: {len(records)}")
    for record in records:
        print(f"Record ID: {record['id']}, Fields: {record['fields']}")

    if records:
        print("Raw Airtable Records fetched successfully.")
        return records
    else:
        print("No records found with property set and state 'READY_TO_PUBLISH'.")
        return []

def get_post_details_from_record(record):
    fields = record['fields']
    details = {
        'property': fields.get('property'),
        'caption': fields.get('caption', ''),
        'hashtag': fields.get('hashtags', ''),
        'video_url': fields.get('video (from reusable_post)')[0]['url'] if fields.get(
            'video (from reusable_post)') else None,
        'image_url': fields.get('image')[0]['url'] if fields.get(
            'image') else None
    }
    print(f"Fetched Post Details: {details}")
    return details

def update_airtable_record_with_media_id(record_id, media_id):
    # Update Airtable record with Instagram media ID
    try:
        table.update(record_id, {"external_instagram_post_id": media_id})
        print(f"Airtable record updated with media ID: {media_id}")
    except Exception as e:
        print(f"Error updating Airtable record with media ID: {e}")

def check_media_status(container_id, access_token):
    print("Checking media status...")
    status_url = f"https://graph.facebook.com/v21.0/{container_id}"
    while True:
        response = requests.get(status_url, params={
            "fields": "status_code",
            "access_token": access_token
        })

        if not response.ok:
            print(f"Error checking media status: {response.json()}")
            return False

        status_response_json = response.json()
        print(f"Media status response: {status_response_json}")

        status = status_response_json.get('status_code')
        if status == 'FINISHED':
            print("Media is ready for publishing.")
            return True
        elif status == 'ERROR':
            print("Error in media processing.")
            return False
        else:
            print(f"Current media status: {status}, retrying in 5 seconds...")
            time.sleep(5)

def schedule_instagram_post(property, message, media_url, media_type):
    ig_account_id = os.getenv(f"INSTAGRAM_{property}_ID")
    access_token = os.getenv(f"FACEBOOK_{property}_PAGE_ACCESS_TOKEN")

    if not ig_account_id or not access_token:
        print(f"Error: Instagram Account ID or Access Token for property '{property}' is not set.")
        return

    try:
        print(f"Uploading image/video to Instagram for property '{property}'...")
        container_url = f"https://graph.facebook.com/v21.0/{ig_account_id}/media"
        if media_type == "REELS":
            container_response = requests.post(container_url, params={
                "media_type": "REELS",
                "video_url": media_url,
                "caption": message,
                "access_token": access_token
            })
        else:
            container_response = requests.post(container_url, params={
                "image_url": media_url,
                "caption": message,
                "access_token": access_token
            })

        print(f"Container response: {container_response.text}")
        container_response_json = container_response.json()
        if container_response.ok:
            container_id = container_response_json.get("id")
            print(f"Instagram container created with ID: {container_id}")

            if check_media_status(container_id, access_token):
                publication_url = f"https://graph.facebook.com/v21.0/{ig_account_id}/media_publish"
                publish_response = requests.post(publication_url, json={
                    "creation_id": container_id,
                    "access_token": access_token
                })

                print(f"Publish response: {publish_response.text}")
                if publish_response.ok:
                    publish_response_json = publish_response.json()
                    media_id = publish_response_json.get("id")
                    print(f"Instagram Image/Reel published successfully. Media ID: {media_id}")

                    # Update Airtable with the media ID
                    update_airtable_record_with_media_id(record_id, media_id)
                else:
                    print(f"Error publishing to Instagram: {publish_response.json()}")
            else:
                print("Instagram media was not ready for publishing.")
        else:
            print(f"Error creating Instagram container: {container_response_json}")

    except Exception as e:
        print(f"An error occurred while scheduling the Instagram post: {e}")

if __name__ == "__main__":
    records = fetch_ready_to_publish_records()
    for record in records:
        record_id = record['id']
        post_details = get_post_details_from_record(record)
        post_message = f"{post_details['caption']} {post_details['hashtag']}"
        video_url = post_details.get('video_url')
        image_url = post_details.get('image_url')

        if video_url:
            schedule_instagram_post(
                post_details['property'], post_message, video_url, "REELS"
            )
        elif image_url:
            schedule_instagram_post(
                post_details['property'], post_message, image_url, "IMAGE"
            )
        else:
            print("No video URL found in the record.")
    else:
        print("No record found.")