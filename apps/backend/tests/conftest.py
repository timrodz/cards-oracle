import os
import sys
from pathlib import Path


os.environ.setdefault("LLM_PROVIDER", "ollama")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
