import os
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

app = FastAPI()

class Message(BaseModel):
    content: str
    author: str
    timestamp: str

class ChatAnalysis(BaseModel):
    messages: List[Message]
    project_context: Optional[Dict] = None

class ProjectUpdate(BaseModel):
    tasks: List[Dict]
    deadlines: Dict[str, str]
    priorities: List[str]
    recommendations: List[str]

# System prompt for the AI
PROJECT_MANAGER_PROMPT = """You are an AI Project Manager analyzing a group chat. Your role is to:
1. Identify tasks and their status
2. Set and track deadlines
3. Prioritize work items
4. Provide recommendations for project progress
5. Identify blockers and dependencies
6. Ensure team accountability

When analyzing messages, focus on:
- Task assignments and updates
- Deadline mentions
- Progress reports
- Blockers or issues
- Team member availability
- Resource needs

Provide clear, actionable insights and maintain a professional tone."""

@app.post("/analyze-chat", response_model=ProjectUpdate)
async def analyze_chat(chat_data: ChatAnalysis):
    try:
        # Format messages for analysis
        formatted_messages = "\n".join([
            f"[{msg.timestamp}] {msg.author}: {msg.content}"
            for msg in chat_data.messages
        ])

        # Create the prompt
        prompt = f"""
        {PROJECT_MANAGER_PROMPT}

        Project Context:
        {chat_data.project_context if chat_data.project_context else 'No specific context provided'}

        Recent Chat Messages:
        {formatted_messages}

        Please analyze the above chat and provide:
        1. A list of identified tasks with their status
        2. Any mentioned or suggested deadlines
        3. Priority items that need immediate attention
        4. Specific recommendations for the team
        """

        # Get AI response
        response = model.generate_content(prompt)
        
        # Parse the response and structure it
        # Note: In a real implementation, you'd want to parse the response more carefully
        # This is a simplified version
        return ProjectUpdate(
            tasks=[{"description": "Task 1", "status": "In Progress"}],  # Example
            deadlines={"Task 1": "2024-03-01"},  # Example
            priorities=["Complete Task 1"],  # Example
            recommendations=["Focus on completing Task 1"]  # Example
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 