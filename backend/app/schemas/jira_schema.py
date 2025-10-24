from pydantic import BaseModel
from typing import List, Optional

class JiraIssueFields(BaseModel):
    project_key: str
    parent_key: str
    summary: str
    description: Optional[str]
    issuetype: Optional[str]