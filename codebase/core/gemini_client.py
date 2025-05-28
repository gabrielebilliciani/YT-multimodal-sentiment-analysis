import google.generativeai as genai
import config
import json
import logging
import sys # For the __main__ block logging
import time # For time.sleep
import re   # For parsing retry_delay
import random # For jitter
from google.api_core.exceptions import ResourceExhausted # Specific exception for 429s

logger = logging.getLogger(__name__)
gemini_model = None

# --- Constants for Retry Logic ---
MAX_API_RETRIES = 3  # Max number of retries for 429 errors
DEFAULT_API_RETRY_SECONDS = 10 # Default base wait if API doesn't specify or parsing fails

def get_gemini_model():
    global gemini_model
    if gemini_model:
        return gemini_model

    if not config.GEMINI_API_KEY:
        logger.error("Gemini API Key is not configured.")
        return None
        
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(config.GEMINI_MODEL_NAME)
        logger.info(f"Gemini model '{config.GEMINI_MODEL_NAME}' initialized successfully.")
        return gemini_model
    except Exception as e:
        logger.error(f"An error occurred during Gemini model initialization: {e}")
        return None

def _gemini_api_call_with_retry(api_call_lambda, context_description="Gemini API Call"):
    """
    Wraps a Gemini API call with retry logic for 429 ResourceExhausted errors.
    `api_call_lambda` should be a function that takes no arguments and performs the API call, returning the response.
    `context_description` is used for logging.
    Returns the API response object on success, or raises the exception on final failure.
    """
    for attempt in range(MAX_API_RETRIES + 1):
        try:
            return api_call_lambda() # Execute the actual API call
        except ResourceExhausted as e: # Catch 429 errors specifically
            error_message = str(e)
            logger.warning(f"[{context_description}] Rate limit hit (429) (Attempt {attempt + 1}/{MAX_API_RETRIES + 1}): {error_message[:200]}...") # Log snippet
            
            if attempt >= MAX_API_RETRIES:
                logger.error(f"[{context_description}] Max retries ({MAX_API_RETRIES}) exceeded. Giving up.")
                raise # Re-raise the exception to be handled by the caller

            retry_seconds_from_api = None
            # Try to parse suggested delay from error message. Example: "retry_delay { seconds: 39 }"
            # The regex now looks for "retry_delay" followed by optional " { seconds: " or just "="
            match = re.search(r"retry_delay(?:=| {\s*seconds:)\s*(\d+)", error_message, re.IGNORECASE)
            if match:
                try:
                    retry_seconds_from_api = int(match.group(1))
                except ValueError:
                    logger.warning(f"[{context_description}] Could not parse retry_delay value '{match.group(1)}'.")

            if retry_seconds_from_api is not None:
                wait_time = retry_seconds_from_api
                logger.info(f"[{context_description}] API suggested retry delay: {wait_time}s.")
            else: # Fallback to exponential backoff
                wait_time = DEFAULT_API_RETRY_SECONDS * (2 ** attempt)
                logger.info(f"[{context_description}] No specific retry_delay found or parsed. Using exponential backoff: {wait_time}s.")
            
            jitter = random.uniform(0, 0.2 * wait_time) # Add up to 20% jitter
            actual_wait_time = wait_time + jitter
            
            logger.info(f"[{context_description}] Waiting for {actual_wait_time:.2f} seconds before retrying...")
            time.sleep(actual_wait_time)
            
        # Important: Let other exceptions propagate immediately
        # except Exception as e_other:
        #     logger.error(f"[{context_description}] A non-429 error occurred: {e_other}")
        #     raise # Re-raise immediately
    # This line should not be reached if the loop correctly re-raises or returns.
    # If it is, it implies an issue in the loop logic.
    # Raise an error to signify this unexpected state.
    raise RuntimeError(f"[{context_description}] Exited retry loop unexpectedly without success or re-raising an error.")

# --- Consumer Product Functions (Modified to use retry helper) ---
def check_video_relevance(video_title, video_description, product_name_for_relevance, product_keywords):
    model = get_gemini_model()
    if not model: return False

    prompt = config.CONSUMER_RELEVANCE_PROMPT.format(
        video_title=video_title,
        video_description=video_description[:250],
        product_name_for_relevance=product_name_for_relevance,
        product_keywords_for_relevance=str(product_keywords)
    )
    context_desc = f"Consumer Relevance: {video_title[:30]}"
    logger.debug(f"[CONSUMER] Sending relevance check to Gemini for title: '{video_title}'")
    
    try:
        api_lambda = lambda: model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1, max_output_tokens=10))
        response = _gemini_api_call_with_retry(api_lambda, context_description=context_desc)
        
        if response and response.text:
            decision = response.text.strip().upper()
            logger.info(f"[CONSUMER] Relevance check for '{video_title}': Gemini responded '{decision}'")
            return decision == "YES"
        else:
            logger.warning(f"[CONSUMER] Relevance check for '{video_title}': Gemini response was None or empty after retries.")
            if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                logger.warning(f"Prompt Feedback for consumer relevance check: {response.prompt_feedback}")
            return False
    except ResourceExhausted:
        logger.error(f"[{context_desc}] Failed after max retries due to 429 error.")
        return False
    except Exception as e:
        logger.error(f"[{context_desc}] An unexpected error occurred: {e}")
        return False

def analyze_video_content(video_url, product_name_context, video_title_from_yt, channel_name_from_yt):
    model = get_gemini_model()
    if not model: return None

    safe_video_title = video_title_from_yt.replace('"', '\\"') # Keep this logic
    safe_channel_name = channel_name_from_yt.replace('"', '\\"')
    safe_product_name = product_name_context.replace('"', '\\"')

    filled_json_structure = config.CONSUMER_JSON_REQUEST.replace(
        "{video_url_placeholder}", video_url
    ).replace(
        "{video_title_placeholder}", safe_video_title
    ).replace(
        "{channel_name_placeholder}", safe_channel_name
    ).replace(
        "{product_name_placeholder}", safe_product_name
    )
    prompt = config.CONSUMER_ANALYSIS_PROMPT.format(
        video_url=video_url,
        product_name=product_name_context,
        json_structure_request=filled_json_structure
    )
    video_file_part = {"file_data": {"mime_type": "video/mp4", "file_uri": video_url}}
    contents = [video_file_part, prompt]
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.25)
    
    context_desc = f"Consumer Full Analysis: {video_url}"
    logger.info(f"[CONSUMER] Sending full analysis request to Gemini for video: {video_url}, product: {product_name_context}")

    try:
        api_lambda = lambda: model.generate_content(contents=contents, generation_config=generation_config)
        response = _gemini_api_call_with_retry(api_lambda, context_description=context_desc)

        if response and response.text:
            logger.info(f"[CONSUMER] Gemini full analysis received for {video_url}.")
            if response.text.strip().startswith("{") and response.text.strip().endswith("}"):
                return response.text
            else:
                logger.warning(f"[CONSUMER] Gemini response for {video_url} not valid JSON.")
                logger.debug(f"[CONSUMER] Raw response: {response.text[:500]}...")
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
                return None
        else:
            logger.warning(f"[CONSUMER] Gemini response for {video_url} was None or empty after retries.")
            if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                 logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
            return None
    except ResourceExhausted:
        logger.error(f"[{context_desc}] Failed after max retries due to 429 error.")
        return None
    except Exception as e:
        logger.error(f"[{context_desc}] An unexpected error occurred: {e}")
        return None

# --- NEW SaaS Product Functions (Modified to use retry helper) ---
def check_saas_video_relevance_tier1(video_title, video_description, channel_title, saas_product_name):
    model = get_gemini_model()
    if not model: return None

    prompt = config.SAAS_TIER1_RELEVANCE_PROMPT.format(
        saas_product_name=saas_product_name,
        video_title=video_title,
        channel_title=channel_title,
        video_description_snippet=video_description[:500]
    )
    context_desc = f"SaaS T1: {video_title[:30]}"
    logger.debug(f"[SAAS Tier 1] Sending relevance check for '{video_title}' re: '{saas_product_name}'")
    
    try:
        tier1_generation_config = genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.1, max_output_tokens=100)
        api_lambda = lambda: model.generate_content(prompt, generation_config=tier1_generation_config)
        response = _gemini_api_call_with_retry(api_lambda, context_description=context_desc)

        if response and response.text:
            try:
                result_json = json.loads(response.text)
                if "is_relevant_to_product" in result_json and "video_type" in result_json:
                    logger.info(f"[SAAS Tier 1] Result for '{video_title}': Relevant={result_json['is_relevant_to_product']}, Type='{result_json['video_type']}'")
                    return result_json
                else:
                    logger.warning(f"[SAAS Tier 1] Unexpected JSON for '{video_title}': {response.text}")
                    return None
            except json.JSONDecodeError:
                logger.warning(f"[SAAS Tier 1] Invalid JSON for '{video_title}': {response.text}")
                return None
        else:
            logger.warning(f"[SAAS Tier 1] Response for '{video_title}' was None or empty after retries.")
            if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
            return None
    except ResourceExhausted:
        logger.error(f"[{context_desc}] Failed after max retries due to 429 error.")
        return None
    except Exception as e:
        logger.error(f"[{context_desc}] An unexpected error occurred: {e}")
        return None


def check_saas_video_relevance_tier2(video_title, video_description, channel_title, saas_product_name, video_type_from_tier1):
    model = get_gemini_model()
    if not model: return False

    prompt = config.SAAS_TIER2_SUITABILITY_PROMPT.format(
        saas_product_name=saas_product_name,
        video_title=video_title,
        channel_title=channel_title,
        video_description_snippet=video_description[:500],
        video_type_from_tier1=video_type_from_tier1
    )
    context_desc = f"SaaS T2: {video_title[:30]}"
    logger.debug(f"[SAAS Tier 2] Sending suitability check for '{video_title}' (Type: {video_type_from_tier1})")
    
    try:
        tier2_generation_config = genai.types.GenerationConfig(temperature=0.1, max_output_tokens=20)
        api_lambda = lambda: model.generate_content(prompt, generation_config=tier2_generation_config)
        response = _gemini_api_call_with_retry(api_lambda, context_description=context_desc)

        if response and response.text:
            decision = response.text.strip().upper()
            logger.info(f"[SAAS Tier 2] Suitability for '{video_title}': Gemini responded '{decision}'")
            return decision == "YES_SUITABLE"
        else:
            logger.warning(f"[SAAS Tier 2] Response for '{video_title}' was None or empty after retries.")
            if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
            return False
    except ResourceExhausted:
        logger.error(f"[{context_desc}] Failed after max retries due to 429 error.")
        return False
    except Exception as e:
        logger.error(f"[{context_desc}] An unexpected error occurred: {e}")
        return False


def analyze_saas_video_content(video_url, saas_product_name_context, video_title_from_yt, channel_name_from_yt):
    model = get_gemini_model()
    if not model: return None

    safe_video_title = video_title_from_yt.replace('"', '\\"')
    safe_channel_name = channel_name_from_yt.replace('"', '\\"')
    safe_saas_product_name = saas_product_name_context.replace('"', '\\"')

    filled_json_structure = config.SAAS_JSON_REQUEST.replace(
        "{video_url_placeholder}", video_url
    ).replace(
        "{video_title_placeholder}", safe_video_title
    ).replace(
        "{channel_name_placeholder}", safe_channel_name
    ).replace(
        "{saas_product_name_placeholder}", safe_saas_product_name
    )
    prompt = config.CONSUMER_ANALYSIS_PROMPT.format( # Re-using this template, ensure it's generic enough
        video_url=video_url,
        product_name=saas_product_name_context,
        json_structure_request=filled_json_structure
    )
    video_file_part = {"file_data": {"mime_type": "video/mp4", "file_uri": video_url}}
    contents = [video_file_part, prompt]
    generation_config = genai.types.GenerationConfig(response_mime_type="application/json", temperature=0.25)
    
    context_desc = f"SaaS Full Analysis: {video_url}"
    logger.info(f"[SAAS] Sending full analysis request to Gemini for video: {video_url}, product: {saas_product_name_context}")

    try:
        api_lambda = lambda: model.generate_content(contents=contents, generation_config=generation_config)
        response = _gemini_api_call_with_retry(api_lambda, context_description=context_desc)

        if response and response.text:
            logger.info(f"[SAAS] Gemini full analysis received for {video_url}.")
            if response.text.strip().startswith("{") and response.text.strip().endswith("}"):
                return response.text
            else:
                logger.warning(f"[SAAS] Gemini response for {video_url} not valid JSON.")
                logger.debug(f"[SAAS] Raw response: {response.text[:500]}...")
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                    logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
                return None
        else:
            logger.warning(f"[SAAS] Gemini response for {video_url} was None or empty after retries.")
            if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                 logger.warning(f"Prompt Feedback: {response.prompt_feedback}")
            return None
    except ResourceExhausted: # Catch if retries were exhausted and helper re-raised
        logger.error(f"[{context_desc}] Failed after max retries due to 429 error.")
        return None
    except Exception as e: # Catch other non-retryable errors re-raised by helper
        logger.error(f"[{context_desc}] An unexpected error occurred: {e}")
        return None

def synthesize_analyses_with_gemini(prompt_template, prompt_fill_data, data_batch_for_prompt):
    """
    Sends a batch of existing JSON analyses and a synthesis prompt to Gemini.
    Args:
        prompt_template (str): The template string for the synthesis prompt.
        prompt_fill_data (dict): Dictionary to format into the prompt_template.
        data_batch_for_prompt (str): A string representing the batch of JSON analyses
                                     (e.g., multiple JSON strings concatenated, or a JSON array string).
    Returns:
        tuple: (textual_summary_str, structured_json_output_str) or (None, None) on error.
    """
    model = get_gemini_model()
    if not model:
        logger.error("Cannot synthesize analyses: Gemini model not initialized.")
        return None, None

    # Add the batch of data to the prompt fill data
    prompt_fill_data["concatenated_json_analyses"] = data_batch_for_prompt
    
    full_prompt = prompt_template.format(**prompt_fill_data)

    # For logging context in the retry helper
    context_desc = f"Synthesis for: {prompt_fill_data.get('brand_name', prompt_fill_data.get('comparison_title', 'Unknown Synthesis'))[:50]}"
    logger.info(f"Sending synthesis request to Gemini. Prompt length (approx): {len(full_prompt)} chars. Context: {context_desc}")
    logger.debug(f"Synthesis prompt (first 500 chars): {full_prompt[:500]}...")
    
    response = None # Initialize response

    try:
        # For synthesis, the response is expected to be text, which we will then parse.
        # The prompt itself requests Gemini to structure Part 2 as JSON.
        synthesis_generation_config = genai.types.GenerationConfig(
            temperature=0.3, # Allow for some summarization and nuanced language
            # max_output_tokens can be quite large for these summaries, consider setting if needed
        )
        
        # Define the API call as a lambda for the retry helper
        api_lambda = lambda: model.generate_content(full_prompt, generation_config=synthesis_generation_config)
        
        # Call the API through the retry helper
        response = _gemini_api_call_with_retry(api_lambda, context_description=context_desc)

        if response and response.text: # Check if response exists and has text after potential retries
            logger.info(f"[{context_desc}] Gemini synthesis response received.")
            raw_response_text = response.text

            textual_summary = None
            json_output_str = None

            if "Part 1: Textual Summary" in raw_response_text and "Part 2: Structured JSON Output" in raw_response_text:
                try:
                    part1_marker = "Part 1: Textual Summary"
                    part2_marker = "Part 2: Structured JSON Output"
                    
                    text_start_index = raw_response_text.find(part1_marker) + len(part1_marker)
                    json_start_index = raw_response_text.find(part2_marker)
                    
                    textual_summary = raw_response_text[text_start_index:json_start_index].strip()
                    
                    # More robust JSON extraction: find first '{' after Part 2 marker and last '}'
                    json_block_start_search = raw_response_text.find('{', json_start_index + len(part2_marker))
                    if json_block_start_search != -1:
                        json_block_end_search = raw_response_text.rfind('}', json_block_start_search) + 1 # Search from start of block
                        if json_block_end_search > json_block_start_search:
                             json_output_str = raw_response_text[json_block_start_search:json_block_end_search].strip()
                             try:
                                 json.loads(json_output_str) # Try parsing to ensure it's valid
                                 logger.info(f"[{context_desc}] Successfully extracted textual summary and valid JSON output for synthesis.")
                             except json.JSONDecodeError as je:
                                 logger.error(f"[{context_desc}] Extracted JSON from Part 2 is invalid: {je}")
                                 logger.debug(f"[{context_desc}] Problematic JSON block: {json_output_str}")
                                 json_output_str = None # Invalidate if parsing fails
                                 # Append error message to textual_summary instead of replacing it entirely
                                 textual_summary = f"{textual_summary}\n\n[ERROR: Could not parse structured JSON from Gemini's Part 2 response. The AI's output for this part was malformed.]"
                        else:
                            logger.warning(f"[{context_desc}] Could not clearly delimit JSON block (end bracket '}}') in Part 2 of synthesis response.")
                            textual_summary = raw_response_text # Fallback: return everything as text
                    else:
                        logger.warning(f"[{context_desc}] Could not clearly delimit JSON block (start bracket '{{') in Part 2 of synthesis response.")
                        textual_summary = raw_response_text # Fallback
                except Exception as e_parse:
                    logger.error(f"[{context_desc}] Error parsing synthesised response into parts: {e_parse}")
                    textual_summary = raw_response_text # Fallback
            else:
                logger.warning(f"[{context_desc}] Synthesis response did not contain expected 'Part 1' and 'Part 2' markers. Treating entire response as textual summary.")
                textual_summary = raw_response_text
            
            return textual_summary, json_output_str
            
        else: # Handles case where response is None or response.text is empty after retries
            logger.warning(f"[{context_desc}] Gemini synthesis response was None or empty after retries.")
            if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                logger.warning(f"[{context_desc}] Prompt Feedback for synthesis: {response.prompt_feedback}")
            return None, None

    except ResourceExhausted: # This will be caught if _gemini_api_call_with_retry re-raises it after max retries
        logger.error(f"[{context_desc}] Synthesis failed after max retries due to 429 error.")
        return None, None
    except Exception as e: # Catches other exceptions from API call or retry logic
        logger.error(f"[{context_desc}] An unexpected error occurred during Gemini synthesis API call: {e}")
        # If response object exists and has feedback, log it even on other errors
        if response and hasattr(response, 'prompt_feedback') and response.prompt_feedback:
             logger.warning(f"[{context_desc}] Prompt Feedback (on error): {response.prompt_feedback}")
        return None, None


if __name__ == '__main__':
    # Ensure logging is configured for standalone testing of this module
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.DEBUG, # DEBUG for testing this module
            format='%(asctime)s [%(levelname)-7s] [%(name)-25s] %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    if config.GEMINI_API_KEY:
        logger.info("--- Testing Gemini Client Functions (Standalone) ---")
        
        # Test Consumer Product Relevance Check
        logger.info("\n--- Testing Consumer Product Relevance Check ---")
        test_title_consumer = "iPhone 16 Ultra Review - Mind BLOWN!"
        test_desc_consumer = "Full deep dive into Apple's new flagship, camera, battery, performance..."
        test_prod_name_consumer = "iPhone 16 Ultra"
        test_keywords_consumer = ["iPhone 16 Ultra", "review"]
        is_relevant_consumer = check_video_relevance(test_title_consumer, test_desc_consumer, test_prod_name_consumer, test_keywords_consumer)
        logger.info(f"Consumer Video Relevance: {is_relevant_consumer}")

        # --- Test SaaS Tier 1 Relevance Check ---
        logger.info("\n--- Testing SaaS Tier 1 Relevance Check ---")
        saas_test_title = "Salesforce Full Demo 2024 - Sales Cloud Deep Dive"
        saas_test_desc = "A complete walkthrough of Salesforce Sales Cloud features for sales teams..."
        saas_test_channel = "SaaS Demos Inc."
        saas_product_name_test = "Salesforce Sales Cloud"
        tier1_result = check_saas_video_relevance_tier1(saas_test_title, saas_test_desc, saas_test_channel, saas_product_name_test)
        if tier1_result:
            logger.info(f"SaaS Tier 1 Result: Relevant={tier1_result.get('is_relevant_to_product')}, Type='{tier1_result.get('video_type')}'")

            # --- Test SaaS Tier 2 Suitability Check (only if Tier 1 was relevant) ---
            if tier1_result.get("is_relevant_to_product"):
                logger.info("\n--- Testing SaaS Tier 2 Suitability Check ---")
                is_suitable_saas = check_saas_video_relevance_tier2(
                    saas_test_title, 
                    saas_test_desc, 
                    saas_test_channel, 
                    saas_product_name_test, 
                    tier1_result.get("video_type", "Other")
                )
                logger.info(f"SaaS Tier 2 Suitability: {is_suitable_saas}")

                # --- Test Full SaaS Analysis (only if Tier 2 was suitable) ---
                # if is_suitable_saas:
                #     logger.info("\n--- Testing Full SaaS Video Analysis (Example - Requires a real video URL) ---")
                #     # You'd need a real SaaS review video URL here for a proper test
                #     saas_video_url_test = "https://www.youtube.com/watch?v=EXAMPLE_SAAS_VIDEO_ID" 
                #     logger.warning(f"Full SaaS analysis test needs a real video URL. Using placeholder: {saas_video_url_test}")
                #     if "EXAMPLE_SAAS_VIDEO_ID" in saas_video_url_test: # Prevent actual call for placeholder
                #         logger.info("Skipping actual SaaS full analysis call due to placeholder URL.")
                #     else:
                #         saas_analysis_result = analyze_saas_video_content(
                #             saas_video_url_test, 
                #             saas_product_name_test, 
                #             saas_test_title, # Using test title as placeholder
                #             saas_test_channel  # Using test channel as placeholder
                #         )
                #         if saas_analysis_result:
                #             logger.info("\n--- SaaS Full Analysis Result (JSON String) ---")
                #             try:
                #                 parsed_saas = json.loads(saas_analysis_result)
                #                 print(json.dumps(parsed_saas, indent=2))
                #             except json.JSONDecodeError as je:
                #                 logger.error(f"Failed to parse SaaS JSON from Gemini: {je}\n{saas_analysis_result}")
                #         else:
                #             logger.error("SaaS full analysis failed or returned no result.")
    else:
        logger.warning("Skipping Gemini client test (Standalone): API key not set.")