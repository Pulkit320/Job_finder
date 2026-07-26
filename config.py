import json
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

DEFAULT_CONFIG_PATH = Path(__file__).parent / "data" / "config.json"

DEFAULT_KEYWORDS = [
    "Software Engineer",
    "AI Engineer",
    "Prompt Engineer",
    "Machine Learning Engineer",
    "Applied AI Engineer",
    "LLM Engineer",
    "Generative AI Engineer",
    "AI Developer",
    "Prompt Developer",
    "Software Engineer 2027",
    "AI Engineer 2027",
    "Graduate Engineer 2027",
    "2027 Batch",
]

DEFAULT_LOCATIONS = [
    "India",
    "Bengaluru",
    "Bangalore",
    "Mumbai",
    "Delhi",
    "Gurugram",
    "Gurgaon",
    "Hyderabad",
    "Noida",
    "Pune",
    "Chennai",
]

DEFAULT_COUNTRIES = ["IN"]

DEFAULT_ENABLED_SOURCES = [
    "greenhouse",
    "lever",
    "workday",
    "wellfound",
    "yc",
    "careers",
    "google",
    "linkedin",
    "indeed",
    "naukri",
]

class AppConfig(BaseModel):
    keywords: List[str] = Field(default_factory=lambda: DEFAULT_KEYWORDS)
    locations: List[str] = Field(default_factory=lambda: DEFAULT_LOCATIONS)
    countries: List[str] = Field(default_factory=lambda: DEFAULT_COUNTRIES)
    remote_only: bool = False
    india_only: bool = True
    entry_level_only: bool = True
    target_graduation_year: int = 2027
    experience_levels: List[str] = Field(default_factory=lambda: ["Entry Level", "2027 Graduating Batch"])
    posting_age_days: int = 3
    max_concurrent_requests: int = 10
    enabled_sources: List[str] = Field(default_factory=lambda: DEFAULT_ENABLED_SOURCES)
    fuzzy_threshold: float = 95.0
    request_timeout_seconds: int = 20

def get_config_path() -> Path:
    config_path = DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    return config_path

def load_config() -> AppConfig:
    config_path = get_config_path()
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig(**data)
        except Exception:
            return AppConfig()
    else:
        cfg = AppConfig()
        save_config(cfg)
        return cfg

def save_config(cfg: AppConfig) -> None:
    config_path = get_config_path()
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(cfg.model_dump_json(indent=2))
