import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application configuration settings."""

    # JIRA settings
    JIRA_EMAIL: str = os.getenv("JIRA_EMAIL")
    JIRA_API_TOKEN: str = os.getenv("JIRA_API_TOKEN")
    JIRA_BASE_URL: str = os.getenv("JIRA_BASE_URL")
    XRAY_CLIENT_ID: str = os.getenv("XRAY_CLIENT_ID")
    XRAY_CLIENT_SECRET: str = os.getenv("XRAY_CLIENT_SECRET")
                              
settings = Settings()