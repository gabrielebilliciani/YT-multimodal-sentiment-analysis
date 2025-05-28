import time
import config # This will now have IS_TEST_MODE and test limits defined
from core import youtube_client, gemini_client, database_manager
import logging # Standard library
import sys
from utils import logging_config # Your custom module for centralized logging

# --- Centralized Logging Setup ---
# Call this ONCE at the start of your application
# Set the desired level, e.g., logging.INFO for production, logging.DEBUG for development/troubleshooting
LOGGING_LEVEL = logging.INFO if config.IS_TEST_MODE else logging.INFO # Example: DEBUG in test, INFO in prod
logging_config.setup_logging(level=LOGGING_LEVEL)

# Get a logger for this specific module (main.py)
logger = logging.getLogger(__name__) # This will use the name "main" if run directly, or "main_orchestrator" if you prefer

def process_consumer_product_with_curated_reviewers(product_config, reviewers_list_for_product):
    """Processes a consumer product using a predefined list of reviewers."""
    product_name_from_config = product_config['name']
    product_keywords = product_config.get('keywords_for_relevance', [product_name_from_config])

    logger.info(f"--- [CONSUMER] Processing Product Config: {product_name_from_config} ---")

    if not reviewers_list_for_product:
        logger.warning(f"[CONSUMER] No reviewers to process for product: {product_name_from_config}.")
        return

    for reviewer_info in reviewers_list_for_product:
        reviewer_name = reviewer_info['name']
        reviewer_channel_id = reviewer_info['id']
        logger.info(f"[CONSUMER] Searching videos from '{reviewer_name}' (ID: {reviewer_channel_id}) for product keywords '{product_keywords}'")

        # Use the renamed function for clarity
        videos_metadata = youtube_client.find_videos_by_channel(
            channel_id=reviewer_channel_id,
            query_string=product_name_from_config,
            max_results=config.DEFAULT_MAX_VIDEO_RESULTS_PER_QUERY
        )

        if not videos_metadata:
            logger.info(f"[CONSUMER] No initial videos found for '{product_name_from_config}' from '{reviewer_name}'.")
            continue

        relevant_videos_found_for_reviewer = 0
        for video_meta in videos_metadata:
            video_id = video_meta['video_id']
            video_title_yt = video_meta['title']
            video_url = video_meta['url']
            video_description_yt = video_meta['description']
            video_published_at = video_meta['published_at']

            if database_manager.is_video_analyzed(video_id, product_name_from_config):
                logger.info(f"[CONSUMER] Video '{video_title_yt}' (ID: {video_id}) for product config '{product_name_from_config}' already analyzed. Skipping.")
                continue

            logger.info(f"[CONSUMER] Checking relevance of video: '{video_title_yt}' for product '{product_name_from_config}'...")
            is_relevant = gemini_client.check_video_relevance( # This is your existing relevance check
                video_title=video_title_yt,
                video_description=video_description_yt,
                product_name_for_relevance=product_name_from_config,
                product_keywords=product_keywords
            )
            sys.stdout.flush()

            if not is_relevant:
                logger.info(f"[CONSUMER] Video '{video_title_yt}' deemed NOT RELEVANT for full analysis of '{product_name_from_config}'. Skipping.")
                continue

            logger.info(f"[CONSUMER] Video '{video_title_yt}' IS RELEVANT. Proceeding with full analysis for '{product_name_from_config}'.")
            relevant_videos_found_for_reviewer += 1

            analysis_json_str = gemini_client.analyze_video_content( # Your existing full analysis for consumer products
                video_url=video_url,
                product_name_context=product_name_from_config,
                video_title_from_yt=video_title_yt,
                channel_name_from_yt=video_meta.get('channel_title', reviewer_name)
            )
            sys.stdout.flush()

            if analysis_json_str:
                database_manager.save_video_analysis(
                    product_config=product_config,
                    video_id=video_id,
                    video_url=video_url,
                    video_title_from_yt=video_title_yt,
                    video_published_at_str=video_published_at,
                    reviewer_channel_id=reviewer_channel_id, # This is known for curated reviewers
                    reviewer_name=reviewer_name,             # This is known
                    analysis_json_str=analysis_json_str
                )
                logger.info(f"[CONSUMER] Successfully analyzed and saved: '{video_title_yt}' (ID: {video_id}) for '{product_name_from_config}'")
            else:
                logger.error(f"[CONSUMER] Failed to get Gemini full analysis for video: '{video_title_yt}' (ID: {video_id})")

            logger.info("Waiting for 5 seconds before next API call...")
            time.sleep(5)

        if relevant_videos_found_for_reviewer == 0:
            logger.info(f"[CONSUMER] No relevant videos found for '{product_name_from_config}' from '{reviewer_name}' after filtering.")

    logger.info(f"--- [CONSUMER] Finished processing for Product Config: {product_name_from_config} ---")


def process_saas_product_general_search(product_config):
    """Processes a SaaS product using general YouTube search and tiered filtering."""
    product_name_from_config = product_config['name']
    product_keywords = product_config.get('keywords_for_relevance', [product_name_from_config])
    # For SaaS, you might want more candidates for initial filtering
    saas_initial_search_max_results = product_config.get('initial_search_max_results', config.SAAS_INITIAL_SEARCH_MAX_RESULTS) 
    saas_max_videos_to_fully_analyze = product_config.get('max_full_analysis_videos', config.SAAS_MAX_VIDEOS_TO_FULLY_ANALYZE)


    logger.info(f"--- [SAAS] Processing Product Config: {product_name_from_config} ---")
    logger.info(f"[SAAS] Performing general YouTube search for keywords '{product_keywords}'")

    # 1. General YouTube Search
    # You can add region_code or relevance_language from product_config if needed
    general_search_query = " ".join(product_keywords) # Combine keywords for a search query
    candidate_videos_metadata = youtube_client.find_general_videos_by_query(
        query_string=general_search_query,
        max_results=saas_initial_search_max_results,
        order='relevance', # Or 'viewCount'
        relevance_language=product_config.get('search_language', 'en') # Default to English
    )

    if not candidate_videos_metadata:
        logger.info(f"[SAAS] No initial video candidates found for '{general_search_query}'.")
        return

    logger.info(f"[SAAS] Found {len(candidate_videos_metadata)} initial video candidates for '{product_name_from_config}'. Starting filtering...")
    
    suitable_videos_for_full_analysis = []
    for video_meta in candidate_videos_metadata:
        video_id = video_meta['video_id']
        video_title_yt = video_meta['title']
        video_description_yt = video_meta['description']

        # A. Check if already analyzed (important to avoid re-filtering and re-analyzing)
        if database_manager.is_video_analyzed(video_id, product_name_from_config):
            logger.info(f"[SAAS] Video '{video_title_yt}' (ID: {video_id}) for product '{product_name_from_config}' already analyzed. Skipping filtering.")
            continue

        # B. Tier 1 Relevance & Type Classification
        logger.debug(f"[SAAS] Tier 1 Relevance Check for '{video_title_yt}'...")
        tier1_result = gemini_client.check_saas_video_relevance_tier1(
            video_title=video_title_yt,
            video_description=video_description_yt,
            channel_title=video_meta.get('channel_title', 'Unknown Channel'),
            saas_product_name=product_name_from_config
        )
        sys.stdout.flush()

        if not tier1_result or not tier1_result.get("is_relevant_to_product"):
            logger.info(f"[SAAS] Tier 1: Video '{video_title_yt}' NOT relevant to product '{product_name_from_config}'. Skipping.")
            continue
        
        video_type_from_tier1 = tier1_result.get("video_type", "Other")
        logger.info(f"[SAAS] Tier 1: Video '{video_title_yt}' IS relevant. Type: '{video_type_from_tier1}'. Proceeding to Tier 2.")

        # C. Tier 2 Suitability for Detailed Analysis
        logger.debug(f"[SAAS] Tier 2 Suitability Check for '{video_title_yt}' (Type: {video_type_from_tier1})...")
        is_suitable_for_analysis = gemini_client.check_saas_video_relevance_tier2(
            video_title=video_title_yt,
            video_description=video_description_yt,
            channel_title=video_meta.get('channel_title', 'Unknown Channel'),
            saas_product_name=product_name_from_config,
            video_type_from_tier1=video_type_from_tier1
        )
        sys.stdout.flush()

        if not is_suitable_for_analysis:
            logger.info(f"[SAAS] Tier 2: Video '{video_title_yt}' (Type: {video_type_from_tier1}) NOT suitable for detailed analysis. Skipping.")
            continue
        
        logger.info(f"[SAAS] Tier 2: Video '{video_title_yt}' (Type: {video_type_from_tier1}) IS SUITABLE for detailed analysis.")
        suitable_videos_for_full_analysis.append(video_meta)

        if len(suitable_videos_for_full_analysis) >= saas_max_videos_to_fully_analyze:
            logger.info(f"[SAAS] Reached limit of {saas_max_videos_to_fully_analyze} suitable videos for '{product_name_from_config}'. Stopping filtering.")
            break
    
    logger.info(f"[SAAS] Found {len(suitable_videos_for_full_analysis)} suitable videos for '{product_name_from_config}' after tiered filtering.")

    # D. Full Analysis for selected suitable videos
    for video_meta_to_analyze in suitable_videos_for_full_analysis:
        video_id = video_meta_to_analyze['video_id']
        video_title_yt = video_meta_to_analyze['title']
        video_url = video_meta_to_analyze['url']
        video_published_at = video_meta_to_analyze['published_at']
        # For SaaS general search, reviewer info comes from the video metadata itself
        reviewer_channel_id_saas = video_meta_to_analyze['channel_id']
        reviewer_name_saas = video_meta_to_analyze['channel_title']

        # Redundant check, but good for safety, as filtering might take time
        if database_manager.is_video_analyzed(video_id, product_name_from_config):
            logger.info(f"[SAAS] Video '{video_title_yt}' (ID: {video_id}) re-checked and already analyzed. Skipping full analysis.")
            continue

        logger.info(f"[SAAS] Performing FULL analysis for: '{video_title_yt}' (URL: {video_url})")
        # Use the specific SaaS analysis function
        analysis_json_str = gemini_client.analyze_saas_video_content(
            video_url=video_url,
            saas_product_name_context=product_name_from_config,
            video_title_from_yt=video_title_yt,
            channel_name_from_yt=reviewer_name_saas # or video_meta_to_analyze.get('channel_title')
        )
        sys.stdout.flush()

        if analysis_json_str:
            database_manager.save_video_analysis(
                product_config=product_config, # Pass the original product_config
                video_id=video_id,
                video_url=video_url,
                video_title_from_yt=video_title_yt,
                video_published_at_str=video_published_at,
                reviewer_channel_id=reviewer_channel_id_saas,
                reviewer_name=reviewer_name_saas,
                analysis_json_str=analysis_json_str
            )
            logger.info(f"[SAAS] Successfully analyzed and saved: '{video_title_yt}' (ID: {video_id}) for '{product_name_from_config}'")
        else:
            logger.error(f"[SAAS] Failed to get Gemini full SaaS analysis for video: '{video_title_yt}' (ID: {video_id})")
        
        logger.info("Waiting for 5 seconds before next API call...")
        time.sleep(5)

    logger.info(f"--- [SAAS] Finished processing for Product Config: {product_name_from_config} ---")


def main():
    logger.info(f"Application starting in {config.APP_MODE} mode...")
    sys.stdout.flush()

    if config.IS_TEST_MODE:
        logger.info(
            f"--- TEST MODE ACTIVE: Categories={config.TEST_MODE_CATEGORIES}, "
            f"Products/Cat={config.TEST_MODE_PRODUCTS_LIMIT_PER_CATEGORY}, "
            f"Reviewers/Prod={config.TEST_MODE_REVIEWERS_LIMIT_PER_PRODUCT} ---"
        )
    else:
        logger.info("--- PRODUCTION MODE ACTIVE (processing all configured items) ---")

    if not config.YOUTUBE_API_KEY or not config.GEMINI_API_KEY:
        logger.critical("CRITICAL: API keys are not configured. Exiting.")
        return

    database_manager.initialize_db()
    if not youtube_client.get_youtube_service() or not gemini_client.get_gemini_model():
        logger.critical("Failed to initialize API services. Check keys/configs. Exiting.")
        return

    for category, all_product_configs_in_category in config.PRODUCTS_TO_ANALYZE.items():
        # Apply test mode category filtering
        if config.IS_TEST_MODE and category not in config.TEST_MODE_CATEGORIES:
            logger.debug(f"Test mode: Skipping category '{category}'.")
            continue

        logger.info(f"Processing category: {category}")

        # Determine if this category uses curated reviewers or general search
        has_curated_reviewers = category in config.REVIEWER_CHANNELS and config.REVIEWER_CHANNELS[category]

        products_to_process_in_category = all_product_configs_in_category
        if config.IS_TEST_MODE: # Apply product limit if in test mode
            products_to_process_in_category = all_product_configs_in_category[:config.TEST_MODE_PRODUCTS_LIMIT_PER_CATEGORY]
            logger.debug(f"Test mode: Limiting products in '{category}' to {len(products_to_process_in_category)}.")

        for product_conf in products_to_process_in_category:
            if has_curated_reviewers:
                all_reviewers_for_this_category = config.REVIEWER_CHANNELS[category]
                reviewers_for_this_product = all_reviewers_for_this_category
                if config.IS_TEST_MODE: # Apply reviewer limit if in test mode for curated path
                    reviewers_for_this_product = all_reviewers_for_this_category[:config.TEST_MODE_REVIEWERS_LIMIT_PER_PRODUCT]
                    logger.debug(f"Test mode: Limiting curated reviewers for '{product_conf['name']}' to {len(reviewers_for_this_product)}.")
                
                process_consumer_product_with_curated_reviewers(product_conf, reviewers_for_this_product)
            else:
                # This is a category for general search (e.g., SaaS)
                logger.info(f"Category '{category}' has no pre-defined reviewers. Initiating general search workflow for product '{product_conf['name']}'.")
                # Test mode limits for SaaS (number of videos to fully analyze) should be handled within process_saas_product_general_search
                # or configured per product in config.py if more granularity is needed for SaaS test mode.
                # For now, test mode for SaaS just means it runs for fewer products/categories based on the top-level test limits.
                process_saas_product_general_search(product_conf)
                
    logger.info("Application finished processing.")

if __name__ == "__main__":
    main()