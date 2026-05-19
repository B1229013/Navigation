"""Configuration constants and paths.

Paths are auto-detected for both WSL and Windows environments.
Model weights and configs are resolved relative to the project root.
"""
import os
from pathlib import Path

# Project root (where this repo lives)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Model weights — check local project first, then WSL paths
_LOCAL_MODELS = PROJECT_ROOT / "models"
_WSL_MODELS = Path("/home/user/UniGoal/data/models")

if (_LOCAL_MODELS / "groundingdino_swint_ogc.pth").exists():
    GROUNDINGDINO_WEIGHTS = _LOCAL_MODELS / "groundingdino_swint_ogc.pth"
elif (_WSL_MODELS / "groundingdino_swint_ogc.pth").exists():
    GROUNDINGDINO_WEIGHTS = _WSL_MODELS / "groundingdino_swint_ogc.pth"
else:
    GROUNDINGDINO_WEIGHTS = _LOCAL_MODELS / "groundingdino_swint_ogc.pth"  # default

# GroundingDINO config — check cloned repo locations
_GDINO_REPO = Path(os.environ.get(
    "GROUNDINGDINO_REPO",
    str(PROJECT_ROOT.parent / "GroundingDINO")
))
_GDINO_CONFIG_CANDIDATES = [
    _GDINO_REPO / "groundingdino" / "config" / "GroundingDINO_SwinT_OGC.py",
    PROJECT_ROOT.parent.parent / "GroundingDINO" / "groundingdino" / "config" / "GroundingDINO_SwinT_OGC.py",
    Path("C:/Users/user/Downloads/GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"),
    Path("/home/user/UniGoal/third_party/Grounded-Segment-Anything/GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"),
]
GROUNDINGDINO_CONFIG = next(
    (p for p in _GDINO_CONFIG_CANDIDATES if p.exists()),
    _GDINO_CONFIG_CANDIDATES[0],  # default to first candidate
)

# SAM weights (optional — not loaded by default to stay under VRAM budget)
SAM_WEIGHTS = _LOCAL_MODELS / "sam_vit_h_4b8939.pth"

# Output
OUTPUT_ROOT = PROJECT_ROOT / "output" / "sessions"

# LLM services
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2-vision")

# Server
SERVER_HOST = os.environ.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))

# Detection thresholds
GROUNDINGDINO_BOX_THRESHOLD = 0.30
GROUNDINGDINO_TEXT_THRESHOLD = 0.25
SAM_TOP_K_BOXES = 5

# Timeouts
VLM_TIMEOUT_S = 60
GOAL_DECOMPOSE_TIMEOUT_S = 30


def ensure_output_dir(session_id: str) -> Path:
    p = OUTPUT_ROOT / session_id
    (p / "photo").mkdir(parents=True, exist_ok=True)
    (p / "annotated").mkdir(parents=True, exist_ok=True)
    return p
