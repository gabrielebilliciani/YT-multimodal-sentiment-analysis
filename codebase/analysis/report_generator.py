# analysis/report_generator.py
import logging
import json
import os
from datetime import datetime

# Relative imports for when this is run as part of the 'analysis' package
from . import analysis_prompts
from . import data_loader
# Absolute imports assuming 'codebase' is the root for these packages
from core import gemini_client
from core import database_manager # Make sure this is consistently used if get_mongo_db is called

# config will be imported in the __main__ block or if this module is imported elsewhere
# where config is already in the path or imported.

logger = logging.getLogger(__name__)

REPORTS_DIR = "reports"

def ensure_reports_dir(sub_dir_name=""):
    """Ensures the reports directory and a specific subdirectory exist."""
    base_path = os.path.join(REPORTS_DIR, sub_dir_name)
    os.makedirs(base_path, exist_ok=True)
    return base_path

def format_analyses_for_prompt(analyses_data):
    """
    Formats a list of analysis dicts into a string for the Gemini prompt.
    Each analysis dict should have 'source_product_config_name', 'source_video_title_yt', 
    'source_video_published_at', and 'analysis_content'.
    """
    formatted_strings = []
    for i, analysis_item in enumerate(analyses_data):
        header = f"--- Review Analysis {i+1} ---\n"
        header += f"Product Context: {analysis_item.get('source_product_config_name', 'N/A')}\n" # Renamed for clarity
        header += f"Video Title (from YouTube): {analysis_item.get('source_video_title_yt', 'N/A')}\n"
        header += f"Video Published (from YouTube): {analysis_item.get('source_video_published_at', 'N/A')}\n"
        content_json_str = json.dumps(analysis_item.get('analysis_content', {}), indent=2)
        formatted_strings.append(f"{header}Analysis Content:\n{content_json_str}\n") # Added "Analysis Content:"
    return "\n".join(formatted_strings)


def generate_longitudinal_brand_report(brand_name, product_line, product_configs_for_brand):
    """
    Generates a longitudinal brand evolution report.
    Args:
        brand_name (str): e.g., "Apple"
        product_line (str): e.g., "iPhone Flagships"
        product_configs_for_brand (list of dict): List of product_config dicts from config.py for this brand.
    """
    logger.info(f"Starting longitudinal brand report generation for: {brand_name} {product_line}")

    # analyses_data, product_details_prompt_list = data_loader.get_reviews_for_longitudinal_analysis(
    #     brand_name, product_configs_for_brand
    # )

    analyses_data, product_details_prompt_list, doc_counts_per_product = data_loader.get_reviews_for_longitudinal_analysis(
        brand_name, product_configs_for_brand
    )

    if not analyses_data:
        logger.warning(f"No data found for {brand_name} {product_line}. Report generation aborted.")
        return

    concatenated_analyses_str = format_analyses_for_prompt(analyses_data)
    
    # Prepare data to fill into the prompt template
    prompt_fill_data = {
        "brand_name": brand_name,
        "product_line": product_line,
        "product_list_details_with_years": "\n".join(product_details_prompt_list),
        "generation_entry_list_for_json": [pc['name'] + f" ({pc.get('year', 'N/A')})" for pc in product_configs_for_brand]
    }

    text_summary, structured_json_str = gemini_client.synthesize_analyses_with_gemini(
        prompt_template=analysis_prompts.LONGITUDINAL_BRAND_EVOLUTION_PROMPT_TEMPLATE,
        prompt_fill_data=prompt_fill_data,
        data_batch_for_prompt=concatenated_analyses_str
    )

    if text_summary or structured_json_str:
        logger.info(f"Successfully generated synthesis for {brand_name} {product_line}.")
        
        report_subdir = os.path.join("brand_evolution", brand_name.replace(" ", "_").replace("/", "_"))
        output_path = ensure_reports_dir(report_subdir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_product_line = product_line.replace(" ", "_").replace("/", "_")
        base_filename = f"{safe_product_line}_evolution_{timestamp}"

        if text_summary:
            with open(os.path.join(output_path, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(f"Longitudinal Analysis Report for: {brand_name} - {product_line}\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("Products Included:\n")
                f.write("\n".join(product_details_prompt_list) + "\n\n")
                f.write("--- Textual Summary from Gemini ---\n")
                f.write(text_summary)
            logger.info(f"Textual summary saved to {output_path}/{base_filename}.txt")

        if structured_json_str:
            try:
                parsed_json = json.loads(structured_json_str)
                with open(os.path.join(output_path, f"{base_filename}.json"), "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Structured JSON saved to {output_path}/{base_filename}.json")
            except json.JSONDecodeError as e:
                logger.error(f"Could not save structured JSON due to parsing error: {e}")
                with open(os.path.join(output_path, f"{base_filename}_raw_error.json"), "w", encoding="utf-8") as f:
                    f.write(structured_json_str)
                logger.warning(f"Raw (potentially problematic) JSON string saved to {output_path}/{base_filename}_raw_error.json")
        
        print(f"\n--- Generated Textual Summary ({brand_name} {product_line}) ---")
        if text_summary: print(text_summary)
        else: print("No textual summary was generated.")
        print("\n--- End of Summary ---")
    else:
        logger.error(f"Failed to generate synthesis for {brand_name} {product_line}.")


def generate_comparative_product_report(product_configs_to_compare, comparison_title, timeframe_segment):
    """
    Generates a comparative product analysis report.
    Args:
        product_configs_to_compare (list of dict): List of product_config dicts.
        comparison_title (str): Title for the comparison.
        timeframe_segment (str): e.g., "Flagships of Late 2023/Early 2024"
    """
    logger.info(f"Starting comparative report generation for: {comparison_title}")

    analyses_data, product_details_prompt_list, doc_counts_per_product = data_loader.get_reviews_for_comparative_analysis(
        product_configs_to_compare
    )

    if not analyses_data:
        logger.warning(f"No data found for products in '{comparison_title}'. Report generation aborted.")
        return

    concatenated_analyses_str = format_analyses_for_prompt(analyses_data)
    
    prompt_fill_data = {
        "product_list_details_with_brands_years": "\n".join(product_details_prompt_list),
        "product_entry_list_for_json": [pc['name'] for pc in product_configs_to_compare],
        "comparison_timeframe_or_segment": timeframe_segment # Added this to fill in the prompt
    }
    
    text_summary, structured_json_str = gemini_client.synthesize_analyses_with_gemini(
        prompt_template=analysis_prompts.COMPARATIVE_PRODUCT_ANALYSIS_PROMPT_TEMPLATE,
        prompt_fill_data=prompt_fill_data,
        data_batch_for_prompt=concatenated_analyses_str
    )

    if text_summary or structured_json_str:
        logger.info(f"Successfully generated synthesis for comparison: {comparison_title}.")

        report_subdir = "comparative_analysis"
        output_path = ensure_reports_dir(report_subdir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = comparison_title.replace(" ", "_").replace("/", "_").replace(":", "_")
        base_filename = f"{safe_title}_{timestamp}"

        if text_summary:
            with open(os.path.join(output_path, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(f"Comparative Analysis Report: {comparison_title}\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("Products Included:\n")
                f.write("\n".join(product_details_prompt_list) + "\n\n")
                f.write("--- Textual Summary from Gemini ---\n")
                f.write(text_summary)
            logger.info(f"Textual summary saved to {output_path}/{base_filename}.txt")

        if structured_json_str:
            try:
                parsed_json = json.loads(structured_json_str)
                with open(os.path.join(output_path, f"{base_filename}.json"), "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Structured JSON saved to {output_path}/{base_filename}.json")
            except json.JSONDecodeError as e:
                logger.error(f"Could not save structured JSON for comparison due to parsing error: {e}")
                with open(os.path.join(output_path, f"{base_filename}_raw_error.json"), "w", encoding="utf-8") as f:
                    f.write(structured_json_str)
                logger.warning(f"Raw (potentially problematic) JSON string saved to {output_path}/{base_filename}_raw_error.json")

        print(f"\n--- Generated Textual Summary ({comparison_title}) ---")
        if text_summary: print(text_summary)
        else: print("No textual summary was generated.")
        print("\n--- End of Summary ---")
    else:
        logger.error(f"Failed to generate synthesis for comparison: {comparison_title}.")

# --- 1. Generate Comparative SaaS Report ---
def generate_comparative_saas_report(saas_product_configs_to_compare, comparison_title, segment_description):
    """
    Generates a comparative SaaS product analysis report.
    """
    logger.info(f"Starting comparative SaaS report generation for: {comparison_title} ({segment_description})")

    # Use the existing comparative data loader, but ensure it includes counts in product_details_prompt_list
    analyses_data, product_details_prompt_list, doc_counts = data_loader.get_reviews_for_comparative_analysis(
        saas_product_configs_to_compare # Pass SaaS product configs here
    )

    if not analyses_data:
        logger.warning(f"No data found for SaaS products in '{comparison_title}'. Report generation aborted.")
        return

    concatenated_analyses_str = format_analyses_for_prompt(analyses_data)
    
    prompt_fill_data = {
        "product_list_details_with_brands_years": "\n".join(product_details_prompt_list), # Should now include counts from data_loader
        "product_entry_list_for_json": [pc['name'] for pc in saas_product_configs_to_compare],
        "comparison_segment_description": segment_description
    }
    
    text_summary, structured_json_str = gemini_client.synthesize_analyses_with_gemini(
        prompt_template=analysis_prompts.COMPARATIVE_SAAS_ANALYSIS_PROMPT_TEMPLATE, # Use new SaaS prompt
        prompt_fill_data=prompt_fill_data,
        data_batch_for_prompt=concatenated_analyses_str
    )

    if text_summary or structured_json_str:
        logger.info(f"Successfully generated SaaS comparison synthesis: {comparison_title}.")
        report_subdir = os.path.join("saas_analysis", "comparative") # New subdir
        output_path = ensure_reports_dir(report_subdir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = comparison_title.replace(" ", "_").replace("/", "_").replace(":", "_")
        base_filename = f"SaaS_Compare_{safe_title}_{timestamp}"

        if text_summary:
            with open(os.path.join(output_path, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(f"Comparative SaaS Analysis Report: {comparison_title}\n")
                f.write(f"Segment: {segment_description}\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("Products Included (with review counts):\n")
                f.write("\n".join(product_details_prompt_list) + "\n\n")
                f.write("--- Textual Summary from Gemini ---\n")
                f.write(text_summary)
            logger.info(f"Textual summary saved to {output_path}/{base_filename}.txt")

        if structured_json_str:
            try:
                parsed_json = json.loads(structured_json_str)
                with open(os.path.join(output_path, f"{base_filename}.json"), "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Structured JSON saved to {output_path}/{base_filename}.json")
            except json.JSONDecodeError as e:
                logger.error(f"Could not save structured JSON for SaaS comparison due to parsing error: {e}")
                # Save raw response for debugging
                with open(os.path.join(output_path, f"{base_filename}_raw_error.json"), "w", encoding="utf-8") as f:
                    f.write(structured_json_str)
                logger.warning(f"Raw (potentially problematic) JSON string saved to {output_path}/{base_filename}_raw_error.json")

        print(f"\n--- Generated Textual Summary (SaaS Compare: {comparison_title}) ---")
        if text_summary: print(text_summary)
        else: print("No textual summary was generated.")
        print("\n--- End of Summary ---")
    else:
        logger.error(f"Failed to generate SaaS comparison synthesis for: {comparison_title}.")


# --- 2. Generate Single SaaS Product Deep Dive Report ---
def generate_single_saas_deep_dive_report(saas_product_config, report_title_suffix="Deep Dive"):
    """
    Generates a deep-dive report for a single SaaS product.
    """
    product_name = saas_product_config['name']
    logger.info(f"Starting single SaaS product deep dive for: {product_name}")

    analyses_data, product_detail_prompt_list, doc_count_dict = data_loader.get_reviews_for_single_saas_product(
        saas_product_config
    )
    
    num_reviews = doc_count_dict.get(product_name, 0)

    if not analyses_data:
        logger.warning(f"No data found for SaaS product '{product_name}'. Report generation aborted.")
        return

    concatenated_analyses_str = format_analyses_for_prompt(analyses_data)
    
    prompt_fill_data = {
        "saas_product_name": product_name,
        "num_reviews_used": "\n".join(product_detail_prompt_list), # This will be like "- HubSpot (Year) - (X reviews)"
        "num_reviews_used_for_json": num_reviews
    }
    
    text_summary, structured_json_str = gemini_client.synthesize_analyses_with_gemini(
        prompt_template=analysis_prompts.SINGLE_SAAS_PRODUCT_DEEP_DIVE_PROMPT_TEMPLATE,
        prompt_fill_data=prompt_fill_data,
        data_batch_for_prompt=concatenated_analyses_str
    )

    if text_summary or structured_json_str:
        logger.info(f"Successfully generated SaaS deep dive for: {product_name}.")
        report_subdir = os.path.join("saas_analysis", "deep_dives") # New subdir
        output_path = ensure_reports_dir(report_subdir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_product_name = product_name.replace(" ", "_").replace("/", "_")
        base_filename = f"SaaS_DeepDive_{safe_product_name}_{report_title_suffix.replace(' ', '_')}_{timestamp}"

        if text_summary:
            with open(os.path.join(output_path, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(f"SaaS Product Deep Dive Report: {product_name}\n")
                f.write(f"Report Title Suffix: {report_title_suffix}\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("Based on data from:\n")
                f.write("\n".join(product_detail_prompt_list) + "\n\n")
                f.write("--- Textual Summary from Gemini ---\n")
                f.write(text_summary)
            logger.info(f"Textual summary saved to {output_path}/{base_filename}.txt")

        if structured_json_str:
            try:
                parsed_json = json.loads(structured_json_str)
                with open(os.path.join(output_path, f"{base_filename}.json"), "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Structured JSON saved to {output_path}/{base_filename}.json")
            except json.JSONDecodeError as e:
                logger.error(f"Could not save structured JSON for SaaS deep dive ({product_name}) due to parsing error: {e}")
                with open(os.path.join(output_path, f"{base_filename}_raw_error.json"), "w", encoding="utf-8") as f:
                    f.write(structured_json_str)
                logger.warning(f"Raw (potentially problematic) JSON string saved to {output_path}/{base_filename}_raw_error.json")
        
        print(f"\n--- Generated Textual Summary (SaaS Deep Dive: {product_name}) ---")
        if text_summary: print(text_summary)
        else: print("No textual summary was generated.")
        print("\n--- End of Summary ---")
    else:
        logger.error(f"Failed to generate SaaS deep dive synthesis for: {product_name}.")


# --- 4. Generate SaaS Category Key Buying Factors Report ---
def generate_saas_category_insights_report(saas_product_configs_for_category, category_name, example_product_list_str="Various Products"):
    """
    Generates a report on key buying factors for a SaaS category.
    """
    logger.info(f"Starting SaaS category insights report for: {category_name}")

    analyses_data, prompt_header_product_list, aggregate_doc_count_dict = data_loader.get_all_reviews_for_saas_category(
        saas_product_configs_for_category
    )
    
    total_reviews = aggregate_doc_count_dict.get("total_in_category", 0)

    if not analyses_data:
        logger.warning(f"No data found for SaaS category '{category_name}'. Report generation aborted.")
        return

    concatenated_analyses_str = format_analyses_for_prompt(analyses_data)
    
    prompt_fill_data = {
        "saas_category_name": category_name,
        "total_reviews_considered": "\n".join(prompt_header_product_list), # Will be like "Data includes reviews from products such as: X, Y, Z..."
        "example_product_list_for_context": example_product_list_str, # Can refine this
        "total_reviews_considered_for_json": total_reviews
    }
    
    text_summary, structured_json_str = gemini_client.synthesize_analyses_with_gemini(
        prompt_template=analysis_prompts.SAAS_CATEGORY_KEY_BUYING_FACTORS_PROMPT_TEMPLATE,
        prompt_fill_data=prompt_fill_data,
        data_batch_for_prompt=concatenated_analyses_str
    )

    if text_summary or structured_json_str:
        logger.info(f"Successfully generated SaaS category insights for: {category_name}.")
        report_subdir = os.path.join("saas_analysis", "category_insights") # New subdir
        output_path = ensure_reports_dir(report_subdir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_category_name = category_name.replace(" ", "_").replace("/", "_")
        base_filename = f"SaaS_Category_{safe_category_name}_{timestamp}"

        if text_summary:
            with open(os.path.join(output_path, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(f"SaaS Category Insights Report: {category_name}\n")
                f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("Based on data from products including:\n")
                f.write(example_product_list_str + "\n")
                f.write(f"(Total {total_reviews} individual review analyses considered from the category)\n\n")
                f.write("--- Textual Summary from Gemini ---\n")
                f.write(text_summary)
            logger.info(f"Textual summary saved to {output_path}/{base_filename}.txt")

        if structured_json_str:
            try:
                parsed_json = json.loads(structured_json_str)
                with open(os.path.join(output_path, f"{base_filename}.json"), "w", encoding="utf-8") as f:
                    json.dump(parsed_json, f, indent=2, ensure_ascii=False)
                logger.info(f"Structured JSON saved to {output_path}/{base_filename}.json")
            except json.JSONDecodeError as e:
                logger.error(f"Could not save structured JSON for SaaS category ({category_name}) due to parsing error: {e}")
                with open(os.path.join(output_path, f"{base_filename}_raw_error.json"), "w", encoding="utf-8") as f:
                    f.write(structured_json_str)
                logger.warning(f"Raw (potentially problematic) JSON string saved to {output_path}/{base_filename}_raw_error.json")

        print(f"\n--- Generated Textual Summary (SaaS Category: {category_name}) ---")
        if text_summary: print(text_summary)
        else: print("No textual summary was generated.")
        print("\n--- End of Summary ---")
    else:
        logger.error(f"Failed to generate SaaS category insights for: {category_name}.")


# Example of how to run these analyses (you might create a separate runner script or add CLI args)
if __name__ == '__main__':
    import sys # Already imported at the top if using Python 3
    
    import config 

    # Ensure logging is configured for standalone testing of this module
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s [%(levelname)-7s] [%(name)-25s] %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    # Make sure API clients are initialized if not already by an outer script
    # database_manager.get_mongo_db() is called by data_loader, which initializes connection
    if database_manager.get_mongo_db() is None: # Explicit check here too for clarity
        logger.critical("MongoDB connection failed. Aborting report generation test.")
        exit() # Use exit() for scripts, not sys.exit() unless specific need
    if gemini_client.get_gemini_model() is None:
        logger.critical("Gemini model initialization failed. Aborting report generation test.")
        exit()

    logger.info("--- Starting Phase 2 Analysis Report Generation (Test Run) ---")

    # # --- Test Longitudinal Analysis ---
    # apple_smartphone_configs = [
    #     p for p in config.PRODUCTS_TO_ANALYZE.get("smartphones", []) # Uses imported config
    #     if p.get("brand") == "Apple"
    # ]
    
    # if apple_smartphone_configs:
    #     generate_longitudinal_brand_report(
    #         brand_name="Apple",
    #         product_line="iPhone Flagships (Longitudinal Analysis)",
    #         product_configs_for_brand=apple_smartphone_configs
    #     )
    # else:
    #     logger.warning("No Apple smartphone configurations found for longitudinal test.")

    # # --- Test Comparative Analysis ---
    # products_for_comparison_configs = []
    # target_comparison_products = ["iPhone 14 Pro Max", "Samsung Galaxy S23 Ultra"] # Reduced for faster test
    
    # # Ensure config is accessible here
    # all_product_configs = config.PRODUCTS_TO_ANALYZE 

    # for cat_products in all_product_configs.values():
    #     for prod_conf in cat_products:
    #         if prod_conf["name"] in target_comparison_products:
    #             products_for_comparison_configs.append(prod_conf)
    
    # products_for_comparison_configs = products_for_comparison_configs[:2] # Limit to 2 for this test

    # if len(products_for_comparison_configs) >= 2:
    #     generate_comparative_product_report(
    #         product_configs_to_compare=products_for_comparison_configs,
    #         comparison_title="Recent Flagship Showdown (2 Phones Test)",
    #         timeframe_segment="Late 2023 / Early 2024 Models Test"
    #     )
    # else:
    #     logger.warning(f"Not enough products found for comparative test (need at least 2 from {target_comparison_products}).")

    # --- Test SaaS Category Insights ---
    # --- NEW: Test SaaS Analyses ---
    logger.info("\n--- Testing SaaS Analyses ---")
    all_saas_crm_configs = config.PRODUCTS_TO_ANALYZE.get("saas_crm", [])

    if not all_saas_crm_configs:
        logger.warning("No SaaS CRM products configured in product_catalog.py. Skipping SaaS tests.")
    else:
        # --- Test 1: Comparative SaaS Report ---
        # Select a few SaaS products for comparison (e.g., first 2 or 3)
        saas_for_comparison = all_saas_crm_configs[:3] # Take first 3 for this test
        if len(saas_for_comparison) >= 2:
            generate_comparative_saas_report(
                saas_product_configs_to_compare=saas_for_comparison,
                comparison_title="SMB CRM Shootout (Test)",
                segment_description="Popular CRM platforms for Small to Medium Businesses"
            )
        else:
            logger.warning(f"Not enough SaaS products ({len(saas_for_comparison)}) for comparative test. Need at least 2.")

        # --- Test 2: Single SaaS Product Deep Dive ---
        # Pick one SaaS product (e.g., the first one in your config)
        if all_saas_crm_configs:
            single_saas_config_to_test = all_saas_crm_configs[0]
            generate_single_saas_deep_dive_report(
                saas_product_config=single_saas_config_to_test,
                report_title_suffix="Full Review Synthesis"
            )
        
        # --- Test 4: SaaS Category Key Buying Factors ---
        # Use all configured SaaS CRM products for this
        if len(all_saas_crm_configs) > 0:
            # Construct an example product list string for the report header
            example_prods = [p['name'] for p in all_saas_crm_configs[:3]] # first 3
            example_list_str = ", ".join(example_prods)
            if len(all_saas_crm_configs) > 3:
                example_list_str += f", and {len(all_saas_crm_configs) - 3} more"
            
            generate_saas_category_insights_report(
                saas_product_configs_for_category=all_saas_crm_configs,
                category_name="General CRM Software", # Or be more specific like "SMB CRM"
                example_product_list_str=example_list_str
            )

    logger.info("--- Phase 2 Analysis Report Generation (Including SaaS) Complete ---")