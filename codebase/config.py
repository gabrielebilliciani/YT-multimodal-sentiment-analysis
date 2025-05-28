# config.py (Main configuration loader)

# Import all settings from configs.settings
from configs.settings import *

# Import specific dictionaries/constants from other config files
from configs.reviewer_lists import REVIEWER_CHANNELS
from configs.product_catalog import PRODUCTS_TO_ANALYZE

from configs.prompts_consumer import (
    GEMINI_RELEVANCE_CHECK_PROMPT_TEMPLATE as CONSUMER_RELEVANCE_PROMPT,
    GEMINI_ANALYSIS_PROMPT_TEMPLATE as CONSUMER_ANALYSIS_PROMPT,
    GEMINI_JSON_STRUCTURE_REQUEST as CONSUMER_JSON_REQUEST
)

from configs.prompts_saas import (
    GEMINI_SAAS_TYPE_RELEVANCE_PROMPT_TEMPLATE as SAAS_TIER1_RELEVANCE_PROMPT,
    GEMINI_SAAS_SUITABILITY_PROMPT_TEMPLATE as SAAS_TIER2_SUITABILITY_PROMPT,
    GEMINI_SAAS_JSON_STRUCTURE_REQUEST as SAAS_JSON_REQUEST
    # Note: We can reuse CONSUMER_ANALYSIS_PROMPT for SaaS, but pass it SAAS_JSON_REQUEST
)

# You might want to create a dictionary to easily access prompts based on category type
# This is optional but can make gemini_client.py cleaner
PROMPT_CONFIGS = {
    "consumer": { # Default or for categories like "smartphones"
        "relevance_check": CONSUMER_RELEVANCE_PROMPT,
        "analysis_prompt": CONSUMER_ANALYSIS_PROMPT,
        "json_structure": CONSUMER_JSON_REQUEST
    },
    "saas_crm": { # Specific for "saas_crm" category
        "tier1_relevance": SAAS_TIER1_RELEVANCE_PROMPT,
        "tier2_suitability": SAAS_TIER2_SUITABILITY_PROMPT,
        "analysis_prompt": CONSUMER_ANALYSIS_PROMPT, # Re-using the general analysis prompt shell
        "json_structure": SAAS_JSON_REQUEST        # But with the SaaS specific JSON structure
    }
    # Add more categories here if they need very different prompt sets
}

# For easier access in gemini_client.py, you could define helper functions here or pass PROMPT_CONFIGS
def get_prompt_config_for_category(category_name):
    """
    Returns the appropriate prompt configuration for a given category.
    Defaults to 'consumer' if the specific category is not found.
    """
    # Determine if the category implies SaaS or Consumer
    # This is a simple check; could be more sophisticated
    if "saas" in category_name.lower() or "crm" in category_name.lower(): # Simple heuristic
        category_type = "saas_crm" # Use the key defined in PROMPT_CONFIGS
    else:
        category_type = "consumer"
    
    return PROMPT_CONFIGS.get(category_type, PROMPT_CONFIGS["consumer"])


# The API Key validation from settings.py will run when settings.py is imported.
# No need to repeat it here.
print(f"Config loaded. APP_MODE: {APP_MODE}, IS_TEST_MODE: {IS_TEST_MODE}")