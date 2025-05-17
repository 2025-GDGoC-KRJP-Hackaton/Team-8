from google import genai
from google.genai import types
import os
import argparse

# Get API key from environment variable
api_key_from_zshrc = os.getenv("MY_API_KEY")
if not api_key_from_zshrc:
    raise ValueError("MY_API_KEY environment variable not set.")

client = genai.Client(api_key=api_key_from_zshrc)

# Set up argument parser
parser = argparse.ArgumentParser(description="Process a Discord chat log and send to Gemini API.")
parser.add_argument('-f', '--file', required=True, help="Path to the input chat log file")
parser.add_argument('-i', '--instruction', required=True, help="Path to the prompt input")
args = parser.parse_args()

# Read chat log
with open(args.file, "r", encoding="utf-8") as f:
    message_history = f.read()

# Read instruction
with open(args.instruction, "r", encoding="utf-8") as f:
    instruction_from_file = f.read()

# Prepare request
prompt = message_history
instruction = instruction_from_file

response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(system_instruction=instruction),
    contents=prompt
)

print(response.text)

