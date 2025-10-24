import httpx
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings
from app.schemas.jira_schema import JiraIssueFields, JiraUpdateIssueFields

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
    raise_on_error: bool = False,
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


async def create_jira_issue(issue: JiraIssueFields) -> Any:
    """Create a new JIRA issue."""
    base_url, auth = __ensure_jira_settings()
    headers = __default_headers()
    endpoint = f"{base_url}/rest/api/3/issue"

    if hasattr(issue, "dict"):
        fields = issue.dict(exclude_unset=True)
    elif isinstance(issue, dict):
        fields = issue
    else:
        fields = vars(issue)

    payload = {"fields": fields}
    return await __send_request("POST", endpoint=endpoint, auth=auth, headers=headers, json=payload)


async def update_jira_issue(issue_key: str, issue: JiraUpdateIssueFields) -> Any:
    """Update an existing JIRA issue. Only updates fields present in the payload."""

    if not issue_key:
        raise ValueError("issue_key must be provided")
    print(issue)
    base_url, auth = __ensure_jira_settings()
    headers = __default_headers()
    endpoint = f"{base_url}/rest/api/3/issue/{issue_key}"

    # extract only provided fields
    if hasattr(issue, "dict"):
        fields = issue.dict(exclude_unset=True)
    elif isinstance(issue, dict):
        # assume dict already only contains intended updates
        fields = {k: v for k, v in issue.items() if v is not None}
    else:
        fields = {k: v for k, v in vars(issue).items() if v is not None}

    payload = {"fields": fields}

    resp = await __send_request(
        "PUT",
        endpoint=endpoint,
        auth=auth,
        headers=headers,
        json=payload,
        raise_on_error=False,
        return_full_response=True,
    )

    if isinstance(resp, dict) and resp.get("ok"):
        return True
    return False


async def bulk_update_issue_cards(updates: list[JiraUpdateIssueFields]) -> Any:
    """Bulk update 'card' related fields for multiple issues.

    Each item is expected to include the issue key (key / issue_key / issueKey)
    and the fields to update (either as top-level fields or nested under "fields").
    Returns a list of results for each item.
    """
    if not updates:
        return []

    base_url, auth = __ensure_jira_settings()
    headers = __default_headers()

    async def _do_update(item):
        if hasattr(item, "dict"):
            payload = item.dict(exclude_unset=True)
        elif isinstance(item, dict):
            payload = item
        else:
            payload = vars(item)

        issue_key = payload.pop("key", None) or payload.pop("issue_key", None) or payload.pop("issueKey", None)
        if not issue_key:
            return {"key": None, "ok": False, "error": "missing issue key"}

        fields = payload.get("fields", payload)
        endpoint = f"{base_url}/rest/api/3/issue/{issue_key}"

        resp = await __send_request(
            "PUT",
            endpoint=endpoint,
            auth=auth,
            headers=headers,
            json={"fields": fields},
            raise_on_error=False,
            return_full_response=True,
        )

        return {
            "key": issue_key,
            "ok": bool(resp.get("ok") if isinstance(resp, dict) else False),
            "status": resp.get("status") if isinstance(resp, dict) else None,
            "error": resp.get("error") if isinstance(resp, dict) else None,
        }

    tasks = [_do_update(item) for item in updates]
    return await asyncio.gather(*tasks)


async def delete_jira_issue(issue_key: str) -> Any:
    """Delete a JIRA issue by its key."""
    if not issue_key:
        raise ValueError("issue_key must be provided")

    base_url, auth = __ensure_jira_settings()
    headers = __default_headers()
    endpoint = f"{base_url}/rest/api/3/issue/{issue_key}"

    resp = await __send_request(
        "DELETE",
        endpoint=endpoint,
        auth=auth,
        headers=headers,
        raise_on_error=False,
        return_full_response=True,
    )

    if isinstance(resp, dict) and resp.get("ok"):
        return True
    return False
