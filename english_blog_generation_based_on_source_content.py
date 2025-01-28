"""
Script Name: Airtable Record Processing with Text Generation
Description:
    This script connects to an Airtable table and retrieves records where the state is "INIT".
    For each record, it uses OpenAI's GPT model to generate an article from the source content
    provided in the record. The generated text is then appended with a disclaimer and updated
    back into the Airtable record, changing the state to "REVIEW_REQUIRED".
       © [2025] [Boes Marie]. All rights reserved.
"""

import os
from dotenv import load_dotenv, find_dotenv
from pyairtable import Api
from openai import OpenAI

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Function to generate text using OpenAI
def generate_text(api_key, prompt, text):
    client = OpenAI(api_key=api_key)
    message = [{"role": "assistant", "content": prompt}, {"role": "user", "content": text}]
    temperature = 1
    max_tokens = 2200
    frequency_penalty = 0.0
    print("Calling GPT for topic: " + (text[:50] + '..' if len(text) > 52 else text))
    response = client.chat.completions.create(
        model="gpt-4",
        messages=message,
        temperature=temperature,
        max_tokens=max_tokens,
        frequency_penalty=frequency_penalty
    )
    return response.choices[0].message.content

def main():
    # Load Airtable and OpenAI credentials from environment variables
    airtable_api_key = os.getenv("AIRTABLE_API_KEY")
    airtable_base_id = os.getenv("AIRTABLE_BASE_ID")
    airtable_table_name = os.getenv("AIRTABLE_TABLE_NAME")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    gpt_prompt = (
        "This is source info, create a new article in English based on this. "
        "The article needs to have a couple of H2 headings. Output should be in markdown."
    )

    # Disclaimer text to be appended
    disclaimer = (
        "\n\n*Disclaimer : This content is a translation of material originally published in"
        " Korean by the National Tax Service of the Republic of Korea. While efforts have been"
        " made to ensure accuracy, this translation is provided for informational purposes only"
        " and does not carry legal weight. In the event of any discrepancy, the original Korean"
        " version shall prevail. Users should consult the official Korean documents for precise"
        " interpretation. This translation does not constitute legal advice. The translators and"
        " publishers shall not be held liable for any loss arising from reliance on this translation.*"
    )

    # Initialize Airtable API object and Table object
    api = Api(airtable_api_key)
    table = api.table(airtable_base_id, airtable_table_name)

    # Fetch records with state 'INIT'
    formula = "{state} = 'INIT'"
    records = table.all(formula=formula)

    for record in records:
        source_content = record['fields'].get('source_content_text', "")
        if source_content:
            generated_text = generate_text(openai_api_key, gpt_prompt, source_content)

            # Merge generated text with the disclaimer
            complete_text = generated_text + disclaimer

            record_id = record['id']
            table.update(record_id, {
                "article_text": complete_text,
                "state": "REVIEW_REQUIRED"
            })
            print(f"Updated record ID {record_id} with generated text, disclaimer, and changed state to REVIEW_REQUIRED.")

if __name__ == "__main__":
    main()