import logging
import sys
import time
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "outputs")
os.makedirs(LOG_DIR, exist_ok=True)
DIAGNOSTIC_LOG_FILE = os.path.join(LOG_DIR, "system_diagnostics.log")

def clear_diagnostic_logs():
    """Clears and resets system_diagnostics.log whenever the backend server starts."""
    try:
        with open(DIAGNOSTIC_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"[{datetime.now(timezone.utc).isoformat()}] Diagnostic log session initialized on server startup.\n")
    except Exception as e:
        pass

def setup_logging(log_level: str = "INFO"):
    logger = logging.getLogger("aquatrace")
    logger.setLevel(log_level.upper())
    
    if not logger.handlers:
        # Stream Handler for console
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler for system_diagnostics.log
        try:
            file_handler = logging.FileHandler(DIAGNOSTIC_LOG_FILE, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            pass

    return logger

logger = setup_logging()

def log_diagnostic_event(stage: str, component: str, status: str, details: Dict[str, Any], run_id: Optional[str] = None):
    """
    Saves structured diagnostic events (success/failure) directly into system_diagnostics.log.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    log_line = f"[{timestamp}] [{status}] [{stage} -> {component}] (run_id={run_id}): {json.dumps(details)}\n"
    
    try:
        with open(DIAGNOSTIC_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        logger.error(f"Failed to append to diagnostic log file {DIAGNOSTIC_LOG_FILE}: {e}")

    if status == "FAILED":
        logger.error(f"DIAGNOSTIC FAILURE [{stage} -> {component}]: {json.dumps(details)}")
    else:
        logger.info(f"DIAGNOSTIC EVENT [{stage} -> {component}]: status={status}")

def log_tool_call(tool_name: str, inputs: Dict[str, Any], duration_seconds: float, success: bool, error_message: Optional[str] = None, run_id: Optional[str] = None):
    log_data = {
        "tool_name": tool_name,
        "inputs": inputs,
        "latency_seconds": round(duration_seconds, 4),
        "success": success,
        "error": error_message
    }
    status = "SUCCESS" if success else "FAILED"
    log_diagnostic_event(
        stage="Tool Execution",
        component=tool_name,
        status=status,
        details=log_data,
        run_id=run_id
    )
