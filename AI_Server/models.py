from pydantic import BaseModel, Field
from typing import List, Optional

class Ticket(BaseModel):
    title: str
    assignee: Optional[str] = None
    due_date: str      # ISO 8601 format
    priority: str = Field(default="MID", pattern="LOW|MID|HIGH")
    description: str

class Plan(BaseModel):
    objective: str
    milestones: List[str]

class Payload(BaseModel):
    tickets: List[Ticket]
