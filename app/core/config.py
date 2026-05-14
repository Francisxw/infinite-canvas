import os
import uuid


def _load_env_file(env_file: str) -> None:
    if not os.path.exists(env_file):
        return
    try:
        with open(env_file, "r", encoding="utf-8-sig") as file:
            for raw_line in file.read().splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                _ = os.environ.setdefault(key, value)
    except Exception as exc:
        print(f"加载 API/.env 失败: {exc}")


def _model_list(env_name: str, primary: str, defaults: list[str]) -> list[str]:
    configured = os.getenv(env_name, "")
    configured_values = [item.strip() for item in configured.split(",") if item.strip()]
    values = configured_values or [primary, *defaults]
    return list(dict.fromkeys(v for v in values if v))


CLIENT_ID = str(uuid.uuid4())
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORKFLOW_DIR = os.path.join(BASE_DIR, "workflows")
def get_workflow_zimage() -> str:
    return os.getenv("WORKFLOW_ZIMAGE", "Z-Image.json")


def get_workflow_path() -> str:
    return os.path.join(WORKFLOW_DIR, get_workflow_zimage())


WORKFLOW_ZIMAGE = get_workflow_zimage()
WORKFLOW_PATH = get_workflow_path()

WORKFLOW_ENHANCE = os.getenv("WORKFLOW_ENHANCE", "Z-Image-Enhance.json")
WORKFLOW_UPSCALE = os.getenv("WORKFLOW_UPSCALE", "upscale.json")
WORKFLOW_ANGLE = os.getenv("WORKFLOW_ANGLE", "2511.json")
WORKFLOW_KLEIN = os.getenv("WORKFLOW_KLEIN", "Flux2-Klein.json")
WORKFLOW_CANVAS_EDIT = os.getenv("WORKFLOW_CANVAS_EDIT", "Flux2-Klein.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
API_ENV_FILE = os.path.join(BASE_DIR, "API", ".env")
DATA_DIR = os.path.join(BASE_DIR, "data")
CONVERSATION_DIR = os.path.join(DATA_DIR, "conversations")
CANVAS_DIR = os.path.join(DATA_DIR, "canvases")
GLOBAL_CONFIG_FILE = os.path.join(BASE_DIR, "global_config.json")
CANVAS_TRASH_RETENTION_MS = 30 * 24 * 60 * 60 * 1000

_load_env_file(API_ENV_FILE)

def get_comfyui_instances() -> list[str]:
    return [s.strip() for s in os.getenv("COMFYUI_INSTANCES", "127.0.0.1:8188").split(",") if s.strip()]


COMFYUI_INSTANCES = get_comfyui_instances()
COMFYUI_ADDRESS = COMFYUI_INSTANCES[0]

def get_ai_base_url() -> str:
    return os.getenv("COMFLY_BASE_URL", "https://ai.comfly.chat").rstrip("/")


def get_ai_api_key() -> str:
    return os.getenv("COMFLY_API_KEY", "")


def get_chat_model() -> str:
    return os.getenv("CHAT_MODEL", "gpt-4o-mini")


def get_image_model() -> str:
    return os.getenv("IMAGE_MODEL", "gpt-image-2")


def get_system_prompt() -> str:
    return os.getenv("SYSTEM_PROMPT", "You are a helpful assistant.")


def get_max_history_messages() -> int:
    return int(os.getenv("MAX_HISTORY_MESSAGES", "30"))


def get_ai_request_timeout() -> float:
    return float(os.getenv("REQUEST_TIMEOUT", "120"))


def get_image_poll_interval() -> float:
    return float(os.getenv("IMAGE_POLL_INTERVAL", "2"))


AI_BASE_URL = get_ai_base_url()
AI_API_KEY = get_ai_api_key()
CHAT_MODEL = get_chat_model()
IMAGE_MODEL = get_image_model()
SYSTEM_PROMPT = get_system_prompt()
MAX_HISTORY_MESSAGES = get_max_history_messages()
AI_REQUEST_TIMEOUT = get_ai_request_timeout()
IMAGE_POLL_INTERVAL = get_image_poll_interval()

def get_chat_models() -> list[str]:
    return _model_list("CHAT_MODELS", get_chat_model(), ["gpt-4o-mini", "gemini-3.1-flash-image-preview-2k"])


def get_image_models() -> list[str]:
    return _model_list("IMAGE_MODELS", get_image_model(), ["nano-banana-pro"])


CHAT_MODELS = get_chat_models()
IMAGE_MODELS = get_image_models()

for path in [OUTPUT_DIR, STATIC_DIR, WORKFLOW_DIR, CONVERSATION_DIR, CANVAS_DIR]:
    os.makedirs(path, exist_ok=True)
