from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class PromptType(str, Enum):
    TICKETS = "TICKETS"
    SHORT_OVERVIEW = "SHORT_OVERVIEW"
    LONG_OVERVIEW = "LONG_OVERVIEW"
    LIST_TASKS = "LIST_TASKS"

class Message(BaseModel):
    author: str = Field(..., description="The author of the message")
    content: str = Field(..., description="The content of the message")

    class Config:
        json_schema_extra = {
            "example": {
                "author": "John",
                "content": "I'll work on the login page"
            }
        }

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="List of chat messages")
    prompt_type: PromptType = Field(default=PromptType.TICKETS, description="Type of analysis to perform")

    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "author": "John",
                        "content": "I'll work on the login page"
                    },
                    {
                        "author": "Alice",
                        "content": "Great, please finish by tomorrow"
                    }
                ],
                "prompt_type": "TICKETS"
            }
        }

class Ticket(BaseModel):
    title: str = Field(..., description="Title of the ticket")
    assignee: Optional[str] = Field(None, description="Person assigned to the ticket")
    due_date: str = Field(..., description="Due date in ISO 8601 format (YYYY-MM-DD)")
    priority: str = Field(default="MID", pattern="LOW|MID|HIGH", description="Priority level of the ticket")
    description: str = Field(..., description="Detailed description of the ticket")

    @validator('due_date')
    def validate_due_date(cls, v):
        try:
            # Try to parse the date string
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('due_date must be in ISO 8601 format (YYYY-MM-DD)')

class ProjectOverview(BaseModel):
    summary: str = Field(..., description="Project summary")
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks")
    team_roles: Dict[str, str] = Field(..., description="Team member roles")
    tech_stack: Optional[List[str]] = Field(None, description="List of technologies used")
    progress: Optional[Dict[str, List[str]]] = Field(None, description="Project progress status")

class Payload(BaseModel):
    tickets: Optional[List[Ticket]] = Field(None, description="List of extracted tickets")
    overview: Optional[ProjectOverview] = Field(None, description="Project overview")
    tasks: Optional[List[Dict[str, Any]]] = Field(None, description="Simple task list")
