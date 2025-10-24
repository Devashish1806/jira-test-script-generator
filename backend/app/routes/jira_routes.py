from fastapi import APIRouter
from app.services.jira_services import (get_jira_issue)
from app.schemas.jira_schema import JiraIssueFields

router = APIRouter()

@router.post("/issue")
async def fetch_jira_issue(jql: str = "project = DEV ORDER BY created DESC", max_results: int = 50):    
    """API endpoint to fetch a JIRA issue by its key."""
    issue = await get_jira_issue(jql, max_results)
    return issue