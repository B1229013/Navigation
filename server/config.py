"""Configuration constants and paths.

All paths are absolute (WSL paths). Model weights live under UniGoal's data
directory; outputs (photos, logs) go to UniGoal's output dir for fast disk I/O.
"""
import os
from pathlib import Path

UNIGOAL_ROOT = Path("/home/user/UniGoal")

SAM_WEIGHTS = UNIGOAL_ROOT / "data" / "models" / "sam_vit_h_4b8939.pth"
GROUNDINGDINO_WEIGHTS = UNIGOAL_ROOT / "data" / "models" / "groundingdino_swint_ogc.pth"
GROUNDINGDINO_CONFIG = UNIGOAL_ROOT / "third_party" / "Grounded-Segment-Anything" / "GroundingDINO" / "groundingdino" / "config" / "GroundingDINO_SwinT_OGC.py"

OUTPUT_ROOT = UNIGOAL_ROOT / "output" / "sessions"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2-vision")

SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))

GROUNDINGDINO_BOX_THRESHOLD = 0.30
GROUNDINGDINO_TEXT_THRESHOLD = 0.25
SAM_TOP_K_BOXES = 5

VLM_TIMEOUT_S = 60
GOAL_DECOMPOSE_TIMEOUT_S = 30


def ensure_output_dir(session_id: str) -> Path:
    p = OUTPUT_ROOT / session_id
    (p / "photo").mkdir(parents=True, exist_ok=True)
    (p / "annotated").mkdir(parents=True, exist_ok=True)
    return p
