"""
Script Name: Generate Markup FAQ Based On Keyword
Description:
    This script automates the generation of FAQ content for records stored in an Airtable database
    using OpenAI's GPT-4 model. It processes records with a specified key phrase and no existing FAQ,
    generating structured FAQ text in HTML format. The generated content is then stored back in the
    Airtable record, enriching the dataset with AI-enhanced information.
               © [2025] [Boes Marie]. All rights reserved.
"""

import os
from dotenv import load_dotenv
from pyairtable import Api
import openai

# Load environment variables
load_dotenv()

# Constants from environment variables
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

def fetch_records_to_process(api, base_id, table_name):
    """Fetch records from Airtable that have a key phrase but no FAQ."""
    table = api.base(base_id).table(table_name)
    formula = "AND(NOT({key_phrase} = ''), {faq} = BLANK())"
    records = table.all(formula=formula)
    return records, table

def generate_text(api_key, prompt, text):
    """Generate FAQ text using OpenAI's GPT model."""
    openai.api_key = api_key

    message = [{"role": "system", "content": prompt}, {"role": "user", "content": text}]
    print(f"Calling GPT for topic: {text[:50] + '..' if len(text) > 52 else text}")

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=message,
        temperature=1,
        max_tokens=1500,
        frequency_penalty=0.0
    )

    return response['choices'][0]['message']['content']

def main(airtable_api_key, base_id, table_name, openai_api_key):
    api = Api(airtable_api_key)
    records, table = fetch_records_to_process(api, base_id, table_name)

    for record in records:
        topic = record['fields'].get('key_phrase')

        faq_text_schema_example = '''
        <div itemscope itemtype="https://schema.org/FAQPage">
            <h2> Frequently Asked Questions (FAQ) </h2>
            <div itemscope itemprop=mainEntity itemtype="https://schema.org/Question">
                <h3 itemprop="name">What is HyalDew Shine?</h3>
                <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
                    <div itemprop="text">
                        HyalDew Shine is a skin booster that contains cross-linked Hyaluronic Acid. 
                        It is used for skin rejuvenation and contains 20 mg/ml of Hyaluronic Acid.
                    </div>
                </div>
            </div>
            <div itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">
                <h3 itemprop="name"> What can HyalDew be used for? </h3>
                <div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">
                    <div itemprop="text">
                        HyalDew is a dermal filler for correcting wrinkles, folds, or scars, 
                        lip augmentation, facial contouring, skin rejuvenation, and improving skin tone.
                    </div>
                </div>
            </div>
        </div>
        '''

        faq_prompt = (
            f"Create 3 frequently asked questions related to {topic} and answer each in 2-3 sentences. "
            f"Output the result in FAQ Schema Structured data in HTML like the example: {faq_text_schema_example}"
        )

        faq_text = generate_text(api_key=openai_api_key, prompt=faq_prompt, text='')
        faq_html = f"{faq_text}"
        table.update(record['id'], {"faq": faq_html})

if __name__ == "__main__":
    main(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME, OPENAI_API_KEY)