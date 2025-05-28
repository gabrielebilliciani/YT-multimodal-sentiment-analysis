import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config # To access YOUTUBE_API_KEY and other configs
import logging # Import logging

logger = logging.getLogger(__name__) # Use module-level logger

youtube_service = None

def get_youtube_service():
    """Initializes and returns the YouTube API service object."""
    global youtube_service
    if youtube_service:
        return youtube_service
    
    if not config.YOUTUBE_API_KEY:
        logger.error("YouTube API Key is not configured.") # Use logger
        return None
        
    try:
        youtube_service = build('youtube', 'v3', developerKey=config.YOUTUBE_API_KEY, cache_discovery=False) # Added cache_discovery=False
        logger.info("YouTube API service initialized successfully.") # Use logger
        return youtube_service
    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        logger.error(f"An HTTP error {e.resp.status} occurred during YouTube service initialization:") # Use logger
        logger.error(json.dumps(error_details, indent=2)) # Use logger
        return None
    except Exception as e:
        logger.error(f"An error occurred during YouTube service initialization: {e}") # Use logger
        return None

def find_videos_by_channel(channel_id, query_string, max_results=config.DEFAULT_MAX_VIDEO_RESULTS_PER_QUERY, order=config.VIDEO_ORDER_PREFERENCE):
    """
    Finds videos for a specific channel ID and a search query.
    (Renamed from find_videos for clarity)
    """
    youtube = get_youtube_service()
    if not youtube:
        logger.warning("YouTube service not available for find_videos_by_channel.") # Use logger
        return [] 

    videos_found = []
    try:
        search_params = {
            'part': 'snippet',
            'channelId': channel_id,
            'q': query_string,
            'maxResults': max_results,
            'order': order,
            'type': 'video'
        }
        logger.info(f"Searching YouTube (Channel Specific): channel='{channel_id}', query='{query_string}', max_results={max_results}, order='{order}'") # Use logger
        search_response = youtube.search().list(**search_params).execute()

        for item in search_response.get('items', []):
            if item.get('id', {}).get('kind') == 'youtube#video':
                video_id = item['id']['videoId']
                video_info = {
                    'title': item['snippet']['title'],
                    'video_id': video_id,
                    'published_at': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'channel_id': item['snippet']['channelId'], # Store channelId
                    'channel_title': item['snippet']['channelTitle']
                }
                videos_found.append(video_info)
        
        logger.info(f"Found {len(videos_found)} video(s) for query '{query_string}' in channel {channel_id}.") # Use logger
        return videos_found

    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        logger.error(f"An HTTP error {e.resp.status} occurred while searching YouTube (Channel Specific):") # Use logger
        logger.error(json.dumps(error_details, indent=2)) # Use logger
        if e.resp.status == 403:
            reason = error_details.get('error',{}).get('errors',[{}])[0].get('reason')
            if reason == 'quotaExceeded':
                logger.critical("CRITICAL: YouTube API daily quota exceeded.") # Use logger
            elif reason == 'forbidden' or reason == 'developerKeyInvalid':
                logger.critical("CRITICAL: YouTube API Key invalid or access denied.") # Use logger
        return []
    except Exception as e:
        logger.error(f"A generic error occurred while searching YouTube (Channel Specific): {e}") # Use logger
        return []

# --- NEW FUNCTION TO ADD ---
def find_general_videos_by_query(query_string, max_results=config.DEFAULT_MAX_VIDEO_RESULTS_PER_QUERY, order=config.VIDEO_ORDER_PREFERENCE, region_code=None, relevance_language=None):
    """
    Performs a general YouTube search for videos based on a query string, not tied to a specific channel.
    Args:
        query_string (str): The search query.
        max_results (int): Maximum number of results to return.
        order (str): Order of results ('date', 'relevance', 'rating', 'title', 'viewCount').
        region_code (str, optional): An ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "IT").
                                     This biases search results towards content relevant to that region.
        relevance_language (str, optional): An ISO 639-1 two-letter language code (e.g., "en", "it", "de").
                                           This biases search results towards content in that language.
    Returns:
        list: A list of video_info dictionaries, or an empty list on error.
    """
    youtube = get_youtube_service()
    if not youtube:
        logger.warning("YouTube service not available for find_general_videos_by_query.") # Use logger
        return []

    videos_found = []
    try:
        search_params = {
            'part': 'snippet',
            'q': query_string,
            'maxResults': max_results,
            'order': order,
            'type': 'video' # Ensure we only get videos
        }
        # Add optional parameters if provided
        if region_code:
            search_params['regionCode'] = region_code
        if relevance_language:
            search_params['relevanceLanguage'] = relevance_language

        logger.info(f"Searching YouTube (General): query='{query_string}', max_results={max_results}, order='{order}', region='{region_code}', lang='{relevance_language}'") # Use logger
        search_response = youtube.search().list(**search_params).execute()

        for item in search_response.get('items', []):
            if item.get('id', {}).get('kind') == 'youtube#video':
                video_id = item['id']['videoId']
                video_info = {
                    'title': item['snippet']['title'],
                    'video_id': video_id,
                    'published_at': item['snippet']['publishedAt'],
                    'description': item['snippet']['description'],
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'channel_id': item['snippet']['channelId'], # Important to capture the channel
                    'channel_title': item['snippet']['channelTitle']
                }
                videos_found.append(video_info)
        
        logger.info(f"Found {len(videos_found)} video(s) for general query '{query_string}'.") # Use logger
        return videos_found

    except HttpError as e:
        error_details = json.loads(e.content.decode('utf-8'))
        logger.error(f"An HTTP error {e.resp.status} occurred while performing general YouTube search:") # Use logger
        logger.error(json.dumps(error_details, indent=2)) # Use logger
        if e.resp.status == 403: # Identical error handling as the other function
            reason = error_details.get('error',{}).get('errors',[{}])[0].get('reason')
            if reason == 'quotaExceeded':
                logger.critical("CRITICAL: YouTube API daily quota exceeded.")
            elif reason == 'forbidden' or reason == 'developerKeyInvalid':
                logger.critical("CRITICAL: YouTube API Key invalid or access denied.")
        return []
    except Exception as e:
        logger.error(f"A generic error occurred while performing general YouTube search: {e}") # Use logger
        return []
# --- END OF NEW FUNCTION ---

if __name__ == '__main__':
    # Ensure logging is configured for standalone testing
    import sys
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)-7s] [%(name)-25s] %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    if config.YOUTUBE_API_KEY:
        logger.info("--- Testing Channel Specific Search ---")
        mkbhd_id = "UCBJycsmduvYEL83R_U4JriQ"
        test_videos_channel = find_videos_by_channel(mkbhd_id, "Pixel 8 review", max_results=2) # Use renamed function
        if test_videos_channel:
            for video in test_videos_channel:
                logger.info(f"  Channel Video Title: {video['title']}, URL: {video['url']}")
        else:
            logger.info("No channel-specific videos found or error occurred.")

        logger.info("\n--- Testing General Video Search ---")
        # Test general search for a SaaS product
        saas_query = "Salesforce Sales Cloud review"
        # For SaaS, you might want to search with a language bias if relevant
        # e.g., relevance_language="en" or region_code="US"
        test_videos_general = find_general_videos_by_query(saas_query, max_results=3, order='relevance', relevance_language="en")
        if test_videos_general:
            for video in test_videos_general:
                logger.info(f"  General Video Title: {video['title']}, Channel: {video['channel_title']}, URL: {video['url']}")
        else:
            logger.info(f"No general videos found for query '{saas_query}' or error occurred.")
    else:
        logger.warning("Skipping YouTube client test: API key not set.")