# configs/prompts_consumer.py

# --- Gemini Consumer Product Relevance Check Prompt ---
GEMINI_RELEVANCE_CHECK_PROMPT_TEMPLATE = """
You are an assistant that determines if a YouTube video is a relevant, in-depth review or detailed hands-on analysis suitable for detailed feature extraction for consumer electronics like smartphones or laptops.
Do not consider short news segments, event recaps without product interaction, or very brief impression videos that lack substance for a full review analysis.
However, consider "X Months Later" reviews as relevant if they are substantial.

Video Title: "{video_title}"
Video Description (first 250 chars): "{video_description}"
Product we are interested in: "{product_name_for_relevance}"
Keywords associated with this product search: {product_keywords_for_relevance}

Based ONLY on the title and description, is this video likely to be a detailed review or substantial hands-on analysis of the specified product, suitable for extracting detailed opinions on its features, performance, and non-verbal cues from the reviewer?

Respond with ONLY "YES" or "NO".
"""

# --- Gemini Consumer Product Full Analysis Prompt Configuration ---
# Ensure all textual output within the JSON is requested in ENGLISH
GEMINI_ANALYSIS_PROMPT_TEMPLATE = """
Analyze the provided YouTube video (URL: {video_url}) which is a review of the consumer product: '{product_name}'.
The video may be in any language that you understand.
However, ALL extracted information and your entire response MUST be structured EXCLUSIVELY in JSON format, AND ALL TEXTUAL CONTENT WITHIN THE JSON (e.g., summaries, comments, sentiments, feature names, quotes) MUST BE IN ENGLISH.

Be as specific as possible, basing your analysis ONLY on the content of the video, INCLUDING VISUAL AND AUDITORY CUES from the reviewer.
If a piece of information is not explicitly mentioned or clearly deducible from the video,
use the value null for non-string fields, an empty string \"\" for textual fields (unless specified otherwise for ENUMs), and an empty list [] for list fields.

When analyzing non-verbal cues:
- For 'overall_reviewer_demeanour', assess the reviewer's general attitude and energy throughout the video. PROVIDE THE ENUM VALUE IN ENGLISH.
- For 'notable_facial_expressions', identify up to 3 key moments where facial expressions strongly convey an opinion or reaction. Describe the context AND PROVIDE ALL TEXT IN ENGLISH.
- For 'tone_of_voice_analysis', describe shifts in vocal tone during different segments that indicate enthusiasm, disappointment, sarcasm, etc. PROVIDE ALL TEXT IN ENGLISH.
- For 'gestures_and_body_language', highlight any significant gestures or body language that reinforce or contradict spoken words. PROVIDE ALL TEXT IN ENGLISH.

The requested JSON structure is as follows, AND ALL STRING VALUES WITHIN IT MUST BE IN ENGLISH:
{json_structure_request}
"""

GEMINI_JSON_STRUCTURE_REQUEST = """
{{
    "video_metadata": {{
        "video_url": "{video_url_placeholder}",
        "video_title": "{video_title_placeholder}",
        "channel_name": "{channel_name_placeholder}",
        "product_reviewed": "{product_name_placeholder}"
    }},
    "overall_assessment": {{
        "overall_sentiment": "ENUM('Positive', 'Negative', 'Mixed', 'Neutral')",
        "sentiment_score_numeric": "FLOAT (optional, from -1.0 to 1.0, or null)",
        "summary_review": "STRING (Brief 2-3 sentence summary of the reviewer's conclusion)",
        "key_positive_takeaways": ["STRING (Positive takeaway 1)"],
        "key_negative_takeaways": ["STRING (Negative takeaway 1)"]
    }},
    "feature_analysis": [
        {{
            "feature_name": "STRING (e.g., Camera, Battery, Design, Display, Performance, Software)",
            "sentiment": "ENUM('Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative', 'Mixed', 'Not Mentioned')",
            "specific_comments": "STRING (Specific comments or justifications for the sentiment on this feature)",
            "key_quote_feature": "STRING (Significant quote related to this feature, or empty string)"
        }}
    ],
    "pricing_and_value": {{
        "price_mention": "BOOLEAN (Was the price mentioned?)",
        "price_currency": "STRING (e.g., USD, EUR, or empty string if not mentioned)",
        "price_amount": "FLOAT (numeric price, or null if not mentioned/applicable)",
        "price_sentiment": "ENUM('Positive', 'Negative', 'Neutral', 'Justified', 'Too High', 'Good Value', 'Not Mentioned')",
        "value_for_money_assessment": "STRING (Reviewer's comment on value for money)"
    }},
    "comparison_context": {{
        "vs_previous_generation": {{
            "mentioned": "BOOLEAN",
            "previous_product_name": "STRING (Name of previous gen product, or empty string)",
            "key_differences_highlighted": "STRING (Main differences/improvements/drawbacks vs. previous gen)",
            "overall_comparison_sentiment": "ENUM('Improvement', 'Regression', 'Similar', 'Different but not comparable', 'Not Mentioned')"
        }},
        "vs_competitors": [
            {{
                "competitor_name": "STRING (Name of mentioned competitor)",
                "comparison_points": "STRING (What aspects were compared)",
                "outcome": "STRING (Who performed better on those points, according to the reviewer)"
            }}
        ]
    }},
    "brand_perception": {{
        "brand_sentiment": "ENUM('Positive', 'Negative', 'Neutral', 'Not Mentioned')",
        "brand_related_comments": "STRING (Specific comments about the manufacturer brand)"
    }},
    "target_audience": {{
        "suggested_by_reviewer": "STRING (Who does the reviewer recommend this product to?)"
    }},
    "non_verbal_cues": {{
        "overall_reviewer_demeanour": "ENUM('Enthusiastic', 'Neutral', 'Sceptical', 'Disappointed', 'Excited', 'Measured', 'Professional', 'Casual', 'Not Clear')",
        "demeanour_justification": "STRING (Briefly explain the demeanour choice based on visual/tonal cues)",
        "notable_facial_expressions": [
            {{
                "expression_type": "ENUM('Smile', 'Frown', 'Surprise', 'Raised Eyebrows', 'Eye Roll', 'Neutral', 'Concentration', 'Other')",
                "context_description": "STRING (What was being discussed or shown when this expression occurred?)",
                "perceived_implication": "STRING (What might this expression imply about the reviewer's feeling/opinion on that specific point?)"
            }}
        ],
        "tone_of_voice_analysis": [
            {{
                "segment_description": "STRING (Describe the part of the review this tone applies to, e.g., 'when discussing camera samples', 'during unboxing')",
                "tone_observed": "ENUM('Excited', 'Monotone', 'Sarcastic', 'Genuine', 'Hesitant', 'Confident', 'Frustrated', 'Authoritative', 'Not Clear')",
                "key_tonal_indicators": "STRING (e.g., 'upward inflection', 'fast pace', 'low pitch', 'pauses')"
            }}
        ],
        "gestures_and_body_language": [
            {{
                "gesture_description": "STRING (e.g., 'emphatic hand gestures', 'leaning forward', 'shrugging shoulders', 'nodding frequently')",
                "context_description": "STRING (What was being discussed when this gesture was prominent?)",
                "perceived_implication": "STRING (What might this gesture imply about engagement or conviction?)"
            }}
        ]
    }},
    "additional_elements": {{
        "key_quote_overall_positive": "STRING (A representative overall positive quote, or empty string)",
        "key_quote_overall_negative": "STRING (A representative overall negative quote, or empty string)",
        "notable_mentions": ["STRING (Other noteworthy aspects not covered above)"]
    }}
}}
"""