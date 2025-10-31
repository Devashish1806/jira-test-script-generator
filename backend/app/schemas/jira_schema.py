from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class ProjectRef(BaseModel):
    key: str = "DEV"
    
class ParentRef(BaseModel):
    key: str = "DEV-3"

class IssueType(str, Enum):
    Story = "story"
    Epic = "epic"
    Test = "test"
    Task = "task"
    Bug = "bug"

class IssueTypeRef(BaseModel):
    name: IssueType = IssueType.Test

class Description(BaseModel):
    type: str = "doc"
    version: int = 1
    content: List[Dict[str, Any]] = [
        {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": "Issue description goes here."
                }
            ]
        }
    ]

class JiraIssueFields(BaseModel):
    project: ProjectRef
    parent: ParentRef
    summary: str
    description: Description = None
    issuetype: IssueTypeRef
    
class JiraUpdateIssueFields(BaseModel):
    project: Optional[ProjectRef] = None
    parent: Optional[ParentRef] = None
    summary: Optional[str] = None
    description: Optional[Description] = None
    issuetype: Optional[IssueTypeRef] = None

class TestType(str, Enum):
    Manual = "Manual"
    Generic = "Generic"
    Cucumber = "Cucumber"

class JiraTestStep(BaseModel):
    action: str = "start"
    data: str = "step data"
    result: str = "expected result"

class JiraTestIssueFields(BaseModel):
    fields: JiraIssueFields
    testtype: TestType = TestType.Manual
    steps: Optional[List[JiraTestStep]] = None