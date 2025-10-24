from pydantic import BaseModel
from typing import List, Optional

class ProjectRef(BaseModel):
    key: str

class IssueType(BaseModel):
    name: Optional[str] = None

class JiraIssueFields(BaseModel):
    project: ProjectRef
    parent: ProjectRef
    summary: str
    issuetype: IssueType
    
class JiraUpdateIssueFields(BaseModel):
    project: Optional[ProjectRef] = None
    parent: Optional[ProjectRef] = None
    summary: Optional[str] = None
    issuetype: Optional[IssueType] = None