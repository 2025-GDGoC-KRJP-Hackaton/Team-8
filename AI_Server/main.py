import os, datetime
from fastapi import FastAPI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from AI_Server.models import Payload            # the schema above
from dotenv import load_dotenv

load_dotenv()                           
app   = FastAPI()
parser = PydanticOutputParser(pydantic_object=Payload)

llm   = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    api_key=os.getenv("GEMINI_API_KEY"),         
    temperature=0.3,
).bind_tools([Payload])

SYSTEM = "You are the Project Manager of this project. Return JSON ONLY, matching the schema."
TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM),
        ("human",
"""[Deadline: {deadline}]
[Date: {today}]

### Few-shot
<example>
User chat:
We need frontend wireframes by Friday. Tina can you own it?
Assistant(JSON):
{{"tickets":[{{"title":"Create frontend wireframes","assignee":'Tina',"due_date":"friday","priority":"MID","description":"Create wireframes for the frontend of the application."}}]}}
</example>

### New chat slice
{chat_slice}

Extract actionable tickets. Group related tickets under a 2-milestone sprint_plan if appropriate.
{format_instructions}"""
        ),
    ]
).partial(
    today=datetime.date.today(),
    format_instructions=parser.get_format_instructions()
)


@app.post("/extract")
async def extract(body: dict):
    prompt  = TEMPLATE.format(**body)            # body has chat_slice, deadline
    result  = await llm.ainvoke(prompt)
    return parser.parse(result.content)          # runtime validation!

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 