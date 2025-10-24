import httpx
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings
from app.schemas.jira_schema import JiraIssueFields

def __ensure_jira_settings() -> Tuple[str, httpx.BasicAuth]:
    """Ensure that JIRA settings are configured properly."""
    if not all([settings.JIRA_EMAIL, settings.JIRA_API_TOKEN, settings.JIRA_BASE_URL]):
        raise ValueError("JIRA settings are not properly configured.")
    
    auth = httpx.BasicAuth(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)
    base_url = settings.JIRA_BASE_URL.rstrip('/')
    
    return base_url, auth


def __default_headers() -> Dict[str, str]:
    """Generate default headers for JIRA API requests."""
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    
async def __send_request(
    method: str,
    endpoint: str,
    *,
    auth: httpx.BasicAuth,
    headers: Dict[str, str],
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None,
    raise_on_error: bool = True,
    return_full_response: bool = False
) -> Any:
    """Send an HTTP request to the JIRA API."""
    url = f"{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                auth=auth,
                headers=headers,
                json=json,
                params=params,
            )
        except httpx.RequestError as exc:
            if raise_on_error:
                raise RuntimeError(f"An error occurred while requesting {exc.request.url!r}.") from exc
            return {"status": None, "ok": False, "error": str(exc)}
            
        try:
            body = response.json()
        except ValueError:
            body = response.text
            
        if response.is_error:
            if raise_on_error:
                raise RuntimeError(f"JIRA API request failed with status {response.status_code}: {body}")
            return {"status": response.status_code, "ok": False, "error": body}
        
        if return_full_response:
            return {"status": response.status_code, "ok": True, "body": body}
        return body
    
    
async def get_jira_issue(jql: str, max_results: int = 50) -> Any:
    """Fetch a JIRA issue by its key."""
    if not jql:
        raise ValueError("JQL query must be provided.")
    
    base_url, auth = __ensure_jira_settings()
    headers = __default_headers()
    endpoint = f"{base_url}/rest/api/3/search/jql"
    
    json_data = {
        "jql": jql,
        "maxResults": max_results,
        "fields": ["summary", "project", "assignee", "reporter", "created", "status"],
        "fieldsByKeys": True,
        # "expand": ["string"],
        "properties": [],
        "reconcileIssues": [
            2154
        ]
    }
    
    return await __send_request("POST", endpoint=endpoint, auth=auth, headers=headers, json=json_data)