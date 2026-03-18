import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
LOGS_DIR = os.path.join(STORAGE_DIR, "logs")
SCREENSHOTS_DIR = os.path.join(STORAGE_DIR, "screenshots")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

local_app_data = os.environ.get("LOCALAPPDATA", "")
default_adb = os.path.join(local_app_data, "Android", "Sdk", "platform-tools", "adb.exe") if local_app_data else "adb"
ADB_PATH = default_adb if os.path.exists(default_adb) else "adb"

# ── Option A: OpenRouter / Cloud API (active) ──────────────────────────────────
OPENAI_API_KEY   = "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"
LLM_BASE_URL     = "https://openrouter.ai/api/v1"
LLM_MODEL        = "openai/gpt-4o-mini"
LLM_VISION_MODEL = "openai/gpt-4o-mini"
ENABLE_VISION_FALLBACK = False  # Cloud model is capable — no moondream needed

# ── Option B: Local Ollama ─────────────────────────────────────────────────────
# OPENAI_API_KEY   = "dummy_key"
# LLM_BASE_URL     = "http://localhost:11434/v1"
# LLM_MODEL        = "llama3.2:latest"
# LLM_VISION_MODEL = "moondream:latest"
# ENABLE_VISION_FALLBACK = True   # Enable for local small models that need vision assist
