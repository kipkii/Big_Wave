from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
V2_ROOT = PROJECT_ROOT.parent
DATA_DIR = PROJECT_ROOT / "data"
EXPORTS_DIR = DATA_DIR / "exports"
DB_PATH = DATA_DIR / "bigwave.db"
KEYWORD_SETS_PATH = DATA_DIR / "keyword_sets.json"

load_dotenv(V2_ROOT / ".env")
load_dotenv(PROJECT_ROOT / ".env")

SUPPORTED_SOURCES = ["youtube", "naver_news", "naver_blog"]
DATA_MODES = ["real", "sample"]
