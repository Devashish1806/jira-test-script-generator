import httpx
from typing import Optional, Dict, Any, Tuple, List
from app.core.config import settings
from app.schemas.jira_schema import JiraIssueFields, JiraUpdateIssueFields, JiraTestIssueFields
import json

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
    

def __ensure_xray_cloud_settings() -> Tuple[str, str, str]:
    """Ensure that Xray Cloud settings are configured properly."""
    if not all([settings.XRAY_CLIENT_ID, settings.XRAY_CLIENT_SECRET, settings.XRAY_BASE_URL]):
        raise ValueError("Xray Cloud settings are not properly configured.")
    
    xbase = settings.XRAY_BASE_URL.rstrip('/')
    client_id = settings.XRAY_CLIENT_ID
    client_secret = settings.XRAY_CLIENT_SECRET
    
    return xbase, client_id, client_secret


async def __default_xray_headers(xbase: str, client_id: str, client_secret: str) -> Dict[str, str]:
    """Generate default headers for Xray Cloud API requests."""
    
    # Authenticate to Xray Cloud to obtain a bearer token
    auth_endpoint = f"{xbase}/api/v2/authenticate"
    auth_headers = {"Content-Type": "application/json", "Accept": "application/json"}

    auth_resp = await __send_request(
        "POST",
        endpoint=auth_endpoint,
        auth=None,
        headers=auth_headers,
        json={"client_id": client_id, "client_secret": client_secret},
        raise_on_error=True,
        return_full_response=False,
    )

    # auth_resp is expected to be a token string when successful
    token = auth_resp if isinstance(auth_resp, str) else (auth_resp.get("token") if isinstance(auth_resp, dict) else None)
    if not token:
        return False

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
   
async def __send_request(
    method: str,
    endpoint: str,
    *,
    auth: httpx.BasicAuth | None,
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


async def create_jira_test_issues(issues: List[JiraTestIssueFields]) -> Any:
    """Create a new JIRA test issue (Xray Cloud)."""
    if not issues:
        raise ValueError("issue must be provided")
    
    xbase, client_id, client_secret = __ensure_xray_cloud_settings()
    headers = await __default_xray_headers(xbase, client_id, client_secret)
    endpoint = f"{xbase}/api/v2/import/test/bulk"

    # Handle array of issues
    payload = []
    if isinstance(issues, list):
        for issue in issues:
            if hasattr(issue, "dict"):
                payload.append(issue.dict(exclude_unset=True))
            elif isinstance(issue, dict):
                payload.append(issue)
            else:
                payload.append(vars(issue))

    return await __send_request("POST", endpoint=endpoint, auth=None, headers=headers, json=payload)


async def status_jira_test_issues(jobId: str) -> Any:
    """Status of new JIRA test issues (Xray Cloud)."""
    if not jobId:
        raise ValueError("jobId must be provided")
    
    xbase, client_id, client_secret = __ensure_xray_cloud_settings()
    headers = await __default_xray_headers(xbase, client_id, client_secret)
    endpoint = f"{xbase}/api/v2/import/test/bulk/{jobId}/status"

    return await __send_request("GET", endpoint=endpoint, auth=None, headers=headers)

