"""
Script Name: Bulk Generate Company Profile Descriptions Based On Website Text
Description:
    This script automates the extraction and enhancement of textual descriptions for company records
    stored in an Airtable database. It uses web scraping and natural language processing to generate
    introductions for company profiles that lack prior descriptions. The process involves:

    1. Fetching Company Data: Retrieves records from Airtable where the `siteUrl` is not empty,
       and the `introduction` is yet to be populated.
    2. Content Extraction: Scrapes text from specified URLs, filtering out irrelevant or sensitive information
       using predefined skip words.
    3. Content Generation: Utilizes OpenAI's API to create detailed, bullet-pointed descriptions for company profiles.
    4. Updating Records: Updates Airtable records with newly generated content, enriching each company's details.
           © [2025] [Boes Marie]. All rights reserved.
"""

import os
import requests
from bs4 import BeautifulSoup
from pyairtable import Api
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
airtable_api_key = os.getenv('AIRTABLE_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')
base_id = os.getenv('AIRTABLE_BASE_ID')
table_name = os.getenv('AIRTABLE_TABLE_NAME')

# Set up APIs
airtable_sdk = Api(airtable_api_key)

# Words to skip when parsing text
SKIP_WORDS = [
    'copyright', '사업자', '대표', 'whatsapp', 'facebook', 'kakao',
    'e-mail', 'email', '+82-'
]

def parent_contains_skip_word(parent, skip_words):
    """Check if any parent element contains a skip word in its ID or class."""
    if parent.parent:
        if parent_contains_skip_word(parent.parent, skip_words):
            return True

    for word in skip_words:
        if 'id' in parent.attrs and word in parent.attrs['id'].lower():
            return True
        elif 'class' in parent.attrs and any(word in cls.lower() for cls in parent.attrs['class']):
            return True

    return False

def get_text(link, skip_words):
    """Extract relevant text from a webpage, excluding elements with skip words."""
    try:
        html = requests.get(link).text
    except Exception as e:
        print(f"Error fetching URL {link}: {e}")
        return ""

    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all(['p', 'span', 'div'])

    result = ""
    for element in elements:
        text = element.get_text()
        if not any(word in text.lower() for word in skip_words) and not parent_contains_skip_word(element.parent, skip_words):
            result += f" {text}"

    return result.strip()

def generate_text(api_key, prompt, text, topic):
    """Generate AI-assisted text using OpenAI's API."""
    client = OpenAI(api_key=api_key)

    message = [
        {"role": "assistant", "content": prompt},
        {"role": "user", "content": text}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=message,
            temperature=1,
            max_tokens=4095,
            frequency_penalty=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error for topic {topic}: {e}")
        return ""

def main():
    company_table = airtable_sdk.table(base_id, table_name)
    company = company_table.all(formula="AND(NOT({introduction} != ''), {siteUrl} != ''))")

    count = 0
    for company in company:
        company_name = company['fields'].get('name', 'Unknown')
        district = company['fields'].get('district', 'Unknown')
        url = company['fields'].get('siteUrl')

        print(f'Processing company: {company_name}, URL: {url}')

        content = get_text(link=url, skip_words=SKIP_WORDS)

        if not content:
            print(f'No content found, skipping company: {company_name}')
            company_table.update(company['id'], {'introduction': 'SKIPPING'})
            continue

        prompt = (
            f"Explain the services offered at {company_name} in {district} in bullet points in English. "
            "Put them into service categories and bold the service name at the beginning of the sentence. "
            "Explain each service in two sentences. Only use bold for headings. Write a company introduction sentence. "
            "Leave out any services where the English procedure name is not commonly known. "
            "(Do not use the words 'likely', 'possibly', and any synonyms of those words)"
        )

        result = generate_text(api_key=openai_api_key, prompt=prompt, text=content, topic=company_name)

        # Check for sample content keywords
        SAMPLE_CONTENT_KEYWORDS = ['example', 'sample', '#', 'certainly']
        if any(word in result for word in SAMPLE_CONTENT_KEYWORDS):
            print(f'Result for {company_name} failed due to sample keyword, skipping.')
            continue

        # Store result in Airtable
        company_table.update(company['id'], {'introduction': result})
        print(f"Processed and updated company: {company_name}")

        count += 1
        if count >= 1000:
            break

if __name__ == "__main__":
    main()