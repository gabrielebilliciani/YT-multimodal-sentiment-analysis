from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
import json
from datetime import datetime, timezone
import config
import logging
import sys # Required for the standalone test logging config

logger = logging.getLogger(__name__)

# Global variables for the client and db object
# These will be managed by get_mongo_db based on config.DATABASE_NAME
mongo_client_instance = None
current_db_object = None
last_used_db_name = None # To track if DATABASE_NAME has changed

def get_mongo_db():
    """
    Establishes and returns a MongoDB database object.
    Ensures connection is to the correct database based on config.DATABASE_NAME
    (which can change between test/prod mode).
    """
    global mongo_client_instance, current_db_object, last_used_db_name

    target_db_name = config.DATABASE_NAME # Get the current target DB name from config

    # If the target DB name has changed since last connection, or if not connected
    if current_db_object is None or last_used_db_name != target_db_name:
        logger.info(f"Target database is '{target_db_name}'. Current is '{last_used_db_name}'. Re-evaluating connection.")
        
        # Close existing client if it exists (to ensure fresh connection if DB name changed)
        if mongo_client_instance:
            try:
                mongo_client_instance.close()
                logger.info("Closed existing MongoDB client instance.")
            except Exception as e_close:
                logger.warning(f"Could not cleanly close existing MongoDB client: {e_close}")
        
        mongo_client_instance = None
        current_db_object = None

        MONGO_CONNECTION_URI = "mongodb://localhost:27017/" # Or from config if you make it configurable

        try:
            logger.info(f"Attempting to connect to MongoDB at: {MONGO_CONNECTION_URI} for database '{target_db_name}'")
            mongo_client_instance = MongoClient(MONGO_CONNECTION_URI, serverSelectionTimeoutMS=5000)
            mongo_client_instance.admin.command('ismaster') # Verify connection
            logger.info("MongoDB connection successful.")
            
            current_db_object = mongo_client_instance[target_db_name] # Select/create the target database
            last_used_db_name = target_db_name # Update the last used name
            logger.info(f"Using MongoDB database: '{current_db_object.name}'")
            
        except ConnectionFailure:
            logger.critical(f"Failed to connect to MongoDB at {MONGO_CONNECTION_URI}. Ensure MongoDB is running.")
            mongo_client_instance = None
            current_db_object = None
            last_used_db_name = None
            return None # Explicitly return None on failure
        except Exception as e:
            logger.error(f"An unexpected error occurred during MongoDB connection: {e}")
            mongo_client_instance = None
            current_db_object = None
            last_used_db_name = None
            return None # Explicitly return None on failure
            
    return current_db_object # Return the (potentially new or existing) db object

def initialize_db():
    """
    For MongoDB, initialization often means ensuring a connection can be made
    and perhaps creating indexes if needed. Collections are created on first insert.
    """
    # 'get_mongo_db()' will return the global 'db' object or None
    # No need to assign to a new local variable 'database_object' here,
    # we can directly use the global 'db' after calling get_mongo_db() to ensure it's populated.
    # However, it's cleaner to always get it and then check.
    current_db_instance = get_mongo_db() 
    
    if current_db_instance is not None: 
        logger.info(f"MongoDB ready. Database: '{current_db_instance.name}'.")
        try:
            current_db_instance.video_reviews.create_index(
                [("video_id", 1), ("product_config_name", 1)], 
                unique=True, 
                background=True
            )
            logger.info("Index on 'video_reviews' for (video_id, product_config_name) ensured.")
        except OperationFailure as e:
            logger.warning(f"Could not create index on video_reviews (it might already exist or other issue): {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during index creation: {e}")
    else:
        logger.error("MongoDB initialization failed: could not connect (get_mongo_db returned None).")


def save_video_analysis(product_config, 
                        video_id, video_url, video_title_from_yt, video_published_at_str,
                        reviewer_channel_id, reviewer_name, analysis_json_str):
    current_db_instance = get_mongo_db()
    if current_db_instance is None: 
        logger.error("Cannot save analysis: MongoDB not connected.")
        return None

    try:
        analysis_dict = json.loads(analysis_json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error: Invalid JSON string provided for analysis: {e}")
        logger.debug(f"Problematic JSON (first 200 chars): {analysis_json_str[:200]}")
        return None

    try:
        video_published_dt = datetime.fromisoformat(video_published_at_str.replace('Z', '+00:00'))
    except ValueError:
        logger.warning(f"Could not parse video_published_at: {video_published_at_str}. Storing as string.")
        video_published_dt = video_published_at_str

    document_to_insert = {
        "product_config_name": product_config['name'],
        "product_brand": product_config.get('brand'),
        "product_generation": product_config.get('generation'),
        "product_release_year": product_config.get('year'),
        "video_id": video_id,
        "video_url": video_url,
        "video_title_yt": video_title_from_yt,
        "video_published_at": video_published_dt,
        "reviewer_channel_id": reviewer_channel_id,
        "reviewer_name": reviewer_name,
        "analysis_timestamp": datetime.now(timezone.utc),
        "gemini_analysis": analysis_dict
    }

    try:
        result = current_db_instance.video_reviews.insert_one(document_to_insert)
        logger.info(f"Saved analysis for video_id: {video_id}, product_config: {product_config['name']}. Mongo ID: {result.inserted_id}")
        return result.inserted_id
    except OperationFailure as e:
        if "E11000 duplicate key error" in str(e):
             logger.warning(f"Analysis for video_id: {video_id}, product_config: {product_config['name']} likely already exists (duplicate key).")
        else:
            logger.error(f"MongoDB operation error saving for video_id {video_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving for video_id {video_id}: {e}")
        return None

def is_video_analyzed(video_id, product_config_name):
    current_db_instance = get_mongo_db()
    if current_db_instance is None: 
        logger.warning("Cannot check if video analyzed: MongoDB not connected. Assuming analyzed to prevent reprocessing.")
        return True 

    count = current_db_instance.video_reviews.count_documents({"video_id": video_id, "product_config_name": product_config_name})
    return count > 0

def get_all_reviews_for_product_config(product_config_name):
    current_db_instance = get_mongo_db()
    if current_db_instance is None: 
        logger.error("Cannot get reviews: MongoDB not connected.")
        return []

    reviews_cursor = current_db_instance.video_reviews.find(
        {"product_config_name": product_config_name},
        sort=[("video_published_at", -1)]
    )
    
    reviews = []
    for doc in reviews_cursor:
        doc["_id"] = str(doc["_id"]) 
        reviews.append(doc)
    return reviews

if __name__ == '__main__':
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO, # .DEBUG for more verbosity
            format='%(asctime)s [%(levelname)-7s] [%(name)-25s] %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )

    logger.info("Testing MongoDB database manager (standalone)...")
    initialize_db() 
    
    db_instance_test = get_mongo_db() 
    if db_instance_test is not None: 
        test_product_config = {"name": "Test Product X Mongo Standalone", "brand": "TestBrand", "generation": "X-SA", "year": 2024}
        test_json_data_str = json.dumps({
            "overall_assessment": {"overall_sentiment": "Standalone Test"},
            "product_reviewed": "Test Product X Mongo Standalone"
        })
        
        db_instance_test.video_reviews.delete_many({"video_id": "testmongo_sa_789", "product_config_name": test_product_config["name"]})
        logger.info(f"Cleaned up previous entries for {test_product_config['name']}")

        save_video_analysis(
            product_config=test_product_config,
            video_id="testmongo_sa_789",
            video_url="http://example.com/testmongo_sa_789",
            video_title_from_yt="Test MongoDB Standalone Video Title",
            video_published_at_str="2024-02-15T11:00:00Z",
            reviewer_channel_id="testmongochannel_sa_789",
            reviewer_name="Test Mongo Standalone Reviewer",
            analysis_json_str=test_json_data_str
        )

        if is_video_analyzed("testmongo_sa_789", test_product_config["name"]):
            logger.info(f"Video 'testmongo_sa_789' for '{test_product_config['name']}' has been analyzed.")
        else:
            logger.error(f"Video 'testmongo_sa_789' for '{test_product_config['name']}' has NOT been analyzed.")

        product_reviews = get_all_reviews_for_product_config(test_product_config["name"])
        if product_reviews:
            logger.info(f"\nFound {len(product_reviews)} reviews for '{test_product_config['name']}':")
            for review in product_reviews:
                logger.info(f"  Reviewer: {review['reviewer_name']}, Video YT Title: {review['video_title_yt']}")
                sentiment = review.get('gemini_analysis', {}).get('overall_assessment', {}).get('overall_sentiment', 'N/A')
                logger.info(f"    Sentiment (example): {sentiment}")
        else:
            logger.info(f"No reviews found for '{test_product_config['name']}'.")
    else:
        logger.error("Could not connect to MongoDB for standalone testing after initialize_db().")