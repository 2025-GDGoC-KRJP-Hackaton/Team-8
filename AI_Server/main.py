import os, datetime
from fastapi import FastAPI, HTTPException
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from models import Payload, ChatRequest, PromptType, ProjectOverview
from dotenv import load_dotenv
import json
import traceback
import re

load_dotenv()                           
app = FastAPI()

# Load prompts from files
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "testing_prompts_c", "prompts")

def load_prompt(prompt_type: PromptType) -> str:
    prompt_file = {
        PromptType.TICKETS: "tickets.inp",
        PromptType.SHORT_OVERVIEW: "short_overview.inp",
        PromptType.LONG_OVERVIEW: "long_overview.inp",
        PromptType.LIST_TASKS: "list_tasks.inp"
    }.get(prompt_type)
    
    if not prompt_file:  # if the prompt file is not found
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Prompt file not found: {prompt_file}")

def clean_json_response(response: str) -> str:
    # Remove markdown code block markers if present
    response = re.sub(r'^```json\n', '', response)
    response = re.sub(r'\n```$', '', response)
    return response.strip()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),         
    temperature=0.3,
).bind_tools([Payload, ProjectOverview])

def create_prompt_template(prompt_type: PromptType) -> ChatPromptTemplate:
    system_prompt = load_prompt(prompt_type)
    
    if prompt_type == PromptType.TICKETS:
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
[Date: {today}]

### Few-shot Examples
<example>
User chat:
- Alice: We need to finish the login page by tomorrow
- Bob: I'll take care of it
- Alice: Great, make sure to include password reset functionality
- Bob: Will do, I'll prioritize that

Assistant(JSON):
{{
    "tickets": [
        {{
            "title": "Complete login page",
            "assignee": "Bob",
            "due_date": "2024-02-21",
            "priority": "HIGH",
            "description": "Implement login page including password reset functionality"
        }}
    ]
}}
</example>

<example>
User chat:
- John: I'll work on the login page
- Alice: Great, please finish by tomorrow
- John: I'll make sure to include password reset

Assistant(JSON):
{{
    "tickets": [
        {{
            "title": "Implement login page with password reset",
            "assignee": "John",
            "due_date": "2024-02-21",
            "priority": "HIGH",
            "description": "Create login page functionality including password reset feature"
        }}
    ]
}}
</example>

### Chat to Analyze
{chat_slice}

Extract ALL actionable tickets from the chat. For each task mentioned:
1. Create a ticket with a clear title
2. Assign it to the person who volunteered or was assigned
3. Set the due date in ISO 8601 format (YYYY-MM-DD)
4. Set priority based on urgency (HIGH/MID/LOW)
5. Write a detailed description

Return the tickets in JSON format matching the schema exactly.
{format_instructions}"""
            )
        ]).partial(today=datetime.date.today().isoformat())
    else:
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
[Date: {today}]

### Chat to Analyze
{chat_slice}

{format_instructions}"""
            )
        ]).partial(today=datetime.date.today().isoformat())

@app.post("/extract")
async def extract(request: ChatRequest):
    try:
        # Format messages for analysis
        chat_slice = "\n".join([
            f"- {msg.author}: {msg.content}"
            for msg in request.messages
        ])
        
        # Create appropriate parser based on prompt type
        if request.prompt_type == PromptType.TICKETS:
            parser = PydanticOutputParser(pydantic_object=Payload)
        else:
            parser = PydanticOutputParser(pydantic_object=ProjectOverview)
        
        # Create and format prompt
        template = create_prompt_template(request.prompt_type)
        prompt = template.format(
            chat_slice=chat_slice,
            format_instructions=parser.get_format_instructions()
        )
        
        # Get AI response
        result = await llm.ainvoke(prompt)
        print("Raw AI Response:", result.content)  # Debug print
        
        try:
            # Clean the response and parse as JSON
            cleaned_response = clean_json_response(result.content)
            print("Cleaned Response:", cleaned_response)  # Debug print
            
            json_response = json.loads(cleaned_response)
            print("Parsed JSON:", json_response)  # Debug print
            
            # Then parse with Pydantic
            parsed = parser.parse(cleaned_response)
            return parsed
        except json.JSONDecodeError as json_error:
            print("JSON Parse Error:", str(json_error))  # Debug print
            print("Raw Response:", result.content)  # Debug print
            print("Cleaned Response:", cleaned_response)  # Debug print
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON response: {str(json_error)}\nRaw response: {result.content}\nCleaned response: {cleaned_response}"
            )
        except Exception as parse_error:
            print("Parse Error:", str(parse_error))  # Debug print
            print("Raw Response:", result.content)  # Debug print
            print("Cleaned Response:", cleaned_response)  # Debug print
            print("Traceback:", traceback.format_exc())  # Debug print
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response: {str(parse_error)}\nRaw response: {result.content}\nCleaned response: {cleaned_response}\nTraceback: {traceback.format_exc()}"
            )
        
    except Exception as e:
        print("General Error:", str(e))  # Debug print
        print("Traceback:", traceback.format_exc())  # Debug print
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}\nTraceback: {traceback.format_exc()}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 