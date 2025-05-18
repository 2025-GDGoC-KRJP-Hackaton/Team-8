from google import genai
from google.genai import types
import os
import json

# Get API key from environment variable
api_key_from_zshrc = os.getenv("MY_API_KEY")
if not api_key_from_zshrc:
    raise ValueError("MY_API_KEY environment variable not set.")

# Initialize the client
client = genai.Client(api_key=api_key_from_zshrc)

# Define paths for instruction and input files
instruction_path = "../prompts/long_overview.inp"
input_path = "../out/tasks2.json"

# Check if files exist
if not os.path.exists(instruction_path):
    raise FileNotFoundError(f"Instruction file not found at: {instruction_path}")
if not os.path.exists(input_path):
    raise FileNotFoundError(f"Input file not found at: {input_path}")

# Read instruction file
with open(instruction_path, "r", encoding="utf-8") as f:
    instruction = f.read()

# Read input file
with open(input_path, "r", encoding="utf-8") as f:
    input_data = f.read()

# Prepare request and send to Gemini API
response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(system_instruction=instruction),
    contents=input_data
)

# Define output path
output_path = "../out/longsum2.out"

# Write the response to the output file
with open(output_path, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"Response successfully written to {output_path}")

