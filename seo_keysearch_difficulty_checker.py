import requests
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv('KEYSEARCH_API_KEY')
base_url = 'https://www.keysearch.co/api'


def get_keyword_data(keyword):
    endpoint = f"{base_url}?key={api_key}&difficulty={keyword}&cr=all"
    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        try:
            data = response.json()
            return data
        except requests.exceptions.JSONDecodeError:
            print("Response content is not valid JSON, printing raw text response:")
            print(response.text)
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


keywords = ["rhinoplasty dermal graft", "What are grafts in rhinoplasty"]

data = []
for keyword in keywords:
    result = get_keyword_data(keyword)
    if result:
        print(f"Result for {keyword}: {result}")
        data.append(result)

if data:
    df = pd.DataFrame(data)
    df['cpc'] = pd.to_numeric(df['cpc'], errors='coerce')
    df['ppc'] = pd.to_numeric(df['ppc'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    df['score'] = pd.to_numeric(df['score'], errors='coerce')

    print(df.head())

    sorted_df = df.sort_values(by='score', ascending=False)
    print("Sorted by score:")
    print(sorted_df)

    df.to_csv('keyword_data.csv', index=False)


import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
df_sorted = df.sort_values(by='score', ascending=True)
plt.barh(df_sorted['keyword'], df_sorted['score'])
plt.xlabel('Score')
plt.title('Keyword Difficulty Scores')
plt.show()