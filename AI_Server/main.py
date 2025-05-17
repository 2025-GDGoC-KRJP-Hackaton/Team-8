import os, datetime
from fastapi import FastAPI, HTTPException
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from models import Payload, ChatRequest, PromptType, ProjectOverview, Summary
from dotenv import load_dotenv
import json
import traceback
import re
from typing import Optional

load_dotenv()                           
app = FastAPI()

# Load prompts from files
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "testing_prompts_c", "prompts")

def load_prompt(prompt_type: PromptType) -> str:
    prompt_file = {
        PromptType.TICKETS: "tickets.inp",
        PromptType.SHORT_OVERVIEW: "short_overview.inp",
        PromptType.LONG_OVERVIEW: "long_overview.inp",
        PromptType.LIST_TASKS: "list_tasks.inp",
        PromptType.SUMMARY: "summary.inp"
    }.get(prompt_type)
    
    if not prompt_file:  # if the prompt file is not found
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    prompt_path = os.path.join(PROMPTS_DIR, prompt_file)
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Prompt file not found: {prompt_file}")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error reading prompt file: {str(e)}")

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
).bind_tools([Payload, ProjectOverview, Summary])

def create_prompt_template(prompt_type: PromptType, counts: Optional[int] = None, timestamp: Optional[str] = None, days_of_week: Optional[str] = None) -> ChatPromptTemplate:
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

### Chat to Analyze
{chat_slice}

Extract exactly {counts} tickets (or fewer if there aren't enough tasks) from the chat. For each task:
1. Create a ticket with a clear title
2. Assign it to the person who volunteered or was assigned
3. Calculate the due date based on mentioned dates or relative time (using {timestamp} as reference)
4. Set priority based on urgency (HIGH/MID/LOW)
5. Write a detailed description

If the message is in Korean, translate the task details to English but keep the original meaning.
Return the tickets in JSON format matching the schema exactly.
{format_instructions}"""
            )
        ]).partial(
            today=datetime.date.today().isoformat(),
            counts=counts or 3,  # Default to 3 if not specified
            timestamp=timestamp or datetime.datetime.now().isoformat(),
            days_of_week=days_of_week or datetime.datetime.now().strftime("%A").upper()
        )
    elif prompt_type == PromptType.SUMMARY:
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
[Date: {today}]

### Chat to Analyze
{chat_slice}

Create a comprehensive written summary of the discussion. Focus on:
1. Main decisions and outcomes
2. Key points discussed
3. Any concerns or blockers raised
4. Future steps and recommendations

Write in a natural, flowing style that captures the essence of the discussion.
Return the summary in the specified JSON format.
{format_instructions}"""
            )
        ]).partial(
            today=datetime.date.today().isoformat(),
            timestamp=timestamp or datetime.datetime.now().isoformat(),
            days_of_week=days_of_week or datetime.datetime.now().strftime("%A").upper()
        )
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
        elif request.prompt_type == PromptType.SUMMARY:
            parser = PydanticOutputParser(pydantic_object=Summary)
        else:
            parser = PydanticOutputParser(pydantic_object=ProjectOverview)
        
        # Create and format prompt
        template = create_prompt_template(
            request.prompt_type,
            counts=request.counts,
            timestamp=request.timestamp,
            days_of_week=request.days_of_week
        )
        prompt = template.format(
            chat_slice=chat_slice,
            format_instructions=parser.get_format_instructions()
        )
        
        # Get AI response
        result = await llm.ainvoke(prompt)
        
        try:
            # Clean the response and parse as JSON
            cleaned_response = clean_json_response(result.content)
            json_response = json.loads(cleaned_response)
            
            # Then parse with Pydantic
            parsed = parser.parse(cleaned_response)
            return parsed
        except json.JSONDecodeError as json_error:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid JSON response: {str(json_error)}"
            )
        except Exception as parse_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response: {str(parse_error)}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 