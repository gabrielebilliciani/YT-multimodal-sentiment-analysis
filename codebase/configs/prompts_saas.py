# configs/prompts_saas.py

# --- Gemini SaaS Product Tier 1 Relevance & Type Classification Prompt ---
GEMINI_SAAS_TYPE_RELEVANCE_PROMPT_TEMPLATE = """
Product of Interest: "{saas_product_name}"
Video Title: "{video_title}"
Channel Title: "{channel_title}"
Video Description (snippet): "{video_description_snippet}"

Based on the information above, please perform two tasks:
1.  Is this video PRIMARILY about the "{saas_product_name}"? (Respond YES or NO)
2.  If YES to point 1, what is the MOST LIKELY primary type of this video? Choose ONE from the following categories:
    - "In-depth Review/Critique"
    - "Feature Showcase/Demo"
    - "User Experience/Testimonial"
    - "Comparison"
    - "Tutorial/How-To"
    - "News/Announcement"
    - "Marketing/Advertisement"
    - "Webinar/Presentation"
    - "Other"
    - "Not Applicable"

Respond ONLY with a JSON object with two keys: "is_relevant_to_product" (boolean) and "video_type" (string from the list above).
Ensure the "video_type" string exactly matches one of the provided categories.
Example: {{"is_relevant_to_product": true, "video_type": "In-depth Review/Critique"}}
"""

# --- Gemini SaaS Product Tier 2 Suitability Prompt ---
GEMINI_SAAS_SUITABILITY_PROMPT_TEMPLATE = """
Product of Interest: "{saas_product_name}"
Video Title: "{video_title}"
Channel Title: "{channel_title}"
Video Description (snippet): "{video_description_snippet}"
Previously Identified Video Type: "{video_type_from_tier1}"

Considering this video is about "{saas_product_name}" and is of type "{video_type_from_tier1}", assess its suitability for a detailed sentiment and feature analysis.
The goal is to understand opinions on features, ease of use, pricing, support, pros, cons, and overall user experience.

We are looking for videos that offer substantive evaluative commentary or opinion.
- "In-depth Review/Critique", "User Experience/Testimonial", and "Comparison" videos are highly suitable.
- "Feature Showcase/Demo" and "Webinar/Presentation" are suitable if they go beyond pure feature listing and include evaluative context, user benefits, or address pain points.
- "Tutorial/How-To" videos are suitable ONLY if they embed significant evaluative commentary or opinions on the software's aspects, not just instructional steps.
- "Marketing/Advertisement" and "News/Announcement" are generally UNSUITABLE unless they contain substantial, verifiable user testimonials or detailed competitive differentiators that reflect user sentiment.

Is this video LIKELY to contain enough substantive evaluative commentary or opinion to be useful for a detailed SaaS analysis?
Respond with ONLY "YES_SUITABLE" or "NO_UNSUITABLE".
"""

# --- Gemini SaaS Product Full Analysis JSON Structure Request ---
# The main analysis prompt (GEMINI_ANALYSIS_PROMPT_TEMPLATE from prompts_consumer.py) can be reused,
# but it will be formatted with THIS specific JSON structure request for SaaS.
# Ensure all textual output within the JSON is requested in ENGLISH
GEMINI_SAAS_JSON_STRUCTURE_REQUEST = """
{{
    "video_metadata": {{
        "video_url": "{video_url_placeholder}",
        "video_title": "{video_title_placeholder}",
        "channel_name": "{channel_name_placeholder}",
        "video_type_assessment_by_ai": "ENUM('Independent Review', 'Vendor Demo', 'User Testimonial', 'Consultant Analysis', 'Comparison', 'Tutorial with Opinions', 'Other')",
        "product_analyzed": "{saas_product_name_placeholder}"
    }},
    "overall_assessment": {{
        "overall_sentiment": "ENUM('Very Positive', 'Positive', 'Neutral', 'Mixed', 'Negative', 'Very Negative')",
        "executive_summary": "STRING (2-4 sentence summary of the video's main conclusions about the SaaS product, IN ENGLISH)",
        "target_business_profile": {{
            "size": ["ENUM('Solopreneur', 'Small Business (1-50 employees)', 'Medium Business (51-500 employees)', 'Large Enterprise (500+ employees)', 'Not Specified')"],
            "industries": ["STRING (e.g., 'Retail', 'Tech Startups', 'Healthcare', 'Not Specified', IN ENGLISH)"],
            "specific_use_cases_highlighted": ["STRING (e.g., 'Lead Management for Sales Teams', 'Content Marketing Automation', IN ENGLISH)"]
        }},
        "key_strengths_highlighted": ["STRING (Overall positive aspects, IN ENGLISH)"],
        "key_weaknesses_highlighted": ["STRING (Overall negative aspects, IN ENGLISH)"]
    }},
    "feature_module_analysis": [
        {{
            "feature_or_module_name": "STRING (e.g., 'Contact Management', 'Email Marketing Automation', 'Reporting Dashboard', 'Workflow Builder', 'Mobile App', IN ENGLISH)",
            "sentiment": "ENUM('Very Positive', 'Positive', 'Neutral', 'Mixed', 'Negative', 'Very Negative', 'Not Mentioned')",
            "functionality_description_summary": "STRING (Brief summary of what this feature does as explained/shown, IN ENGLISH)",
            "ease_of_use_comments": "STRING (Specific comments on usability of this feature, IN ENGLISH)",
            "integration_comments": "STRING (If applicable, comments on how this feature integrates with others, IN ENGLISH)",
            "key_quote_feature": "STRING (Significant quote about this feature, IN ENGLISH)"
        }}
    ],
    "usability_and_ux": {{
        "overall_ease_of_use_sentiment": "ENUM('Very Intuitive', 'Intuitive', 'Average Learning Curve', 'Complex/Steep Learning Curve', 'Frustrating', 'Not Discussed')",
        "ui_design_critique": "STRING (Comments on the user interface design - aesthetics, layout, IN ENGLISH)",
        "navigation_comments": "STRING (Comments on ease of navigating the software, IN ENGLISH)",
        "onboarding_experience_mention": "STRING (Comments on initial setup or learning process, if any, IN ENGLISH)"
    }},
    "pricing_and_value_perception": {{
        "pricing_model_discussed": "STRING (e.g., 'Subscription per user', 'Tiered plans', 'Usage-based', 'Not Detailed', IN ENGLISH)",
        "price_point_sentiment": "ENUM('Excellent Value', 'Good Value', 'Fair Price', 'Expensive but Justified', 'Overpriced', 'Not Discussed')",
        "value_for_money_assessment": "STRING (Overall comment on value relative to cost/features, IN ENGLISH)",
        "hidden_costs_or_upsells_mentioned": "BOOLEAN"
    }},
    "customer_support_and_resources": {{
        "support_quality_mention": "STRING (Comments on customer support responsiveness/helpfulness, IN ENGLISH)",
        "documentation_quality_mention": "STRING (Comments on help docs, tutorials, community forums, IN ENGLISH)",
        "sentiment": "ENUM('Excellent', 'Good', 'Adequate', 'Poor', 'Not Mentioned')"
    }},
    "implementation_and_customization": {{
        "implementation_complexity_mention": "STRING (Comments on how easy/hard it is to set up/implement, IN ENGLISH)",
        "customization_capabilities_mention": "STRING (Comments on how well it can be tailored to specific needs, IN ENGLISH)",
        "sentiment": "ENUM('Highly Flexible', 'Moderately Flexible', 'Limited Flexibility', 'Rigid', 'Not Mentioned')"
    }},
    "performance_and_reliability": {{
        "speed_and_responsiveness_comments": "STRING (IN ENGLISH)",
        "uptime_or_bug_mentions": "STRING (IN ENGLISH)",
        "sentiment": "ENUM('Excellent', 'Good', 'Acceptable', 'Problematic', 'Not Mentioned')"
    }},
    "comparison_to_alternatives": [
        {{
            "competitor_name": "STRING (IN ENGLISH)",
            "compared_on_aspects": ["STRING (e.g., 'Pricing', 'Specific Feature X', 'Ease of Use', IN ENGLISH)"],
            "comparative_outcome_summary": "STRING ({saas_product_name_placeholder} was considered better/worse/different because..., IN ENGLISH)"
        }}
    ],
    "non_verbal_cues_presenter": {{
        "presenter_type": "ENUM('Likely Vendor Employee', 'Consultant/Expert', 'User', 'Unclear', 'N/A if no clear presenter')",
        "overall_presentation_style": "ENUM('Enthusiastic Demo', 'Objective Analysis', 'Personal Story', 'Formal Presentation', 'Instructional', 'N/A')",
        "confidence_in_statements_visual_tonal": "ENUM('High', 'Medium', 'Low', 'Mixed', 'Not Applicable', 'N/A')",
        "notable_expressions_or_tone_shifts": ["STRING (Describe key moments and perceived meaning, IN ENGLISH)"]
    }},
    "final_recommendation_summary": {{
        "recommendation_level": "ENUM('Highly Recommend', 'Recommend', 'Recommend with Caveats', 'Consider Alternatives', 'Do Not Recommend', 'No Clear Recommendation')",
        "ideal_user_profile_summary": "STRING (Who would benefit most from this SaaS, according to the video, IN ENGLISH)"
    }}
}}
"""