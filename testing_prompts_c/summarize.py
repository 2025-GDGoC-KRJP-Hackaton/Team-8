from google import genai
from google.genai import types
import os
import argparse


api_key_from_zshrc = os.getenv("MY_API_KEY")

client = genai.Client(api_key=api_key_from_zshrc)

parser = argparse.ArgumentParser(description="Process a Discord chat log and send to Gemini API.")
parser.add_argument('-f', '--file', required=True, help="Path to the input chat log file")
args = parser.parse_args()

with open(args.file, "r", encoding="utf-8") as f:
	message_history = f.read()

prompt = message_history 
instruction = "You are a project manager and you divide each person's role in the project. You print an overview of the project, tasks of each person, and techstack. Also write the current progress."


response = client.models.generate_content(
	model="gemini-2.0-flash", 
	config=types.GenerateContentConfig(system_instruction=instruction),
	contents=prompt
)
print(response.text)
