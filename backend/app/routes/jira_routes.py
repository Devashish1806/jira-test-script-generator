from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.services.jira_services import (
    get_jira_issue,
    create_jira_issue,
    update_jira_issue,
    bulk_update_issue_cards,
    delete_jira_issue,
    create_jira_test_issues,
    status_jira_test_issues
)
from app.schemas.jira_schema import JiraIssueFields, JiraUpdateIssueFields, JiraTestIssueFields

router = APIRouter()

@router.get("/issues")
async def list_jira_issues(jql: str = "project = DEV ORDER BY created DESC", max_results: int = 50):
    """List JIRA issues by JQL."""
    issues = await get_jira_issue(jql, max_results)
    return issues

@router.get("/issue/{issue_key}")
async def get_jira_issue_by_key(issue_key: str):
    """Fetch a single JIRA issue by its key."""
    jql = f'key = {issue_key}'
    issue = await get_jira_issue(jql, max_results=1)
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    return issue

@router.post("/issue")
async def create_issue(issue: JiraIssueFields):
    """Create a new JIRA issue."""
    created = await create_jira_issue(issue)
    return created

@router.put("/issue/{issue_key}")
async def update_issue(issue_key: str, issue: JiraUpdateIssueFields):
    """Update an existing JIRA issue (replace fields)."""
    updated = await update_jira_issue(issue_key, issue)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found or not updated")
    return updated

@router.patch("/issues/cards")
async def update_issue_cards(updates: List[JiraUpdateIssueFields]):
    """
    Bulk update 'card' related fields for multiple issues.
    Expects a list where each item contains the issue key and the fields to update.
    """
    result = await bulk_update_issue_cards(updates)
    return {"updated": result}

@router.delete("/issue/{issue_key}")
async def delete_issue(issue_key: str):
    """Delete a JIRA issue by its key."""
    deleted = await delete_jira_issue(issue_key)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found or not deleted")
    return {"detail": f"Issue {issue_key} deleted successfully."}

@router.post("/issues/test")
async def create_test_issue(issues: List[JiraTestIssueFields]):
    """Create a JIRA Test issue (uses Xray/test-specific fields)."""
    created = await create_jira_test_issues(issues)
    if not created:
        raise HTTPException(status_code=400, detail="Failed to create test issue")
    return created

@router.get("/issues/test/{job_id}/status")
async def get_test_issues_status(job_id: str):
    """Get the status of a bulk test issue creation job in Xray Cloud."""
    status = await status_jira_test_issues(job_id)
    if not status:
        raise HTTPException(
            status_code=404, 
            detail=f"Job {job_id} not found or status check failed"
        )
    return status