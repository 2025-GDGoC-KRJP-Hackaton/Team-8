import os, datetime
from fastapi import FastAPI, HTTPException
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from models import Payload, ChatRequest, PromptType, ProjectOverview
from dotenv import load_dotenv

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
            "due_date": "tomorrow",
            "priority": "HIGH",
            "description": "Implement login page including password reset functionality"
        }}
    ]
}}
</example>

### Chat to Analyze
{chat_slice}

Extract actionable tickets from the chat.
{format_instructions}"""
            )
        ]).partial(today=datetime.date.today())
    else:
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", """
[Date: {today}]

### Chat to Analyze
{chat_slice}

{format_instructions}"""
            )
        ]).partial(today=datetime.date.today())

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
        return parser.parse(result.content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 