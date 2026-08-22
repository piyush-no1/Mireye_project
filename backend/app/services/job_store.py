import json
import os
from typing import Dict, Any, Optional
from app.config import settings

class JobStore:
    """In-memory and file-backed job status tracking store."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self, run_id: str, query: str) -> Dict[str, Any]:
        job_data = {
            "run_id": run_id,
            "status": "pending",
            "query": query,
            "error": None,
        }
        self._jobs[run_id] = job_data
        return job_data

    def update_status(
        self,
        run_id: str,
        status: str,
        error: Optional[str] = None
    ):
        if run_id in self._jobs:
            self._jobs[run_id]["status"] = status
            if error:
                self._jobs[run_id]["error"] = error
        else:
            self._jobs[run_id] = {
                "run_id": run_id,
                "status": status,
                "query": "",
                "error": error
            }

    def get_job(self, run_id: str) -> Optional[Dict[str, Any]]:
        if run_id in self._jobs:
            return self._jobs[run_id]
        
        # Check if result file exists on disk
        output_file = os.path.join(settings.output_dir, f"{run_id}.json")
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    status = data.get("status", "completed")
                    errors = data.get("errors", [])
                    err_msg = errors[0]["message"] if errors else None
                    return {
                        "run_id": run_id,
                        "status": status,
                        "query": data.get("query", ""),
                        "error": err_msg
                    }
            except Exception:
                pass
        return None

job_store = JobStore()
