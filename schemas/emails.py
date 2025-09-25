from pydantic import BaseModel
from typing import List, Dict, Any

class EmailAnalysisResponse(BaseModel):
    sender: str
    subject: str
    date: str
    body_preview: str
    attachments: List[str]
    analysis: Dict[str, Any]