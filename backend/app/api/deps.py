from app.config import settings, Settings
from app.services.job_store import job_store, JobStore

def get_settings() -> Settings:
    return settings

def get_job_store() -> JobStore:
    return job_store
