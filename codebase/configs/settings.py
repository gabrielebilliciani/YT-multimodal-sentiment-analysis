# configs/settings.py
import os
from dotenv import load_dotenv

load_dotenv() # Load .env file from the root of the project (where main.py is likely run)

# --- API Keys ---
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Application Mode ---
APP_MODE = os.getenv("APP_MODE", "PRODUCTION").upper()
IS_TEST_MODE = (APP_MODE == "TEST")

# --- Database Configuration ---
DATABASE_NAME = "reviews_analysis_mongo" # Explicitly define the MongoDB database name

# --- Database Configuration ---
# Define a base name and append a suffix for test mode
_DATABASE_BASE_NAME = "reviews_analysis" # Base name for your MongoDB database

if IS_TEST_MODE:
    DATABASE_NAME = f"{_DATABASE_BASE_NAME}_test" # e.g., "reviews_analysis_test_mongo"
else:
    DATABASE_NAME = f"{_DATABASE_BASE_NAME}_mongo"  # e.g., "reviews_analysis_prod_mongo"
                                                      # Or just _mongo if you prefer the original name for prod

# --- YouTube Search Parameters ---
DEFAULT_MAX_VIDEO_RESULTS_PER_QUERY = 5 # For curated reviewer search
SAAS_INITIAL_SEARCH_MAX_RESULTS = 50 # For SaaS CRM search
SAAS_MAX_VIDEOS_TO_FULLY_ANALYZE = 7 # For each product

VIDEO_ORDER_PREFERENCE = 'relevance'

# --- Gemini Model Configuration ---
GEMINI_MODEL_NAME = "gemini-2.0-flash" # "gemini-1.5-flash-latest"

# --- Test Mode Specific Limits ---
# These are only used if IS_TEST_MODE is True (defined above)
TEST_MODE_CATEGORIES = ["smartphones", "saas_crm"]
TEST_MODE_PRODUCTS_LIMIT_PER_CATEGORY = 1
TEST_MODE_REVIEWERS_LIMIT_PER_PRODUCT = 1 # Applies to curated reviewer categories

# --- API Key Validation ---
# Moved here as it's a general setting check
if not YOUTUBE_API_KEY:
    print("CRITICAL WARNING: YOUTUBE_API_KEY is not set. YouTube functionality will fail.")
if not GEMINI_API_KEY:
    print("CRITICAL WARNING: GEMINI_API_KEY is not set. Gemini functionality will fail.")