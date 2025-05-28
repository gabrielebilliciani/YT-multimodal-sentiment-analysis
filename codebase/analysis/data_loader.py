# analysis/data_loader.py
import logging
from core.database_manager import get_mongo_db

logger = logging.getLogger(__name__)

def get_reviews_for_longitudinal_analysis(brand_name, product_configs_to_include):
    """
    Fetches 'gemini_analysis' data for a brand across product configurations.
    Returns:
        list: Contextual analyses [{source_..., analysis_content: ...}].
        list: Product details for prompt header.
        dict: Counts of documents per product_config_name {product_name: count}.
    """
    db = get_mongo_db()
    if db is None:
        logger.error("MongoDB not connected. Cannot load data for longitudinal analysis.")
        return [], [], {}

    all_contextual_analyses = []
    product_details_for_prompt = []
    doc_counts_per_product = {} # To store counts

    product_config_names_for_query = [pc['name'] for pc in product_configs_to_include]
    logger.info(f"Loading data for longitudinal analysis of brand '{brand_name}', specifically for products: {product_config_names_for_query}")

    for pc in product_configs_to_include:
        product_config_name = pc['name']
        product_year = pc.get('year', 'N/A')
        product_details_for_prompt.append(f"- {product_config_name} ({product_year})")
        
        reviews_cursor = db.video_reviews.find(
            {"product_config_name": product_config_name, "product_brand": brand_name},
            sort=[("video_published_at", 1)] 
        )
        
        product_specific_analyses_count = 0
        for doc in reviews_cursor: 
            if "gemini_analysis" in doc and isinstance(doc["gemini_analysis"], dict):
                all_contextual_analyses.append({
                    "source_product_config_name": product_config_name,
                    "source_video_title_yt": doc.get("video_title_yt"),
                    "source_video_published_at": str(doc.get("video_published_at")),
                    "analysis_content": doc["gemini_analysis"]
                })
                product_specific_analyses_count +=1
            else:
                logger.warning(f"Skipping document for {product_config_name} (ID: {str(doc.get('_id'))}) due to missing or malformed 'gemini_analysis'.")
        
        doc_counts_per_product[product_config_name] = product_specific_analyses_count # Store count
        logger.info(f"Found {product_specific_analyses_count} analyses for product: {product_config_name}")
    
    logger.info(f"Collected {len(all_contextual_analyses)} total individual review analyses for brand '{brand_name}' across the specified products.")
    return all_contextual_analyses, product_details_for_prompt, doc_counts_per_product

def get_reviews_for_comparative_analysis(product_configs_to_compare):
    """
    Fetches 'gemini_analysis' data for a list of specific products.
    Returns:
        list: Contextual analyses.
        list: Product details for prompt header.
        dict: Counts of documents per product_config_name.
    """
    db = get_mongo_db()
    if db is None:
        logger.error("MongoDB not connected. Cannot load data for comparative analysis.")
        return [], [], {}

    all_contextual_analyses = []
    product_details_for_prompt = []
    doc_counts_per_product = {} # To store counts

    product_config_names_for_query = [pc['name'] for pc in product_configs_to_compare]
    logger.info(f"Loading data for comparative analysis of products: {product_config_names_for_query}")

    for pc in product_configs_to_compare:
        product_config_name = pc['name']
        product_brand = pc.get('brand', 'N/A')
        product_year = pc.get('year', 'N/A')
        product_details_for_prompt.append(f"- {product_brand} {product_config_name} ({product_year})")

        reviews_cursor = db.video_reviews.find(
            {"product_config_name": product_config_name},
            sort=[("video_published_at", 1)]
        )
        product_specific_analyses_count = 0
        for doc in reviews_cursor:
            if "gemini_analysis" in doc and isinstance(doc["gemini_analysis"], dict):
                all_contextual_analyses.append({
                    "source_product_config_name": product_config_name,
                    "source_video_title_yt": doc.get("video_title_yt"),
                    "source_video_published_at": str(doc.get("video_published_at")),
                    "analysis_content": doc["gemini_analysis"]
                })
                product_specific_analyses_count +=1
            else:
                logger.warning(f"Skipping document for {product_config_name} (ID: {str(doc.get('_id'))}) due to missing or malformed 'gemini_analysis'.")
        
        doc_counts_per_product[product_config_name] = product_specific_analyses_count # Store count
        logger.info(f"Found {product_specific_analyses_count} analyses for product: {product_config_name}")

    logger.info(f"Collected {len(all_contextual_analyses)} total individual review analyses for comparison.")
    return all_contextual_analyses, product_details_for_prompt, doc_counts_per_product

def get_reviews_for_single_saas_product(product_config):
    """
    Fetches 'gemini_analysis' data for a single SaaS product.
    Returns:
        list: Contextual analyses for the product.
        list: Product detail string for prompt header.
        dict: Count of documents for the product {product_name: count}.
    """
    db = get_mongo_db()
    if db is None:
        logger.error("MongoDB not connected. Cannot load data for single SaaS product analysis.")
        return [], [], {}

    product_analyses = []
    product_config_name = product_config['name']
    product_brand = product_config.get('brand', 'N/A')
    product_year = product_config.get('year', 'N/A') # Less relevant for SaaS but keep for consistency
    
    logger.info(f"Loading data for single SaaS product deep dive: {product_config_name}")

    reviews_cursor = db.video_reviews.find(
        {"product_config_name": product_config_name},
        sort=[("video_published_at", 1)]
    )
    
    product_specific_analyses_count = 0
    for doc in reviews_cursor:
        if "gemini_analysis" in doc and isinstance(doc["gemini_analysis"], dict):
            product_analyses.append({
                "source_product_config_name": product_config_name, # Technically redundant here but good for format_analyses_for_prompt
                "source_video_title_yt": doc.get("video_title_yt"),
                "source_video_published_at": str(doc.get("video_published_at")),
                "analysis_content": doc["gemini_analysis"]
            })
            product_specific_analyses_count += 1
        else:
            logger.warning(f"Skipping document for {product_config_name} (ID: {str(doc.get('_id'))}) - missing/malformed 'gemini_analysis'.")
            
    doc_count_for_product = {product_config_name: product_specific_analyses_count}
    # For single product, the "details list" is just one item. Include count here.
    product_detail_for_prompt = [f"- {product_brand} {product_config_name} ({product_year}) - ({product_specific_analyses_count} reviews)"]
    
    logger.info(f"Collected {product_specific_analyses_count} analyses for product: {product_config_name}")
    return product_analyses, product_detail_for_prompt, doc_count_for_product


def get_all_reviews_for_saas_category(saas_product_configs_in_category):
    """
    Fetches all 'gemini_analysis' data for a list of SaaS products belonging to a category.
    Returns:
        list: All contextual analyses from all products in the category.
        list: A summary list of products included for the prompt header.
        dict: Aggregate count of all documents considered { "total_in_category": count }.
    """
    db = get_mongo_db()
    if db is None:
        logger.error("MongoDB not connected. Cannot load data for SaaS category analysis.")
        return [], [], {}

    all_category_analyses = []
    product_names_in_category_for_prompt = []
    total_docs_in_category = 0
    
    product_config_names_for_query = [pc['name'] for pc in saas_product_configs_in_category]
    logger.info(f"Loading all data for SaaS category analysis, products: {product_config_names_for_query}")

    for pc in saas_product_configs_in_category:
        product_config_name = pc['name']
        product_brand = pc.get('brand', 'N/A')
        # Add product to list for prompt context
        product_names_in_category_for_prompt.append(f"{product_brand} {product_config_name}")

        reviews_cursor = db.video_reviews.find(
            {"product_config_name": product_config_name},
            # sort=[("video_published_at", 1)] # Sort might be less critical here, but can keep
        )
        
        product_specific_analyses_count_for_log = 0
        for doc in reviews_cursor:
            if "gemini_analysis" in doc and isinstance(doc["gemini_analysis"], dict):
                all_category_analyses.append({
                    "source_product_config_name": product_config_name, # Good to keep for context even in aggregated prompt
                    "source_video_title_yt": doc.get("video_title_yt"),
                    "source_video_published_at": str(doc.get("video_published_at")),
                    "analysis_content": doc["gemini_analysis"]
                })
                total_docs_in_category += 1
                product_specific_analyses_count_for_log += 1
            else:
                logger.warning(f"Skipping document for {product_config_name} (ID: {str(doc.get('_id'))}) for category analysis - missing/malformed 'gemini_analysis'.")
        logger.debug(f"Added {product_specific_analyses_count_for_log} analyses from {product_config_name} to category pool.")

    # Create a summary list of products for the prompt header
    # Could be a simple comma-separated string or a few examples if too long
    if len(product_names_in_category_for_prompt) > 5:
        example_products_str = ", ".join(product_names_in_category_for_prompt[:3]) + f", and {len(product_names_in_category_for_prompt)-3} more."
    else:
        example_products_str = ", ".join(product_names_in_category_for_prompt)
    
    prompt_header_product_list = [f"Data includes reviews from products such as: {example_products_str}"]
    
    aggregate_doc_count = {"total_in_category": total_docs_in_category}
    logger.info(f"Collected {total_docs_in_category} total individual review analyses for the SaaS category.")
    return all_category_analyses, prompt_header_product_list, aggregate_doc_count