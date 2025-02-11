from openai import OpenAI
import google.generativeai as genai
import random
import os
from dotenv import load_dotenv

load_dotenv()


class AI:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")


    def generate_text_openai(self, prompt, text):
        client = OpenAI(api_key=self.openai_api_key)

        message = [{"role": "assistant", "content": prompt}, {"role": "user", "content": text}]
        temperature = 1
        max_tokens = 4095
        frequency_penalty = 0.0

        print("Calling GPT for topic: " + (text[:50] + '..') if len(text) > 52 else text)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=message,
            temperature=temperature,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty
        )
        return response.choices[0].message.content

    def generate_text_gemini(self, prompt, text):
        genai.configure(api_key=self.gemini_api_key)
        combined_input = AI.combine_input(prompt, text)

        model = genai.GenerativeModel("gemini-1.5-flash")

        print("Calling Gemini API for input")

        response = model.generate_content(combined_input)
        return (response.text)

    @staticmethod
    def combine_input(prompt, text):
        return f"{prompt}\n\n{text}"

    def generate_random_content(self, prompt, text):
        choice = random.choice(['openai', 'gemini'])

        if choice == 'openai':
            print("Randomly selected: OpenAI")
            return self.generate_text_openai(prompt, text)
        else:
            print("Randomly selected: Gemini")
            return self.generate_text_gemini(prompt, text)

